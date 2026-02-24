# Gesture Model Lab (i.MX95 / DART-MX95)

This folder is a separate model-evaluation workspace. It does **not** modify `gesture-demo`.

## Purpose
- Compare candidate hand/gesture models with real benchmarks on i.MX95.
- Convert TFLite models with eIQ Neutron converter.
- Measure CPU vs NPU delegate latency.

## Source models tested
From `PINTO_model_zoo`:
- `386_naruto_handsign_detection` (TFLite int8 variants)
- `094_hand_recrop` (TFLite int8 variants)

From existing demo baseline:
- `palm_detection_builtin_256_integer_quant.tflite`
- `hand_landmark_3d_256_integer_quant.tflite`

Not converted in this round:
- `481_WHC` provides ONNX models only in this package. Neutron converter expects TFLite input.
- `033_Hand_Detection_and_Tracking` was not re-downloaded here because it is the same MediaPipe baseline pair already present in `gesture-demo` (palm + landmark).

## Layout
- `assets/original/`: original TFLite models
- `assets/converted/`: Neutron-converted TFLite models and converter stats
- `benchmark_tflite.py`: single-model benchmark tool
- `run_benchmarks.sh`: batch benchmark (CPU and NPU delegate)
- `summarize_results.py`: print CSV summary from JSON results
- `deploy`: deploy to board by IP

## Neutron conversion (host)
```bash
./convert_models.sh
```

Each conversion writes:
- `*_neutron.tflite`
- `*.stats.txt`
- `*_subgraph_*_statistics.txt`

## Deploy to board
```bash
./deploy 192.168.0.10
```

## Run benchmarks on board
```bash
cd /opt/gesture-model-lab
LOOPS=120 WARMUP=20 ./run_benchmarks.sh
python3 summarize_results.py
```

Latest board run summary is stored at:
- `results/benchmark_board_192.168.0.10_2026-02-24.md`

## Notes
- If delegate path differs, set:
```bash
NEUTRON_DELEGATE=/usr/lib/libneutron_delegate.so ./run_benchmarks.sh
```
- Some models may fail on NPU due to unsupported ops/driver/runtime constraints.
- In this environment, Naruto Handsign TFLite variants failed to allocate due to LOGISTIC quantization constraints in the runtime.
