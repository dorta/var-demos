# 01 - Hand Gesture Full

## Tested BSP Image
Validated on:
`mx95__yocto-walnascar-6.12.20_2.0.0-v1.4__android-15.0.0_2.0.0-v1.1.wic.zst`

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
./hand-gesture-full
```

Useful options:
```bash
./hand-gesture-full --list-cameras
./hand-gesture-full --camera /dev/video13 --use-npu 1
./hand-gesture-full --camera /dev/video0 --setup-mipi --use-npu 1
./hand-gesture-full --use-npu 0
```

## Deploy
```bash
./deploy 192.168.0.10
```
Default remote path: `/opt/01-hand-gesture-full`

## Performance profile summary
- Best behavior quality among hand demos.
- Landmark stage is the main latency bottleneck.
