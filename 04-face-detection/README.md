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
- `assets/yolo_face_detect.tflite`
- `assets/yolo_face_detect_neutron.tflite`

## Model origin
- Source model from eIQ model zoo:
  `eiq-model-zoo/tasks/vision/object-detection/faceDet/yolo_face_detect.tflite`

## Conversion reference
Converted with eIQ Neutron SDK (`imx95` target):
```bash
$SDK/bin/neutron-converter \
  --input yolo_face_detect.tflite \
  --target imx95 \
  --output yolo_face_detect_neutron.tflite \
  --dump-statistics-file
```

## Run
```bash
./04-face-detection
```

Useful options:
```bash
./04-face-detection --camera /dev/video13 --use-npu 1
./04-face-detection --camera /dev/video0 --windowed
./04-face-detection --use-npu 0
```

## Deploy
```bash
./deploy 192.168.0.10
```
Default remote path: `/opt/04-face-detection`

## Performance profile summary
- One of the best-performing NPU demos in this repository.
- Suitable for quick executive-level demonstration.
