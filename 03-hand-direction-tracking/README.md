# 03 - Hand Direction Tracking

## Tested BSP Image
Validated on:
`mx95__yocto-walnascar-6.12.20_2.0.0-v1.4__android-15.0.0_2.0.0-v1.1.wic.zst`

## What this demo does
This demo tracks hand movement direction in real time.

Pipeline:
`palm detection -> recrop refinement -> lightweight trajectory classifier`

Output labels:
- `NO_HAND`
- `STILL`
- `MOVE_LEFT`
- `MOVE_RIGHT`
- `MOVE_UP`
- `MOVE_DOWN`
- `WAVE`

## Why use this demo
Use this when you need directional hand interaction with high responsiveness.

## Models included
- `assets/palm_detection_builtin_256_integer_quant.tflite`
- `assets/palm_detection_builtin_256_integer_quant_neutron.tflite`
- `assets/hand_recrop_model_full_integer_quant.tflite`
- `assets/hand_recrop_model_full_integer_quant_neutron.tflite`
- `assets/anchors.csv`

Classifier implementation:
- `lite_gesture_classifier.py`

## Model origin
- Palm and recrop models are the same fast pair used in demo 02.
- Direction classifier is custom project code (motion-history heuristic).

## Conversion reference
Converted with eIQ Neutron SDK (`imx95` target), same as demo 02.

## Run
```bash
./03-hand-direction-tracking
```

Useful options:
```bash
./03-hand-direction-tracking --camera /dev/video13 --use-npu 1
./03-hand-direction-tracking --camera /dev/video0 --windowed
./03-hand-direction-tracking --use-npu 0
```

## Deploy
```bash
./deploy 192.168.0.10
```
Default remote path: `/opt/03-hand-direction-tracking`

## Accuracy note
- This is intentionally lightweight and fast.
- It is not a full 21-landmark semantic hand-pose model.
