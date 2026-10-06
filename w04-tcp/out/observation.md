## Task 1

Stop-and-wait, not a sliding window. The channel duplicates packets and loses ACKs, and a duplicate data packet must be acknowledged without being appended a second time. With one numbered chunk in flight, an ACK counts only when its number is that chunk, so a late ACK for an earlier chunk cannot open the next one. Reordering never delivers a future chunk, because a future chunk is not sent yet. That is the case that made the smaller protocol the one that stays correct.

Seed 246 moved 2,000 bytes as 250 chunks of 8 bytes. The data channel sent 318 packets (40 lost, 8 duplicated). The minimum is 250, so reliability cost about 1.27 data packets per chunk. Loss is what the timer is for. Duplication is what would have corrupted the file if the receiver had appended every arrival.

스톱앤웨이트이고, 슬라이딩 윈도우가 아니다. 채널은 패킷을 복제하고 ACK를 잃는다. 중복된 데이터 패킷은 다시 붙이지 않고 ACK만 해야 한다. 번호가 있는 청크는 한 번에 하나만 나가므로, ACK는 그 청크 번호일 때만 인정된다. 그래서 이전 청크의 늦은 ACK가 다음 청크를 열 수 없다. 재정렬은 미래의 청크를 전달하지 않는다. 미래의 청크는 아직 보내지 않기 때문이다. 더 작은 프로토콜이 맞게 남는 경우가 이것이다.

시드 246은 2,000바이트를 8바이트 청크 250개로 옮겼다. 데이터 채널은 패킷 318개를 보냈다(40개 손실, 8개 중복). 최소는 250이므로, 신뢰성 비용은 청크당 데이터 패킷 약 1.27개다. 손실은 타이머가 있는 이유다. 중복은, 수신자가 도착하는 것마다 붙였다면 파일을 망가뜨렸을 것이다.

## Task 2

Interface capture was blocked (`pktmon` access denied, no Npcap), so Part A is the 9th-edition Wireshark Lab TCP trace `tcp-wireshark-trace1-1.pcapng`, not this PC. Frames 1, 2 and 3 are the handshake on `192.168.86.68:55639` to `128.119.245.12:80`. The client initial sequence number is 4236649187 and the server's is 1068969752. They are not zero, and not each other, so a delayed segment from an old connection on the same ports is not accepted as part of this one. The SYN offers MSS 1460, window scale 6 and SACK permitted. The SYN-ACK offers MSS 1460, window scale 7 and SACK permitted. The POST is to `gaia.cs.umass.edu` `/wireshark-labs/lab3-1-reply.htm` (HTTP date 3 Feb 2021). The private client address and that URL are how the capture identifies someone else's textbook upload.

After the handshake the server's window field is scaled by 2^7. At frame 145 the scaled advertised window was 173824 bytes and the bytes in flight peaked at 75296. Early on, three 1448-byte segments (4344 bytes) were outstanding against a scaled window of 31872. The receiver window was never full, so it was not the limit. §3.7's other limit is the congestion window over the RTT: the sender was not filling the room the receiver had offered.

Both throughput samples are this PC on KUWIFI, minutes apart, not two networks and not two times of day. First sample: median 82.82 Mbps, spread 66.22–94.86 (35%), handshake median 10.7 ms. Second: median 84.77 Mbps, spread 83.69–99.24 (18%), handshake median 11.4 ms. The spread on one network is Wi-Fi contention plus a 5 MB transfer that is still partly in slow start; handshake outliers of about 40 ms did not line up with the slow runs. Because the path did not change, this does not show that a worse handshake costs throughput. The §3.7 mechanism, if a second path had a longer RTT, is that throughput is about the congestion window divided by RTT, and slow start needs more round trips to open that window.

> Wireshark lab trace files from J.F. Kurose and K.W. Ross,
> *Computer Networking: A Top-Down Approach*, 9th ed.
> <https://gaia.cs.umass.edu/kurose_ross/>
> Copyright 1996-2025 J.F. Kurose, K.W. Ross. All Rights Reserved.

인터페이스 캡처는 막혀 있었다(`pktmon` 접근 거부, Npcap 없음). 그래서 Part A는 9판 Wireshark Lab TCP 트레이스 `tcp-wireshark-trace1-1.pcapng`이고, 이 PC의 캡처가 아니다. 프레임 1, 2, 3은 `192.168.86.68:55639`에서 `128.119.245.12:80`으로 가는 핸드셰이크다. 클라이언트 초기 순서 번호는 4236649187이고 서버는 1068969752다. 둘 다 0이 아니고 서로 같지도 않다. 그래서 같은 포트의 옛 연결에서 늦어진 세그먼트는 이 연결의 일부로 받아들여지지 않는다. SYN은 MSS 1460, 윈도우 스케일 6, SACK 허용을 제안한다. SYN-ACK는 MSS 1460, 윈도우 스케일 7, SACK 허용을 제안한다. POST는 `gaia.cs.umass.edu`의 `/wireshark-labs/lab3-1-reply.htm`이다(HTTP 날짜 2021년 2월 3일). 사설 클라이언트 주소와 그 URL이, 이 캡처가 다른 사람의 교재 업로드임을 보여 준다.

핸드셰이크 이후 서버의 윈도우 필드는 2^7로 스케일된다. 프레임 145에서 스케일된 광고 윈도우는 173824바이트였고, 전송 중인 바이트는 75296에서 정점을 찍었다. 초반에는 1448바이트 세그먼트 세 개(4344바이트)가 스케일된 윈도우 31872에 대해 나가 있었다. 수신 윈도우는 한 번도 가득 차지 않았으므로 한계가 아니었다. §3.7의 다른 한계는 RTT 동안의 혼잡 윈도우다. 송신자는 수신자가 내준 여유를 채우지 않았다.

처리량 표본 둘 다 이 PC의 KUWIFI이고, 몇 분 간격이다. 네트워크가 둘도 아니고 하루 중 다른 시각도 아니다. 첫 표본은 중앙값 82.82 Mbps, 범위 66.22–94.86(35%), 핸드셰이크 중앙값 10.7 ms다. 둘째는 중앙값 84.77 Mbps, 범위 83.69–99.24(18%), 핸드셰이크 중앙값 11.4 ms다. 한 네트워크에서의 폭은 Wi-Fi 경합과, 아직 슬로 스타트에 일부 있는 5 MB 전송 때문이다. 약 40 ms의 핸드셰이크 이상치는 느린 실행과 맞지 않았다. 경로가 바뀌지 않았으므로, 더 나쁜 핸드셰이크가 처리량을 깎는다는 것을 보여 주지 않는다. 둘째 경로의 RTT가 더 길었다면 §3.7의 메커니즘은, 처리량이 대략 혼잡 윈도우를 RTT로 나눈 값이고 슬로 스타트는 그 윈도우를 여는 데 왕복이 더 필요하다는 것이다.

## Task 3

The baseline's goodput, 986.8 per 1000 slots, is the highest because a window of 64 keeps the pipe and the queue full. It is still the worst sender: average queue 8.8, loss 37.4%, 2340 retransmissions. Any other flow on this link waits behind that queue. Goodput of the greedy flow is not the cost that matters.

`YourControl` slow-starts and then holds the window at 24. The pipe holds about 20 packets (1 packet per slot times a 20-slot RTT) and the queue holds 10, so 24 leaves the pipe full and about four packets of queue. The harness measured average queue 3.9, loss 0, goodput 977.8, which is 99% of the baseline.

Uncapped AIMD that halves on a loss landed at goodput 807.2, loss 1.9%, average queue 2.9. Making the backoff gentler, multiplying by 0.8 instead of 0.5, raised goodput to 915.0 and pushed the average queue to 5.2, which misses the queue cap. The gentler cut bought throughput by sitting closer to the drop. Holding at 24 never enters that region, so the backoff does not have to run.

기준선의 goodput 986.8/1000 슬롯이 가장 높은 이유는 윈도우 64가 파이프와 큐를 가득 채우기 때문이다. 그래도 가장 나쁜 송신자다. 평균 큐 8.8, 손실 37.4%, 재전송 2340이다. 이 링크의 다른 흐름은 그 큐 뒤에서 기다린다. 욕심 많은 흐름의 goodput이 중요한 비용은 아니다.

`YourControl`은 슬로 스타트한 뒤 윈도우를 24에 고정한다. 파이프는 약 20패킷(슬롯당 1패킷 × RTT 20슬롯)이고 큐는 10이므로, 24는 파이프를 채우고 큐에 약 네 패킷을 남긴다. 하네스 측정은 평균 큐 3.9, 손실 0, goodput 977.8이고, 기준선의 99%다.

손실 때 반으로 줄이는 상한 없는 AIMD는 goodput 807.2, 손실 1.9%, 평균 큐 2.9에 닿았다. 백오프를 부드럽게 해서 0.5 대신 0.8을 곱하면 goodput은 915.0으로 오르고 평균 큐는 5.2가 되어 큐 상한을 넘긴다. 더 부드러운 감소는 드롭에 더 가까이 앉아서 처리량을 산 것이다. 24에 고정하면 그 영역에 들어가지 않으므로 백오프가 돌 필요가 없다.
