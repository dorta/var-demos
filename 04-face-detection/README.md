# 04 - Face Detection

## Tested BSP Image
Validated on:
`mx95__yocto-walnascar-6.12.20_2.0.0-v1.4__android-15.0.0_2.0.0-v1.1.wic.zst`

## What this demo does
This demo performs real-time face detection from camera stream.

Pipeline:
`face detector model -> box decode + NMS -> draw boxes`

## Why use this demo
Use this when you need a very fast and stable NPU showcase.

## Models included
- `assets/original/yolo_face_detect.tflite`
- `assets/converted/yolo_face_detect_neutron.tflite`

## Model origin (name + link)
- Model name: `yolo_face_detect.tflite`
- Source model path (eIQ model zoo):
  `eiq-model-zoo/tasks/vision/object-detection/faceDet/yolo_face_detect.tflite`
- Upstream repository:
  `https://github.com/nxp-imx/eiq-model-zoo`

## Conversion steps (eIQ Neutron SDK)
Converted for i.MX95 (`--target imx95`) from `assets/original` to `assets/converted`:
```bash
$SDK/bin/neutron-converter \
  --input assets/original/yolo_face_detect.tflite \
  --target imx95 \
  --output assets/converted/yolo_face_detect_neutron.tflite \
  --dump-statistics-file
```

## Run
```bash
./face-detection
```

Useful options:
```bash
./face-detection --camera /dev/video13 --use-npu 1
./face-detection --camera /dev/video0 --windowed
./face-detection --use-npu 0
```

## Deploy
Use the repository root deploy script:
```bash
cd ..
./deploy-all 192.168.0.10 04
```

## Performance profile summary
- One of the best-performing NPU demos in this repository.
- Suitable for quick executive-level demonstration.
