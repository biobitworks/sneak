"""Repeatable export-contract tests; no network, account data, or live Vercel claims."""
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from scripts import build_vercel_preview as preview


class VercelProjectionTests(unittest.TestCase):
    def test_repeated_export_identical_bytes(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            x = preview.generate(pathlib.Path(a))
            y = preview.generate(pathlib.Path(b))
            self.assertEqual(x["outputs_sha256"], y["outputs_sha256"])
            self.assertEqual(x["aok_candidate_root"], y["aok_candidate_root"])
            self.assertEqual((pathlib.Path(a)/"EXPORT_MANIFEST.json").read_bytes(),
                             (pathlib.Path(b)/"EXPORT_MANIFEST.json").read_bytes())

    def test_offline_gate_and_sanitized_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            receipt = preview.generate(base)
            graph = json.loads((base/"data/graph.json").read_text())
            audit = json.loads((base/"data/audit.json").read_text())
            self.assertEqual(graph["scan"]["gate"], "BLOCKED")
            self.assertEqual(graph["deployment"]["lomo"], "NOT_COMPUTED")
            self.assertEqual(graph["deployment"]["mmr"], "NOT_COMPUTED")
            self.assertEqual(audit["mandatory_verified"], 0)
            self.assertFalse(audit["entry_gate"])
            self.assertFalse(graph["deployment"]["api_live"])
            self.assertFalse(graph["deployment"]["cognee_live"])
            self.assertFalse(graph["deployment"]["band_live"])
            for node in graph["nodes"]:
                self.assertFalse(set(node) & {"source", "actor", "api_key", "token"})
            self.assertEqual(receipt["export_merkle_root"], "NOT_COMPUTED")
            self.assertIs(receipt["signed"], False)

    def test_static_assets_and_routes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            preview.generate(base)
            config = json.loads((base/"vercel.json").read_text())
            routes = {r["source"]: r["destination"] for r in config["rewrites"]}
            self.assertEqual(routes["/api/graph"], "/data/graph.json")
            self.assertEqual(routes["/api/audit"], "/data/audit.json")
            for path in ("index.html", "audit.html", "heatmap.html", "static/app.js", "static/audit.js", "static/style.css", "static/heatmap.js", "static/heatmap.css"):
                self.assertTrue((base / path).is_file())
            self.assertIn(b"PROTECTED VERCEL SNAPSHOT", (base / "index.html").read_bytes())
            self.assertIn(b"Disallow: /", (base/"robots.txt").read_bytes())

    def test_verifier_fail_closed(self):
        with patch.object(preview, "build_graph", return_value={
                "integrity": {"pass": False, "errors": ["tampered"]}}):
            with self.assertRaisesRegex(ValueError, "verification failed"):
                preview.snapshot()


if __name__ == "__main__":
    unittest.main()
