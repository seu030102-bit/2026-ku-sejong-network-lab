# Week 3 Task 2 · Does DNS steer you?

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
| `www.microsoft.com` | 3 | `akamaiedge.net` | yes | third party | different |
| `www.netflix.com` | 2 | `netflix.com` | no | not third party | same |
| `www.adobe.com` | 3 | `akamai.net` | yes | third party | different |
| `www.cnn.com` | 2 | `fastly.net` | yes | third party | different |
| `www.apple.com` | 4 | `akamaiedge.net` | yes | third party | different |
| `www.korea.ac.kr` | 1 | `ac.kr` | no | not third party | same |
| `www.stanford.edu` | 2 | `netlifyglobalcdn.com` | yes | third party | same |
| `www.bbc.co.uk` | 3 | `fastly.net` | yes | third party | different |
| `www.spotify.com` | 2 | `fastly.net` | yes | third party | different |
| `www.github.com` | 2 | `github.com` | no | not third party | different |
| `www.wikipedia.org` | 2 | `wikimedia.org` | no | third party | same |
| `www.nytimes.com` | 4 | `fastly.net` | yes | third party | different |

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

**8 of 11 sites answered differently to a different resolver.**

N is the CDN-hosted sites, including a site's own CDN. The one site left out
is `www.korea.ac.kr`, which has no CNAME and returned `163.152.6.10` to all
three resolvers. The 8 that differed: `www.microsoft.com`, `www.adobe.com`, `www.cnn.com`, `www.apple.com`, `www.bbc.co.uk`, `www.spotify.com`, `www.github.com`, `www.nytimes.com`.

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
