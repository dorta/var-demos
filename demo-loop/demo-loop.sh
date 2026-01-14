#!/bin/bash

# Copyright 2026 Variscite Ltd.
#
# This software is proprietary and confidential to Variscite Ltd. It is
# intended for internal use only and must not be distributed, modified,
# or disclosed to any third party without explicit written permission
# from Variscite Ltd.
#
# Variscite Demo Loop (VAR-SOM-AM62P)
#
# - Detect active display mode (800x480 vs 1280x800)
# - Run OpenGLES demo, then show the corresponding slide in a loop

set -euo

SLIDE_SECONDS=42
GRAPHICS_SECONDS=42

MEDIA_DIR="/opt/assets/demo-loop"

log() { echo "[INFO] $*"; }
die() { echo "[ERROR] $*" >&2; exit 1; }

pick_assets() {
  local res="$1"
  local slide width height demo

  case "$res" in
    800x480)
      slide="${MEDIA_DIR}/VAR-SOM-AM62P-demo-800x480.png"
      width=800
      height=480
      ;;
    1280x800)
      slide="${MEDIA_DIR}/VAR-SOM-AM62P-demo-1280x800.png"
      width=1280
      height=800
      ;;
    *)
      die "Unexpected selection: res='$res'"
      ;;
  esac

  demo="/usr/bin/SGX/demos/Wayland/OpenGLESSkinning"

  [[ -f "$slide" ]] || die "Slide not found: $slide"
  [[ -x "$demo" ]] || die "OpenGLES demo not found/executable: $demo"

  echo "$slide|$width|$height|$demo"
}

run_opengles_demo() {
  local demo="$1" width="$2" height="$3"

  log "OpenGLES demo (${GRAPHICS_SECONDS}s): ${demo} (${width}x${height})"

  "$demo" -width="$width" -height="$height" -quitaftertime="${GRAPHICS_SECONDS}" \
    >/dev/null 2>&1 || true
}

show_slide() {
  local png="$1"

  log "Slide (${SLIDE_SECONDS}s): $png"

  command -v mpv >/dev/null 2>&1 || die "mpv not found"

  mpv --fs --really-quiet --image-display-duration="${SLIDE_SECONDS}" "$png" \
    >/dev/null 2>&1 || true
}

run_loop() {
  while true; do
    run_opengles_demo "$DEMO" "$WIDTH" "$HEIGHT"
    show_slide "$SLIDE"
  done
}

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

main() {
  local assets rest

  RES="$(detect_res_from_model)"

  log "Detected display: $RES"

  assets="$(pick_assets "$RES")"
  SLIDE="${assets%%|*}"
  rest="${assets#*|}"
  WIDTH="${rest%%|*}"
  rest="${rest#*|}"
  HEIGHT="${rest%%|*}"
  DEMO="${assets##*|}"

  log "Selected OpenGLES demo: $DEMO"
  log "Selected slide: $SLIDE"
  log "Selected resolution: ${WIDTH}x${HEIGHT}"

  run_loop
}

main "$@"