"""Unit tests for MVP hash travel (sponsor + optional + agent→Snyk leaves)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sneak.merkle import leaf, root, verify
from sneak.mvp_hash_travel import (
    agent_snyk_leaf_record,
    atom_leaf_record,
    build_mvp_travel,
)


class MvpHashTravelTests(unittest.TestCase):
    def test_each_leaf_travels_to_same_mvp_root(self):
        records = [
            atom_leaf_record(
                atom_id="REQ-AOK-M01",
                kind="SponsorMandatoryAtom",
                requirement="Use actual Band Desktop.",
                observed_outcome="NOT_TESTED",
                verified=False,
                tried=True,
                sponsor_digest="abc",
            ),
            atom_leaf_record(
                atom_id="REQ-AOK-S01",
                kind="OptionalBonusAtom",
                requirement="Use a real Snyk scanning product.",
                observed_outcome="NOT_TESTED",
                verified=False,
                tried=True,
                sponsor_digest="def",
            ),
            agent_snyk_leaf_record(
                agent_id="agent-1",
                handle="biobitworks/tom",
                role="architect",
                snyk_binding_digest="snykbind",
                live_snyk="NOT_TESTED",
            ),
        ]
        travel = build_mvp_travel(records, breakpoint_id="TEST-MVP")
        self.assertTrue(travel["mvp_root"])
        self.assertEqual(travel["mmr"], "NOT_COMMITTED")
        self.assertEqual(travel["sponsor_count"], 1)
        self.assertEqual(travel["optional_count"], 1)
        self.assertEqual(travel["agent_snyk_count"], 1)
        self.assertTrue(all(t["verifies_to_mvp_root"] for t in travel["hash_travels"]))
        # Independent recompute
        ordered = sorted(records, key=lambda r: r["id"])
        xs = [leaf(r) for r in ordered]
        self.assertEqual(root(xs).hex(), travel["mvp_root"])
        for i, t in enumerate(
            sorted(travel["hash_travels"], key=lambda x: x["id"])
        ):
            # travels list follows same order as receipt leaves (id ascending)
            pass
        for t in travel["hash_travels"]:
            self.assertTrue(
                verify(bytes.fromhex(t["leaf"]), t["proof"], bytes.fromhex(t["mvp_root"]))
            )


if __name__ == "__main__":
    unittest.main()
