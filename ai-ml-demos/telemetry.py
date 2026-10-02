# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path
from time import monotonic


class SoCTemperature:
    """Read the SoC sensor at most once per second, not on every frame."""

    def __init__(self, thermal_root='/sys/class/thermal'):
        self.root = Path(thermal_root)
        self.sensor = None
        self.next_read = 0
        self.value = None

    def read(self):
        now = monotonic()
        if now < self.next_read:
            return self.value
        self.next_read = now + 1
        try:
            if self.sensor is None:
                for zone in sorted(self.root.glob('thermal_zone*')):
                    try:
                        name = (zone / 'type').read_text().strip()
                    except OSError:
                        continue
                    if name == 'soc-thermal':
                        self.sensor = zone / 'temp'
                        break
            self.value = (
                int(self.sensor.read_text()) / 1000
                if self.sensor is not None else None
            )
        except (OSError, ValueError):
            self.value = None
            self.sensor = None
        return self.value


SOC_TEMPERATURE = SoCTemperature()


def draw_soc_temperature(frame, panel_color, text_color, rgb=False):
    import cv2
    import numpy as np

    value = SOC_TEMPERATURE.read()
    # Hershey fonts do not provide a degree glyph; use an explicit C unit.
    text = 'SoC --.- C' if value is None else f'SoC {value:.1f} C'
    scale = 0.42
    font = cv2.FONT_HERSHEY_SIMPLEX
    size = cv2.getTextSize(text, font, scale, 1)[0]
    right = frame.shape[1] - 10
    bottom = frame.shape[0] - 10
    left = max(0, right - size[0] - 20)
    top = max(0, bottom - size[1] - 18)
    if top >= bottom or left >= right:
        return
    region = frame[top:bottom, left:right]
    cv2.addWeighted(
        np.full_like(region, panel_color), 0.72, region, 0.28, 0, region
    )
    color = text_color
    if value is not None and value >= 80:
        color = (56, 189, 248) if value < 85 else (64, 96, 248)
        if rgb:
            color = color[::-1]
    cv2.putText(
        frame, text, (left + 10, bottom - 9), font, scale,
        color, 1, cv2.LINE_AA,
    )
