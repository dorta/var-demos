# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause
"""One MPlus-style overlay for all board-specific inference backends."""

import hashlib
from functools import lru_cache
from pathlib import Path
import cv2
import numpy as np

PANEL = (24, 28, 32)
TEXT = (242, 244, 246)
PALETTE = ((167, 211, 34), (248, 189, 56), (36, 191, 251),
           (250, 139, 167), (133, 113, 251), (53, 230, 163))
FONT = cv2.FONT_HERSHEY_SIMPLEX
FIELD_TOP = 68


@lru_cache(maxsize=1)
def som_name():
    try:
        compatible = Path('/proc/device-tree/compatible').read_bytes().split(b'\0')
    except OSError:
        return 'i.MX SoM'
    for identifier, title in ((b'fsl,imx8mp', 'i.MX 8M Plus'),
                              (b'fsl,imx93', 'i.MX 93'), (b'fsl,imx95', 'i.MX 95')):
        if identifier in compatible:
            return title
    return 'i.MX SoM'


@lru_cache(maxsize=1)
def logo_image():
    root = Path(__file__).resolve().parent
    candidates = [root.parent / 'multimedia/video-player/media/variscite-logo-white.png']
    candidates.extend(sorted(root.glob('*/media/variscite-logo-white.png')))
    for path in candidates:
        if not path.is_file():
            continue
        logo = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if logo is None or logo.ndim != 3 or logo.shape[2] not in (3, 4):
            continue
        scale = min(150 / logo.shape[1], 28 / logo.shape[0])
        logo = cv2.resize(logo, (max(1, round(logo.shape[1] * scale)),
                                max(1, round(logo.shape[0] * scale))),
                          interpolation=cv2.INTER_AREA)
        logo.setflags(write=False)
        return logo
    return None


def branding(frame, rgb=False):
    panel(frame, 10, 10, frame.shape[1] - 20, 42, rgb)
    logo = logo_image()
    if logo is None:
        cv2.putText(frame, 'VARISCITE', (22, 38), FONT, .65,
                    TEXT[::-1] if rgb else TEXT, 1, cv2.LINE_AA)
    else:
        height, width = logo.shape[:2]
        region = frame[17:17 + height, 22:22 + width]
        height, width = region.shape[:2]
        color = logo[:height, :width, :3]
        if rgb:
            color = color[:, :, ::-1]
        if logo.shape[2] == 4:
            alpha = logo[:height, :width, 3:4].astype(np.float32) / 255
            region[:] = np.rint(color * alpha + region * (1 - alpha)).astype(np.uint8)
        else:
            region[:] = color
    cv2.putText(frame, som_name(), (192, 38), FONT, .65,
                TEXT[::-1] if rgb else TEXT, 1, cv2.LINE_AA)


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


def field(frame, label, value, unit='', row=0, rgb=False):
    """All values start in one fixed column, including source dimensions."""
    width = min(320, frame.shape[1] - 20)
    x, y = frame.shape[1] - width - 10, FIELD_TOP + row * 38
    panel(frame, x, y, width, 34, rgb)
    color = TEXT[::-1] if rgb else TEXT
    value_column = min(150, max(1, width // 2))
    label = fitted_text(label, max(1, value_column - 20), .6)
    cv2.putText(frame, label, (x + 9, y + 23), FONT, .6, color, 1, cv2.LINE_AA)
    text = fitted_text(value, max(1, width - value_column - (48 if unit else 12)), .6)
    cv2.putText(frame, text, (x + value_column, y + 23),
                FONT, .6, color, 1, cv2.LINE_AA)
    if unit:
        cv2.putText(frame, unit, (x + width - 40, y + 23),
                    FONT, .6, color, 1, cv2.LINE_AA)


def metric(frame, label, value, unit='', row=0, rgb=False):
    field(frame, label, f'{value:.1f}', unit, row, rgb)


def fps(frame, value, rgb=False):
    metric(frame, 'FPS', value, row=1, rgb=rgb)


def video_resolution(frame, size, rgb=False):
    width, height = size
    field(frame, 'VIDEO', f'{width} x {height}', row=2, rgb=rgb)


def camera_resolution(frame, size, rgb=False):
    """Show negotiated capture dimensions, never the resized working frame."""
    width, height = size
    field(frame, 'CAMERA', f'{width} x {height}', row=2, rgb=rgb)


def statistics(frame, ms, fps=None, rgb=False):
    metric(frame, 'INFERENCE', ms, 'ms', rgb=rgb)
    if fps is not None:
        metric(frame, 'FPS', fps, row=1, rgb=rgb)


def model(frame, title, rgb=False):
    branding(frame, rgb)
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
    width = max(1, min(320, frame.shape[1] - 360))
    panel(frame, 10, FIELD_TOP, width, len(rows) * 32 + 14, rgb)
    accent = color_for('person', rgb)
    cv2.rectangle(frame, (10, FIELD_TOP), (14, FIELD_TOP + len(rows) * 32 + 14), accent, -1)
    for row, (label, score) in enumerate(rows):
        y = FIELD_TOP + 24 + row * 32
        cv2.putText(frame, fitted_text(label, width - 100, .6), (26, y),
                    FONT, .6, TEXT[::-1] if rgb else TEXT, 1, cv2.LINE_AA)
        if score is not None:
            cv2.putText(frame, f'{score:4.0%}', (10 + width - 76, y),
                        FONT, .6, TEXT[::-1] if rgb else TEXT, 1, cv2.LINE_AA)


def box(frame, bounds, name, score=None, rgb=False, show_label=True):
    left, top, right, bottom = bounds
    color = color_for(name, rgb)
    corner = max(10, min(24, (right - left) // 5, (bottom - top) // 5))
    cv2.rectangle(frame, (left, top), (right, bottom), color, 1)
    for x, y, dx, dy in ((left, top, 1, 1), (right, top, -1, 1),
                         (left, bottom, 1, -1), (right, bottom, -1, -1)):
        cv2.line(frame, (x, y), (x + dx * corner, y), color, 3, cv2.LINE_AA)
        cv2.line(frame, (x, y), (x, y + dy * corner), color, 3, cv2.LINE_AA)
    if not show_label:
        return
    text = name if score is None else f'{name}  {score:.0%}'
    (width, height), baseline = cv2.getTextSize(text, FONT, .55, 1)
    label_height = height + baseline + 10
    label_top = top - label_height if top >= label_height + 4 else top
    cv2.rectangle(frame, (left, label_top),
                  (min(frame.shape[1] - 1, left + width + 14),
                   label_top + label_height), color, -1)
    cv2.putText(frame, text, (left + 7, label_top + height + 5),
                FONT, .55, PANEL[::-1] if rgb else PANEL, 1, cv2.LINE_AA)
