#!/usr/bin/env python3
"""Week 5 · Task 1 — Subnets and longest-prefix match.

Textbook §4.3.2 (IPv4 addressing, CIDR) and §4.3.3 (forwarding).

Two things a router does with every packet: work out which prefixes the
destination falls inside, and pick the longest one. The second is the whole
of "longest prefix match", and it is the reason the internet's routing table
can hold a million entries and still be answerable.

You build both, from integers up. No `ipaddress` module - that library is
exactly the thing you are supposed to understand this week.

    python3 task1_forward.py --verify
"""
import argparse


def _octet(text):
    if not text.isdigit():
        raise ValueError(f"bad octet {text!r}")
    value = int(text)
    if value > 255:
        raise ValueError(f"octet out of range: {value}")
    return value


def parse_ipv4(text):
    parts = text.split(".")
    if len(parts) != 4:
        raise ValueError(f"not an IPv4 address: {text!r}")
    number = 0
    for part in parts:
        number = (number << 8) | _octet(part)
    return number


def _mask(prefix_len):
    if prefix_len == 0:
        return 0
    return (0xFFFFFFFF << (32 - prefix_len)) & 0xFFFFFFFF


def _format_ipv4(number):
    return ".".join(str((number >> shift) & 0xFF) for shift in (24, 16, 8, 0))


def parse_cidr(cidr):
    """'163.152.6.0/24' -> (network as int, prefix length).

    Requirements: reject a prefix length outside 0-32, and reject an address
    whose host bits are set when they should not be (163.152.6.5/24 is a
    common way to write a host, but it is not a network).
    """
    if "/" not in cidr:
        raise ValueError(f"missing prefix length: {cidr!r}")
    address, length_text = cidr.split("/", 1)
    if not length_text.isdigit():
        raise ValueError(f"bad prefix length: {length_text!r}")
    prefix_len = int(length_text)
    if prefix_len > 32:
        raise ValueError(f"prefix length out of range: {prefix_len}")
    network = parse_ipv4(address)
    if network & (~_mask(prefix_len) & 0xFFFFFFFF):
        raise ValueError(f"host bits set: {cidr}")
    return network, prefix_len


def network_range(cidr):
    """'163.152.6.0/24' -> (first usable, last usable, broadcast) as strings.

    For a prefix of /30 or shorter the network address and the all-ones
    address are reserved, so the usable hosts sit strictly between them.
    /31 and /32 have no room for that. RFC 3021 makes both addresses of a
    /31 usable hosts and removes the broadcast, and a /32 is a single host.
    Those two cases return the addresses themselves in every slot: there is
    no separate broadcast to report.
    """
    network, prefix_len = parse_cidr(cidr)
    broadcast = network | (~_mask(prefix_len) & 0xFFFFFFFF)
    if prefix_len >= 31:
        return _format_ipv4(network), _format_ipv4(broadcast), _format_ipv4(broadcast)
    return (
        _format_ipv4(network + 1),
        _format_ipv4(broadcast - 1),
        _format_ipv4(broadcast),
    )


class ForwardingTable:
    """Longest-prefix-match forwarding.

    add(cidr, next_hop)  ·  lookup(address) -> next_hop or None

    The default route 0.0.0.0/0 matches everything and is the shortest prefix,
    so it must lose to any other match. If two entries have the same prefix
    length, the table is malformed - the first next hop stays, the later one
    is ignored.
    """

    def __init__(self):
        self.entries = []

    def add(self, cidr, next_hop):
        network, prefix_len = parse_cidr(cidr)
        for plen, net, _hop in self.entries:
            if plen == prefix_len and net == network:
                return
        self.entries.append((prefix_len, network, next_hop))

    def lookup(self, address):
        number = parse_ipv4(address)
        best = None
        for prefix_len, network, hop in self.entries:
            if number & _mask(prefix_len) == network and (best is None or prefix_len > best[0]):
                best = (prefix_len, hop)
        return None if best is None else best[1]


# ------------------------------------------------------------------- harness
RANGE_CASES = [
    ("192.168.0.0/24",  "192.168.0.1",   "192.168.0.254",  "192.168.0.255"),
    ("10.0.0.0/8",      "10.0.0.1",      "10.255.255.254", "10.255.255.255"),
    ("172.16.32.0/20",  "172.16.32.1",   "172.16.47.254",  "172.16.47.255"),
    ("203.0.113.64/26", "203.0.113.65",  "203.0.113.126",  "203.0.113.127"),
]

TABLE = [
    ("0.0.0.0/0",       "default-gw"),
    ("10.0.0.0/8",      "campus"),
    ("10.20.0.0/16",    "eng-building"),
    ("10.20.30.0/24",   "lab-floor"),
    ("10.20.30.64/26",  "lab-rack-2"),
    ("192.168.1.0/24",  "home"),
]

LOOKUP_CASES = [
    ("10.20.30.70",   "lab-rack-2"),     # inside all four 10.x entries
    ("10.20.30.10",   "lab-floor"),
    ("10.20.99.1",    "eng-building"),
    ("10.99.0.1",     "campus"),
    ("8.8.8.8",       "default-gw"),
    ("192.168.1.77",  "home"),
]


def verify():
    fails = 0
    for cidr, first, last, bcast in RANGE_CASES:
        try:
            got = network_range(cidr)
        except NotImplementedError:
            print("  network_range is still a stub"); return 1
        except Exception as e:
            print(f"  FAIL  {cidr:<18} raised {e!r}"); fails += 1; continue
        ok = tuple(got) == (first, last, bcast)
        print(f"  {'ok  ' if ok else 'FAIL'}  {cidr:<18} {got}")
        fails += not ok

    t = ForwardingTable()
    try:
        for cidr, hop in TABLE:
            t.add(cidr, hop)
    except NotImplementedError:
        print("  ForwardingTable is still a stub"); return 1

    for addr, expect in LOOKUP_CASES:
        got = t.lookup(addr)
        ok = got == expect
        print(f"  {'ok  ' if ok else 'FAIL'}  {addr:<16} -> {got}  (want {expect})")
        fails += not ok

    print(f"\n  {len(RANGE_CASES) + len(LOOKUP_CASES) - fails}"
          f"/{len(RANGE_CASES) + len(LOOKUP_CASES)} ok")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())
