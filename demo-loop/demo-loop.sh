#!/bin/bash

# Copyright 2025-2026 Variscite Ltd.
#
# This software is proprietary and confidential to Variscite Ltd. It is
# intended for internal use only and must not be distributed, modified,
# or disclosed to any third party without explicit written permission
# from Variscite Ltd.

set -e


log() { echo "[INFO] $*"; }
die() { echo "[ERROR] $*" >&2; exit 1; }

pick_assets() {
  local som="$1" res="$2"
  local video1 video2

  case "$som:$res" in
    dart:800x480)
      video1="/opt/assets/demo-loop/pin2pin-video-800x480.mp4"
      video2="/opt/assets/demo-loop/variscite-mplus-npu-ssd-detection-hd-1280-720p.mp4"
      ;;
    dart:1280x800)
      video1="/opt/assets/demo-loop/pin2pin-video-1280x720.mp4"
      video2="/opt/assets/demo-loop/variscite-mplus-npu-ssd-detection-hd-1280-720p.mp4"
      ;;
    var-som:800x480)
      video1="/opt/assets/demo-loop/pin2pin-video-800x480.mp4"
      video2="/opt/assets/demo-loop/variscite-mplus-npu-ssd-detection-hd-1280-720p.mp4"
      ;;
    var-som:1280x800)
      video1="/opt/assets/demo-loop/pin2pin-video-1280x720.mp4"
      video2="/opt/assets/demo-loop/variscite-mplus-npu-ssd-detection-hd-1280-720p.mp4"
      ;;
    *)
      die "Unexpected selection: som='$som' res='$res'"
      ;;
  esac

  [[ -f "$video1" ]] || die "Video1 not found: $video1"
  [[ -f "$video2" ]] || die "Video2 not found: $video2"

  echo "$video1|$video2"
}

read_model() {
  tr -d '\0' </proc/device-tree/model 2>/dev/null || true
}

detect_som_and_res_from_model() {
  local model som res

  model="$(read_model)"
  [[ -n "$model" ]] || die "Unable to read /proc/device-tree/model"

  if echo "$model" | grep -qi "VAR-SOM-MX8M-PLUS"; then
    som="var-som"
  elif echo "$model" | grep -qi "DART-MX8M-PLUS"; then
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
  VIDEO1="${assets%%|*}"
  VIDEO2="${assets##*|}"

  log "Selected video1: $VIDEO1"
  log "Selected video2: $VIDEO2"

  VIDEOS=(
    "$VIDEO1"
    "$VIDEO2"
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
}

main
