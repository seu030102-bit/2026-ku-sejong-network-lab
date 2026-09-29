## Task 1

Stop-and-wait, not a sliding window. The channel duplicates packets and loses ACKs, and a duplicate data packet must be acknowledged without being appended a second time. With one numbered chunk in flight, an ACK counts only when its number is that chunk, so a late ACK for an earlier chunk cannot open the next one. Reordering never delivers a future chunk, because a future chunk is not sent yet. That is the case that made the smaller protocol the one that stays correct.

Seed 246 moved 2,000 bytes as 250 chunks of 8 bytes. The data channel sent 318 packets (40 lost, 8 duplicated). The minimum is 250, so reliability cost about 1.27 data packets per chunk. Loss is what the timer is for. Duplication is what would have corrupted the file if the receiver had appended every arrival.

## Task 2

Interface capture was blocked (`pktmon` access denied, no Npcap), so Part A is the 9th-edition Wireshark Lab TCP trace `tcp-wireshark-trace1-1.pcapng`, not this PC. Frames 1, 2 and 3 are the handshake on `192.168.86.68:55639` to `128.119.245.12:80`. The client initial sequence number is 4236649187 and the server's is 1068969752. They are not zero, and not each other, so a delayed segment from an old connection on the same ports is not accepted as part of this one. The SYN offers MSS 1460, window scale 6 and SACK permitted. The SYN-ACK offers MSS 1460, window scale 7 and SACK permitted. The POST is to `gaia.cs.umass.edu` `/wireshark-labs/lab3-1-reply.htm` (HTTP date 3 Feb 2021). The private client address and that URL are how the capture identifies someone else's textbook upload.

After the handshake the server's window field is scaled by 2^7. At frame 145 the scaled advertised window was 173824 bytes and the bytes in flight peaked at 75296. Early on, three 1448-byte segments (4344 bytes) were outstanding against a scaled window of 31872. The receiver window was never full, so it was not the limit. §3.7's other limit is the congestion window over the RTT: the sender was not filling the room the receiver had offered.

Both throughput samples are this PC on KUWIFI, minutes apart, not two networks and not two times of day. First sample: median 82.82 Mbps, spread 66.22–94.86 (35%), handshake median 10.7 ms. Second: median 84.77 Mbps, spread 83.69–99.24 (18%), handshake median 11.4 ms. The spread on one network is Wi-Fi contention plus a 5 MB transfer that is still partly in slow start; handshake outliers of about 40 ms did not line up with the slow runs. Because the path did not change, this does not show that a worse handshake costs throughput. The §3.7 mechanism, if a second path had a longer RTT, is that throughput is about the congestion window divided by RTT, and slow start needs more round trips to open that window.

> Wireshark lab trace files from J.F. Kurose and K.W. Ross,
> *Computer Networking: A Top-Down Approach*, 9th ed.
> <https://gaia.cs.umass.edu/kurose_ross/>
> Copyright 1996-2025 J.F. Kurose, K.W. Ross. All Rights Reserved.

## Task 3

The baseline's goodput, 986.8 per 1000 slots, is the highest because a window of 64 keeps the pipe and the queue full. It is still the worst sender: average queue 8.8, loss 37.4%, 2340 retransmissions. Any other flow on this link waits behind that queue. Goodput of the greedy flow is not the cost that matters.

`YourControl` slow-starts and then holds the window at 24. The pipe holds about 20 packets (1 packet per slot times a 20-slot RTT) and the queue holds 10, so 24 leaves the pipe full and about four packets of queue. The harness measured average queue 3.9, loss 0, goodput 977.8, which is 99% of the baseline.

Uncapped AIMD that halves on a loss landed at goodput 807.2, loss 1.9%, average queue 2.9. Making the backoff gentler, multiplying by 0.8 instead of 0.5, raised goodput to 915.0 and pushed the average queue to 5.2, which misses the queue cap. The gentler cut bought throughput by sitting closer to the drop. Holding at 24 never enters that region, so the backoff does not have to run.
