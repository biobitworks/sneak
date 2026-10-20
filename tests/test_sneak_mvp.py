import copy
import http.client
import json
import pathlib
import tempfile
import threading
import unittest

from apps.sneak_mvp import REPO_ROOT
from apps.sneak_mvp import aok, graph, snyk_adapter
from apps.sneak_mvp.server import make_server

SPEC = REPO_ROOT / 'apps/sneak_mvp/fixtures/aok_spec.json'


class AoKTests(unittest.TestCase):
    def test_same_canonical_bytes_deterministic(self):
        x = {'b': [1, 2], 'a': {'z': True, 'a': None}}
        y = {'a': {'a': None, 'z': True}, 'b': [1, 2]}
        self.assertEqual(aok.canonical(x), aok.canonical(y))
        spec = aok.load_json(SPEC)
        self.assertEqual(aok.canonical(aok.build(spec, REPO_ROOT)), aok.canonical(aok.build(spec, REPO_ROOT)))

    def test_tampered_evidence_rejected(self):
        b = aok.build(aok.load_json(SPEC), REPO_ROOT)
        self.assertTrue(aok.verify(b, REPO_ROOT)['pass'])
        bad = copy.deepcopy(b)
        bad['leaves'][0]['record']['claim']['text'] = 'tampered'
        self.assertFalse(aok.verify(bad, REPO_ROOT)['pass'])
        bad = copy.deepcopy(b)
        bad['leaves'][0]['record']['source']['sha256'] = '0' * 64
        self.assertFalse(aok.verify(bad, REPO_ROOT)['pass'])

    def test_source_bytes_change_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'a.txt').write_text('before')
            source = aok.hash_source(root, 'a.txt')
            (root / 'a.txt').write_text('after')
            self.assertNotEqual(source, aok.hash_source(root, 'a.txt'))


class ScanTests(unittest.TestCase):
    def test_bad_json_blocks(self):
        c = snyk_adapter.classify(0, b'{bad')
        self.assertEqual(c['outcome'], 'ERROR')
        self.assertEqual(snyk_adapter.gate(c, {'dirty': False, 'commit': 'a'}), 'BLOCKED')

    def test_exit_over_one_blocks(self):
        c = snyk_adapter.classify(2, b'{"error":"failure"}')
        self.assertEqual(c['outcome'], 'ERROR')
        self.assertEqual(snyk_adapter.gate(c, {'dirty': False, 'commit': 'a'}), 'BLOCKED')

    def test_incomplete_json_blocks(self):
        for data in (b'{}', b'{"ok":true}', b'{"runs":[]}', b'[]'):
            with self.subTest(data=data):
                self.assertEqual(snyk_adapter.classify(0, data)['outcome'], 'ERROR')

    def test_valid_findings_block(self):
        data = b'{"ok":false,"vulnerabilities":[{"id":"x","severity":"high"}]}'
        c = snyk_adapter.classify(1, data)
        self.assertEqual(c['outcome'], 'FINDINGS')
        self.assertEqual(snyk_adapter.gate(c, {'dirty': False, 'commit': 'a'}), 'BLOCKED')

    def test_clean_result_requires_clean_target(self):
        c = snyk_adapter.classify(0, b'{"ok":true,"vulnerabilities":[]}')
        self.assertEqual(c['outcome'], 'NO_ISSUES')
        self.assertEqual(snyk_adapter.gate(c, {'dirty': True, 'commit': 'a'}), 'BLOCKED')


class GraphHttpTests(unittest.TestCase):
    def test_graph_and_audit(self):
        g = graph.build_graph()
        self.assertTrue(g['integrity']['pass'])
        self.assertEqual(g['aok']['leaf_count'], 9)
        self.assertTrue(g['edges'])
        a = graph.build_audit()
        self.assertEqual(a['mandatory_total'], 30)
        self.assertEqual(a['mandatory_verified'], 0)
        self.assertFalse(a['entry_gate'])

    def test_http_endpoints_and_host_guard(self):
        srv = make_server(port=0)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            port = srv.server_address[1]
            for path in ('/', '/audit', '/static/style.css', '/api/graph', '/api/audit'):
                with self.subTest(path=path):
                    c = http.client.HTTPConnection('127.0.0.1', port)
                    c.request('GET', path)
                    r = c.getresponse()
                    body = r.read()
                    self.assertEqual(r.status, 200)
                    self.assertTrue(body)
                    if path.startswith('/api/'):
                        self.assertIsInstance(json.loads(body), dict)
                    c.close()
            c = http.client.HTTPConnection('127.0.0.1', port)
            c.request('GET', '/api/graph', headers={'Host': 'evil.example'})
            self.assertEqual(c.getresponse().status, 403)
            c.close()
        finally:
            srv.shutdown()
            srv.server_close()
            t.join()


if __name__ == '__main__':
    unittest.main()
