#!/bin/sh

# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ASSET_VERSION=${ASSET_VERSION:-v1}
ASSET_BASE_URL=${ASSET_BASE_URL:-"https://nyc3.digitaloceanspaces.com/variscite-marketing/demos/high-resolution-video-detection/${ASSET_VERSION}/samples"}
ASSET_DIR=${ASSET_DIR:-"${SCRIPT_DIR}/assets/videos"}
MANIFEST="${ASSET_DIR}/SHA256SUMS"

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Error: required command not found: $1" >&2
        exit 1
    fi
}

download() {
    url=$1
    destination=$2
    temporary="${destination}.part"

    echo "Downloading ${url}"
    curl \
        --fail \
        --location \
        --retry 5 \
        --retry-all-errors \
        --connect-timeout 15 \
        --output "${temporary}" \
        "${url}"
    mv -f "${temporary}" "${destination}"
}

check_runtime() {
    missing=0

    for plugin in appsink decodebin imxvideoconvert_g2d; do
        if ! gst-inspect-1.0 "${plugin}" >/dev/null 2>&1; then
            echo "Error: missing GStreamer plugin: ${plugin}" >&2
            missing=1
        fi
    done

    if [ ! -r /usr/lib/libvx_delegate.so ]; then
        echo "Error: missing NPU delegate: /usr/lib/libvx_delegate.so" >&2
        missing=1
    fi

    if ! python3 - <<'PY'
import cv2
import gi
import numpy
import tflite_runtime.interpreter
PY
    then
        echo "Error: one or more required Python modules are missing." >&2
        missing=1
    fi

    if [ "${missing}" -ne 0 ]; then
        exit 1
    fi
}

require_command curl
require_command gst-inspect-1.0
require_command install
require_command python3
require_command sha256sum

check_runtime
install -d "${ASSET_DIR}"
download "${ASSET_BASE_URL}/SHA256SUMS" "${MANIFEST}"

while read -r expected filename; do
    case "${filename}" in
        video_1280x720.mp4|video_1280x800.mp4|video_1920x1080.mp4)
            destination="${ASSET_DIR}/${filename}"
            if [ -f "${destination}" ] && \
               printf '%s  %s\n' "${expected}" "${destination}" | \
                   sha256sum -c - >/dev/null 2>&1; then
                echo "Using verified ${filename}"
            else
                download "${ASSET_BASE_URL}/${filename}" "${destination}"
            fi
            ;;
        *)
            echo "Error: unexpected file in SHA256SUMS: ${filename}" >&2
            exit 1
            ;;
    esac
done < "${MANIFEST}"

(cd "${ASSET_DIR}" && sha256sum -c SHA256SUMS)

echo
echo "Installation complete."
echo "List presets: python3 ${SCRIPT_DIR}/high-resolution-video-detection.py"
echo "Run on XWayland:"
echo "  XDG_RUNTIME_DIR=/run/user/0 DISPLAY=:0 python3 ${SCRIPT_DIR}/high-resolution-video-detection.py --combination 2"
