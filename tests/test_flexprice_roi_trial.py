import json
import sys
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.flexprice_roi_trial import FIXTURE, canonical, digest, measure, send_events

class Handler(BaseHTTPRequestHandler):
    events=[]
    def log_message(self, *args):
        pass
    def do_POST(self):
        assert self.path == "/v1/events"
        assert self.headers.get("x-api-key") == "mock-only-key"
        value=json.loads(self.rfile.read(int(self.headers.get("Content-Length"))))
        Handler.events.append(value)
        self.send_response(202)
        self.send_header("Content-Type","application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"accepted"}')

class TestROI(unittest.TestCase):
    def setUp(self):
        self.source=json.loads(FIXTURE.read_text())
    def test_reproducible_receipt(self):
        x=measure(self.source)
        self.assertEqual(canonical(x),canonical(measure(self.source)))
        self.assertEqual(x["receipt_sha256"],digest({k:v for k,v in x.items() if k!="receipt_sha256"}))
        self.assertEqual(x["status"],"SIMULATED_NOT_OBSERVED")
        self.assertEqual(x["live_flexprice_metering"],"NOT_TESTED")
    def test_per_agent_model_human_attribution(self):
        x=measure(self.source)
        self.assertEqual(x["task_count"],2)
        self.assertEqual(x["metrics"]["baseline"]["tokens"],8000)
        self.assertEqual(x["metrics"]["sneak"]["tokens"],5000)
        self.assertEqual(x["token_reduction_fraction"],"0.375000")
        for scenario in ["baseline","sneak"]:
            self.assertEqual(len(x["metrics"][scenario]["agents"]),3)
            self.assertEqual(len(x["metrics"][scenario]["models"]),3)
            self.assertEqual(len(x["metrics"][scenario]["humans"]),2)
        self.assertEqual(len({e["event_id"] for e in x["events"]}),6)
        self.assertTrue(all(e["properties"]["evidence_class"]=="SIMULATED_NOT_OBSERVED" for e in x["events"]))
    def test_reject_unfair_comparison(self):
        self.source["rows"][-1]["task_id"]="different"
        with self.assertRaises(ValueError):
            measure(self.source)
    def test_local_mock_202_is_not_live_billing(self):
        Handler.events=[]
        server=HTTPServer(("127.0.0.1",0),Handler)
        thread=Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            events=measure(self.source)["events"]
            receipt=send_events(events,f"http://127.0.0.1:{server.server_port}/v1","mock-only-key")
            self.assertEqual(len(receipt),6)
            self.assertEqual([e["event_id"] for e in Handler.events],[e["event_id"] for e in events])
            self.assertTrue(all(v["http_status"]==202 for v in receipt))
        finally:
            server.shutdown()
            server.server_close()

if __name__ == "__main__":
    unittest.main()
