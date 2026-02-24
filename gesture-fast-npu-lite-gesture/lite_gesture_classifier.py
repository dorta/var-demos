#!/usr/bin/env python3

from collections import deque
from dataclasses import dataclass


@dataclass
class GestureResult:
    label: str
    score: float


class LiteGestureClassifier:
    """Very lightweight gesture classifier based on hand box trajectory.

    Labels:
    - NO_HAND
    - STILL
    - MOVE_LEFT / MOVE_RIGHT / MOVE_UP / MOVE_DOWN
    - WAVE
    """

    def __init__(self, history_size=12):
        self.history = deque(maxlen=history_size)

    def reset(self):
        self.history.clear()

    def update(self, center_xy, now_s):
        if center_xy is None:
            self.reset()
            return GestureResult("NO_HAND", 1.0)

        x, y = center_xy
        self.history.append((float(x), float(y), float(now_s)))

        if len(self.history) < 4:
            return GestureResult("STILL", 0.2)

        xs = [p[0] for p in self.history]
        ys = [p[1] for p in self.history]
        ts = [p[2] for p in self.history]

        dx = xs[-1] - xs[0]
        dy = ys[-1] - ys[0]
        span_x = max(xs) - min(xs)
        span_y = max(ys) - min(ys)
        dt = max(ts[-1] - ts[0], 1e-6)

        vx = dx / dt
        vy = dy / dt

        signs = []
        for i in range(1, len(xs) - 1):
            dv = xs[i + 1] - xs[i]
            if abs(dv) > 2.0:
                signs.append(1 if dv > 0 else -1)

        sign_changes = 0
        for i in range(1, len(signs)):
            if signs[i] != signs[i - 1]:
                sign_changes += 1

        if span_x > 80 and span_y < 90 and sign_changes >= 2:
            conf = min(1.0, 0.45 + 0.12 * sign_changes)
            return GestureResult("WAVE", conf)

        if abs(vx) > 140 and abs(vx) > abs(vy) * 1.2:
            return GestureResult("MOVE_RIGHT" if vx > 0 else "MOVE_LEFT", min(1.0, abs(vx) / 350.0))

        if abs(vy) > 140 and abs(vy) > abs(vx) * 1.2:
            return GestureResult("MOVE_DOWN" if vy > 0 else "MOVE_UP", min(1.0, abs(vy) / 350.0))

        motion = (span_x + span_y) / max(len(self.history), 1)
        if motion < 8.0:
            return GestureResult("STILL", 0.9)

        return GestureResult("STILL", 0.4)
