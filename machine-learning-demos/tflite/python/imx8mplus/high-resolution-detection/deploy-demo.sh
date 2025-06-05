#!/bin/bash

# Copyright 2021-2025 Variscite LTD
# SPDX-License-Identifier: BSD-3-Clause

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <TARGET_IP>"
    exit 1
fi

TARGET_IP="$1"
TARGET_USER="root"
TARGET_PATH="/home/root/detection-demo"

echo "[INFO] Deploying to ${TARGET_USER}@${TARGET_IP}:${TARGET_PATH}"

ssh ${TARGET_USER}@${TARGET_IP} "mkdir -p ${TARGET_PATH}"

scp detection-hd-fullhd-video-npu.py utils_draw.py run-demo.sh \
    ${TARGET_USER}@${TARGET_IP}:${TARGET_PATH}/

scp -r model ${TARGET_USER}@${TARGET_IP}:${TARGET_PATH}/

scp -r media ${TARGET_USER}@${TARGET_IP}:${TARGET_PATH}/

scp README.md ${TARGET_USER}@${TARGET_IP}:${TARGET_PATH}/

echo "[SUCCESS] All files deployed successfully to ${TARGET_IP}"
echo "To run the demo, SSH into the target and execute:"
echo "  cd ${TARGET_PATH} && ./run-demo.sh"
