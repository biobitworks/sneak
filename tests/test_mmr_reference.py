"""Checks every identity cited in docs/knowledge/MERKLE_MMR_KNOWLEDGE_BASE.md."""
import hashlib, json, math, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import mmr_reference as R  # noqa: E402

H = R.H
leafs = lambda n: [H(b"\x00" + f"d{i}".encode()) for i in range(n)]


class MerkleTests(unittest.TestCase):
    def test_reproduces_repo_snapshot_root(self):
        rc = json.loads((ROOT / "receipts/repository_bootstrap/SNAPSHOT.json").read_text())
        leaves = [bytes.fromhex(x["leaf"]) for x in rc["leaves"]]
        self.assertEqual(R.merkle_root(leaves).hex(), rc["root"])
        # leaf = H(0x00 || canonical record) as documented
        first = rc["leaves"][0]
        self.assertEqual(H(b"\x00" + bytes.fromhex(first["canonical_hex"])).hex(), first["leaf"])

    def test_promotion_equals_rfc6962_split(self):
        for n in range(1, 1025):
            xs = leafs(n)
            self.assertEqual(R.merkle_root(xs), R.merkle_root_rfc6962(xs), n)

    def test_proofs_verify_and_length_bound(self):
        for n in range(1, 130):
            xs, root = leafs(n), R.merkle_root(leafs(n))
            lengths = []
            for i in range(n):
                p = R.merkle_proof(xs, i)
                self.assertTrue(R.merkle_verify(xs[i], p, root))
                lengths.append(len(p))
            self.assertEqual(max(lengths), math.ceil(math.log2(n)) if n > 1 else 0, n)

    def test_tamper_rejected(self):
        xs = leafs(9); root = R.merkle_root(xs); p = R.merkle_proof(xs, 4)
        self.assertFalse(R.merkle_verify(H(b"x"), p, root))
        flipped = [("left" if s == "right" else "right", h) for s, h in p]
        self.assertFalse(R.merkle_verify(xs[4], flipped, root))

    def test_second_preimage_needs_domain_separation(self):
        h = lambda b: hashlib.sha256(b).digest()
        d = [f"d{i}".encode() for i in range(4)]

        def naive_root(data):  # leaf = h(d), parent = h(l||r): no prefixes
            row = [h(x) for x in data]
            while len(row) > 1:
                row = [h(row[i] + row[i + 1]) for i in range(0, len(row), 2)]
            return row[0]

        def sep_root(data):    # Sneak: leaf = h(0x00||d), parent = h(0x01||l||r)
            return R.merkle_root([h(b"\x00" + x) for x in data])

        L = [h(x) for x in d]
        forged = [L[0] + L[1], L[2] + L[3]]          # two "documents" that are really internal nodes
        self.assertEqual(naive_root(d), naive_root(forged))      # attack succeeds without prefixes
        Ls = [h(b"\x00" + x) for x in d]
        forged_sep = [Ls[0] + Ls[1], Ls[2] + Ls[3]]
        self.assertNotEqual(sep_root(d), sep_root(forged_sep))   # prefixes defeat it

    def test_duplicate_last_node_mutation(self):
        a, b, c = leafs(3)
        dup = lambda row: row + [row[-1]] if len(row) % 2 else row
        def btc(row):  # Bitcoin-style: duplicate the odd node
            while len(row) > 1:
                row = dup(row)
                row = [H(b"\x01" + row[i] + row[i + 1]) for i in range(0, len(row), 2)]
            return row[0]
        self.assertEqual(btc([a, b, c]), btc([a, b, c, c]))            # CVE-2012-2459 shape
        self.assertNotEqual(R.merkle_root([a, b, c]), R.merkle_root([a, b, c, c]))  # promotion


class MMRTests(unittest.TestCase):
    def test_size_peaks_heights_identities(self):
        m = R.MMR()
        for n in range(1, 1025):
            m.append(f"x{n}".encode())
            self.assertEqual(m.size, R.size_for_leaves(n))
            pk = R.peaks(m.size)
            self.assertEqual(len(pk), bin(n).count("1"))
            self.assertEqual([R.height(p) for p in pk],
                             [i for i in range(n.bit_length() - 1, -1, -1) if n >> i & 1])
            self.assertTrue(R.valid_size(m.size))

    def test_grin_examples(self):
        # Size 4 (3 leaves): heights 0,0,1,0; peaks at positions 2 and 3.
        self.assertEqual([R.height(p) for p in range(4)], [0, 0, 1, 0])
        self.assertEqual(R.peaks(4), [2, 3])
        # Size 11 (7 leaves): peaks 7,10,11 in 1-based numbering = 6,9,10 in 0-based.
        self.assertEqual([R.height(p) for p in range(11)], [0, 0, 1, 0, 0, 1, 2, 0, 0, 1, 0])
        self.assertEqual([p + 1 for p in R.peaks(11)], [7, 10, 11])

    def test_navigation_formulas(self):
        for pos in range(2000):
            h = R.height(pos)
            if h > 0:  # left child = pos - 2^h ; right child = pos - 1
                self.assertEqual(R.height(pos - (1 << h)), h - 1)
                self.assertEqual(R.height(pos - 1), h - 1)
            # right sibling of a left child is pos + 2^(h+1) - 1 and has the same height
            if R.height(pos + 1) <= h:
                self.assertEqual(R.height(pos + (1 << (h + 1)) - 1), h)

    def test_invalid_sizes(self):
        valid = {R.size_for_leaves(n) for n in range(1, 300)}
        for s in range(1, 500):
            self.assertEqual(R.valid_size(s), s in valid, s)

    def test_proofs_and_tamper(self):
        m = R.MMR()
        for n in range(1, 70):
            m.append(f"leaf{n}".encode())
            root = m.root()
            for i in range(n):
                p = m.proof(i)
                self.assertTrue(R.mmr_verify(f"leaf{i + 1}".encode(), p, root))
                self.assertEqual(len(p["path"]), R.height(p["peak_pos"]))
        p = m.proof(10)
        self.assertFalse(R.mmr_verify(b"forged", p, m.root()))
        bad = dict(p, leaf_pos=p["leaf_pos"] + 1)
        self.assertFalse(R.mmr_verify(b"leaf11", bad, m.root()))

    def test_append_only_history(self):
        m = R.MMR()
        for n in range(1, 40):
            before = list(m.nodes)
            m.append(f"y{n}".encode())
            self.assertEqual(m.nodes[:len(before)], before)  # appending never rewrites old nodes


if __name__ == "__main__":
    unittest.main()
