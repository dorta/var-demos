#!/bin/bash

# Copyright 2021-2025 Variscite LTD
# SPDX-License-Identifier: BSD-3-Clause

set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP="$SCRIPT_DIR/detection-hd-fullhd-video-npu.py"
MODEL="$SCRIPT_DIR/model/ssd_mobilenet_v1_1_default_1.tflite"
LABEL="$SCRIPT_DIR/model/labels_ssd_mobilenet_v1.txt"

wait_for_weston() {
    echo "[INFO] Waiting for Weston to be available..."
    while [ ! -S /run/user/0/wayland-0 ] && [ ! -S /run/user/0/wayland-1 ]; do
        sleep 1
    done
    echo "[INFO] Weston detected."
    if [ -S /run/user/0/wayland-1 ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
        export WAYLAND_DISPLAY=wayland-1
    fi
}

run_demo() {
    local COMB="$1"
    local DEBUG_FLAG="$2"

    echo "[INFO] Running combination #$COMB"
    python3 "$APP" \
        --model "$MODEL" \
        --label "$LABEL" \
        --combination "$COMB" \
        $DEBUG_FLAG
}

main() {
    DEBUG_FLAG=""

    if [[ "$1" == "--debug" ]]; then
        DEBUG_FLAG="--debug"
        echo "[INFO] Debug mode enabled"
    fi

    wait_for_weston

    echo "=============================="
    echo "      Variscite Detection     "
    echo "=============================="
    echo ""
    echo "Available combinations:"
    echo ""

    python3 "$APP"

    echo ""
    read -p "Enter combination number to run (1-18): " COMB

    if ! [[ "$COMB" =~ ^[0-9]+$ ]] || [ "$COMB" -lt 1 ] || [ "$COMB" -gt 18 ]; then
        echo "[ERROR] Invalid selection: $COMB"
        exit 1
    fi

    run_demo "$COMB" "$DEBUG_FLAG"
}

main "$@"
