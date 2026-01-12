#!/bin/bash

# Copyright 2026 Variscite Ltd.
#
# This software is proprietary and confidential to Variscite Ltd. It is
# intended for internal use only and must not be distributed, modified,
# or disclosed to any third party without explicit written permission
# from Variscite Ltd.
#
# Variscite Demo Loop (DART-MX93 / VAR-SOM-MX93)
#
# - Detect SoM (DART vs VAR-SOM)
# - Detect active display mode (800x480 vs 1280x800)
# - Show the corresponding slide, then play pin2pin video in a loop
# - ML video recorded

set -euo

SLIDE_SECONDS=30

MEDIA_DIR="/opt/assets/demo-loop"

log() { echo "[INFO] $*"; }
die() { echo "[ERROR] $*" >&2; exit 1; }

pick_assets() {
  local som="$1" res="$2"
  local slide video ml

  case "$som:$res" in
    dart:800x480)
      slide="${MEDIA_DIR}/dart-mx93-91-demo_800x480.png"
      video="${MEDIA_DIR}/pin2pin-video-800x480.mp4"
      ml="${MEDIA_DIR}/mx93_mldemo_800x480.mp4"
      ;;
    dart:1280x800)
      slide="${MEDIA_DIR}/dart-mx93-91-demo_1280x800.png"
      video="${MEDIA_DIR}/pin2pin-video-1280x720.mp4"
      ml="${MEDIA_DIR}/mx93_mldemo_1280x800.mp4"
      ;;
    var-som:800x480)
      slide="${MEDIA_DIR}/var-som-mx93-91-demo_800x480.png"
      video="${MEDIA_DIR}/pin2pin-video-800x480.mp4"
      ml="${MEDIA_DIR}/mx93_mldemo_800x480.mp4"
      ;;
    var-som:1280x800)
      slide="${MEDIA_DIR}/var-som-mx93-91-demo_1280x800.png"
      video="${MEDIA_DIR}/pin2pin-video-1280x720.mp4"
      ml="${MEDIA_DIR}/mx93_mldemo_1280x800.mp4"
      ;;
    *)
      die "Unexpected selection: som='$som' res='$res'"
      ;;
  esac

  [[ -f "$slide" ]] || die "Slide not found: $slide"
  [[ -f "$video" ]] || die "Video not found: $video"
  [[ -f "$ml" ]] || die "Video not found: $ml"

  echo "$slide|$video|$ml"
}

play_mjpeg_mp4() {
  local mp4="$1"
  log "Video (MJPEG/MP4): $mp4"

  gst-launch-1.0 -q \
    filesrc location="$mp4" ! \
    qtdemux name=d d.video_0 ! queue ! jpegparse ! jpegdec ! videoconvert ! videoscale ! waylandsink fullscreen=true \
    >/dev/null 2>&1 || true
}

show_slide() {
  local png="$1"
  log "Slide (${SLIDE_SECONDS}s): $png"

  gst-launch-1.0 -q \
    multifilesrc num-buffers="$SLIDE_SECONDS" location="$png" caps="image/png,framerate=1/1" ! \
    pngdec ! videoconvert ! videoscale ! waylandsink fullscreen=true \
    >/dev/null 2>&1 || true
}

run_loop() {
  while true; do
    play_mjpeg_mp4 "$ML"
    show_slide "$SLIDE"
    play_mjpeg_mp4 "$VIDEO"
  done
}

read_model() {
  tr -d '\0' </proc/device-tree/model 2>/dev/null || true
}

detect_som_and_res_from_model() {
  local model som res

  model="$(read_model)"
  [[ -n "$model" ]] || die "Unable to read /proc/device-tree/model"

  if echo "$model" | grep -qi "VAR-SOM-MX93"; then
    som="var-som"
  elif echo "$model" | grep -qi "DART-MX93"; then
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
  local det assets rest
  det="$(detect_som_and_res_from_model)"
  SOM="${det%%|*}"
  RES="${det##*|}"

  log "Detected SoM: $SOM"
  log "Detected display: $RES"

  assets="$(pick_assets "$SOM" "$RES")"
  SLIDE="${assets%%|*}"
  rest="${assets#*|}"
  VIDEO="${rest%%|*}"
  ML="${assets##*|}"

  log "Selected ML video: $ML"
  log "Selected slide: $SLIDE"
  log "Selected pin2pin video: $VIDEO"

  run_loop
}

main "$@"