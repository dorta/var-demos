# 03 - Hand Direction Tracking

## Tested BSP Image

Validated on:

* `mx95__yocto-walnascar-6.12.20_2.0.0-v1.4__android-15.0.0_2.0.0-v1.1.wic.zst`

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

- `assets/original/palm_detection_builtin_256_integer_quant.tflite`
- `assets/original/hand_recrop_model_full_integer_quant.tflite`
- `assets/converted/palm_detection_builtin_256_integer_quant_neutron.tflite`
- `assets/converted/hand_recrop_model_full_integer_quant_neutron.tflite`
- `assets/shared/anchors.csv`

Classifier implementation:

- `lite_gesture_classifier.py`

## Model origin (name + link)

- Palm model name: `palm_detection_builtin_256_integer_quant.tflite`
  - Source used in this repo: previously validated project baseline artifact.
  - Reference family: MediaPipe Palm Detection:
    `https://github.com/google-ai-edge/mediapipe/tree/master/mediapipe/modules/palm_detection`
- Recrop model name: `hand_recrop_model_full_integer_quant.tflite`
  - Source: PINTO model zoo hand recrop family (`094_hand_recrop`):
    `https://github.com/PINTO0309/PINTO_model_zoo/tree/main/094_hand_recrop`
- Anchor file name: `anchors.csv`
  - Source used in this repo: paired with the palm detector from the same validated baseline.
- Direction classifier:
  - `lite_gesture_classifier.py` (custom motion-history heuristic, project code).

## Conversion steps (eIQ Neutron SDK)

Converted for i.MX95 (`--target imx95`) from `assets/original` to `assets/converted`:

```sh
$SDK/bin/neutron-converter \
  --input assets/original/palm_detection_builtin_256_integer_quant.tflite \
  --target imx95 \
  --output assets/converted/palm_detection_builtin_256_integer_quant_neutron.tflite \
  --dump-statistics-file

$SDK/bin/neutron-converter \
  --input assets/original/hand_recrop_model_full_integer_quant.tflite \
  --target imx95 \
  --output assets/converted/hand_recrop_model_full_integer_quant_neutron.tflite \
  --dump-statistics-file
```

## Run

```sh
./hand-direction-tracking
```

Useful options:

```sh
./hand-direction-tracking --camera /dev/video13 --use-npu 1
./hand-direction-tracking --camera /dev/video0 --windowed
./hand-direction-tracking --use-npu 0
```

## Deploy

Use the repository root deploy script:

```sh
./deploy-all 192.168.0.10 03
```

## Accuracy note

- This is intentionally lightweight and fast.
- It is not a full 21-landmark semantic hand-pose model.
