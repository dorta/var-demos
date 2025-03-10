# Copyright 2025 Variscite LTD
# SPDX-License-Identifier: BSD-3-Clause

# File paths for model and delegate library
DELEGATE_LIB = "/opt/person-detection-demo/assets/libneutron_delegate.so"
MODEL_CPU = "/opt/person-detection-demo/assets/yolov8n_quant.tflite"
MODEL_NPU = "/opt/person-detection-demo/assets/yolov8n_quant_neutron.tflite"

# GStreamer pipeline for camera input
CAMERA_DEFAULT_RES = (1280, 720)
LIBCAMERA_DEFAULT_PATH = "/base/soc/bus@42000000/i2c@42530000/ov5640_mipi0@3c"

LIBCAMERA_PIPELINE = (
    "libcamerasrc camera-name={device} ! "
    "video/x-raw, format=NV12, width={width}, height={height}, framerate=30/1 ! "
    "imxvideoconvert_g2d ! videoconvert ! video/x-raw, format=BGR ! "
    "appsink"
)

CAMERA_PIPELINE = (
    "v4l2src device={device} ! "
    "video/x-raw, format=NV12, width={width}, height={height}, framerate=30/1 ! "
    "imxvideoconvert_g2d ! videoconvert ! video/x-raw, format=BGR ! "
    "appsink"
)

# GStreamer pipeline for video file input
VIDEO_PIPELINE = (
    "filesrc location={filepath} ! "
    "qtdemux ! queue ! h264parse ! v4l2h264dec ! "
    "imxvideoconvert_g2d ! videoconvert ! video/x-raw, format=BGR ! "
    "appsink"
)
