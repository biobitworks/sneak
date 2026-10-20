"""Unit tests for live clients with network disabled (fake unavailable)."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.band_client import BandClient
from sneak.cognee_client import CogneeClient
from sneak.secrets import presence_receipt


class LiveClientUnitTests(unittest.TestCase):
    def test_cognee_unavailable_without_env(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            # Ensure secrets file path does not leak into this test if present:
            c = CogneeClient(base_url="", api_key="")
            self.assertFalse(c.available)

    def test_band_unavailable_without_key(self):
        c = BandClient(api_key="")
        self.assertFalse(c.available)

    def test_presence_receipt_never_includes_values(self):
        r = presence_receipt()
        # Only key names / paths / modes — never secret material.
        for k in ("keys_present", "env_overrides_present", "path_configured"):
            self.assertIn(k, r)
        self.assertFalse(r.get("value_inspected"))
        joined = " ".join(r.get("keys_present") or [])
        self.assertNotIn("=", joined)


if __name__ == "__main__":
    unittest.main()
