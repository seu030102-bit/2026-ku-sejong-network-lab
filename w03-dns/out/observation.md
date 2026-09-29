## Task 1

The root server did not hand back an address for `www.korea.ac.kr`. In `out/dns.pcapng` frame 2 (transaction ID 29346) the answer count is 0 and the authority section carries six `NS` records for `.kr`: the root is authoritative for the root zone only, so it can delegate the TLD and cannot answer the hostname. That walk asked three servers (`198.41.0.4`, `210.101.61.1`, `163.152.11.6`). A laptop normally asks its recursive resolver once.

When a delegation arrived with no glue `A` record, the resolver started a separate iterative walk from the root for that nameserver name, then went on. `www.stanford.edu` did this seven times (`ns5`–`ns7.dnsmadeeasy.com` and four `nsone.net` names), which is why that one name took 27 queries. `www.microsoft.com` did it three times, for the out-of-bailiwick `azure-dns.net`, `.org`, and `.info` servers. `www.korea.ac.kr` had glue at both referrals, so it cost no extra lookup.

## Task 2

A delegation and an answer are the same DNS message with different sections filled in. Frame 2 has answer count 0, six `NS` records, and the AA bit clear; frame 6 (ID 9556) has the AA bit set and one `A` record, `163.152.6.10`, in the answer section.

The third-party rule compares the last two labels of the original name and the final CNAME, and treats "no CNAME" as "not a third party." It is wrong on `www.wikipedia.org`: the chain ends at `dyna.wikimedia.org`, so the labels differ and the rule says third party, but Wikimedia operates both names and every resolver returned `103.102.166.224`. The same cut cannot even name `www.korea.ac.kr` or `www.bbc.co.uk`, because it keeps the public suffix (`ac.kr`, `co.uk`).

**8 of 11 sites answered differently to a different resolver** (system, `8.8.8.8`, Quad9), counting CDN-hosted names and leaving out `www.korea.ac.kr`. That only partly supports claim (b). This PC stayed on one network; Google usually matched the system resolver, and Quad9 often did not, so the change is which resolver answered, not where the laptop was.

## Task 3

`BaselineCache` ignores the TTL and keeps every record for 60 seconds. That single mistake is both bugs: records shorter than 60 s are served after they expire, and records longer than 60 s are thrown away early. `www.microsoft.com` is the one it handles worst — TTL 20 s and the most popular name in the workload, 189 of its 322 lookups were stale, which is 189 of the 266 stale answers. `dns.google` and `a.root-servers.net` (TTL 86400 s) show the performance side: about 20 upstream fetches in the simulated hour instead of one.

The floor is **275** upstream queries. A correct cache must not answer once `now` passes the fetch time plus the TTL, and refreshing earlier only adds a fetch, so no correct cache can go below the miss count of a cache that stores each record for exactly its TTL. `YourCache` makes 275 upstream queries and 0 stale answers, which is that floor.
