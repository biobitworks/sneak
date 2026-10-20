#!/usr/bin/env python3
"""Reference Merkle tree and Merkle Mountain Range (MMR) for Sneak teammates.

Teaching/verification code: small, dependency-free and deliberately explicit.
It is NOT byte-compatible with Grin (Grin uses Blake2b and its own encodings).

Conventions
- H = SHA-256. Positions are 0-based. Integers are 8-byte big-endian.
- Merkle tree (identical to scripts/custody_snapshot.py):
    leaf   = H(0x00 || data)
    parent = H(0x01 || left || right)
    odd node at a level is promoted unchanged.
- MMR (position-committed, Grin-style shape):
    leaf   = H(0x00 || pos || data)
    parent = H(0x01 || pos || left || right)
    root   = bag peaks right-to-left: acc = peak[-1];
             acc = H(0x02 || size || peak[i] || acc) for i from right-1 down to 0.
"""
import hashlib, struct

H = lambda b: hashlib.sha256(b).digest()
u64 = lambda n: struct.pack(">Q", n)


# ---------------- Merkle tree ----------------
def merkle_levels(leaves):
    if not leaves:
        raise ValueError("empty tree")
    out = [list(leaves)]
    while len(out[-1]) > 1:
        row = out[-1]
        out.append([H(b"\x01" + row[i] + row[i + 1]) if i + 1 < len(row) else row[i]
                    for i in range(0, len(row), 2)])
    return out


def merkle_root(leaves):
    return merkle_levels(leaves)[-1][0]


def merkle_root_rfc6962(leaves):
    """RFC 6962 style: split at the largest power of two strictly less than n."""
    n = len(leaves)
    if n == 1:
        return leaves[0]
    k = 1 << ((n - 1).bit_length() - 1)
    return H(b"\x01" + merkle_root_rfc6962(leaves[:k]) + merkle_root_rfc6962(leaves[k:]))


def merkle_proof(leaves, index):
    proof = []
    for row in merkle_levels(leaves)[:-1]:
        if index % 2:
            proof.append(("left", row[index - 1]))
        elif index + 1 < len(row):
            proof.append(("right", row[index + 1]))
        index //= 2
    return proof


def merkle_verify(leaf, proof, root):
    v = leaf
    for side, sib in proof:
        v = H(b"\x01" + sib + v) if side == "left" else H(b"\x01" + v + sib)
    return v == root


# ---------------- MMR position arithmetic ----------------
def all_ones(x):
    return x != 0 and (x & (x + 1)) == 0


def height(pos):
    """Height of the node at 0-based position pos (leaves are height 0)."""
    p = pos + 1                                   # work in 1-based
    while not all_ones(p):
        p -= (1 << (p.bit_length() - 1)) - 1      # jump to the left subtree
    return p.bit_length() - 1


def size_for_leaves(n):
    """Number of nodes in an MMR with n leaves: 2n - popcount(n)."""
    return 2 * n - bin(n).count("1")


def peaks(size):
    """0-based positions of the peaks of an MMR with `size` nodes, left to right."""
    out, offset, remaining = [], 0, size
    while remaining:
        h = (remaining + 1).bit_length() - 1      # largest perfect tree: 2^h - 1 <= remaining
        tree = (1 << h) - 1
        out.append(offset + tree - 1)
        offset += tree
        remaining -= tree
    return out


def valid_size(size):
    return sum((1 << (height(p) + 1)) - 1 for p in peaks(size)) == size and \
        all(height(p) > height(q) for p, q in zip(peaks(size), peaks(size)[1:]))


# ---------------- MMR ----------------
class MMR:
    def __init__(self):
        self.nodes = []          # node hashes indexed by 0-based position
        self.leaf_pos = []       # position of each leaf, by leaf index

    @property
    def size(self):
        return len(self.nodes)

    def append(self, data: bytes):
        pos = self.size
        self.leaf_pos.append(pos)
        self.nodes.append(H(b"\x00" + u64(pos) + data))
        h = 0
        # Merge while the next position would be a parent (its height exceeds the current one).
        while height(self.size) > h:
            parent = self.size
            left = parent - (1 << (h + 1))        # left child of a height-(h+1) node
            right = parent - 1
            self.nodes.append(H(b"\x01" + u64(parent) + self.nodes[left] + self.nodes[right]))
            h += 1
        return pos

    def peak_hashes(self):
        return [self.nodes[p] for p in peaks(self.size)]

    def root(self):
        ph = self.peak_hashes()
        acc = ph[-1]
        for p in reversed(ph[:-1]):
            acc = H(b"\x02" + u64(self.size) + p + acc)
        return acc

    def proof(self, leaf_index):
        pos = self.leaf_pos[leaf_index]
        pk = set(peaks(self.size))
        path = []
        while pos not in pk:
            h = height(pos)
            if height(pos + 1) > h:               # pos is a right child
                sib, parent = pos - ((1 << (h + 1)) - 1), pos + 1
                path.append(("left", sib, self.nodes[sib]))
            else:                                  # pos is a left child
                sib = pos + (1 << (h + 1)) - 1
                parent = sib + 1
                path.append(("right", sib, self.nodes[sib]))
            pos = parent
        return {"size": self.size, "leaf_pos": self.leaf_pos[leaf_index], "path": path,
                "peak_pos": pos, "peaks": self.peak_hashes()}


def mmr_verify(data: bytes, proof, root):
    pos = proof["leaf_pos"]
    v = H(b"\x00" + u64(pos) + data)
    for side, sib_pos, sib in proof["path"]:
        h = height(pos)
        expected = pos - ((1 << (h + 1)) - 1) if side == "left" else pos + (1 << (h + 1)) - 1
        if sib_pos != expected:
            return False
        parent = pos + 1 if side == "left" else sib_pos + 1
        v = H(b"\x01" + u64(parent) + (sib + v if side == "left" else v + sib))
        pos = parent
    pk = peaks(proof["size"])
    if pos not in pk or proof["peaks"][pk.index(pos)] != v:
        return False
    ph = proof["peaks"]
    acc = ph[-1]
    for p in reversed(ph[:-1]):
        acc = H(b"\x02" + u64(proof["size"]) + p + acc)
    return acc == root


if __name__ == "__main__":
    m = MMR()
    for i in range(7):
        m.append(f"leaf-{i}".encode())
    print({"leaves": 7, "size": m.size, "heights": [height(p) for p in range(m.size)],
           "peaks_0based": peaks(m.size), "root": m.root().hex()})
