import copy
import http.client
import json
import pathlib
import tempfile
import threading
import unittest
from unittest import mock

from apps.sneak_mvp import graph, integration_graph
from apps.sneak_mvp.server import make_server

class TeammateImportTests(unittest.TestCase):
    def test_imported_file_identities(self):
        r=integration_graph.imported_files()
        self.assertTrue(r["verified"],r.get("errors"))
        self.assertGreaterEqual(r["file_count"],100)
        self.assertEqual(r["mmr"],"NOT_COMPUTED")

    def test_merkle_tamper_rejected(self):
        data=integration_graph.read(integration_graph.MANIFEST)
        self.assertEqual(integration_graph.root_for(data["records"]),data["root"])
        tampered=copy.deepcopy(data)
        tampered["records"][0]["sha256"]="0"*64
        self.assertNotEqual(integration_graph.root_for(tampered["records"]),data["root"])
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/"tampered.json"
            p.write_text(json.dumps(tampered))
            with mock.patch.object(integration_graph,"MANIFEST",p):
                self.assertFalse(integration_graph.imported_files()["verified"])

    def test_stack_does_not_promote_unsupported_claims(self):
        x=integration_graph.stack()
        self.assertEqual(x["release_gate"],"BLOCKED")
        self.assertEqual(x["band"]["live_desktop"],"NOT_VERIFIED")
        self.assertEqual(x["cognee"]["band_action_dispatch"],"NOT_EXECUTED")
        self.assertNotEqual(x["snyk"]["gate"],"PASS")
        g=graph.build_graph()
        self.assertTrue(g["integrity"]["pass"])
        self.assertIn("IMPORT-TEAM",{n["id"] for n in g["nodes"]})
        self.assertEqual(graph.build_audit()["mandatory_verified"],0)

    def test_api_read_only_integration(self):
        srv=make_server(port=0)
        th=threading.Thread(target=srv.serve_forever,daemon=True);th.start()
        try:
            with mock.patch.object(integration_graph,"live_check",return_value={"band":{"runtime_account":"NOT_AUTHENTICATED"},"release_gate":"BLOCKED"}):
                # API map binds the function at import time; patch that callable as well.
                from apps.sneak_mvp import server
                with mock.patch.dict(server.API,{"/api/check":integration_graph.live_check}):
                    for p in ("/api/stack","/api/check"):
                        c=http.client.HTTPConnection("127.0.0.1",srv.server_address[1],timeout=3)
                        c.request("GET",p)
                        r=c.getresponse();data=json.loads(r.read())
                        self.assertEqual(r.status,200)
                        self.assertEqual(data["release_gate"],"BLOCKED")
                        c.close()
        finally:
            srv.shutdown();srv.server_close();th.join()

if __name__=="__main__":
    unittest.main()
