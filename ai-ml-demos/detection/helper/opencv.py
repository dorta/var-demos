# Copyright 2021 Variscite LTD
# SPDX-License-Identifier: BSD-3-Clause

import os
import sys
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from helper.config import FONT

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from telemetry import draw_soc_temperature


PALETTE = (
    (167, 211, 34),
    (248, 189, 56),
    (36, 191, 251),
    (250, 139, 167),
    (133, 113, 251),
    (53, 230, 163),
)
PANEL_COLOR = (24, 28, 32)
TEXT_COLOR = (242, 244, 246)


def create_window(title, windowed=False):
    cv2.namedWindow(title, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    if not windowed:
        cv2.setWindowProperty(
            title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
        )


@lru_cache(maxsize=1)
def _display_size():
    size = os.environ.get('VAR_AI_DISPLAY_SIZE')
    if not size:
        try:
            with open(
                '/sys/class/graphics/fb0/virtual_size',
                encoding='utf-8'
            ) as size_file:
                size = size_file.read().strip()
        except OSError:
            return None
    try:
        return tuple(
            int(value) for value in size.replace('x', ',').split(',')
        )
    except ValueError:
        return None


def fit_to_display(frame, windowed=False):
    if windowed:
        return frame

    display_size = _display_size()
    if display_size is None:
        return frame
    target_width, target_height = display_size

    frame_height, frame_width = frame.shape[:2]
    target_ratio = target_width / target_height
    frame_ratio = frame_width / frame_height
    if frame_ratio > target_ratio:
        crop_width = round(frame_height * target_ratio)
        left = (frame_width - crop_width) // 2
        frame = frame[:, left:left + crop_width]
    elif frame_ratio < target_ratio:
        crop_height = round(frame_width / target_ratio)
        top = (frame_height - crop_height) // 2
        frame = frame[top:top + crop_height, :]

    return cv2.resize(frame, (target_width, target_height))


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
    try:
        hours, minutes, seconds = str(value).split(':')
        total = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        return total * 1000
    except (TypeError, ValueError):
        return float(value)


def _model_title(model_name):
    name = os.path.basename(str(model_name)).lower()
    if 'ssd_mobilenet_v1' in name:
        return 'SSD MobileNet V1 | NPU'
    return f"{os.path.splitext(name)[0].replace('_', ' ')} | NPU"


def _draw_badge(frame, text, row=0):
    scale = 0.48
    thickness = 1
    padding_x = 9
    padding_y = 7
    size, baseline = cv2.getTextSize(
        text, FONT['hershey'], scale, thickness
    )
    right = frame.shape[1] - 10
    top = 10 + row * (size[1] + baseline + 2 * padding_y + 4)
    left = right - size[0] - 2 * padding_x
    bottom = top + size[1] + baseline + 2 * padding_y
    _blend_panel(frame, left, top, right, bottom)
    cv2.putText(
        frame, text, (left + padding_x, bottom - padding_y - baseline),
        FONT['hershey'], scale, TEXT_COLOR, thickness, cv2.LINE_AA
    )


def _draw_model(frame, model_name):
    scale = 0.42
    thickness = 1
    text = _model_title(model_name)
    size = cv2.getTextSize(text, FONT['hershey'], scale, thickness)[0]
    width = min(frame.shape[1] - 20, size[0] + 20)
    left = 10
    bottom = frame.shape[0] - 10
    top = bottom - size[1] - 18
    _blend_panel(frame, left, top, left + width, bottom, 0.72)
    cv2.putText(
        frame, text, (left + 10, bottom - 9), FONT['hershey'], scale,
        TEXT_COLOR, thickness, cv2.LINE_AA
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
    thickness = 1
    text_size, baseline = cv2.getTextSize(
        label, FONT['hershey'], scale, thickness
    )
    label_height = text_size[1] + baseline + 10
    label_width = text_size[0] + 14
    label_top = top - label_height if top >= label_height + 4 else top
    label_right = min(frame.shape[1] - 1, left + label_width)
    cv2.rectangle(
        frame, (left, label_top), (label_right, label_top + label_height),
        color, -1
    )
    cv2.putText(
        frame, label, (left + 7, label_top + text_size[1] + 5),
        FONT['hershey'], scale, PANEL_COLOR, thickness, cv2.LINE_AA
    )


def put_info_on_frame(frame, result, time, labels, model_name, _source_file):
    frame_height, frame_width = frame.shape[:2]
    for obj in result:
        y_min, x_min, y_max, x_max = obj['pos']
        class_id = int(obj['_id'])
        left = max(0, min(frame_width - 1, int(x_min * frame_width)))
        right = max(0, min(frame_width - 1, int(x_max * frame_width)))
        top = max(0, min(frame_height - 1, int(y_min * frame_height)))
        bottom = max(0, min(frame_height - 1, int(y_max * frame_height)))
        if right <= left or bottom <= top:
            continue

        name = labels.get(class_id, f'class {class_id}')
        score = obj.get('score')
        label = name if score is None else f'{name}  {score:.0%}'
        color = PALETTE[class_id % len(PALETTE)]
        _draw_box(frame, (left, top, right, bottom), label, color)

    _draw_badge(frame, f'INFERENCE  {_inference_ms(time):.1f} ms')
    _draw_model(frame, model_name)
    draw_soc_temperature(frame, PANEL_COLOR, TEXT_COLOR)
    return frame


def put_fps_on_frame(frame, fps):
    _draw_badge(frame, f'FPS  {fps:.1f}', row=1)
    return frame
