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
from runtime import display_view


PANEL_COLOR = (24, 28, 32)
TEXT_COLOR = (242, 244, 246)
MUTED_COLOR = (184, 190, 196)
ACCENT_COLOR = (167, 211, 34)


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
    region = frame[top:bottom, left:right]
    panel = np.full_like(region, PANEL_COLOR)
    cv2.addWeighted(panel, opacity, region, 1 - opacity, 0, region)


def _inference_ms(value):
    hours, minutes, seconds = str(value).split(':')
    total = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    return total * 1000


def _model_title(model_name):
    name = os.path.basename(str(model_name)).lower()
    if 'mobilenet_v1' in name:
        return 'MobileNet V1 | NPU'
    return f"{os.path.splitext(name)[0].replace('_', ' ')} | NPU"


def _draw_badge(frame, text, row=0):
    scale = 0.6
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


def _draw_results(frame, top_result, labels):
    scale = 0.6
    lines = [f'{labels[index]}  {score:.0%}' for index, score in top_result]
    sizes = [
        cv2.getTextSize(text, FONT['hershey'], scale, 1)[0]
        for text in lines
    ]
    if not sizes:
        return
    line_height = max(size[1] for size in sizes) + 12
    width = min(frame.shape[1] - 20, max(size[0] for size in sizes) + 32)
    left = 10
    top = 10
    bottom = top + line_height * len(lines) + 12
    _blend_panel(frame, left, top, left + width, bottom)
    cv2.rectangle(frame, (left, top), (left + 4, bottom), ACCENT_COLOR, -1)
    for row, (text, size) in enumerate(zip(lines, sizes)):
        color = TEXT_COLOR if row == 0 else MUTED_COLOR
        y = top + 10 + row * line_height + size[1]
        cv2.putText(
            frame, text, (left + 16, y), FONT['hershey'], scale,
            color, 1, cv2.LINE_AA
        )


def _draw_model(frame, model_name):
    scale = 0.5
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


def put_info_on_frame(frame, top_result, labels,
                      inference_time, model_name, _source_file):
    frame, _ = display_view(frame)
    _draw_results(frame, top_result, labels)
    _draw_badge(frame, f'INFERENCE  {_inference_ms(inference_time):.1f} ms')
    _draw_model(frame, model_name)
    draw_soc_temperature(frame, PANEL_COLOR, TEXT_COLOR)
    return frame


def put_fps_on_frame(frame, fps):
    _draw_badge(frame, f'FPS  {fps:.1f}', row=1)
    return frame
