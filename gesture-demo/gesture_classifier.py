#!/usr/bin/env python3

from collections import Counter, deque
from math import acos, degrees
from typing import Dict, Optional

import numpy as np


class GestureClassifier:
    def __init__(self) -> None:
        self._history = deque(maxlen=6)

    @staticmethod
    def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
        ba = a - b
        bc = c - b
        denom = (np.linalg.norm(ba) * np.linalg.norm(bc)) + 1e-6
        cos_val = float(np.clip(np.dot(ba, bc) / denom, -1.0, 1.0))
        return degrees(acos(cos_val))

    @staticmethod
    def _is_extended(points: np.ndarray, mcp: int, pip: int, tip: int, wrist: int = 0) -> bool:
        ang = GestureClassifier._angle(points[mcp], points[pip], points[tip])
        d_tip = np.linalg.norm(points[tip] - points[wrist])
        d_pip = np.linalg.norm(points[pip] - points[wrist])
        return ang > 155.0 and d_tip > (d_pip * 1.07)

    def classify(self, points: Optional[np.ndarray]) -> str:
        if points is None or len(points) < 21:
            self._history.clear()
            return "No hand"

        ext: Dict[str, bool] = {
            "thumb": self._is_extended(points, 2, 3, 4),
            "index": self._is_extended(points, 5, 6, 8),
            "middle": self._is_extended(points, 9, 10, 12),
            "ring": self._is_extended(points, 13, 14, 16),
            "pinky": self._is_extended(points, 17, 18, 20),
        }

        count = sum(ext.values())

        if count == 0:
            label = "Fist"
        elif count >= 4:
            label = "Open Palm"
        elif ext["index"] and ext["middle"] and not ext["ring"] and not ext["pinky"]:
            label = "Peace"
        elif ext["index"] and not ext["middle"] and not ext["ring"] and not ext["pinky"]:
            label = "Point"
        elif ext["thumb"] and not ext["index"] and not ext["middle"] and not ext["ring"] and not ext["pinky"]:
            label = "Thumbs Up" if points[4][1] < points[3][1] else "Thumbs Down"
        elif ext["thumb"] and ext["index"] and not ext["middle"] and not ext["ring"] and not ext["pinky"]:
            label = "L"
        else:
            label = "Unknown"

        self._history.append(label)
        stable, freq = Counter(self._history).most_common(1)[0]
        if freq >= max(2, len(self._history) // 2):
            return stable
        return label
