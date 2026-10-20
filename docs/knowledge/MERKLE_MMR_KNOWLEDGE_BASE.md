# Knowledge base: Merkle trees and Merkle Mountain Ranges (MMR)

Status: IMPLEMENTED, for teammate review. Every identity marked **[tested]** is checked by `tests/test_mmr_reference.py` against `scripts/mmr_reference.py`. "Tested" means checked over the stated range, not mathematically proven. Practical steps are in `HOWTO_MERKLE_MMR.md`.

Conventions: H = SHA-256 (32-byte output), `||` = byte concatenation, positions are **0-based** unless marked 1-based, integers in hashes are 8-byte big-endian.

---

## 1. Definitions

| Term | Definition |
|---|---|
| **Hash function H** | Maps any byte string to a fixed-size digest (32 bytes for SHA-256). Deterministic and fast to compute. |
| **Preimage resistance** | Given a digest y, it is infeasible to find any x with H(x) = y. |
| **Second-preimage resistance** | Given x, it is infeasible to find x' ≠ x with H(x') = H(x). |
| **Collision resistance** | It is infeasible to find *any* x ≠ x' with H(x) = H(x'). The property Merkle proofs rely on. |
| **Canonical encoding** | One agreed byte representation per record. Sneak uses ASCII JSON, sorted keys, `ensure_ascii`, compact separators, no trailing newline. Without it, the same record can hash two ways. |
| **Domain separation** | A prefix byte that tags *what kind* of thing is being hashed: 0x00 for a leaf, 0x01 for an internal node (and 0x02 for MMR bagging in our reference). It stops a leaf being passed off as an internal node (§3.4). |
| **Merkle tree** | A binary tree in which each leaf is the hash of a data record and each internal node is the hash of its two children. Introduced by Ralph Merkle (1979). |
| **Leaf** | `H(0x00 || canonical(record))`. |
| **Internal node** | `H(0x01 || left || right)`; left and right are each exactly 32 bytes. |
| **Root** | The single top node. It commits to every leaf, their order and their count. |
| **Inclusion proof (audit path)** | The sibling hashes on the path from one leaf to the root, each tagged *left* or *right*. |
| **Promotion** | When a level has an odd number of nodes, the last node moves up unchanged; it is not paired with itself (§3.5). |
| **Merkle Mountain Range (MMR)** | An append-only list of *perfect* binary trees ("mountains") of strictly decreasing height. Nodes are stored in insertion order in a flat array. |
| **Peak** | The root of one mountain. An MMR has as many peaks as there are 1-bits in its leaf count. |
| **Height** | Leaves have height 0; a parent is one higher than its children. |
| **Position** | A node's index in the flat MMR array, in insertion order. |
| **Size** | Total number of nodes (leaves + internal) in an MMR. Not every integer is a valid size (§4.1). |
| **Bagging** | Folding all peak hashes into one root. |
| **Append-only** | Adding data only appends nodes; existing nodes never change **[tested]**. |
| **Consistency proof** | Evidence that an older root is a prefix of a newer one, i.e. history was appended to, not rewritten. Not implemented in Sneak (PROPOSED). |
| **Pruning** | Discarding data or hashes no longer needed while keeping enough to verify the root (Grin prunes spent outputs). |

---

## 2. What a root does and does not prove

A verified inclusion proof shows that **these exact bytes** sit at **this position** under **this root**. It does not show:

- that the content is true or legally usable;
- who made it (that needs a signature, which is why Sneak records `signed: false`);
- when it existed (that needs an external timestamp or anchor);
- anything about data outside the tree.

In Sneak's state vocabulary, a matching root supports *integrity* only. It never moves a requirement atom to `verified=true` on its own.

---

## 3. Merkle tree math (Sneak's custody construction)

### 3.1 Construction

```
leaf_i  = H(0x00 || canonical(record_i))          records sorted by UTF-8 path
level_0 = [leaf_0, …, leaf_{n-1}]
level_{k+1}[j] = H(0x01 || level_k[2j] || level_k[2j+1])   if 2j+1 < |level_k|
               = level_k[2j]                                otherwise (promotion)
root = the only element of the last level
```

This is exactly what `scripts/custody_snapshot.py` does. **[tested]** The reference code reproduces the committed root of `receipts/repository_bootstrap/SNAPSHOT.json` (`dcabcb5d…`, 167 leaves).

Example with 5 leaves (promotion at two levels):

```
                 R = H(01 || P || L4)
               /                    \
      P = H(01 || A || B)            L4   (promoted twice)
       /            \
  A=H(01||L0||L1)  B=H(01||L2||L3)
   /    \          /    \
  L0    L1        L2    L3        L4
```

### 3.2 Equivalence with RFC 6962 (Certificate Transparency)

RFC 6962 defines the root recursively, splitting n leaves at k = the largest power of two strictly less than n:

```
MTH(D[0:n]) = H(0x01 || MTH(D[0:k]) || MTH(D[k:n]))
```

**[tested for n = 1…1024]** Level-by-level promotion gives the same root as this recursive split. Sneak's R6 script also asserts this per run (`recursive_root == iterative`).

### 3.3 Proof size and cost

- Proof length is at most ⌈log₂ n⌉ siblings, and some leaf reaches that maximum. **[tested for n = 1…129]**
- Verifying costs one hash per sibling: ⌈log₂ n⌉ hashes.
- Proof size is 32·⌈log₂ n⌉ bytes plus one side bit per step.

Sneak's 167-leaf snapshot: ⌈log₂ 167⌉ = 8. That matches the 8-step proofs in the receipt, so a proof is 256 bytes of hashes. Downloading all leaves instead would be 167 × 32 = 5,344 bytes, and the gap widens as n grows.

### 3.4 Why domain separation matters (second-preimage attack)

Without prefixes, a leaf is `H(d)` and an internal node is `H(l || r)`, so they can't be told apart. An attacker takes the two level-1 nodes of a 4-leaf tree and presents `L0||L1` and `L2||L3` as two "documents". The 2-leaf tree over those fake documents has **the same root** as the real 4-leaf tree. **[tested]** With the 0x00/0x01 prefixes the roots differ, so the attack fails. **[tested]**

### 3.5 Why promotion, not duplication (CVE-2012-2459 shape)

Bitcoin pairs an odd last node with a copy of itself. As a result, `[a, b, c]` and `[a, b, c, c]` have the **same** root. **[tested]** That ambiguity was exploited in CVE-2012-2459. Sneak promotes the odd node instead, so the two lists have different roots. **[tested]**

### 3.6 Security argument (sketch)

Suppose a verifier accepts a forged leaf `x' ≠ x` with some proof against an honestly built root. Walk up the path: the computed value starts different and ends equal to the root. So at some step two *different* inputs, each a 0x00- or 0x01-prefixed string of fixed layout, hash to the *same* output. That pair is a SHA-256 collision. Fixed 32-byte children and the prefix byte make each input parse one way only, which is why canonical encoding and domain separation are prerequisites.

The generic birthday bound for a 256-bit hash is about 2¹²⁸ evaluations. After q hash evaluations, the chance of any collision is about q² / 2²⁵⁷.

### 3.7 Position binding

The left/right sides fix the leaf's position. At each level with a sibling, *left* means the node is a right child (index bit 1) and *right* means it is a left child (bit 0). A promoted level has no sibling and so adds no proof step. Recovering the exact index therefore needs the sides **plus** the leaf count n. Flipping any side changes the computed root, so verification fails. **[tested]**

---

## 4. Merkle Mountain Range math

### 4.1 Size, peaks and valid sizes

For n leaves:

```
size(n)  = 2n − popcount(n)                         [tested n = 1…1024]
#peaks   = popcount(n)                              [tested]
peak heights = indices of the 1-bits of n, highest first   [tested]
a peak of height h roots 2^h leaves and 2^(h+1) − 1 nodes
```

So the binary form of the leaf count is the mountain range. With n = 7 = 0b111 there are three peaks, of heights 2, 1 and 0.

Valid sizes are 1, 3, 4, 7, 8, 10, 11, 15, … Sizes such as 2, 5, 6 and 9 cannot occur. A receipt claiming one of them is malformed. **[tested for sizes 1…499]**

### 4.2 Height of a position

```
p = pos + 1                          (switch to 1-based)
while p is not all 1-bits:           (all-ones: p & (p+1) == 0)
    p = p − (2^(bitlen(p) − 1) − 1)  (jump left over a complete subtree)
height = bitlen(p) − 1
```

### 4.3 Navigation (node at position pos, height h)

| Move | Formula |
|---|---|
| left child | pos − 2^h |
| right child | pos − 1 |
| right sibling (of a left child) | pos + 2^(h+1) − 1 |
| parent of a left child | pos + 2^(h+1) |
| parent of a right child | pos + 1 |
| is pos a right child? | height(pos + 1) > h |

**[tested for pos < 2000]** These match the Grin wiki's rules: moving to the right sibling adds 2^(h+1) − 1, and moving to the left child subtracts 2^h.

### 4.4 Worked example: 7 leaves, size 11

```
height 2            6
                  /   \
height 1        2       5         9
               / \     / \       / \
height 0      0   1   3   4     7   8    10
```

Heights by position: `[0,0,1,0,0,1,2,0,0,1,0]`. Peaks: **6, 9, 10** in 0-based numbering, which are **7, 10, 11** in the Grin wiki's 1-based numbering. **[tested]**

The Grin wiki's size-4 example (3 leaves) has heights `[0,0,1,0]` and peaks 2 and 3. **[tested]**

### 4.5 Hashing (reference construction)

```
leaf(pos, d)     = H(0x00 || u64(pos) || d)
parent(pos, l,r) = H(0x01 || u64(pos) || l || r)
root(size)       = bag right-to-left:
                   acc = peak[last]
                   acc = H(0x02 || u64(size) || peak[i] || acc)   for i = last−1 … 0
```

Committing the position stops a node being moved, and committing the size stops two MMRs of different sizes sharing a root. Grin follows the same pattern but uses Blake2b and its own encoding, so **our hashes are not Grin-compatible** by design.

### 4.6 Append

1. Write the new leaf at position `size`.
2. While the next free position would be a parent, i.e. `height(size) > h`: hash the two children (left = `size − 2^(h+1)`, right = `size − 1`) into the parent and raise h by 1.

Each append adds one leaf plus up to ⌊log₂ n⌋ parents; on average it adds about 2 nodes, since `size(n) / n → 2`. Existing nodes are never rewritten. **[tested]**

### 4.7 MMR inclusion proof

A proof contains the leaf position, the MMR size, the sibling path up to the leaf's peak, and all peak hashes.

- Path length = the height of that peak. **[tested]** This is at most ⌊log₂ n⌋.
- Peak count = popcount(n), which is at most ⌊log₂ n⌋ + 1.
- To verify: recompute the peak from the leaf, check it equals the claimed peak at the expected position, then re-bag the peaks and compare with the root. Moving the leaf to another position fails. **[tested]**

### 4.8 Merkle tree vs MMR, and why Sneak cares

| | Merkle tree (current Sneak custody) | MMR |
|---|---|---|
| Adding an item | Root and many internal nodes change | Only new nodes are appended |
| Old proofs after an append | Become stale | The path to a peak survives until that peak merges |
| History | One snapshot per root | Every earlier size's peaks are recoverable, which enables consistency proofs |
| Fit for an append-only receipt or FCO ledger | Poor | Natural |

Sneak's receipts all say `"mmr": "NOT_COMMITTED"`, and that is accurate: custody today is a snapshot Merkle tree. Before anyone claims **MMR_COMMITTED**, these should be true (PROPOSED criteria for review):

1. An MMR over a defined append-only stream, e.g. `data/contributions/fco_ledger.jsonl` lines or receipt files, with a written leaf encoding.
2. Its root published at each append, in a receipt and posted in BAND.
3. An independent verifier, in a second language, recomputing the root, inclusion proofs and a consistency proof between two published sizes.
4. Tamper tests that reject a rewritten old leaf, a reordered leaf, and an invalid size.
5. Receipt metadata such as `mmr` and `signed` bound by the verifier (red-team RT-03 shows it currently is not).

---

## 5. Sources and review notes

- Sutanu Dutta, "The Story of Merkle Tree", Medium (2023): <https://medium.com/@sutanu3011/the-story-of-merkle-tree-42f9f268b1d5>. Conceptual introduction and use cases. *Review note:* it gives no formulas, names no hash function, and says nothing about odd-node handling or proof size. Its DynamoDB example is unsourced. The math above comes from the references below and the tests, not from this article.
- Grin documentation, "Merkle Mountain Range": <https://docs.grin.mw/wiki/chain-state/merkle-mountain-range/>. Shape, navigation, position-committed hashing, peak bagging, pruning and proof structure. *Review note:* the page mixes 0- and 1-based positions; §4.4 maps both.
- Background, not re-fetched in this session: RFC 6962 / RFC 9162 (Certificate Transparency Merkle trees); CVE-2012-2459 (Bitcoin duplicate-node mutation); R. Merkle, "A Digital Signature Based on a Conventional Encryption Function" (CRYPTO '87); Peter Todd's original MMR proposal.
