# 01 - Hand Gesture Full

## What this demo does
This is the complete hand gesture pipeline:
- palm detection
- 21 hand landmarks
- gesture classification from landmarks

Pipeline:
`palm -> landmarks -> gesture`

## Why use this demo
Use this when you want the most complete hand understanding (finger/joint-based behavior).

## Models included
- `assets/original/palm_detection_builtin_256_integer_quant.tflite`
- `assets/original/hand_landmark_3d_256_integer_quant.tflite`
- `assets/converted/palm_detection_builtin_256_integer_quant_neutron.tflite`
- `assets/converted/hand_landmark_3d_256_integer_quant_neutron.tflite`
- `assets/shared/anchors.csv`

## Model origin
- MediaPipe-style hand models used in NXP/eIQ hand tracking flows.

## Conversion reference
Converted with eIQ Neutron SDK (`imx95` target):
```bash
$SDK/bin/neutron-converter --input <original_model.tflite> --target imx95 --output <converted_model.tflite> --dump-statistics-file
```

## Run
```bash
python3 main.py
```

Useful options:
```bash
python3 main.py --list-cameras
python3 main.py --camera /dev/video13 --use-npu 1
python3 main.py --camera /dev/video0 --setup-mipi --use-npu 1
python3 main.py --use-npu 0
```

## Deploy
```bash
./deploy 192.168.0.10
```
Default remote path: `/opt/01-hand-gesture-full`

## Performance profile summary
- Best behavior quality among hand demos.
- Landmark stage is the main latency bottleneck.
