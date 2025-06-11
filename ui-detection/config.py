#!/usr/bin/env python3

# Copyright 2021-2025 Variscite Ltd.
# SPDX-License-Identifier: Variscite Proprietary License

# This software is proprietary and confidential to Variscite Ltd. It is
# intended for internal use only and must not be distributed, modified,
# or disclosed to any third party without explicit written permission
# from Variscite Ltd.

DEMO_DURATION = 120

# File paths for images, model and delegate library
LOADING_CAMERA_IMAGE = "/opt/assets/pngs/lcam.png"
LOADING_INTERPRETER_IMAGE = "/opt/assets/pngs/ltflite.png"

ML_DELEGATE_LIB = "/usr/lib/libvx_delegate.so"
ML_LABELS = "/opt/assets/model/labels_ssd_mobilenet_v1.txt"
ML_MODEL_NPU = "/opt/assets/model/ssd_mobilenet_v1_1_default_1.tflite"
ML_SSD_LABELS_LIST = ["person", "backpack", "handbag", "tie", "suitcase", "bottle", "cup",
                   "chair", "laptop", "mouse", "keyboard", "cell phone", "book", "clock"]

VARISCITE_VIDEO_DART = "DART-MX8M-PLUS.mp4"
VARISCITE_VIDEO_VAR_SOM = "VAR-SOM-MX8M-PLUS.mp4"

# GStreamer pipeline for camera input
CAMERA_DEFAULT_PATH = "/dev/video0"
CAMERA_DEFAULT_RES = (640, 480)
CAMERA_PIPELINE = (
    "v4l2src device={cam_path} ! "
    "video/x-raw,width={cam_width},height={cam_height},framerate=30/1 ! "
    "queue leaky=downstream max-size-buffers=1 ! "
    "videoconvert ! appsink")
