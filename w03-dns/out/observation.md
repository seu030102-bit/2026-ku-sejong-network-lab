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

---

## 한글

### Task 1

루트 서버는 `www.korea.ac.kr`의 주소를 바로 주지 않았다. `out/dns.pcapng` 프레임 2(트랜잭션 ID 29346)는 응답 개수가 0이고, authority 구간에 `.kr`의 `NS` 레코드가 여섯 개 있다. 루트는 루트 존만 담당하므로 TLD를 위임할 수 있을 뿐, 그 호스트 이름에 답할 수 없다. 이 조회는 서버 세 곳(`198.41.0.4`, `210.101.61.1`, `163.152.11.6`)에 물어 봤다. 노트북은 보통 재귀 리졸버에 한 번만 묻는다.

글루 `A` 레코드 없이 위임이 오면, 그 네임서버 이름을 루트부터 다시 반복 조회한 뒤 이어서 진행했다. `www.stanford.edu`는 이것을 일곱 번 했다(`ns5`–`ns7.dnsmadeeasy.com`과 `nsone.net` 이름 네 개). 그래서 그 이름 하나에 질의가 27번 나갔다. `www.microsoft.com`은 세 번이었다. `azure-dns.net`, `.org`, `.info`는 위임한 존 밖에 있어서다. `www.korea.ac.kr`은 두 번의 위임에 글루가 다 있어서 추가 조회가 없었다.

### Task 2

위임과 응답은 같은 DNS 메시지이고, 채워진 구간만 다르다. 프레임 2는 응답 개수 0, `NS` 여섯 개, AA 비트가 꺼져 있다. 프레임 6(ID 9556)은 AA 비트가 켜져 있고, answer 구간에 `A` 레코드 `163.152.6.10`이 하나 있다.

제3자 판정 규칙은 원래 이름과 마지막 CNAME의 끝 두 라벨을 비교하고, CNAME이 없으면 제3자가 아니라고 본다. `www.wikipedia.org`에서 틀린다. 체인이 `dyna.wikimedia.org`로 끝나 라벨이 달라 제3자로 보이지만, 둘 다 위키미디어가 운영하고 세 리졸버 모두 `103.102.166.224`를 줬다. 같은 자르기는 `www.korea.ac.kr`과 `www.bbc.co.uk`의 이름도 제대로 못 붙인다. 공공 접미사(`ac.kr`, `co.uk`)만 남기기 때문이다.

CDN을 쓰는 이름만 세고 `www.korea.ac.kr`은 빼면, **11개 중 8개**가 리졸버(시스템, `8.8.8.8`, Quad9)마다 다른 주소를 줬다. 주장 (b)를 일부만 뒷받침한다. 이 PC는 네트워크를 옮기지 않았다. Google은 대개 시스템 리졸버와 같았고 Quad9는 다른 경우가 많아서, 바뀐 것은 노트북 위치가 아니라 어느 리졸버가 답했는가이다.

### Task 3

`BaselineCache`는 TTL을 무시하고 모든 레코드를 60초 동안 보관한다. 그 한 가지 실수가 두 버그다. TTL이 60초보다 짧은 레코드는 만료된 뒤에도 나가고, 60초보다 긴 레코드는 너무 일찍 버려진다. 가장 심한 이름은 `www.microsoft.com`이다. TTL이 20초이고 워크로드에서 가장 자주 묻혀서, 322번 중 189번이 만료된 답이었다. 전체 stale 266개 중 189개다. `dns.google`과 `a.root-servers.net`(TTL 86400초)은 성능 쪽이다. 모의 한 시간 동안 한 번이면 될 조회를 약 20번 했다.

하한은 upstream **275**회다. 올바른 캐시는 조회 시각에 TTL을 더한 시각을 지나면 답하면 안 되고, 그보다 일찍 다시 물으면 조회만 늘어난다. 그래서 레코드를 정확히 TTL 동안만 보관하는 캐시의 미스 횟수보다 아래로 갈 수 없다. `YourCache`가 upstream 275회, stale 0이고, 그 수가 하한이다.
