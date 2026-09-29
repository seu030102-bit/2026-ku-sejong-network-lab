#!/usr/bin/env python3
"""Week 5 · Task 3 — Make longest-prefix match fast.

Textbook §4.3.3.

`LinearTable` is correct and it is what you probably wrote in Task 1: keep the
prefixes in a list, check every one, remember the longest that matched. On six
entries that is fine. A real router holds close to a million, and it has to
answer while the packet is still in the buffer.

Beat it:

    python3 bench.py
    python3 bench.py --yours

Correctness first: `bench.py` checks every one of your answers against the
linear table. A fast router that forwards to the wrong next hop is not a
router, it is an outage.
"""


class LinearTable:
    """Correct, and slow in the obvious way."""

    def __init__(self):
        self.entries = []                     # (prefix_len, network, next_hop)

    def add(self, network, prefix_len, next_hop):
        self.entries.append((prefix_len, network, next_hop))

    def lookup(self, address):
        best = None
        for plen, net, hop in self.entries:
            mask = (0xFFFFFFFF << (32 - plen)) & 0xFFFFFFFF
            if address & mask == net and (best is None or plen > best[0]):
                best = (plen, hop)
        return best[1] if best else None


class YourTable:
    """One hash table per prefix length, searched from /32 down to /0.

    A lookup masks the address and probes that length's dict. The first hit is
    the longest match, so it stops. There are 33 lengths, independent of how
    many prefixes were inserted. Memory is one dict entry per prefix, plus 33
    empty dicts for lengths the table never uses.

    A binary trie would touch at most 32 nodes and is what hardware builds,
    because a wire-speed lookup cannot depend on hashing. In CPython a dict
    probe is one bytecode sequence and a trie node is an object chase, so the
    hash tables win here even though they are the worse shape in silicon.
    """

    def __init__(self):
        self.by_length = [{} for _ in range(33)]
        self.masks = tuple((0xFFFFFFFF << (32 - plen)) & 0xFFFFFFFF for plen in range(33))
        self.order = []

    def add(self, network, prefix_len, next_hop):
        bucket = self.by_length[prefix_len]
        if not bucket:
            self.order.append(prefix_len)
            self.order.sort(reverse=True)
        bucket[network] = next_hop

    def lookup(self, address):
        by_length = self.by_length
        masks = self.masks
        for prefix_len in self.order:
            hop = by_length[prefix_len].get(address & masks[prefix_len])
            if hop is not None:
                return hop
        return None
