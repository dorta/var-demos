# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause
"""One MPlus-style overlay for all board-specific inference backends."""

import hashlib
from functools import lru_cache
import cv2
import numpy as np

PANEL = (24, 28, 32)
TEXT = (242, 244, 246)
PALETTE = ((167, 211, 34), (248, 189, 56), (36, 191, 251),
           (250, 139, 167), (133, 113, 251), (53, 230, 163))
FONT = cv2.FONT_HERSHEY_SIMPLEX


def color_for(name, rgb=False):
    # Different SSD label files use different class indices. Color by name.
    name = name.strip().lower()
    index = {'person': 0, 'car': 2}.get(name)
    if index is None:
        index = hashlib.sha256(name.encode()).digest()[0] % len(PALETTE)
    color = PALETTE[index]
    return color[::-1] if rgb else color


@lru_cache(maxsize=32)
def panel_background(shape, rgb):
    background = np.empty(shape, dtype=np.uint8)
    background[:] = PANEL[::-1] if rgb else PANEL
    background.setflags(write=False)
    return background


def panel(frame, x, y, width, height, rgb=False, opacity=.78):
    x, y = max(0, x), max(0, y)
    region = frame[y:min(frame.shape[0], y + height),
                   x:min(frame.shape[1], x + width)]
    if region.size:
        cv2.addWeighted(panel_background(region.shape, rgb), opacity,
                        region, 1 - opacity, 0, region)


def fitted_text(text, width, scale):
    text = str(text)
    original = text
    while text and cv2.getTextSize(text, FONT, scale, 1)[0][0] > width:
        text = text[:-1]
    if text != original:
        return text[:-3] + '...' if len(text) > 3 else text
    return text


def badge(frame, text, row=0, rgb=False):
    # Fixed width and left edge: varying digits must never shift the panel.
    width = min(250, frame.shape[1] - 20)
    x, y = frame.shape[1] - width - 10, 10 + row * 38
    panel(frame, x, y, width, 34, rgb)
    cv2.putText(frame, fitted_text(text, width - 18, .6), (x + 9, y + 23),
                FONT, .6, TEXT[::-1] if rgb else TEXT, 1, cv2.LINE_AA)


def metric(frame, label, value, unit='', row=0, rgb=False):
    """Use pixel-aligned numeric columns, not proportional-font spaces."""
    width = min(250, frame.shape[1] - 20)
    x, y = frame.shape[1] - width - 10, 10 + row * 38
    panel(frame, x, y, width, 34, rgb)
    color = TEXT[::-1] if rgb else TEXT
    label = fitted_text(label, max(1, width - 132), .6)
    cv2.putText(frame, label, (x + 9, y + 23), FONT, .6, color, 1, cv2.LINE_AA)
    text = f'{value:.1f}'
    value_width = cv2.getTextSize(text, FONT, .6, 1)[0][0]
    cv2.putText(frame, text, (x + width - 42 - value_width, y + 23),
                FONT, .6, color, 1, cv2.LINE_AA)
    if unit:
        cv2.putText(frame, unit, (x + width - 32, y + 23),
                    FONT, .6, color, 1, cv2.LINE_AA)


def fps(frame, value, rgb=False):
    metric(frame, 'FPS', value, row=1, rgb=rgb)


def video_resolution(frame, size, rgb=False):
    width, height = size
    badge(frame, f'VIDEO  {width} x {height}', row=2, rgb=rgb)


def statistics(frame, ms, fps=None, rgb=False):
    metric(frame, 'INFERENCE', ms, 'ms', rgb=rgb)
    if fps is not None:
        metric(frame, 'FPS', fps, row=1, rgb=rgb)


def model(frame, title, rgb=False):
    x, y = 10, frame.shape[0] - 44
    width = max(1, frame.shape[1] - 180)
    panel(frame, x, y, width, 34, rgb, .72)
    cv2.putText(frame, fitted_text(title, width - 20, .5), (x + 10, y + 23),
                FONT, .5, TEXT[::-1] if rgb else TEXT, 1, cv2.LINE_AA)


def temperature(frame, value, rgb=False):
    width, height = 140, 34
    x, y = frame.shape[1] - width - 10, frame.shape[0] - height - 10
    panel(frame, x, y, width, height, rgb, .72)
    text = 'SoC --.- C' if value is None else f'SoC {value:5.1f} C'
    color = TEXT[::-1] if rgb else TEXT
    if value is not None and value >= 80:
        color = (56, 189, 248) if value < 85 else (64, 96, 248)
        if rgb:
            color = color[::-1]
    cv2.putText(frame, text, (x + 10, y + 23), FONT, .5,
                color, 1, cv2.LINE_AA)


def results(frame, rows, rgb=False):
    rows = list(rows)
    if not rows:
        return
    width = max(1, min(320, frame.shape[1] - 290))
    panel(frame, 10, 10, width, len(rows) * 32 + 14, rgb)
    accent = color_for('person', rgb)
    cv2.rectangle(frame, (10, 10), (14, 10 + len(rows) * 32 + 14), accent, -1)
    for row, (label, score) in enumerate(rows):
        y = 34 + row * 32
        cv2.putText(frame, fitted_text(label, width - 100, .6), (26, y),
                    FONT, .6, TEXT[::-1] if rgb else TEXT, 1, cv2.LINE_AA)
        if score is not None:
            cv2.putText(frame, f'{score:4.0%}', (10 + width - 76, y),
                        FONT, .6, TEXT[::-1] if rgb else TEXT, 1, cv2.LINE_AA)


def box(frame, bounds, name, score=None, rgb=False):
    left, top, right, bottom = bounds
    color = color_for(name, rgb)
    corner = max(10, min(24, (right - left) // 5, (bottom - top) // 5))
    cv2.rectangle(frame, (left, top), (right, bottom), color, 1)
    for x, y, dx, dy in ((left, top, 1, 1), (right, top, -1, 1),
                         (left, bottom, 1, -1), (right, bottom, -1, -1)):
        cv2.line(frame, (x, y), (x + dx * corner, y), color, 3, cv2.LINE_AA)
        cv2.line(frame, (x, y), (x, y + dy * corner), color, 3, cv2.LINE_AA)
    text = name if score is None else f'{name}  {score:.0%}'
    (width, height), baseline = cv2.getTextSize(text, FONT, .55, 1)
    label_height = height + baseline + 10
    label_top = top - label_height if top >= label_height + 4 else top
    cv2.rectangle(frame, (left, label_top),
                  (min(frame.shape[1] - 1, left + width + 14),
                   label_top + label_height), color, -1)
    cv2.putText(frame, text, (left + 7, label_top + height + 5),
                FONT, .55, PANEL[::-1] if rgb else PANEL, 1, cv2.LINE_AA)
