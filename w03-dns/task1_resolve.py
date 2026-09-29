#!/usr/bin/env python3
"""Week 3 · Task 1 — Build your own iterative resolver.

Textbook §2.4.2 - §2.4.3.

`dig +trace` walks root -> TLD -> authoritative for you. In this task you do
that walk yourself: start at a root server, read the delegation it returns,
ask the next server, and keep going until somebody answers authoritatively.

You may shell out to `dig` for the transport, or use a DNS library
(`dnspython` is in the container). Either is fine - what matters is that
*you* follow the delegations rather than letting a tool do it.

    python3 task1_resolve.py www.korea.ac.kr
    python3 task1_resolve.py --verify        # check yourself against dig

Pass condition
--------------
`--verify` resolves five names with your resolver and with `dig`, and the
addresses must agree. A name behind a CDN may legitimately return a different
address each time; the harness compares the *set of authoritative nameservers*
you ended at for those, not the address.
"""
import argparse, re, subprocess, sys

# Root servers. Everything starts here; there is no earlier step.
ROOT_SERVERS = [
    "198.41.0.4",       # a.root-servers.net
    "199.9.14.201",     # b.root-servers.net
    "192.33.4.12",      # c.root-servers.net
]

# (name, kind).  "stable" names must match dig exactly.  "cdn" names are served
# from many replicas and may legitimately give you a different address than dig
# got a second earlier - for those we only require that you reached an answer.
VERIFY_NAMES = [
    ("www.korea.ac.kr", "stable"),
    ("dns.google", "stable"),
    ("en.wikipedia.org", "stable"),
    ("www.stanford.edu", "stable"),
    ("www.microsoft.com", "cdn"),
]


class Resolver:
    """Iterative resolver. Every query is +norecurse; this class follows referrals.

    resolve(name) -> (address, path)
        address : an A record, as a string
        path    : the servers asked, in order, including walks done to find
                  glue that a delegation did not carry
    """

    MAX_DEPTH = 16
    MAX_STEPS = 48

    def __init__(self):
        self.glueless = []

    def resolve(self, name):
        self.path = []
        self._stack = []
        self._ns_cache = {}
        self.glueless = []
        address = self._resolve(self._norm(name), 0)
        return address, list(self.path)

    def _norm(self, name):
        return name.rstrip(".").lower()

    def _resolve(self, name, depth):
        if depth > self.MAX_DEPTH:
            raise RuntimeError(f"depth cap exceeded while resolving {name}")
        if name in self._stack:
            raise RuntimeError(f"loop detected at {name}")
        self._stack.append(name)
        try:
            return self._iterative(name, depth)
        finally:
            self._stack.pop()

    def _iterative(self, name, depth):
        """Walk one name from the root. Fall back to the next server on silence."""
        stack = [(list(ROOT_SERVERS), 0)]
        steps = 0
        while stack and steps < self.MAX_STEPS:
            steps += 1
            servers, index = stack[-1]
            if index >= len(servers):
                stack.pop()
                continue
            stack[-1] = (servers, index + 1)
            server = servers[index]
            self.path.append(server)
            parsed = self._query(server, name)
            if parsed is None:
                continue
            kind, payload = self._classify(parsed, name)
            if kind == "answer":
                return payload
            if kind == "cname":
                return self._resolve(payload, depth + 1)
            if kind == "referral":
                nxt = self._referral_targets(payload, parsed["additional"], depth)
                if nxt:
                    stack.append((nxt, 0))
                continue
            # NODATA / REFUSED / useless packet: try the next server.
        raise RuntimeError(f"no authoritative A record for {name}")

    def _classify(self, parsed, name):
        chased = self._chase(parsed["answer"], name)
        if chased is not None:
            return chased
        ns = [r for r in parsed["authority"] if r["type"] == "NS"]
        if ns and not parsed["aa"]:
            return "referral", ns
        if parsed["aa"] and not chased:
            return "next", None
        if ns:
            return "referral", ns
        return "next", None

    def _chase(self, answer, qname):
        """Follow CNAME records that arrived in this one packet. An A ends it.
        A CNAME with no address in the packet means start a new walk."""
        owner = qname
        seen = set()
        while owner not in seen:
            seen.add(owner)
            addresses = [r for r in answer if r["type"] == "A" and r["owner"] == owner]
            if addresses:
                return "answer", addresses[0]["data"]
            cnames = [r for r in answer if r["type"] == "CNAME" and r["owner"] == owner]
            if not cnames:
                if owner != qname:
                    return "cname", owner
                return None
            owner = cnames[0]["data"]
        raise RuntimeError(f"CNAME loop inside one response for {qname}")

    def _referral_targets(self, ns_records, additional, depth):
        glue = {}
        for rec in additional:
            if rec["type"] == "A":
                glue.setdefault(rec["owner"], rec["data"])
        targets = []
        for rec in ns_records:
            nsname = rec["data"]
            if nsname in glue:
                ip = glue[nsname]
            elif nsname in self._ns_cache:
                ip = self._ns_cache[nsname]
            else:
                # The delegation named a server and did not hand us its address.
                self.glueless.append(nsname)
                ip = self._resolve(nsname, depth + 1)
                self._ns_cache[nsname] = ip
            if ip not in targets:
                targets.append(ip)
        return targets

    def _query(self, server, name):
        cmd = [
            "dig", f"@{server}", name, "A",
            "+norecurse", "+time=2", "+tries=1", "+nocmd", "+bufsize=1232",
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        except (subprocess.TimeoutExpired, OSError):
            return None
        text = proc.stdout or ""
        if "->>HEADER<<-" not in text:
            return None
        return self._parse(text)

    def _parse(self, text):
        flags = ""
        header = re.search(r"flags:\s*([^;]*);", text)
        if header:
            flags = header.group(1)
        section = None
        records = {"answer": [], "authority": [], "additional": []}
        for line in text.splitlines():
            if line.startswith(";;") and "SECTION" in line:
                if "ANSWER SECTION" in line:
                    section = "answer"
                elif "AUTHORITY SECTION" in line:
                    section = "authority"
                elif "ADDITIONAL SECTION" in line:
                    section = "additional"
                else:
                    section = None
                continue
            if not section or not line or line.startswith(";"):
                continue
            parts = line.split()
            if len(parts) < 5 or parts[2] != "IN":
                continue
            rtype = parts[3]
            if rtype not in ("A", "NS", "CNAME"):
                continue
            data = parts[4]
            if rtype in ("NS", "CNAME"):
                data = data.rstrip(".").lower()
            records[section].append({
                "owner": parts[0].rstrip(".").lower(),
                "type": rtype,
                "data": data,
            })
        return {
            "aa": "aa" in flags.split(),
            "answer": records["answer"],
            "authority": records["authority"],
            "additional": records["additional"],
        }


# ------------------------------------------------------------------- harness
def dig_answer(name):
    """What the system resolver says, for comparison."""
    out = subprocess.run(["dig", "+short", name, "A"],
                         capture_output=True, text=True).stdout
    return [l for l in out.split() if l and l[0].isdigit()]


def verify():
    r, failures = Resolver(), 0
    for name, kind in VERIFY_NAMES:
        try:
            addr, path = r.resolve(name)
        except NotImplementedError:
            print("Nothing implemented yet - write Resolver.resolve first.")
            return 1
        except Exception as e:
            print(f"  FAIL  {name:<22} your resolver raised {e!r}")
            failures += 1
            continue
        expected = dig_answer(name)
        if addr in expected:
            note = ""
        elif kind == "cdn":
            note = "  <- differs, but this name is CDN-hosted. Explain it."
        else:
            note = "  <- should have matched"
            failures += 1
        print(f"  {'FAIL' if note.endswith('matched') else 'ok  '}  {name:<22} "
              f"you={addr:<16} dig={','.join(expected) or '-'}   "
              f"hops={len(path)}{note}")
    print(f"\n  {len(VERIFY_NAMES) - failures}/{len(VERIFY_NAMES)} ok")
    return 1 if failures else 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("name", nargs="?", default="www.korea.ac.kr")
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()

    if a.verify:
        sys.exit(verify())

    addr, path = Resolver().resolve(a.name)
    for i, server in enumerate(path, 1):
        print(f"  {i}. asked {server}")
    print(f"\n  {a.name} -> {addr}")


if __name__ == "__main__":
    main()
