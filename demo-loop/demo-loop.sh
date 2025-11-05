#!/bin/bash

# Copyright 2025 Variscite Ltd.
#
# This software is proprietary and confidential to Variscite Ltd. It is
# intended for internal use only and must not be distributed, modified,
# or disclosed to any third party without explicit written permission
# from Variscite Ltd.

set -e

VIDEOS=(
  "/opt/assets/demo-loop/variscite-intro.mp4"
  "/opt/assets/demo-loop/variscite-mplus-npu-ssd-detection-hd-1280-720p.mp4"
)

while true; do
  for v in "${VIDEOS[@]}"; do
    echo "[INFO] Playing: $v"
    gst-launch-1.0 -q \
      filesrc location="$v" ! decodebin ! \
      videoconvert ! videorate ! video/x-raw,framerate=25/1 ! \
      imxvideoconvert_g2d ! waylandsink fullscreen=true
  done
done