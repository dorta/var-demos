#!/usr/bin/env bash
set -euo pipefail

DELEGATE_DEFAULT="/usr/lib/libneutron_delegate.so"
DELEGATE="${NEUTRON_DELEGATE:-$DELEGATE_DEFAULT}"
LOOPS="${LOOPS:-120}"
WARMUP="${WARMUP:-20}"

mkdir -p results

test_one() {
  local model="$1"
  local tag="$2"
  local mode="${3:-both}"
  local run_cpu=1
  local run_npu=1

  if [[ "$mode" == "cpu" ]]; then
    run_npu=0
  elif [[ "$mode" == "npu" ]]; then
    run_cpu=0
  fi

  if [[ $run_cpu -eq 1 ]]; then
    echo "\n==== $tag (CPU) ===="
    set +e
    python3 benchmark_tflite.py --model "$model" --warmup "$WARMUP" --loops "$LOOPS" \
      --json-out "results/${tag}_cpu.json"
    local rc=$?
    set -e
    if [[ $rc -ne 0 ]]; then
      echo "WARN: CPU benchmark failed for $tag"
    fi
  fi

  if [[ $run_npu -eq 1 && -f "$DELEGATE" ]]; then
    echo "\n==== $tag (NPU delegate) ===="
    set +e
    python3 benchmark_tflite.py --model "$model" --delegate "$DELEGATE" --warmup "$WARMUP" --loops "$LOOPS" \
      --json-out "results/${tag}_npu.json"
    local rc=$?
    set -e
    if [[ $rc -ne 0 ]]; then
      echo "WARN: NPU benchmark failed for $tag"
    fi
  else
    echo "WARN: delegate not found at $DELEGATE"
  fi
}

models=(
  "assets/original/palm_detection_builtin_256_integer_quant.tflite:palm_orig:both"
  "assets/converted/palm_detection_builtin_256_integer_quant_neutron.tflite:palm_neutron:npu"
  "assets/original/hand_landmark_3d_256_integer_quant.tflite:landmark_orig:both"
  "assets/converted/hand_landmark_3d_256_integer_quant_neutron.tflite:landmark_neutron:npu"
  "assets/original/naruto_handsign_detection_yolox_nano_integer_quant.tflite:naruto_iq_orig:both"
  "assets/converted/naruto_handsign_detection_yolox_nano_integer_quant_neutron.tflite:naruto_iq_neutron:npu"
  "assets/original/naruto_handsign_detection_yolox_nano_full_integer_quant.tflite:naruto_fiq_orig:both"
  "assets/converted/naruto_handsign_detection_yolox_nano_full_integer_quant_neutron.tflite:naruto_fiq_neutron:npu"
  "assets/original/hand_recrop_model_integer_quant.tflite:recrop_iq_orig:both"
  "assets/converted/hand_recrop_model_integer_quant_neutron.tflite:recrop_iq_neutron:npu"
  "assets/original/hand_recrop_model_full_integer_quant.tflite:recrop_fiq_orig:both"
  "assets/converted/hand_recrop_model_full_integer_quant_neutron.tflite:recrop_fiq_neutron:npu"
)

for item in "${models[@]}"; do
  model="$(echo "$item" | cut -d: -f1)"
  tag="$(echo "$item" | cut -d: -f2)"
  mode="$(echo "$item" | cut -d: -f3)"
  if [[ -f "$model" ]]; then
    test_one "$model" "$tag" "$mode"
  else
    echo "SKIP: missing $model"
  fi
done

echo "\nBenchmark finished. Results in results/*.json"
