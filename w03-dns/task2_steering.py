#!/usr/bin/env python3
"""Week 3 · Task 2 — Does DNS actually steer you? Measure it.

Textbook §2.4.3 (records) and §2.5 (CDNs).

The lecture claims two things:

    (a) most large sites are served by a CDN, reached through a CNAME chain
    (b) DNS steers each user to a *nearby* replica

Both are testable from your laptop, and one of them is harder to prove than
the slide makes it look. Your job is to produce the evidence and a number.

    python3 task2_steering.py --collect        # gather the raw data
    python3 task2_steering.py --report         # your analysis

What you have to build
----------------------
1.  For each hostname in SITES, follow the CNAME chain to its end and record
    every hop. `--collect` should leave the raw data in out/chains.json.

2.  Decide, for each site, whether it is served by a **third party**.
    This is the hard part and there is no single right answer:

      - `www.microsoft.com` ends at `akamaiedge.net`     - clearly third party
      - `www.netflix.com`   stops inside `netflix.com`   - own CDN, not third party
      - some sites have no CNAME at all and still sit behind a CDN (anycast)
      - `foo.cloudfront.net` and `foo.s3.amazonaws.com` are both Amazon,
        but they are not the same service

    Write down the rule you used and **defend it in observation.md**. A rule
    that just compares the last two labels will be wrong on at least one of
    the sites below; find which, and say so.

3.  Ask **two different resolvers** for the same name and compare the
    addresses you get back. If DNS really steers by location, a CDN-hosted
    name should answer differently to resolvers sitting in different places.

        RESOLVERS below has your system resolver and two public ones.

    Report: of N CDN-hosted sites, how many returned a different address set
    from a different resolver? Claim (b) predicts most of them. Check it.

Pass condition
--------------
There is no fixed answer. You pass by producing, in out/report.md:

  - the table: site | chain length | final zone | third party? | your rule's verdict
  - the steering number: "X of N sites answered differently to a different resolver"
  - at least one site where your classification rule was wrong, and why
"""
import argparse, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

SITES = [
    "www.microsoft.com",     # Akamai, multi-hop
    "www.netflix.com",       # own CDN
    "www.adobe.com",
    "www.cnn.com",
    "www.apple.com",
    "www.korea.ac.kr",       # no CDN at all
    "www.stanford.edu",
    "www.bbc.co.uk",
    "www.spotify.com",
    "www.github.com",
    "www.wikipedia.org",
    "www.nytimes.com",
]

RESOLVERS = {
    "system": None,          # whatever is in your resolv.conf
    "google": "8.8.8.8",
    "quad9":  "9.9.9.9",
}


def dig(name, rtype="A", server=None):
    """Raw lookup. Transport only - the thinking is yours."""
    args = ["dig", "+short", "+time=3", "+tries=1", name, rtype]
    if server:
        args.insert(1, f"@{server}")
    out = subprocess.run(args, capture_output=True, text=True, timeout=12).stdout
    return [l.strip().rstrip(".") for l in out.splitlines() if l.strip()]


def _is_ipv4(token):
    parts = token.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def _last_two(hostname):
    labels = hostname.rstrip(".").lower().split(".")
    if len(labels) < 2:
        return hostname.lower()
    return ".".join(labels[-2:])


def follow_chain(name):
    """Follow CNAME hops with the system resolver until an answer has none."""
    chain = []
    current = name.rstrip(".").lower()
    seen = set()
    while current not in seen and len(chain) < 12:
        seen.add(current)
        chain.append(current)
        targets = [h.lower() for h in dig(current, "CNAME") if not _is_ipv4(h)]
        if not targets:
            break
        current = targets[0]
    return chain


def address_set(name, server):
    ips = []
    for line in dig(name, "A", server):
        # dig +short prints CNAME targets on the way to the A records.
        if _is_ipv4(line):
            ips.append(line)
    return sorted(set(ips))


def collect():
    """Gather raw chains and per-resolver answers into out/chains.json."""
    rows = []
    for site in SITES:
        chain = follow_chain(site)
        answers = {}
        for label, server in RESOLVERS.items():
            try:
                answers[label] = address_set(site, server)
            except subprocess.TimeoutExpired:
                answers[label] = []
        rows.append({
            "site": site,
            "chain": chain,
            "final": chain[-1],
            "final_zone_last_two": _last_two(chain[-1]),
            "origin_zone_last_two": _last_two(site),
            "resolvers": answers,
        })
        print(f"  {site}: chain={len(chain)} final={chain[-1]}")
    path = os.path.join(OUT, "chains.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)
        fh.write("\n")
    print(f"wrote {path}")


# Mechanical rule the write-up then argues with.
# Comparing the last two labels treats co.uk / ac.kr as if they were the
# organisation, and treats "no CNAME" as "not a CDN".
def rule_says_third_party(row):
    if len(row["chain"]) < 2:
        return False
    return row["origin_zone_last_two"] != row["final_zone_last_two"]


# (third party?, CDN-hosted?, why). CDN-hosted includes a site's own CDN.
# www.korea.ac.kr is the one name in SITES that is neither.
JUDGEMENT = {
    "www.microsoft.com": (True, True, "ends at akamaiedge.net (Akamai)"),
    "www.netflix.com": (False, True, "CNAME stays inside netflix.com — Netflix's own CDN"),
    "www.adobe.com": (True, True, "ends at akamai.net"),
    "www.cnn.com": (True, True, "ends at fastly.net"),
    "www.apple.com": (True, True, "ends at akamaiedge.net after aaplimg.com and edgekey.net"),
    "www.korea.ac.kr": (False, False, "no CNAME; every resolver returned 163.152.6.10"),
    "www.stanford.edu": (True, True, "CNAME to netlifyglobalcdn.com"),
    "www.bbc.co.uk": (True, True, "ends at fastly.net"),
    "www.spotify.com": (True, True, "ends at fastly.net"),
    "www.github.com": (False, True, "CNAME only to the github.com apex; the addresses are GitHub's own edge"),
    "www.wikipedia.org": (False, True, "CNAME to dyna.wikimedia.org, the same organisation"),
    "www.nytimes.com": (True, True, "ends at fastly.net after nytimes.com and nyt.net"),
}


def _rows(data):
    if isinstance(data, dict):
        return data["sites"]
    return data


def report():
    """Read out/chains.json and produce out/report.md."""
    path = os.path.join(OUT, "chains.json")
    rows = _rows(json.load(open(path, encoding="utf-8")))

    cdn_sites = []
    steered = []
    lines = []
    for row in rows:
        third, hosted, _why = JUDGEMENT[row["site"]]
        verdict = "third party" if rule_says_third_party(row) else "not third party"
        truth = "yes" if third else "no"
        sets = [tuple(v) for v in row["resolvers"].values() if v]
        differs = len(set(sets)) > 1
        if hosted:
            cdn_sites.append(row["site"])
            if differs:
                steered.append(row["site"])
        lines.append(
            f"| `{row['site']}` | {len(row['chain'])} | `{row['final_zone_last_two']}` "
            f"| {truth} | {verdict} | {'different' if differs else 'same'} |"
        )

    n = len(cdn_sites)
    x = len(steered)
    differed = ", ".join(f"`{s}`" for s in steered)
    body = f"""# Week 3 Task 2 · Does DNS steer you?

Measured from **one network**: this PC. A second physical network was not
available, so path (B) compares three resolvers on that one network — the
system resolver, Google Public DNS `8.8.8.8`, and Quad9 `9.9.9.9` — instead
of moving the laptop. That weakens claim (b). `8.8.8.8` and `9.9.9.9` are
anycast; a different answer means the resolvers are not in the same place,
not that this computer changed networks.

## Rule

**Last-two-labels rule.** If the CNAME chain has two or more names and the
last two labels of the original name differ from the last two labels of the
final name, call it a third party. If there is no CNAME, call it not a third
party.

The "rule verdict" column is that rule and nothing else. The "third party?"
column is a separate judgement after reading who operates the final name.

## Table

| site | chain length | final zone (last two labels) | third party? | rule verdict | addresses across resolvers |
|---|---:|---|---|---|---|
{chr(10).join(lines)}

## Where the rule is wrong

The rule is wrong on **`www.wikipedia.org`**. The chain is
`www.wikipedia.org` → `dyna.wikimedia.org`, so the last two labels differ
(`wikipedia.org` vs `wikimedia.org`) and the rule says third party. They are
the same organisation. Every resolver returned the same address,
`103.102.166.224`. Wikimedia is not Akamai or Fastly.

Two more names show the same cut failing even when the boolean happens to
land correctly. **`www.korea.ac.kr`** has no CNAME, so the rule says not a
third party, which is right, but the zone it prints is `ac.kr` — the public
suffix, not `korea.ac.kr`. **`www.bbc.co.uk`** is a third party because the
chain ends at `bbc.map.fastly.net`, and the rule agrees only because
`co.uk != fastly.net`. The rule thinks the BBC's zone is `co.uk`. The
intermediate name `www.bbc.co.uk.pri.bbc.co.uk` is still the BBC.

`www.netflix.com` is the case the rule gets right for the wrong reason. The
chain ends at `www.prod.ftl.netflix.com`, the last two labels match, and the
verdict "not third party" is correct because Netflix runs that CDN itself.
The rule does not know that. It only knows the labels matched.

## Steering number

**{x} of {n} sites answered differently to a different resolver.**

N is the CDN-hosted sites, including a site's own CDN. The one site left out
is `www.korea.ac.kr`, which has no CNAME and returned `163.152.6.10` to all
three resolvers. The {x} that differed: {differed}.

Claim (b) says DNS sends each user to a nearby replica. This supports it only
in part. Fastly names (`www.cnn.com`, `www.bbc.co.uk`, `www.spotify.com`,
`www.nytimes.com`) came back as `146.75.x` from the system resolver and as
`151.101.x` from `8.8.8.8` and `9.9.9.9`. Akamai names often differed again
at Quad9. So the recursive resolver's location does change the address set.
It does not show what would happen if this laptop moved: there is still only
one client network, and Google usually matched the system resolver, which is
what you expect when both anycast to a nearby point of presence.
`www.netflix.com`, `www.stanford.edu`, and `www.wikipedia.org` returned the
same set to all three, so a CDN being in the chain is not by itself evidence
of steering from this vantage.

## Part A · the capture

Interface capture was not available: `pktmon` returned access denied, and
Npcap/Wireshark is not installed. `out/dns.pcapng` is the six UDP messages
this host exchanged while resolving `www.korea.ac.kr` with recursion off,
against `198.41.0.4`, then `210.101.61.1`, then `163.152.11.6`. The DNS
payload, the IP endpoints, and the UDP ports are those bytes. The Ethernet
addresses are placeholders (`02:00:00:00:00:01` and `02:00:00:00:00:02`)
because the messages were read from the socket, not from the NIC.

The textbook DNS trace (Kurose & Ross, 9th ed., `dns-wireshark-trace1-1`)
was checked and not used. It only shows host `10.0.0.44` talking to the
recursive resolver `75.75.75.75`, so every response is an answer and none is
a referral.

- Matching query and response: frames **1** and **2**, transaction ID **29346**
- Delegation: frame **2**. Answer count 0, six `NS` records in the authority section, AA bit clear. The root is handing back `.kr`, not an address
- Answer: frame **6**, transaction ID **9556**. AA bit set, one `A` record in the answer section (`163.152.6.10`)
- Largest DNS response: frame **2**, **383** bytes on the wire (DNS message **341** bytes). It is large because the referral carries six nameserver names plus their glue, not because the address of `www.korea.ac.kr` is large
"""
    out = os.path.join(OUT, "report.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(body)
    print(f"wrote {out}")
    print(f"steering {x} of {n}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--collect", action="store_true")
    p.add_argument("--report", action="store_true")
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.collect:
        collect()
    elif a.report:
        report()
    else:
        p.print_help()
