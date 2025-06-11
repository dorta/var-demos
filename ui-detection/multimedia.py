#!/usr/bin/env python3

# Copyright 2021-2025 Variscite Ltd.
# SPDX-License-Identifier: Variscite Proprietary License

# This software is proprietary and confidential to Variscite Ltd. It is
# intended for internal use only and must not be distributed, modified,
# or disclosed to any third party without explicit written permission
# from Variscite Ltd.

import colorsys
import os
import random
import signal
import subprocess
from time import sleep
from typing import List, Tuple

import cv2
import gi
gi.require_versions({'Gdk': "3.0", 'Gst': "1.0"})
from gi.repository import Gdk, Gst
import numpy as np

from config import *


INTERFACE_CSS = b"""
                    checkbutton {
                        color: #0055a5;
                        background: #fefefe;
                        border: 2px solid #fefefe;
                        border-radius: 5px;
                    }

                    checkbutton:checked {
                        color: #fefefe;
                        background: #0055a5;
                    }
                """

FONT = {'hershey': cv2.FONT_HERSHEY_SIMPLEX,
        'size': 0.8,
        'color': {'black': (0, 0, 0),
                  'blue': (255, 0, 0),
                  'green': (0, 255, 0),
                  'orange': (0, 127, 255),
                  'red': (0, 0, 255),
                  'white': (255, 255, 255)},
        'thickness': 2}


def generate_boxes_colors(labels):
    """
    Generates random colors for drawing boxes around detected objects
    """
    hsv_tuples = [(x / len(labels), 1., 1.) for x in range(len(labels))]
    colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
    colors = list(map(lambda x: (int(x[0] * 255),
                                    int(x[1] * 255),
                                    int(x[2] * 255)), colors))
    random.seed(10101)
    random.shuffle(colors)
    random.seed(None)

    return colors


def get_cameras() -> List[str]:
    """
    Retrieves the list of available camera device paths.
    """

    devices = []

    try:
        Gst.init(None)
    except Exception as e:
        print(f"GStreamer initialization failed: {e}")
        return devices

    monitor = Gst.DeviceMonitor()
    monitor.add_filter("Video/Source")

    if not monitor.start():
        print("Failed to start device monitor.")
        return devices

    try:
        for device in monitor.get_devices():
            props = device.get_properties()
            if props:
                path = props.get_string("device.path")
                if path:
                    devices.append(path)
    finally:
        monitor.stop()

    return devices


def get_camera_pipeline(camera: str, width: int, height: int) -> str:
    """
    Returns a formatted GStreamer pipeline string for camera input.
    """
    cameras = get_cameras()

    if cameras:
        if camera not in cameras:
            print(f"{camera} is not a valid capute device. Using {cameras[0]}")
            camera_path = cameras[0]
        else:
            camera_path = camera

        return CAMERA_PIPELINE.format(cam_path=camera_path, cam_width=width, cam_height=height)

    raise RuntimeError("No video device found.")


def get_display_dimensions() -> Tuple[int, int]:
    """
    Retrieves the dimensions of the display.
    """
    width = 0
    height = 0

    display = Gdk.Display.get_default()

    if display:
        monitor = display.get_monitor(0)

        if monitor:
            geometry = monitor.get_geometry()
            width = geometry.width
            height = geometry.height

    return (width, height)

def get_video_file_from_som(som_type) -> str:
    """
    Returns the name of the video file to be played
    based on the argument passed from the script.
    """

    if som_type == "dart":
        return VARISCITE_VIDEO_DART
    elif som_type == "var-som":
        return VARISCITE_VIDEO_VAR_SOM
    else:
        return None

def overlay_image(frame: np.ndarray, top_result, labels) -> np.ndarray:
    """
    Draws information on single images and frames such as inference time,
    scores, model name, and source file.
    """

    colors = generate_boxes_colors(labels)
    image_height, image_width, _ = frame.shape
    for obj in top_result:
        pos = obj['pos']
        _id = obj['_id']

        x1 = int(pos[1] * image_width)
        x2 = int(pos[3] * image_width)
        y1 = int(pos[0] * image_height)
        y2 = int(pos[2] * image_height)

        top = max(0, np.floor(y1 + 0.5).astype('int32'))
        left = max(0, np.floor(x1 + 0.5).astype('int32'))
        bottom = min(image_height, np.floor(y2 + 0.5).astype('int32'))
        right = min(image_width, np.floor(x2 + 0.5).astype('int32'))

        label_size = cv2.getTextSize(
                            labels[_id], FONT['hershey'],
                            FONT['size'], FONT['thickness'])[0]

        label_rect_left = int(left - 3)
        label_rect_top = int(top - 3)
        label_rect_right = int(left + 3 + label_size[0])
        label_rect_bottom = int(top - 5 - label_size[1])

        cv2.rectangle(
            frame, (left, top), (right, bottom),
            colors[int(_id) % len(colors)], 6)
        cv2.rectangle(
            frame, (label_rect_left, label_rect_top),
            (label_rect_right, label_rect_bottom),
            colors[int(_id) % len(colors)], -1)
        cv2.putText(
            frame, labels[_id], (left, int(top - 4)),
            FONT['hershey'], FONT['size'],
            FONT['color']['black'], FONT['thickness'])

    return frame


def preprocess_image(image: np.ndarray, interpreter) -> np.ndarray:
    input_details = interpreter.input_details
    input_shape = input_details[0]['shape']

    height, width = input_shape[1], input_shape[2]

    # Resize and handle channel order
    image_resized = cv2.resize(image, (width, height))
    # If input expects 3 channels and OpenCV returns BGR, convert to RGB
    if len(input_shape) == 4 and input_shape[3] == 3:
        image_resized = cv2.cvtColor(image_resized, cv2.COLOR_BGR2RGB)
    elif len(input_shape) == 4 and input_shape[3] == 1:
        image_resized = cv2.cvtColor(image_resized, cv2.COLOR_BGR2GRAY)
        image_resized = np.expand_dims(image_resized, axis=-1)  # (h, w, 1)

    # Add batch dimension
    image_expanded = np.expand_dims(image_resized, axis=0)

    # Cast to model's input dtype
    dtype = input_details[0]['dtype']
    image_expanded = image_expanded.astype(dtype)

    if dtype == np.float32 and image_expanded.max() > 1.0:
        image_expanded = image_expanded / 255.0

    return image_expanded


def run_video(args) -> None:
    """
    Runs the respective machine video.
    """
    #video_file = get_video_file()
    video_file = get_video_file_from_som(args.som)
    if not video_file:
        print(f"[ERROR] Invalid SoM type: {args.som}")
        return

    # Disable touch screen
    freeze_screen = subprocess.Popen(
        ['evtest', '--grab', '/dev/input/event2'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    try:
        play_video = subprocess.Popen(['gst-launch-1.0', 'playbin', 'video-sink="waylandsink',
                                       'window-width=800', 'window-height=480"',
                                      f'uri=file:///opt/assets/unboxing/{video_file}'])
        play_video.wait()
        sleep(1)
    finally:
        # Try to terminate freeze_screen, fallback to SIGKILL if necessary
        try:
            freeze_screen.terminate()
            freeze_screen.wait(timeout=2)
        except Exception:
            try:
                os.kill(freeze_screen.pid, signal.SIGKILL)
            except Exception:
                pass
