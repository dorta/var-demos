#!/bin/bash

# Copyright 2026 Variscite Ltd.
#
# This software is proprietary and confidential to Variscite Ltd. It is
# intended for internal use only and must not be distributed, modified,
# or disclosed to any third party without explicit written permission
# from Variscite Ltd.
#
# Variscite Demo Loop (DART-6UL / VAR-SOM-6UL)
#
# - Detect SoM (DART vs VAR-SOM)
# - Detect active display mode (800x480 vs 1280x800)
# - Show the corresponding slide, then play pin2pin video in a loop
#

set -e

VIDEO_DESKTOP_WAIT_SECONDS=20
SLIDE_SECONDS=20
POST_SLIDE_DESKTOP_SECONDS=30

# X11 demo environment
export DISPLAY=${DISPLAY:-:0.0}

log() { echo "[INFO] $*"; }
die() { echo "[ERROR] $*" >&2; exit 1; }

have_timeout() { command -v timeout >/dev/null 2>&1; }

pick_assets() {
  local som="$1" res="$2"
  local slide video

  case "$som:$res" in
    dart:800x480)
      slide="/opt/assets/demo-loop/DART-6UL-800x480.png"
      video="/opt/assets/demo-loop/pin2pin-video-800x480.mp4"
      ;;
    dart:1280x800)
      slide="/opt/assets/demo-loop/DART-6UL-1280x800.png"
      video="/opt/assets/demo-loop/pin2pin-video-1280x720.mp4"
      ;;
    var-som:800x480)
      slide="/opt/assets/demo-loop/VAR-SOM-6UL-800x480.png"
      video="/opt/assets/demo-loop/pin2pin-video-800x480.mp4"
      ;;
    var-som:1280x800)
      slide="/opt/assets/demo-loop/VAR-SOM-6UL-1280x800.png"
      video="/opt/assets/demo-loop/pin2pin-video-1280x720.mp4"
      ;;
    *)
      die "Unexpected selection: som='$som' res='$res'"
      ;;
  esac

  [[ -f "$slide" ]] || die "Slide not found: $slide"
  [[ -f "$video" ]] || die "Video not found: $video"

  echo "$slide|$video"
}

show_slide() {
  local png="$1"
  local w h

  case "$RES" in
    1280x800) w=1280; h=800 ;;
    800x480|*) w=800;  h=480 ;;
  esac

  log "Slide (${SLIDE_SECONDS}s): $png"

  timeout "${SLIDE_SECONDS}s" \
    gst-launch-1.0 -q \
      filesrc location="$png" ! \
      pngdec ! \
      imagefreeze ! \
      videoconvert ! \
      video/x-raw,format=UYVY,width=$w,height=$h ! \
      imxv4l2sink \
    >/dev/null 2>&1 || true
}

play_video() {
  local mp4="$1"
  log "Video: $mp4"

  gst-play-1.0 -q "$mp4" >/dev/null 2>&1 || true
}

run_loop() {
  while true; do
    play_video "$VIDEO"
    sleep "${VIDEO_DESKTOP_WAIT_SECONDS}"
    show_slide "$SLIDE"
    sleep "${POST_SLIDE_DESKTOP_SECONDS}"
  done
}

read_model() {
  tr -d '\0' </proc/device-tree/model 2>/dev/null || true
}

detect_som_and_res_from_model() {
  local model som res

  model="$(read_model)"
  [[ -n "$model" ]] || die "Unable to read /proc/device-tree/model"

  if echo "$model" | grep -qi "VAR-SOM-6UL"; then
    som="var-som"
  elif echo "$model" | grep -qi "DART-6UL"; then
    som="dart"
  else
    die "Unknown SoM model: $model"
  fi

  if echo "$model" | grep -qi "1280x800"; then
    res="1280x800"
  else
    res="800x480"
  fi

  echo "$som|$res"
}

main() {
  local det assets
  det="$(detect_som_and_res_from_model)"
  SOM="${det%%|*}"
  RES="${det##*|}"

  log "Detected SoM: $SOM"
  log "Detected display: $RES"

  assets="$(pick_assets "$SOM" "$RES")"
  SLIDE="${assets%%|*}"
  VIDEO="${assets##*|}"

  log "Selected slide: $SLIDE"
  log "Selected video: $VIDEO"

  run_loop
}

main
