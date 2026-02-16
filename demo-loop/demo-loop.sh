#!/bin/bash

# Copyright 2025-2026 Variscite Ltd.
#
# This software is proprietary and confidential to Variscite Ltd. It is
# intended for internal use only and must not be distributed, modified,
# or disclosed to any third party without explicit written permission
# from Variscite Ltd.
#
# Variscite Demo Loop (DART-MX8M-MINI / VAR-SOM-MX8M-MINI)
#
# - Detect SoM (DART vs VAR-SOM)
# - Detect active display mode (800x480 vs 1280x800)
# - Show the corresponding slide, then play pin2pin video in a loop
# - 3D demo
#

set -e

SLIDE_SECONDS=30

log() { echo "[INFO] $*"; }
die() { echo "[ERROR] $*" >&2; exit 1; }

have_timeout() { command -v timeout >/dev/null 2>&1; }

pick_assets() {
  local som="$1" res="$2"
  local slide video

  case "$som:$res" in
    dart:800x480)
      slide="/opt/assets/demo-loop/dart-mx8m-mini-demo-800x480.png"
      video="/opt/assets/demo-loop/pin2pin-video-800x480.mp4"
      ;;
    dart:1280x800)
      slide="/opt/assets/demo-loop/dart-mx8m-mini-demo-1280x800.png"
      video="/opt/assets/demo-loop/pin2pin-video-1280x720.mp4"
      ;;
    var-som:800x480)
      slide="/opt/assets/demo-loop/var-som-mx8m-mini-nano-demo-800x480.png"
      video="/opt/assets/demo-loop/pin2pin-video-800x480.mp4"
      ;;
    var-som:1280x800)
      slide="/opt/assets/demo-loop/var-som-mx8m-mini-nano-demo-1280x800.png"
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
    imxvideoconvert_g2d ! \
    waylandsink fullscreen=true
}

run_3d_demo_if_available() {
  if [[ -x /opt/imx-gpu-sdk/GLES2/Bloom___Wayland/GLES2.Bloom___Wayland ]]; then
    log "Running 3D demo (30 seconds)"
    /opt/imx-gpu-sdk/GLES2/Bloom___Wayland/GLES2.Bloom___Wayland --ExitAfterFrame 650
  fi
}

run_loop() {
  while true; do
    run_3d_demo_if_available
    show_slide "$SLIDE"
    play_video "$VIDEO"
  done
}

read_model() {
  tr -d '\0' </proc/device-tree/model 2>/dev/null || true
}

detect_som_and_res_from_model() {
  local model som res

  model="$(read_model)"
  [[ -n "$model" ]] || die "Unable to read /proc/device-tree/model"

  if echo "$model" | grep -qi "VAR-SOM-MX8M-MINI"; then
    som="var-som"
  elif echo "$model" | grep -qi "DART-MX8M-MINI"; then
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
