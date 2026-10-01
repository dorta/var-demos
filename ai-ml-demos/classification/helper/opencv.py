# Copyright 2021 Variscite LTD
# SPDX-License-Identifier: BSD-3-Clause

import os

import cv2
import numpy as np

from helper.config import FONT


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

def _blend_panel(frame, left, top, right, bottom, opacity=0.78):
    region = frame[top:bottom, left:right]
    panel = np.full_like(region, PANEL_COLOR)
    cv2.addWeighted(panel, opacity, region, 1 - opacity, 0, region)


def _inference_ms(value):
    hours, minutes, seconds = str(value).split(':')
    total = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    return total * 1000


def _source_name(source):
    source = str(source)
    return source if source.startswith('/dev/') else os.path.basename(source)


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


def _draw_results(frame, top_result, labels):
    scale = 0.52
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


def _draw_metadata(frame, model_name, source_file):
    scale = 0.42
    lines = (
        f'MODEL  {os.path.basename(str(model_name))}',
        f'SOURCE  {_source_name(source_file)}',
    )
    sizes = [
        cv2.getTextSize(text, FONT['hershey'], scale, 1)[0]
        for text in lines
    ]
    width = min(frame.shape[1] - 20, max(size[0] for size in sizes) + 20)
    line_height = max(size[1] for size in sizes) + 8
    left = 10
    bottom = frame.shape[0] - 10
    top = bottom - line_height * len(lines) - 8
    _blend_panel(frame, left, top, left + width, bottom, 0.72)
    for row, (text, size) in enumerate(zip(lines, sizes)):
        y = top + 10 + row * line_height + size[1]
        cv2.putText(
            frame, text, (left + 10, y), FONT['hershey'], scale,
            TEXT_COLOR, 1, cv2.LINE_AA
        )


def put_info_on_frame(frame, top_result, labels,
                      inference_time, model_name, source_file):
    _draw_results(frame, top_result, labels)
    _draw_badge(frame, f'INFERENCE  {_inference_ms(inference_time):.1f} ms')
    _draw_metadata(frame, model_name, source_file)
    return frame


def put_fps_on_frame(frame, fps):
    _draw_badge(frame, f'FPS  {fps:.1f}', row=1)
    return frame
