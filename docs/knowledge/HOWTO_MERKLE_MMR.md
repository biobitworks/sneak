# How to: verify and review Merkle and MMR custody in Sneak

Status: IMPLEMENTED, for teammate review. Definitions and math are in `MERKLE_MMR_KNOWLEDGE_BASE.md`. All commands run from the repo root with Python 3.11+ and Node 20+.

## 1. Run the checks (5 minutes)

```
python3 -m unittest discover -s tests -v          # includes tests/test_mmr_reference.py
python3 scripts/custody_snapshot.py verify receipts/repository_bootstrap/SNAPSHOT.json
node scripts/verify_custody_snapshot.mjs receipts/repository_bootstrap/SNAPSHOT.json
python3 scripts/mmr_reference.py                  # prints the 7-leaf / size-11 MMR example
```

Expected result: all tests OK; both verifiers print root `dcabcb5d…` with 167 leaves; the MMR example prints peaks `[6, 9, 10]`.

## 2. Recompute one leaf by hand

```
python3 - <<'EOF'
import json, hashlib
rc = json.load(open("receipts/repository_bootstrap/SNAPSHOT.json"))
item = rc["leaves"][0]
rec = item["record"]
data = open(rec["path"], "rb").read()                    # 1. the file's bytes
assert hashlib.sha256(data).hexdigest() == rec["sha256"]  # 2. content hash
canon = json.dumps(rec, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
assert canon.hex() == item["canonical_hex"]               # 3. canonical record bytes
leaf = hashlib.sha256(b"\x00" + canon).hexdigest()
assert leaf == item["leaf"]                               # 4. leaf = H(0x00 || canonical)
print("leaf ok", leaf)
EOF
```

If step 1 fails, your working copy differs from the snapshot commit. Check out `snapshot_commit` first, or read the bytes with `git show <commit>:<path>`.

## 3. Verify an inclusion proof by hand

```
python3 - <<'EOF'
import json, hashlib
rc = json.load(open("receipts/repository_bootstrap/SNAPSHOT.json"))
item = rc["leaves"][42]
v = bytes.fromhex(item["leaf"])
for step in item["proof"]:
    s = bytes.fromhex(step["hash"])
    v = hashlib.sha256(b"\x01" + (s + v if step["side"] == "left" else v + s)).digest()
print(len(item["proof"]), "steps; matches root:", v.hex() == rc["root"])
EOF
```

You should see 8 steps (⌈log₂ 167⌉ = 8) and `True`.

## 4. Try to break it (the red-team habit)

Copy the receipt, change one thing, and confirm **both** verifiers reject it:

| Tamper | Expected |
|---|---|
| one byte of a tracked file | REJECT |
| one leaf hash, one record sha256, or the root | REJECT |
| swap two leaves, or flip one proof side | REJECT |
| delete a leaf and decrement `leaf_count` | REJECT |
| set `"signed": true` or `"mmr": "COMMITTED"` | **currently ACCEPT**: known defect RT-03 (PR #4) |

Work on a copy or a throwaway clone, never on committed receipts.

## 5. Use the reference MMR

```
python3 - <<'EOF'
import sys; sys.path.insert(0, "scripts")
import mmr_reference as R
m = R.MMR()
for i in range(7):
    m.append(f"leaf-{i}".encode())
p = m.proof(3)                                   # proof for the 4th leaf
print("size", m.size, "peaks", R.peaks(m.size))
print("verifies:", R.mmr_verify(b"leaf-3", p, m.root()))
print("forged:", R.mmr_verify(b"leaf-X", p, m.root()))
EOF
```

Useful helpers: `R.height(pos)`, `R.peaks(size)`, `R.size_for_leaves(n)`, `R.valid_size(size)`.

## 6. Reviewer checklist for any custody or MMR receipt

- [ ] Hash function, canonical encoding, leaf and node prefixes, ordering and odd-node rule are written in the receipt.
- [ ] Leaves are computed from bytes at a named Git commit, not "whatever is on disk".
- [ ] Recomputed independently: a second implementation, ideally in another language, gets the same root.
- [ ] Every inclusion proof verifies, and tampered copies are rejected (§4).
- [ ] The receipt cannot include itself: it is a subsequent artifact, and it says so.
- [ ] For an MMR: the size is valid (`R.valid_size`), there are popcount(n) peaks, positions are committed in hashes, and the size is committed in bagging.
- [ ] No overclaim: a matching root means integrity only. Not truth, rights, signature, time or MMR commitment unless separately evidenced.
- [ ] State words are used exactly (PROPOSED, IMPLEMENTED, EXECUTED, OBSERVED, SUPPORTED, FAILED, NEGATIVE, NOT_TESTED, UNKNOWN, NOT_COMPUTED).

## 7. Common mistakes

- **Hashing pretty-printed JSON.** Whitespace changes the hash; use the canonical form.
- **Sorting by Unicode string instead of UTF-8 bytes.** These differ for non-ASCII paths; Sneak requires ASCII paths.
- **Duplicating the odd node.** This creates the CVE-2012-2459 ambiguity; Sneak promotes it instead.
- **Dropping the 0x00/0x01 prefixes.** This allows the second-preimage forgery shown in the tests.
- **Calling a snapshot Merkle root an "MMR".** It isn't one; see knowledge base §4.8 for the criteria.
- **Mixing 0- and 1-based MMR positions.** Grin's wiki uses both; the reference code is 0-based throughout.

## 8. Submitting your review

Comment on the PR. If you add material (e.g. a consistency-proof implementation), commit it and mint it as an FCO:
`python3 scripts/contribution_fco.py mint --contributor <handle> --kind code --title "..." --commit HEAD --path <files>`
