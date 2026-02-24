# Gesture Fast NPU Lite Classifier (new app)

Separate app. It does not modify `gesture-demo` or `gesture-fast-npu-demo`.

## Goal
Keep high FPS using only models that performed well on NPU and add a lightweight gesture classifier.

## Pipeline
1. `palm_detection_builtin_256_integer_quant_neutron.tflite` (NPU)
2. `hand_recrop_model_full_integer_quant_neutron.tflite` (NPU)
3. Lightweight motion-based classifier (CPU math only)

## Gesture labels
- `NO_HAND`
- `STILL`
- `MOVE_LEFT`
- `MOVE_RIGHT`
- `MOVE_UP`
- `MOVE_DOWN`
- `WAVE`

## Run
```bash
python3 main.py
```

Optional:
```bash
python3 main.py --camera /dev/video13 --use-npu 1
python3 main.py --camera /dev/video0 --use-npu 1 --windowed
python3 main.py --use-npu 0
```

## Deploy
```bash
./deploy 192.168.0.10 /opt/gesture-fast-npu-lite-gesture
```

## Notes
- This is a lightweight classifier by trajectory heuristic, not 21-landmark semantic classification.
- It is designed for speed and responsiveness.
