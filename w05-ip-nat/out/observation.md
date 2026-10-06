## Task 1

For `/30` and shorter, the network address and the all-ones address are reserved, so the usable hosts sit between them. `/31` and `/32` have no such middle. RFC 3021 makes both addresses of a `/31` ordinary hosts and drops the broadcast, and a `/32` is one host. `network_range` returns those addresses in every slot: `/31` is `(low, high, high)` and `/32` is `(addr, addr, addr)`. The third value is not a separate broadcast.

`10.20.30.70` matches five entries: `0.0.0.0/0` (default-gw), `10.0.0.0/8` (campus), `10.20.0.0/16` (eng-building), `10.20.30.0/24` (lab-floor), and `10.20.30.64/26` (lab-rack-2). The four `10` prefixes are the ones the harness comment means. Longest prefix wins, so `/26` and `lab-rack-2`. If the same prefix were added twice with different next hops, the first next hop stays and the later one is ignored. The table is malformed either way, and a silent overwrite would be harder to see.

`/30` 이하에서는 네트워크 주소와 모두 1인 주소가 예약되므로, 쓸 수 있는 호스트는 그 사이에 있다. `/31`과 `/32`에는 그런 중간이 없다. RFC 3021은 `/31`의 두 주소를 모두 일반 호스트로 두고 브로드캐스트를 없애며, `/32`는 호스트 하나다. `network_range`는 그 주소를 모든 칸에 넣는다. `/31`은 `(low, high, high)`이고 `/32`는 `(addr, addr, addr)`이다. 세 번째 값은 따로 떨어진 브로드캐스트가 아니다.

`10.20.30.70`은 다섯 항목에 맞는다. `0.0.0.0/0`(default-gw), `10.0.0.0/8`(campus), `10.20.0.0/16`(eng-building), `10.20.30.0/24`(lab-floor), `10.20.30.64/26`(lab-rack-2). `10`으로 시작하는 네 접두사가 하네스 주석이 말하는 것이다. 가장 긴 접두사가 이기므로 `/26`과 `lab-rack-2`다. 같은 접두사가 다음 홉만 다르게 두 번 들어오면 먼저 넣은 다음 홉이 남고 나중 것은 무시된다. 어느 쪽이든 표는 잘못된 것이고, 조용히 덮어쓰면 더 알아보기 어렵다.

## Task 2

This PC is behind **one NAT**. The Wi-Fi address is `172.16.24.87/24` (RFC 1918), the gateway `172.16.24.1` is inside that subnet, and ipify sees `163.152.233.24`, which is public and not in `100.64.0.0/10`. A second, carrier-grade NAT would have hidden that `163.152` address too. Traceroute shows private campus hops (`172.16.0.2`, `192.168.98.132`) and then `163.152.233.129` before the provider. The later `10.x` hops are provider router interfaces, not this host's source address.

Both labelled records are KUWIFI minutes apart. The private address, the mask, the gateway, and the public address were the same, because the network did not change. In the textbook DHCP trace, Discover is frame 5, `0.0.0.0:68` to `255.255.255.255:67`. The source cannot be anything else: the client has no address yet, so it also cannot name a server and has to broadcast. The granted lease is 86400 seconds. At half of that (43200 s, T1) the client unicasts a renewal to the server that answered.

이 PC는 NAT **하나** 뒤에 있다. Wi-Fi 주소는 `172.16.24.87/24`(RFC 1918)이고, 게이트웨이 `172.16.24.1`은 그 서브넷 안이며, ipify가 보는 주소는 `163.152.233.24`다. 이것은 공인이고 `100.64.0.0/10`에 없다. 두 번째인 캐리어급 NAT가 있었다면 그 `163.152` 주소도 가렸을 것이다. 트레이스라우트는 사설 캠퍼스 홉(`172.16.0.2`, `192.168.98.132`) 다음에 `163.152.233.129`를 거쳐 사업자로 간다. 그 뒤의 `10.x` 홉은 사업자 라우터 인터페이스이고, 이 호스트의 출발 주소가 아니다.

두 라벨 모두 KUWIFI를 몇 분 간격으로 잰 것이다. 사설 주소, 마스크, 게이트웨이, 공인 주소가 같았다. 네트워크가 바뀌지 않았기 때문이다. 교재 DHCP 트레이스에서 Discover는 프레임 5이고, `0.0.0.0:68`에서 `255.255.255.255:67`로 간다. 출발 주소는 다른 것일 수 없다. 클라이언트는 아직 주소가 없어서 서버를 지목할 수도 없고, 브로드캐스트해야 한다. 부여된 임대는 86400초다. 그 절반(43200초, T1)에 클라이언트는 응답한 서버로 유니캐스트 갱신을 보낸다.

## Task 3

`YourTable` is one dict per prefix length, probed from the longest length present down, stopping at the first hit. Memory is one entry per prefix (5,000 here) plus the empty length dicts that were never filled. Lookup time is proportional to the number of **distinct lengths** in the table, at most 33, not to the number of routes. On this harness that was 1795× the linear scan, 0.020 s against 36.6 s, with no wrong answers.

Hardware still walks the address one bit at a time. That walk is a fixed 32 steps and pipelines. A hash table is variable work and a poor fit for a forwarding ASIC. In CPython the dict probe is one C call and a trie node is an object chase, so the hash tables are faster here even though they are the worse machine.

`YourTable`은 접두사 길이마다 딕셔너리 하나다. 표에 있는 가장 긴 길이부터 내려가며 찾고, 처음 맞는 곳에서 멈춘다. 메모리는 접두사당 항목 하나(여기서 5,000개)와, 채우지 않은 빈 길이 딕셔너리다. 조회 시간은 경로 개수가 아니라 표에 있는 **서로 다른 길이**의 개수에 비례하고, 최대 33이다. 이 하네스에서는 선형 탐색의 1795배였고, 36.6초 대비 0.020초, 오답은 0이다.

하드웨어는 여전히 주소를 한 비트씩 걷는다. 그 걷기는 32단계로 고정되고 파이프라인된다. 해시 테이블은 일이 가변적이고 포워딩 ASIC에 맞지 않다. CPython에서는 딕셔너리 탐색이 C 호출 하나이고 트라이 노드는 객체 따라가기이므로, 여기서는 해시 테이블이 더 나쁘게 맞는 기계인데도 더 빠르다.
