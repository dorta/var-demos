# Gesture Fast NPU Demo (new app)

This is a separate app from `gesture-demo`, focused on low latency with models that benchmarked well on i.MX95 NPU.

## Models
- `palm_detection_builtin_256_integer_quant_neutron.tflite`
- `hand_recrop_model_full_integer_quant_neutron.tflite`

CPU fallbacks are also included.

## Run on board
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
./deploy 192.168.0.10
```

## What it does
- Opens camera
- Runs palm detector (fast hand region proposal)
- Runs hand recrop model on detected hand region
- Draws hand box and overlays Palm/Recrop latency + FPS

This app is intended as a fast NPU baseline to build a next gesture stage on top.
