"""Unit tests for Cognee-over-time custody chain scoring (no live network)."""

from __future__ import annotations

import unittest

from sneak.cognee_custody_chain import (
    CUSTODY_EPOCHS,
    chain_summary,
    custody_event_records,
    match_markers,
    score_epoch,
)
from sneak.merkle import breakpoint_receipt, verify


class CogneeCustodyChainTests(unittest.TestCase):
    def test_epochs_include_known_gap_029(self):
        ids = [e["id"] for e in CUSTODY_EPOCHS]
        self.assertIn("SNEAK-015", ids)
        self.assertIn("SNEAK-024", ids)
        self.assertIn("SNEAK-029", ids)
        e029 = next(e for e in CUSTODY_EPOCHS if e["id"] == "SNEAK-029")
        self.assertIn("BAND", e029["expected_gap_reason"])

    def test_match_markers_majority(self):
        m = match_markers(
            "sneak-024-conversation-custody BP-sneak024",
            ["NO-SUCH-MARKER", "BP-sneak024", "sneak-024-conversation-custody"],
        )
        self.assertTrue(m["captured"])
        self.assertEqual(m["missing"], ["NO-SUCH-MARKER"])

    def test_score_gap_and_capture(self):
        epoch = next(e for e in CUSTODY_EPOCHS if e["id"] == "SNEAK-029")
        miss = score_epoch(epoch, hits=[], search_ok=True, mvp_root="8d1036e3deadbeef")
        self.assertFalse(miss["captured"])
        self.assertIsNotNone(miss["gap_reason"])

        hit = score_epoch(
            epoch,
            hits=[
                {
                    "text": (
                        "sneak-029-mvp-hash-travel SNEAK-029 mvp_root="
                        "8d1036e3bbaa64231dee0e0873a5f3e040192a14752967b5f9526d18ab5dc6ef"
                    )
                }
            ],
            search_ok=True,
            mvp_root="8d1036e3bbaa64231dee0e0873a5f3e040192a14752967b5f9526d18ab5dc6ef",
        )
        self.assertTrue(hit["captured"])
        self.assertIsNone(hit["gap_reason"])

    def test_chain_summary_and_merkle_breakpoint(self):
        epochs = [
            score_epoch(
                next(e for e in CUSTODY_EPOCHS if e["id"] == "SNEAK-015"),
                hits=[{"text": "SNEAK-015 live-block-eval-must-deny block-eval"}],
                search_ok=True,
            ),
            score_epoch(
                next(e for e in CUSTODY_EPOCHS if e["id"] == "SNEAK-029"),
                hits=[],
                search_ok=True,
                mvp_root="8d1036e3",
            ),
        ]
        summary = chain_summary(epochs)
        self.assertEqual(summary["captured_count"], 1)
        self.assertEqual(summary["gap_count"], 1)
        self.assertFalse(summary["continuous_chain"])
        self.assertEqual(summary["mmr"], "NOT_COMMITTED")

        records = custody_event_records(epochs)
        bp = breakpoint_receipt(
            schema="sneak.cognee_custody_chain.v1",
            breakpoint_id="SNEAK-030",
            parent_id="SNEAK-029",
            records=records,
            meaning="test custody chain",
        )
        self.assertEqual(bp["leaf_count"], 2)
        self.assertEqual(bp["mmr"], "NOT_COMMITTED")
        self.assertFalse(bp["signed"])
        for leaf in bp["leaves"]:
            self.assertTrue(
                verify(
                    bytes.fromhex(leaf["leaf"]),
                    leaf["proof"],
                    bytes.fromhex(bp["root"]),
                )
            )


if __name__ == "__main__":
    unittest.main()
