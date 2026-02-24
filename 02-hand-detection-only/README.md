# 02 - Hand Detection Only

## Tested BSP Image
Validated on:
`mx95__yocto-walnascar-6.12.20_2.0.0-v1.4__android-15.0.0_2.0.0-v1.1.wic.zst`

## What this demo does
This demo only detects/localizes the hand region very quickly.

Pipeline:
`palm detection -> recrop refinement`

## Why use this demo
Use this when you want very fast hand presence/tracking without complex gesture semantics.

## Models included
- `assets/palm_detection_builtin_256_integer_quant.tflite`
- `assets/palm_detection_builtin_256_integer_quant_neutron.tflite`
- `assets/hand_recrop_model_full_integer_quant.tflite`
- `assets/hand_recrop_model_full_integer_quant_neutron.tflite`
- `assets/anchors.csv`

## Model origin
- Palm: MediaPipe/NXP baseline used across the project.
- Recrop: PINTO model zoo `094_hand_recrop` candidate.

## Conversion reference
Converted with eIQ Neutron SDK (`imx95` target):
```bash
$SDK/bin/neutron-converter --input <original_model.tflite> --target imx95 --output <converted_model.tflite> --dump-statistics-file
```

## Run
```bash
./hand-detection-only
```

Useful options:
```bash
./hand-detection-only --camera /dev/video13 --use-npu 1
./hand-detection-only --camera /dev/video0 --windowed
./hand-detection-only --use-npu 0
```

## Deploy
```bash
./deploy 192.168.0.10
```
Default remote path: `/opt/02-hand-detection-only`

## Performance profile summary
- Fastest hand-localization-oriented demo.
- No semantic gesture output.
