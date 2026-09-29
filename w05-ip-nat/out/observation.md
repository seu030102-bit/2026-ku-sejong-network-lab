## Task 1

For `/30` and shorter, the network address and the all-ones address are reserved, so the usable hosts sit between them. `/31` and `/32` have no such middle. RFC 3021 makes both addresses of a `/31` ordinary hosts and drops the broadcast, and a `/32` is one host. `network_range` returns those addresses in every slot: `/31` is `(low, high, high)` and `/32` is `(addr, addr, addr)`. The third value is not a separate broadcast.

`10.20.30.70` matches five entries: `0.0.0.0/0` (default-gw), `10.0.0.0/8` (campus), `10.20.0.0/16` (eng-building), `10.20.30.0/24` (lab-floor), and `10.20.30.64/26` (lab-rack-2). The four `10` prefixes are the ones the harness comment means. Longest prefix wins, so `/26` and `lab-rack-2`. If the same prefix were added twice with different next hops, the first next hop stays and the later one is ignored. The table is malformed either way, and a silent overwrite would be harder to see.

## Task 2

This PC is behind **one NAT**. The Wi-Fi address is `172.16.24.87/24` (RFC 1918), the gateway `172.16.24.1` is inside that subnet, and ipify sees `163.152.233.24`, which is public and not in `100.64.0.0/10`. A second, carrier-grade NAT would have hidden that `163.152` address too. Traceroute shows private campus hops (`172.16.0.2`, `192.168.98.132`) and then `163.152.233.129` before the provider. The later `10.x` hops are provider router interfaces, not this host's source address.

Both labelled records are KUWIFI minutes apart. The private address, the mask, the gateway, and the public address were the same, because the network did not change. In the textbook DHCP trace, Discover is frame 5, `0.0.0.0:68` to `255.255.255.255:67`. The source cannot be anything else: the client has no address yet, so it also cannot name a server and has to broadcast. The granted lease is 86400 seconds. At half of that (43200 s, T1) the client unicasts a renewal to the server that answered.

## Task 3

`YourTable` is one dict per prefix length, probed from the longest length present down, stopping at the first hit. Memory is one entry per prefix (5,000 here) plus the empty length dicts that were never filled. Lookup time is proportional to the number of **distinct lengths** in the table, at most 33, not to the number of routes. On this harness that was 1795× the linear scan, 0.020 s against 36.6 s, with no wrong answers.

Hardware still walks the address one bit at a time. That walk is a fixed 32 steps and pipelines. A hash table is variable work and a poor fit for a forwarding ASIC. In CPython the dict probe is one C call and a trie node is an object chase, so the hash tables are faster here even though they are the worse machine.
