# Copyright 2021-2025 Variscite LTD
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
    ("media/hd/combined_videos_1280x720.mp4", (1280, 720), "lvds_small", (800, 480), "windowed"),
    ("media/hd/combined_videos_1280x720.mp4", (1280, 720), "lvds_small", (800, 480), "fullscreen"),
    ("media/hd/combined_videos_1280x720.mp4", (1280, 720), "lvds_large", (1280, 800), "windowed"),
    ("media/hd/combined_videos_1280x720.mp4", (1280, 720), "lvds_large", (1280, 800), "fullscreen"),
    ("media/hd/combined_videos_1280x720.mp4", (1280, 720), "monitor_4k", (3840, 2160), "windowed"),
    ("media/hd/combined_videos_1280x720.mp4", (1280, 720), "monitor_4k", (3840, 2160), "fullscreen"),

    ("media/hd/combined_videos_1280x800.mp4", (1280, 800), "lvds_small", (800, 480), "windowed"),
    ("media/hd/combined_videos_1280x800.mp4", (1280, 800), "lvds_small", (800, 480), "fullscreen"),
    ("media/hd/combined_videos_1280x800.mp4", (1280, 800), "lvds_large", (1280, 800), "windowed"),
    ("media/hd/combined_videos_1280x800.mp4", (1280, 800), "lvds_large", (1280, 800), "fullscreen"),
    ("media/hd/combined_videos_1280x800.mp4", (1280, 800), "monitor_4k", (3840, 2160), "windowed"),
    ("media/hd/combined_videos_1280x800.mp4", (1280, 800), "monitor_4k", (3840, 2160), "fullscreen"),

    ("media/fullhd/combined_videos_1920x1080.mp4", (1920, 1080), "lvds_small", (800, 480), "windowed"),
    ("media/fullhd/combined_videos_1920x1080.mp4", (1920, 1080), "lvds_small", (800, 480), "fullscreen"),
    ("media/fullhd/combined_videos_1920x1080.mp4", (1920, 1080), "lvds_large", (1280, 800), "windowed"),
    ("media/fullhd/combined_videos_1920x1080.mp4", (1920, 1080), "lvds_large", (1280, 800), "fullscreen"),
    ("media/fullhd/combined_videos_1920x1080.mp4", (1920, 1080), "monitor_4k", (3840, 2160), "windowed"),
    ("media/fullhd/combined_videos_1920x1080.mp4", (1920, 1080), "monitor_4k", (3840, 2160), "fullscreen"),
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

def show_available_combinations():
    print("Available combinations:\n")
    print(f"{'ID':<4} {'Video':<25} {'VideoRes':<10} {'AR_Video':<8} {'Display':<12} {'DisplayRes':<12} {'AR_Display':<10} {'Mode':<10} {'Resize Needed':<40} {'AR Match'}")
    print("-" * 170)
    rows = [
        (1,  "videos_1280x720.mp4",  "1280x720",  "16:9",   "lvds_small",  "800x480",   "5:3",     "windowed",   "No resize (windowed)",                          "No"),
        (2,  "videos_1280x720.mp4",  "1280x720",  "16:9",   "lvds_small",  "800x480",   "5:3",     "fullscreen", "No resize (bars expected)",                     "No"),
        (3,  "videos_1280x720.mp4",  "1280x720",  "16:9",   "lvds_large",  "1280x800",  "16:10",   "windowed",   "No resize (windowed)",                          "No"),
        (4,  "videos_1280x720.mp4",  "1280x720",  "16:9",   "lvds_large",  "1280x800",  "16:10",   "fullscreen", "No resize (bars expected)",                     "No"),
        (5,  "videos_1280x720.mp4",  "1280x720",  "16:9",   "monitor_4k",  "3840x2160", "16:9",    "windowed",   "No resize (windowed)",                          "Yes"),
        (6,  "videos_1280x720.mp4",  "1280x720",  "16:9",   "monitor_4k",  "3840x2160", "16:9",    "fullscreen", "Resize needed (resolution mismatch)",           "Yes"),
        (7,  "videos_1280x800.mp4",  "1280x800",  "16:10",  "lvds_small",  "800x480",   "5:3",     "windowed",   "No resize (windowed)",                          "No"),
        (8,  "videos_1280x800.mp4",  "1280x800",  "16:10",  "lvds_small",  "800x480",   "5:3",     "fullscreen", "No resize (bars expected)",                     "No"),
        (9,  "videos_1280x800.mp4",  "1280x800",  "16:10",  "lvds_large",  "1280x800",  "16:10",   "windowed",   "No resize (windowed)",                          "Yes"),
        (10, "videos_1280x800.mp4",  "1280x800",  "16:10",  "lvds_large",  "1280x800",  "16:10",   "fullscreen", "No resize (exact fit)",                         "Yes"),
        (11, "videos_1280x800.mp4",  "1280x800",  "16:10",  "monitor_4k",  "3840x2160", "16:9",    "windowed",   "No resize (windowed)",                          "No"),
        (12, "videos_1280x800.mp4",  "1280x800",  "16:10",  "monitor_4k",  "3840x2160", "16:9",    "fullscreen", "No resize (bars expected)",                     "No"),
        (13, "videos_1920x1080.mp4", "1920x1080", "16:9",   "lvds_small",  "800x480",   "5:3",     "windowed",   "No resize (windowed)",                          "No"),
        (14, "videos_1920x1080.mp4", "1920x1080", "16:9",   "lvds_small",  "800x480",   "5:3",     "fullscreen", "No resize (bars expected)",                     "No"),
        (15, "videos_1920x1080.mp4", "1920x1080", "16:9",   "lvds_large",  "1280x800",  "16:10",   "windowed",   "No resize (windowed)",                          "No"),
        (16, "videos_1920x1080.mp4", "1920x1080", "16:9",   "lvds_large",  "1280x800",  "16:10",   "fullscreen", "No resize (bars expected)",                     "No"),
        (17, "videos_1920x1080.mp4", "1920x1080", "16:9",   "monitor_4k",  "3840x2160", "16:9",    "windowed",   "No resize (windowed)",                          "Yes"),
        (18, "videos_1920x1080.mp4", "1920x1080", "16:9",   "monitor_4k",  "3840x2160", "16:9",    "fullscreen", "Resize needed (resolution mismatch)",           "Yes"),
    ]

    for r in rows:
        print(f"{r[0]:<4} {r[1]:<25} {r[2]:<10} {r[3]:<8} {r[4]:<12} {r[5]:<12} {r[6]:<10} {r[7]:<10} {r[8]:<40} {r[9]}")

    print("\nNotes:")
    print("'No resize (bars expected)' means black bars may appear to preserve the original aspect ratio.")
    print("'Resize needed' means the image will be resized and might look stretched or distorted.")
    print("'Exact fit' means perfect match between video and screen — no distortion or bars.")
    print("'AR Match' indicates if the video and display share the same aspect ratio (ideal scenario).")
    exit(0)
