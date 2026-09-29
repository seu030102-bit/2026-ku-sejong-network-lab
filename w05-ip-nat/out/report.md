# Week 5 Task 2 · Where this machine is

Both records in `out/addresses.json` are this PC on **KUWIFI**, a few minutes apart. A second network was not available, so this is not a campus-versus-tethering comparison. Nothing below is a classmate's address.

## This network

Read from `ipconfig /all` on the MediaTek Wi-Fi adapter, not from a parsed field:

| | |
|---|---|
| interface address | `172.16.24.87` |
| mask | `255.255.255.0` (`/24`) |
| default gateway | `172.16.24.1` |
| DHCP server | `192.168.98.23` |
| public address (ipify) | `163.152.233.24` |

The subnet is `172.16.24.0/24`. By hand: the network address is `172.16.24.0`, the broadcast is `172.16.24.255`, and the usable hosts are `172.16.24.1` through `172.16.24.254`. `network_range("172.16.24.0/24")` in Task 1 returns that same triple.

`172.16.24.1` is inside that usable range. It has to be. The host reaches its gateway by ARP on this link, and ARP only resolves an address in the connected subnet. A gateway outside `172.16.24.0/24` would itself need a route, which is the thing the gateway is supposed to be.

The DHCP server `192.168.98.23` is **not** in that range. That is a relay, not a second subnet of this host: the on-link gateway forwards the DHCP exchange to a server that lives on another campus network.

## How many NATs

`172.16.24.87` is RFC 1918. `163.152.233.24` is not, and it is not in `100.64.0.0/10`. ipify is outside the campus, so the address it reports is the one on the public Internet. That is **one NAT**: the campus translates `172.16.24.87` to `163.152.233.24`.

A second NAT, the usual carrier-grade one, would hide `163.152.233.24` as well. ipify would then see the provider's address, often with `100.64.0.0/10` on the near side of that outer translator. It does not.

`tracert -d 1.1.1.1` agrees. The first replies are still private (`172.16.0.2`, then `192.168.98.132`, the same network as the DHCP server). The next hop is `163.152.233.129`, in the same `/24` as the public address. After that the path enters `175.121.235.141` and later shows `10.103.0.142` and `10.222.25.128`. Those `10.x` addresses are router interfaces inside the provider. They are not this host's source address: ipify still saw `163.152.233.24`, so the provider is not translating it.

The immediate configured gateway `172.16.24.1` did not answer the traceroute. The first ICMP time-exceeded came from `172.16.0.2`.

## The two records

| | KUWIFI | KUWIFI, minutes later |
|---|---|---|
| private | `172.16.24.87/24` | `172.16.24.87/24` |
| gateway | `172.16.24.1` | `172.16.24.1` |
| public | `163.152.233.24` | `163.152.233.24` |

The public address did not change. The private address did not change. Both samples are the same attachment, so there is no second network in which either one could have changed. What this weakens: it does not show that moving to a phone network would change the public address, the private prefix, or the number of NATs.

## Part C · DHCP, from the textbook trace

Interface capture is blocked here (`pktmon` access denied, no Npcap), and a DORA only happens on join. `out/dhcp.pcapng` is the 9th-edition DHCP trace, not this PC. The client calls itself `MacBook-Pro-6` and is offered `192.168.86.65` by `192.168.86.1`. This machine is `172.16.24.87` on KUWIFI.

| message | frame | source | destination |
|---|---:|---|---|
| Discover | 5 | `0.0.0.0:68` | `255.255.255.255:67` |
| Offer | 12 | `192.168.86.1:67` | `192.168.86.65:68` |
| Request | 16 | `0.0.0.0:68` | `255.255.255.255:67` |
| Ack | 17 | `192.168.86.1:67` | `192.168.86.65:68` |

Discover's source is `0.0.0.0` because the client has no address yet. It cannot be the address it is asking for. The destination has to be the limited broadcast: the client does not know which server will answer, and it has no subnet broadcast of its own.

The Discover asks for a lease of 7776000 seconds. The Offer and the Ack grant **86400 seconds** (one day), with renewal time 43200 and rebinding time 75600. Half of 86400 is 43200, which is T1. At T1 the client unicasts a DHCPREQUEST to `192.168.86.1` to extend the same lease. At T2, seven eighths of the lease, that renewal has failed and the client broadcasts to find any server.

The Ack does not have to be a broadcast. Between Discover and Ack the server has learned the client's hardware address and has chosen `192.168.86.65` (`yiaddr`). It can send the Ack to that address. Discover and Request stay at `0.0.0.0` because the client has not bound the address yet.

> Wireshark lab trace files from J.F. Kurose and K.W. Ross,
> *Computer Networking: A Top-Down Approach*, 9th ed.
> <https://gaia.cs.umass.edu/kurose_ross/>
> Copyright 1996-2025 J.F. Kurose, K.W. Ross. All Rights Reserved.
