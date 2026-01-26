# Copyright 2025-2026 Variscite Ltd.
#
# This software is proprietary and confidential to Variscite Ltd. It is
# intended for internal use only and must not be distributed, modified,
# or disclosed to any third party without explicit written permission
# from Variscite Ltd.

import re
import subprocess
from typing import List, Tuple

import cv2
import gi
import numpy as np

gi.require_version('Gdk', '3.0')
from gi.repository import Gdk

from config import LIBCAMERA_PIPELINE, VIDEO_PIPELINE
from interpreter import Interpreter


def setup_camera(width: int, height: int) -> None:
    """
    Configures the camera using media-ctl commands.
    """
    commands = [
        f"media-ctl -l '\"ov5640_mainline 2-003c\":0->\"csidev-4ad30000.csi\":0 [1]'",
        f"media-ctl -l '\"csidev-4ad30000.csi\":1 -> \"4ac10000.syscon:formatter@20\":0 [1]'",
        f"media-ctl -V '\"ov5640_mainline 2-003c\":0 [fmt:UYVY8_1X16/{width}x{height} field:none]'",
        f"media-ctl -V '\"csidev-4ad30000.csi\":0 [fmt:UYVY8_1X16/{width}x{height} field:none]'",
        f"media-ctl -V '\"4ac10000.syscon:formatter@20\":0 [fmt:UYVY8_1X16/{width}x{height} field:none]'",
        f"media-ctl -V '\"crossbar\":2 [fmt:UYVY8_1X16/{width}x{height} field:none]'",
        f"media-ctl -V '\"mxc_isi.0\":0 [fmt:UYVY8_1X16/{width}x{height} field:none]'",
        f"media-ctl -V '\"mxc_isi.1\":0 [fmt:UYVY8_1X16/{width}x{height} field:none]'",
        f"media-ctl -V '\"mxc_isi.2\":0 [fmt:UYVY8_1X16/{width}x{height} field:none]'",
        f"media-ctl -V '\"mxc_isi.3\":0 [fmt:UYVY8_1X16/{width}x{height} field:none]'",
        f"media-ctl -V '\"mxc_isi.4\":0 [fmt:UYVY8_1X16/{width}x{height} field:none]'",
        f"media-ctl -V '\"mxc_isi.5\":0 [fmt:UYVY8_1X16/{width}x{height} field:none]'",
        f"media-ctl -V '\"mxc_isi.6\":0 [fmt:UYVY8_1X16/{width}x{height} field:none]'",
        f"media-ctl -V '\"mxc_isi.7\":0 [fmt:UYVY8_1X16/{width}x{height} field:none]'"
    ]

    # Execute media-ctl commands
    for cmd in commands:
        print(f"Executing: {cmd}")  # Debugging: Print the command before execution
        try:
            subprocess.run(cmd, shell=True, check=True, stderr=subprocess.PIPE, text=True)
            print(f"Executed successfully: {cmd}")
        except subprocess.CalledProcessError as e:
            print(f"Error executing: {cmd}\n{e.stderr}")


def get_cameras() -> List[str]:
    """
    Retrieves the list of available camera device paths.
    """
    try:
        result = subprocess.run(
            ['cam', '-l'],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True
        )

        output = result.stdout

        pattern = re.compile(r'\(([^)]*)\)')

        paths = []
        for line in output.splitlines():
            if re.match(r'^\d+:', line.strip()):
                match = pattern.search(line)
                if match:
                    paths.append(match.group(1))

        return paths

    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def get_camera_pipeline(camera: str, width: int, height: int) -> str:
    """
    Returns a formatted GStreamer pipeline string for camera input.
    """
    cameras = get_cameras()

    if cameras:
        if camera not in cameras:
            camera_path = cameras[0]
        else:
            camera_path = camera

        return LIBCAMERA_PIPELINE.format(device=camera_path, width=width, height=height)

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


def get_video_pipeline(filepath: str) -> str:
    """
    Returns a formatted GStreamer pipeline string for video file input.
    """
    return VIDEO_PIPELINE.format(filepath=filepath)


def preprocess_image(image: np.ndarray, interpreter: Interpreter) -> np.ndarray:
    """
    Preprocesses an input image for inference.
    """
    input_shape = interpreter.input_shape
    resized_image = cv2.resize(image, input_shape, interpolation=cv2.INTER_NEAREST).astype(np.float32)
    normalized_image = np.round((resized_image / 255.0 / interpreter.input_scale) +
                                interpreter.input_zero_point).astype(np.int8)
    return normalized_image.reshape((1, *input_shape, 3))
