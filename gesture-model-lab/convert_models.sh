#!/usr/bin/env bash
set -euo pipefail

SDK_DEFAULT="/home/dorta/pier/tools/eiq-neutron-sdk-linux-3.0.0"
SDK="${EIQ_NEUTRON_SDK:-$SDK_DEFAULT}"
CONVERTER="$SDK/bin/neutron-converter"
TARGET="${NEUTRON_TARGET:-imx95}"
IN_DIR="assets/original"
OUT_DIR="assets/converted"

if [[ ! -x "$CONVERTER" ]]; then
  echo "ERROR: converter not found at $CONVERTER"
  exit 1
fi

export LD_LIBRARY_PATH="$SDK/lib:${LD_LIBRARY_PATH:-}"
mkdir -p "$OUT_DIR"

convert_one() {
  local in_model="$1"
  local out_model="$2"
  local stats_txt="$3"
  echo "\n== Converting: $in_model =="
  "$CONVERTER" \
    --input "$in_model" \
    --target "$TARGET" \
    --output "$out_model" \
    --dump-statistics \
    --dump-statistics-file | tee "$stats_txt"
}

convert_one "$IN_DIR/palm_detection_builtin_256_integer_quant.tflite" \
            "$OUT_DIR/palm_detection_builtin_256_integer_quant_neutron.tflite" \
            "$OUT_DIR/palm_detection_builtin_256_integer_quant_neutron.stats.txt"

convert_one "$IN_DIR/hand_landmark_3d_256_integer_quant.tflite" \
            "$OUT_DIR/hand_landmark_3d_256_integer_quant_neutron.tflite" \
            "$OUT_DIR/hand_landmark_3d_256_integer_quant_neutron.stats.txt"

convert_one "$IN_DIR/naruto_handsign_detection_yolox_nano_integer_quant.tflite" \
            "$OUT_DIR/naruto_handsign_detection_yolox_nano_integer_quant_neutron.tflite" \
            "$OUT_DIR/naruto_handsign_detection_yolox_nano_integer_quant_neutron.stats.txt"

convert_one "$IN_DIR/naruto_handsign_detection_yolox_nano_full_integer_quant.tflite" \
            "$OUT_DIR/naruto_handsign_detection_yolox_nano_full_integer_quant_neutron.tflite" \
            "$OUT_DIR/naruto_handsign_detection_yolox_nano_full_integer_quant_neutron.stats.txt"

convert_one "$IN_DIR/hand_recrop_model_integer_quant.tflite" \
            "$OUT_DIR/hand_recrop_model_integer_quant_neutron.tflite" \
            "$OUT_DIR/hand_recrop_model_integer_quant_neutron.stats.txt"

convert_one "$IN_DIR/hand_recrop_model_full_integer_quant.tflite" \
            "$OUT_DIR/hand_recrop_model_full_integer_quant_neutron.tflite" \
            "$OUT_DIR/hand_recrop_model_full_integer_quant_neutron.stats.txt"

echo "\nConversion finished. Output dir: $OUT_DIR"
ls -lh "$OUT_DIR"
