import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / "src"))
from sneak.cognee_client import CogneeClient

class FakeResponse:
    status=200
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,n): return b'{"status":"ok"}'

class CogneeClientTests(unittest.TestCase):
    def test_non_https_remote_rejected(self):
        with self.assertRaises(ValueError):
            CogneeClient("http://public.example",api_key="test-only")
    def test_loopback_allowed(self):
        self.assertEqual(CogneeClient("http://127.0.0.1:18000",api_key=None).base,"http://127.0.0.1:18000")
    @patch("urllib.request.urlopen")
    def test_file_upload_contract(self,open_mock):
        open_mock.return_value=FakeResponse()
        c=CogneeClient("https://example.invalid",api_key="test-only")
        self.assertEqual(c.add_text("synthetic only","demo")["http_status"],200)
        req=open_mock.call_args[0][0]
        self.assertIn(b'filename="synthetic-review.txt"',req.data)
        self.assertIn(b'name="datasetName"',req.data)
        self.assertIn(b'synthetic only',req.data)
        self.assertNotIn(b'test-only',req.data)
    @patch("urllib.request.urlopen")
    def test_search_camelcase_contract(self,open_mock):
        open_mock.return_value=FakeResponse()
        c=CogneeClient("https://example.invalid",api_key="test-only")
        c.search("What next?","demo")
        req=open_mock.call_args[0][0]
        self.assertEqual(json.loads(req.data)["searchType"],"CHUNKS")
        self.assertEqual(json.loads(req.data)["datasets"],["demo"])
if __name__=="__main__":unittest.main()
