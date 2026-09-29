#!/usr/bin/env python3
"""Week 4 · Task 1 — Build reliable delivery on top of an unreliable channel.

Textbook §3.4 (reliable data transfer) and §3.5 (TCP's sequence numbers).

`UnreliableChannel` below loses packets, reorders them, duplicates them, and
delays them. It is the network as §3.4 models it. Your job is to move a file
across it and have the bytes arrive intact and in order.

That is the whole of TCP's reliability story with the congestion control taken
out, and it is worth building once by hand before you ever trust a socket again.

    python3 task1_rdt.py --verify
"""
import argparse, hashlib, random

PAYLOAD = 8            # bytes per packet - small, so you see the sequencing


class UnreliableChannel:
    """Loses 10%, duplicates 3%, reorders, and delays. Deterministic by seed.

    You may not make it nicer. You may not read its internals. It is the only
    way your sender can reach your receiver.
    """

    def __init__(self, seed=246, loss=0.10, dup=0.03, reorder=0.10):
        self.rng = random.Random(seed)
        self.loss, self.dup, self.reorder = loss, dup, reorder
        self.wire = []          # packets in flight, in no particular order
        self.stats = {"sent": 0, "lost": 0, "duplicated": 0, "delivered": 0}

    def send(self, packet):
        """Hand a packet to the network. It may never come out."""
        self.stats["sent"] += 1
        if self.rng.random() < self.loss:
            self.stats["lost"] += 1
            return
        copies = 2 if self.rng.random() < self.dup else 1
        self.stats["duplicated"] += copies - 1
        for _ in range(copies):
            if self.rng.random() < self.reorder and self.wire:
                self.wire.insert(self.rng.randrange(len(self.wire)), packet)
            else:
                self.wire.append(packet)

    def receive(self):
        """Take the next packet out, or None if the network has nothing."""
        if not self.wire:
            return None
        self.stats["delivered"] += 1
        return self.wire.pop(0)


class Sender:
    """Stop-and-wait. One numbered chunk in flight, retransmit on silence.

    A sliding window would also pass, but a duplicate ACK and a reordered data
    packet both show up here, and stop-and-wait makes the two failures
    different: an ACK counts only when its number is the one in flight, and a
    repeated data number is the receiver's problem, not a second copy of the
    bytes. The channel keeps the packet object it was given, so each send is a
    fresh tuple.
    """

    TIMEOUT = 8

    def __init__(self, data_channel, ack_channel, data):
        self.data_channel = data_channel
        self.ack_channel = ack_channel
        self.chunks = [data[i:i + PAYLOAD] for i in range(0, len(data), PAYLOAD)]
        self.next_seq = 0
        self.inflight = None
        self.quiet = 0

    def step(self):
        if self.next_seq >= len(self.chunks) and self.inflight is None:
            return False
        ack = self.ack_channel.receive()
        while ack is not None:
            if (isinstance(ack, tuple) and ack[0] == "ACK"
                    and self.inflight is not None and ack[1] == self.inflight):
                self.inflight = None
                self.quiet = 0
                self.next_seq += 1
            ack = self.ack_channel.receive()
        if self.next_seq >= len(self.chunks):
            return False
        if self.inflight is None:
            self.inflight = self.next_seq
            self.quiet = 0
            self._send(self.inflight)
        else:
            self.quiet += 1
            if self.quiet >= self.TIMEOUT:
                self.quiet = 0
                self._send(self.inflight)
        return True

    def _send(self, seq):
        self.data_channel.send(("DATA", seq, self.chunks[seq]))


class Receiver:
    """Reassemble by sequence number. A duplicate is ACKed and not appended."""

    def __init__(self, data_channel, ack_channel):
        self.data_channel = data_channel
        self.ack_channel = ack_channel
        self.expected = 0
        self.buf = bytearray()

    def step(self):
        pkt = self.data_channel.receive()
        while pkt is not None:
            if isinstance(pkt, tuple) and pkt[0] == "DATA":
                _, seq, payload = pkt
                if seq == self.expected:
                    self.buf.extend(payload)
                    self.expected += 1
                if seq < self.expected:
                    self.ack_channel.send(("ACK", seq))
            pkt = self.data_channel.receive()

    def data(self):
        return bytes(self.buf)


# ------------------------------------------------------------------- harness
def verify(seed=246, size=2000, max_steps=200_000):
    original = bytes(random.Random(seed).getrandbits(8) for _ in range(size))
    up, down = UnreliableChannel(seed), UnreliableChannel(seed + 1)

    # Data goes out over `up`, ACKs come back over `down`. Both are unreliable.
    sender = Sender(up, down, original)
    receiver = Receiver(up, down)

    for _ in range(max_steps):
        alive = sender.step()
        receiver.step()
        if not alive and len(receiver.data() or b"") >= size:
            break

    got = receiver.data() or b""
    ok = hashlib.sha256(got).hexdigest() == hashlib.sha256(original).hexdigest()
    print(f"  bytes    sent {size}   received {len(got)}")
    print(f"  channel  {up.stats}")
    print(f"  result   {'IDENTICAL' if ok else 'CORRUPTED OR INCOMPLETE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    p.add_argument("--seed", type=int, default=246)
    a = p.parse_args()
    raise SystemExit(verify(a.seed) if a.verify else p.print_help())
