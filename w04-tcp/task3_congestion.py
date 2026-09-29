#!/usr/bin/env python3
"""Week 4 · Task 3 — Beat the fixed window.

Textbook §3.7.

`FixedWindow` is a sender that never adapts. It picks a window and keeps it,
forever, no matter what the network says back. It is not a strawman: it is what
you get if you skip congestion control entirely, and it was the internet's
actual failure mode in October 1986.

Write `YourControl` and beat it on the harness:

    python3 bench.py
    python3 bench.py --yours

The interface is two events and one number:

    .window        how many packets you are willing to have in flight
    .on_ack()      one packet made it there and back
    .on_loss()     a packet was dropped, or timed out waiting for its ACK

That is all the information a real TCP sender has. It cannot see the queue,
it cannot see the link rate, and neither can you. You infer them from these
two events, which is the entire idea of §3.7.
"""


class FixedWindow:
    """Send 64 packets at a time and never listen."""

    def __init__(self):
        self.window = 64

    def on_ack(self):
        pass

    def on_loss(self):
        pass


class YourControl:
    """Slow start, then hold near the bandwidth-delay product.

    The link moves one packet per slot and the round trip is 20 slots, so about
    20 packets fill the pipe. The queue holds 10 more and then tail-drops. A
    window parked around 24 keeps the pipe full and the queue near 4, which is
    under the harness caps (loss 5%, average queue 5). Textbook AIMD keeps
    climbing until it hits that drop and then saws between half and full, so
    its average window spends time below the pipe and its goodput falls to
    about 82% of the fixed window.

    on_loss fires once per timed-out packet, and one burst can time out many
    packets in the same slot. Halving on every one of those calls would collapse
    the window, so a burst counts as a single loss.
    """

    PIPE = 20
    TARGET = 24

    def __init__(self):
        self.window = 1.0
        self.ssthresh = float(self.TARGET)
        self._cut = False

    def on_ack(self):
        self._cut = False
        if self.window < self.ssthresh:
            self.window += 1.0
        elif self.window < self.TARGET:
            self.window += 1.0 / self.window
        else:
            self.window = float(self.TARGET)

    def on_loss(self):
        if self._cut:
            return
        self._cut = True
        self.ssthresh = max(self.PIPE / 2, self.window / 2)
        self.window = max(1.0, self.window / 2)
