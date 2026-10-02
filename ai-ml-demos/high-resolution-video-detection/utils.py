# Copyright 2025 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

import collections
import os
import re
import sys
from pathlib import Path
from contextlib import contextmanager
from datetime import timedelta
from time import monotonic

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from telemetry import draw_soc_temperature


FONT = {
    'hershey': cv2.FONT_HERSHEY_SIMPLEX,
    'size': 0.8,
    'color': {
        'black': (0, 0, 0),
        'blue': (255, 0, 0),
        'green': (0, 255, 0),
        'orange': (0, 127, 255),
        'red': (0, 0, 255),
        'white': (255, 255, 255)
    },
    'thickness': 2
}

PALETTE = (
    (34, 211, 167),
    (56, 189, 248),
    (251, 191, 36),
    (167, 139, 250),
    (251, 113, 133),
    (163, 230, 53),
)
PANEL_COLOR = (24, 28, 32)
TEXT_COLOR = (242, 244, 246)

COMBINATIONS = [
    ("assets/videos/video_1280x720.mp4", (1280, 720), "lvds_small", (800, 480), "windowed"),
    ("assets/videos/video_1280x720.mp4", (1280, 720), "lvds_small", (800, 480), "fullscreen"),
    ("assets/videos/video_1280x720.mp4", (1280, 720), "lvds_large", (1280, 800), "windowed"),
    ("assets/videos/video_1280x720.mp4", (1280, 720), "lvds_large", (1280, 800), "fullscreen"),
    ("assets/videos/video_1280x720.mp4", (1280, 720), "monitor_4k", (3840, 2160), "windowed"),
    ("assets/videos/video_1280x720.mp4", (1280, 720), "monitor_4k", (3840, 2160), "fullscreen"),

    ("assets/videos/video_1280x800.mp4", (1280, 800), "lvds_small", (800, 480), "windowed"),
    ("assets/videos/video_1280x800.mp4", (1280, 800), "lvds_small", (800, 480), "fullscreen"),
    ("assets/videos/video_1280x800.mp4", (1280, 800), "lvds_large", (1280, 800), "windowed"),
    ("assets/videos/video_1280x800.mp4", (1280, 800), "lvds_large", (1280, 800), "fullscreen"),
    ("assets/videos/video_1280x800.mp4", (1280, 800), "monitor_4k", (3840, 2160), "windowed"),
    ("assets/videos/video_1280x800.mp4", (1280, 800), "monitor_4k", (3840, 2160), "fullscreen"),

    ("assets/videos/video_1920x1080.mp4", (1920, 1080), "lvds_small", (800, 480), "windowed"),
    ("assets/videos/video_1920x1080.mp4", (1920, 1080), "lvds_small", (800, 480), "fullscreen"),
    ("assets/videos/video_1920x1080.mp4", (1920, 1080), "lvds_large", (1280, 800), "windowed"),
    ("assets/videos/video_1920x1080.mp4", (1920, 1080), "lvds_large", (1280, 800), "fullscreen"),
    ("assets/videos/video_1920x1080.mp4", (1920, 1080), "monitor_4k", (3840, 2160), "windowed"),
    ("assets/videos/video_1920x1080.mp4", (1920, 1080), "monitor_4k", (3840, 2160), "fullscreen"),
]

PROFILE_ENABLED = False

def profile(func):
    def wrapper(*args, **kwargs):
        if not PROFILE_ENABLED:
            return func(*args, **kwargs)
        start = monotonic()
        result = func(*args, **kwargs)
        duration = (monotonic() - start) * 1000
        print(f"[PROFILE] {func.__name__}: {duration:.2f} ms")
        return result
    return wrapper

class Timer:
    def __init__(self):
        self.time = 0

    @contextmanager
    def timeit(self):
        begin = monotonic()
        try:
            yield
        finally:
            end = monotonic()
            self.convert(end - begin)

    def convert(self, elapsed):
        self.time = str(timedelta(seconds=elapsed))


class Framerate:
    def __init__(self):
        self.fps = 0.0
        self.last_update = monotonic()
        self.window = collections.deque(maxlen=30)

    def update(self):
        now = monotonic()
        self.window.append(now - self.last_update)
        self.last_update = now
        self.fps = len(self.window) / sum(self.window)
        return self.fps

@contextmanager
def debug_profile(name, enabled):
    start = monotonic()
    yield
    if enabled:
        print(f"[DEBUG] {name}: {(monotonic() - start) * 1000:.2f} ms")

def load_labels(path):
    p = re.compile(r'\s*(\d+)(.+)')
    with open(path, 'r', encoding='utf-8') as f:
        lines = (p.match(line).groups() for line in f.readlines())
        return {int(num): text.strip() for num, text in lines}

def _blend_panel(frame, left, top, right, bottom, opacity=0.78):
    left = max(0, left)
    top = max(0, top)
    right = min(frame.shape[1], right)
    bottom = min(frame.shape[0], bottom)
    if left >= right or top >= bottom:
        return
    region = frame[top:bottom, left:right]
    panel = np.full_like(region, PANEL_COLOR)
    cv2.addWeighted(panel, opacity, region, 1 - opacity, 0, region)


def _inference_ms(value):
    hours, minutes, seconds = str(value).split(':')
    total = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    return total * 1000


def _draw_badge(frame, text, row=0):
    scale = 0.48
    size, baseline = cv2.getTextSize(text, FONT['hershey'], scale, 1)
    right = frame.shape[1] - 10
    top = 10 + row * (size[1] + baseline + 22)
    left = right - size[0] - 18
    bottom = top + size[1] + baseline + 14
    _blend_panel(frame, left, top, right, bottom)
    cv2.putText(
        frame, text, (left + 9, bottom - 7 - baseline),
        FONT['hershey'], scale, TEXT_COLOR, 1, cv2.LINE_AA
    )


def _model_title(model_name):
    name = os.path.basename(str(model_name)).lower()
    if 'ssd_mobilenet_v1' in name:
        return 'SSD MobileNet V1 | NPU'
    return f"{os.path.splitext(name)[0].replace('_', ' ')} | NPU"


def _draw_model(frame, model_name):
    scale = 0.42
    text = _model_title(model_name)
    size = cv2.getTextSize(text, FONT['hershey'], scale, 1)[0]
    width = min(frame.shape[1] - 20, size[0] + 20)
    left = 10
    bottom = frame.shape[0] - 10
    top = bottom - size[1] - 18
    _blend_panel(frame, left, top, left + width, bottom, 0.72)
    cv2.putText(
        frame, text, (left + 10, bottom - 9), FONT['hershey'], scale,
        TEXT_COLOR, 1, cv2.LINE_AA
    )


def _draw_box(frame, bounds, label, color):
    left, top, right, bottom = bounds
    width = max(1, right - left)
    height = max(1, bottom - top)
    corner = max(10, min(24, width // 5, height // 5))
    cv2.rectangle(frame, (left, top), (right, bottom), color, 1)
    for start, end in (
        ((left, top), (left + corner, top)),
        ((left, top), (left, top + corner)),
        ((right, top), (right - corner, top)),
        ((right, top), (right, top + corner)),
        ((left, bottom), (left + corner, bottom)),
        ((left, bottom), (left, bottom - corner)),
        ((right, bottom), (right - corner, bottom)),
        ((right, bottom), (right, bottom - corner)),
    ):
        cv2.line(frame, start, end, color, 3, cv2.LINE_AA)

    scale = 0.46
    text_size, baseline = cv2.getTextSize(label, FONT['hershey'], scale, 1)
    label_height = text_size[1] + baseline + 10
    label_top = top - label_height if top >= label_height + 4 else top
    label_right = min(frame.shape[1] - 1, left + text_size[0] + 14)
    cv2.rectangle(
        frame, (left, label_top), (label_right, label_top + label_height),
        color, -1
    )
    cv2.putText(
        frame, label, (left + 7, label_top + text_size[1] + 5),
        FONT['hershey'], scale, PANEL_COLOR, 1, cv2.LINE_AA
    )


def put_info_on_frame(frame, results, inf_time, labels, model_name,
                      _source_file, fps=None):
    frame_height, frame_width = frame.shape[:2]
    for obj in results:
        y_min, x_min, y_max, x_max = obj['box']
        class_id = int(obj['class'])
        left = max(0, min(frame_width - 1, int(x_min * frame_width)))
        right = max(0, min(frame_width - 1, int(x_max * frame_width)))
        top = max(0, min(frame_height - 1, int(y_min * frame_height)))
        bottom = max(0, min(frame_height - 1, int(y_max * frame_height)))
        if right <= left or bottom <= top:
            continue
        name = labels.get(class_id, f'class {class_id}')
        label = f"{name}  {obj['score']:.0%}"
        _draw_box(
            frame, (left, top, right, bottom), label,
            PALETTE[class_id % len(PALETTE)]
        )

    _draw_badge(frame, f'INFERENCE  {_inference_ms(inf_time):.1f} ms')
    if fps is not None:
        _draw_badge(frame, f'FPS  {fps:.1f}', row=1)
    _draw_model(frame, model_name)
    draw_soc_temperature(frame, PANEL_COLOR, TEXT_COLOR, rgb=True)
    return frame


def resize_with_letterbox(frame, display_res):
    target_width, target_height = display_res
    frame_height, frame_width = frame.shape[:2]
    scale = min(target_width / frame_width, target_height / frame_height)
    resized_width = max(1, int(frame_width * scale))
    resized_height = max(1, int(frame_height * scale))
    resized = cv2.resize(frame, (resized_width, resized_height))

    output = np.zeros((target_height, target_width, 3), dtype=frame.dtype)
    x_offset = (target_width - resized_width) // 2
    y_offset = (target_height - resized_height) // 2
    output[
        y_offset:y_offset + resized_height,
        x_offset:x_offset + resized_width
    ] = resized
    return output

def show_available_combinations():
    print("Available combinations:\n")
    print(
        f"{'ID':<4} {'Video':<42} {'Video size':<12} "
        f"{'Display':<12} {'Display size':<14} {'Mode'}"
    )
    print("-" * 103)
    for index, combination in enumerate(COMBINATIONS, start=1):
        video, video_res, display, display_res, mode = combination
        video_size = f"{video_res[0]}x{video_res[1]}"
        display_size = f"{display_res[0]}x{display_res[1]}"
        print(
            f"{index:<4} {video:<42} {video_size:<12} "
            f"{display:<12} {display_size:<14} {mode}"
        )
    exit(0)
