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

## Model origin (name + link)
- Palm model name: `palm_detection_builtin_256_integer_quant.tflite`
  - Source used in this repo: previously validated project baseline artifact.
  - Reference family: MediaPipe Palm Detection:
    `https://github.com/google-ai-edge/mediapipe/tree/master/mediapipe/modules/palm_detection`
- Landmark model name: `hand_landmark_3d_256_integer_quant.tflite`
  - Source used in this repo: previously validated project baseline artifact.
  - Reference family: MediaPipe Hand Landmark:
    `https://github.com/google-ai-edge/mediapipe/tree/master/mediapipe/modules/hand_landmark`
- Anchor file name: `anchors.csv`
  - Source used in this repo: paired with the palm detector from the same validated baseline.

## Conversion steps (eIQ Neutron SDK)
Converted for i.MX95 (`--target imx95`) from `assets/original` to `assets/converted`:
```bash
$SDK/bin/neutron-converter \
  --input assets/original/palm_detection_builtin_256_integer_quant.tflite \
  --target imx95 \
  --output assets/converted/palm_detection_builtin_256_integer_quant_neutron.tflite \
  --dump-statistics-file

$SDK/bin/neutron-converter \
  --input assets/original/hand_landmark_3d_256_integer_quant.tflite \
  --target imx95 \
  --output assets/converted/hand_landmark_3d_256_integer_quant_neutron.tflite \
  --dump-statistics-file
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
Use the repository root deploy script:
```bash
cd ..
./deploy-all 192.168.0.10 01
```

## Performance profile summary
- Best behavior quality among hand demos.
- Landmark stage is the main latency bottleneck.
