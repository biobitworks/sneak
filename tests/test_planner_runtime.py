"""Unit tests for planner credential loading and adapter construction."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.planner_runtime import (
    PLAN_TRACK_REPLY,
    build_planner_adapter,
    load_planner_credentials,
    planner_presence_receipt,
)


class PlannerRuntimeTests(unittest.TestCase):
    def test_presence_receipt_never_includes_secrets(self):
        r = planner_presence_receipt(online=True, connection_status="connected")
        blob = str(r).lower()
        self.assertNotIn("band_a_", blob)
        self.assertFalse(r["value_inspected"])
        self.assertTrue(r["online"])

    def test_load_credentials_from_yaml(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "cfg.yaml"
            path.write_text(
                "planner:\n  agent_id: aaa-bbb\n  api_key: secret-value-xyz\n",
                encoding="utf-8",
            )
            env = {
                k: v
                for k, v in __import__("os").environ.items()
                if k not in ("BAND_PLANNER_AGENT_ID", "BAND_PLANNER_API_KEY")
            }
            with mock.patch.dict("os.environ", env, clear=True):
                with mock.patch(
                    "sneak.planner_runtime.export_to_environ", return_value=[]
                ):
                    agent_id, api_key = load_planner_credentials(path)
            self.assertEqual(agent_id, "aaa-bbb")
            self.assertEqual(api_key, "secret-value-xyz")

    def test_plan_track_reply_keeps_done_false(self):
        self.assertIn("Done = FALSE", PLAN_TRACK_REPLY)
        self.assertIn("NOT_COMMITTED", PLAN_TRACK_REPLY)
        self.assertIn("human-pending", PLAN_TRACK_REPLY)

    def test_build_adapter_without_starting(self):
        try:
            import band  # noqa: F401
        except ImportError:
            self.skipTest("band-sdk not installed")
        adapter = build_planner_adapter()
        self.assertEqual(adapter.replies_sent, 0)
        self.assertTrue(hasattr(adapter, "on_message"))


if __name__ == "__main__":
    unittest.main()
