"""Tests for scripts/breakpoint_ledger.py (uses a temporary ledger, never the project one)."""
import json, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import breakpoint_ledger as B  # noqa: E402

Z = "0" * 64


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="bp-test-"))
        self.path, self.box = self.tmp / "ledger.jsonl", self.tmp / "outbox"
        self.L = B.Ledger(self.path, self.box)
        self.rq = self.L.root_question("How many?", r"\b30\b", Z)

    def step(self, rnd, text, parent=None, stream="model:a"):
        return self.L.step(self.rq["bp_id"], stream, rnd, "model_call", Z, Z, B.sha(text.encode()),
                           output_text=text, parent_bp=parent or self.rq["bp_id"], tokens={"total_tokens": 7}, model="a")

    def test_ids_recompute_and_verify(self):
        self.step(1, "It is 30.")
        r = B.verify(self.path)
        self.assertTrue(r["pass"], r["errors"]); self.assertEqual(r["entries"], 2)
        self.assertRegex(self.rq["bp_id"], r"^BP-[0-9a-f]{16}$")

    def test_breakpoint_true_false_and_deltas(self):
        a = self.step(1, "maybe 12")
        b = self.step(2, "30", parent=a["bp_id"])
        c = self.step(3, "30", parent=b["bp_id"])
        self.assertEqual([a["identity"]["breakpoint"], b["identity"]["breakpoint"]], [False, True])
        d = self.L.deltas(self.rq["bp_id"])["model:a"]
        self.assertEqual([x["delta"] for x in d], ["FIRST", "TURNED_TRUE", "SAME"])
        # a different step in the same round must not be compared with model_call
        self.L.step(self.rq["bp_id"], "model:a", 1, "normalize_answer", Z, Z, B.sha(b"12"), output_text="12", parent_bp=a["bp_id"], model="a")
        n = [x for x in self.L.deltas(self.rq["bp_id"])["model:a"] if x["step"] == "normalize_answer"]
        self.assertEqual(n[0]["delta"], "FIRST")
        self.assertEqual(c["identity"]["output_sha256"], b["identity"]["output_sha256"])

    def test_same_text_different_source_is_unique(self):
        m1 = self.L.message("band", "room1", "msg-1", "tom", "hello")
        m2 = self.L.message("band", "room1", "msg-2", "tom", "hello")
        m3 = self.L.message("band", "room1", "msg-3", "tom", "hello", parent_bp=m1["bp_id"])
        self.assertEqual(len({m1["bp_id"], m2["bp_id"], m3["bp_id"]}), 3)

    def test_idempotent_replay_no_duplicate_outbox(self):
        self.step(1, "30"); self.step(1, "30")
        self.assertEqual(B.verify(self.path)["entries"], 2)
        flex = (self.box / "flexprice.jsonl").read_text().splitlines()
        self.assertEqual(len(flex), 1)

    def test_parent_and_root_must_exist(self):
        with self.assertRaises(ValueError):
            self.L.message("band", "r", "s", "x", "t", parent_bp="BP-0000000000000000")
        with self.assertRaises(ValueError):
            self.L.step("BP-0000000000000000", "m", 1, "s", Z, Z, Z)

    def test_output_text_must_match_hash(self):
        with self.assertRaises(ValueError):
            self.L.step(self.rq["bp_id"], "m", 1, "s", Z, Z, Z, output_text="30")

    def test_tamper_detected(self):
        self.step(1, "30")
        lines = self.path.read_text().splitlines()
        row = json.loads(lines[1]); row["identity"]["breakpoint"] = False
        lines[1] = json.dumps(row); self.path.write_text("\n".join(lines) + "\n")
        self.assertFalse(B.verify(self.path)["pass"])

    def test_global_and_stream_mmr_sizes(self):
        self.step(1, "30", stream="model:a"); self.step(1, "30", stream="model:b")
        self.L.link("commit", "abc", note="x")
        v = B.verify(self.path)
        self.assertTrue(v["pass"])
        self.assertEqual(v["streams"], {"root": 1, "model:a": 1, "model:b": 1, "links": 1})
        import mmr_reference as M
        self.assertEqual(self.L.global_mmr.size, M.size_for_leaves(4))

    def test_reload_reproduces_roots(self):
        self.step(1, "30"); self.L.message("chat", "c", "1", "byron", "hi")
        again = B.Ledger(self.path, self.box)
        self.assertEqual(again.global_mmr.root(), self.L.global_mmr.root())


if __name__ == "__main__":
    unittest.main()
