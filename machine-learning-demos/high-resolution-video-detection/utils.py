# Copyright 2025 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

import colorsys
import random
import re
from contextlib import contextmanager
from datetime import timedelta
from time import monotonic

import cv2
import numpy as np


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

def generate_colors(labels):
    hsv_tuples = [(x / len(labels), 1., 1.) for x in range(len(labels))]
    colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
    colors = list(map(lambda x: (int(x[0] * 255), int(x[1] * 255),
                                 int(x[2] * 255)), colors))
    random.seed(10101)
    random.shuffle(colors)
    random.seed(None)
    return colors

def put_info_on_frame(frame, results, inf_time, labels, model_name, source_file):
    colors = generate_colors(labels)
    inference_position = (3, 20)
    frame_height, frame_width, _ = frame.shape

    for obj in results:
        y_min, x_min, y_max, x_max = obj['box']
        _id = obj['class']
        score = obj['score']

        x1 = int(x_min * frame_width)
        x2 = int(x_max * frame_width)
        y1 = int(y_min * frame_height)
        y2 = int(y_max * frame_height)

        top = max(0, y1)
        left = max(0, x1)
        bottom = min(frame_height, y2)
        right = min(frame_width, x2)

        label = f"{labels.get(_id, 'Unknown')} {score:.2f}"

        label_size = cv2.getTextSize(label, FONT['hershey'], FONT['size'], FONT['thickness'])[0]
        label_rect_left = int(left - 3)
        label_rect_top = int(top - 3)
        label_rect_right = int(left + 3 + label_size[0])
        label_rect_bottom = int(top - 5 - label_size[1])

        color = colors[_id % len(colors)]

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (label_rect_left, label_rect_top), (label_rect_right, label_rect_bottom), color, -1)
        cv2.putText(frame, label, (left, int(top - 4)), FONT['hershey'], FONT['size'],
                    FONT['color']['black'], FONT['thickness'])

    if inf_time:
        cv2.putText(frame, f"INFERENCE TIME: {inf_time}", inference_position,
                    FONT['hershey'], 0.5, FONT['color']['black'], 2, cv2.LINE_AA)
        cv2.putText(frame, f"INFERENCE TIME: {inf_time}", inference_position,
                    FONT['hershey'], 0.5, FONT['color']['white'], 1, cv2.LINE_AA)

    y_offset = frame.shape[0] - cv2.getTextSize(source_file, FONT['hershey'], 0.5, 2)[0][1]

    cv2.putText(frame, f"SOURCE: {source_file}", (3, y_offset),
                FONT['hershey'], 0.5, FONT['color']['black'], 2, cv2.LINE_AA)
    cv2.putText(frame, f"SOURCE: {source_file}", (3, y_offset),
                FONT['hershey'], 0.5, FONT['color']['white'], 1, cv2.LINE_AA)

    y_offset -= (cv2.getTextSize(model_name, FONT['hershey'], 0.5, 2)[0][1] + 3)

    cv2.putText(frame, f"MODEL: {model_name}", (3, y_offset),
                FONT['hershey'], 0.5, FONT['color']['black'], 2, cv2.LINE_AA)
    cv2.putText(frame, f"MODEL: {model_name}", (3, y_offset),
                FONT['hershey'], 0.5, FONT['color']['white'], 1, cv2.LINE_AA)

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
