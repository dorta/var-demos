#!/bin/bash

# Copyright 2025-2026 Variscite Ltd.
#
# This software is proprietary and confidential to Variscite Ltd. It is
# intended for internal use only and must not be distributed, modified,
# or disclosed to any third party without explicit written permission
# from Variscite Ltd.

set -e

SLIDE_SECONDS=30

log() { echo "[INFO] $*"; }
die() { echo "[ERROR] $*" >&2; exit 1; }

have_timeout() { command -v timeout >/dev/null 2>&1; }

read_model() {
  tr -d '\0' </proc/device-tree/model 2>/dev/null || true
}

detect_res_from_model() {
  local model res
  model="$(read_model)"
  [[ -n "$model" ]] || die "Unable to read /proc/device-tree/model"

  if echo "$model" | grep -qi "1280x800"; then
    res="1280x800"
  else
    res="800x480"
  fi

  echo "$res"
}

pick_assets() {
  local res="$1"
  local slide video

  case "$res" in
    800x480)
      slide="/opt/assets/demo-loop/VAR-SMARC-MX8M-PLUS_800x480.png"
      video="/opt/assets/demo-loop/variscite-mplus-npu-ssd-detection-hd-1280-720p.mp4"
      ;;
    1280x800)
      slide="/opt/assets/demo-loop/VAR-SMARC-MX8M-PLUS_1280x800.png"
      video="/opt/assets/demo-loop/variscite-mplus-npu-ssd-detection-hd-1280-720p.mp4"
      ;;
    *)
      die "Unexpected display resolution: '$res'"
      ;;
  esac

  [[ -f "$slide" ]] || die "Slide not found: $slide"
  [[ -f "$video" ]] || die "Video not found: $video"

  echo "$slide|$video"
}

show_slide() {
  local png="$1"
  log "Slide (${SLIDE_SECONDS}s): $png"

  if have_timeout; then
    timeout "${SLIDE_SECONDS}s" \
      gst-launch-1.0 -q \
        filesrc location="$png" ! pngdec ! imagefreeze ! \
        videoconvert ! videorate ! video/x-raw,framerate=25/1 ! \
        waylandsink fullscreen=true \
      >/dev/null 2>&1 || true
  else
    gst-launch-1.0 -q \
      filesrc location="$png" ! pngdec ! imagefreeze ! \
        videoconvert ! videorate ! video/x-raw,framerate=25/1 ! \
        waylandsink fullscreen=true \
      >/dev/null 2>&1 &
    local pid=$!
    sleep "${SLIDE_SECONDS}"
    kill "$pid" >/dev/null 2>&1 || true
    wait "$pid" >/dev/null 2>&1 || true
  fi
}

play_video() {
  local mp4="$1"
  log "Video: $mp4"

  gst-launch-1.0 -q \
    filesrc location="$mp4" ! decodebin ! \
    videoconvert ! videorate ! video/x-raw,framerate=25/1 ! \
    imxvideoconvert_g2d ! waylandsink fullscreen=true
}

main() {
  local res assets
  local SLIDE VIDEO

  res="$(detect_res_from_model)"
  log "Detected display: $res"

  assets="$(pick_assets "$res")"
  SLIDE="${assets%%|*}"
  VIDEO="${assets##*|}"

  log "Selected slide: $SLIDE"
  log "Selected video: $VIDEO"

  while true; do
    show_slide "$SLIDE"
    play_video "$VIDEO"
  done
}

main