# AI and ML demo experiments

[Documentation](README.md) · [Project Overview](../README.md)

Experiments for i.MX 8M Plus. Hand landmarks now have an experimental
implementation and initial CPU/NPU checks; see the
[hand gesture guide](../ai-ml-demos/hand-gesture/README.md) for limitations.
The other entries remain proposals, not installed or benchmarked demos.

## Priority experiments

1. **Hand and gesture recognition** (`hand-gesture`): detect palms, estimate
   21 hand landmarks and recognize common gestures. Initial implementation
   uses four geometric labels with temporal stabilization. Expand real-hand
   accuracy tests and multi-hour runs before treating it as event-ready.
2. **Human pose** (`pose-estimation`): MoveNet Lightning, with skeleton
   overlay and measured camera/video latency.
3. **Segmentation** (`semantic-segmentation`): DeepLabV3 or a small person
   segmenter, with an alpha mask rather than bounding boxes.
4. **Detection and tracking** (`object-tracking`): compare SSD MobileNetV2
   and YOLOv4 Tiny, then track objects and count line crossings. Tracking is
   an additional algorithm, not an inherent capability of the detector.
5. **Face detection** (`face-detection`): UltraFace; no identification or
   personal-data collection in the initial demo.
6. **Depth estimation** (`depth-estimation`): MiDaS v2, showing relative
   depth only, not calibrated physical distances.
7. **Offline speech translation** (`speech-translation`): microphone,
   multilingual speech recognition and short-phrase translation. Compare
   Gemma 3 270M with a small model specific to the language pair. Neither
   real-time speed nor NPU acceleration is established on our board.

NXP lists these vision-model candidates for i.MX 8M Plus in its
[NNStreamer examples](https://github.com/nxp-imx/nxp-nnstreamer-examples/blob/main/tasks/README.md).
This documents a starting point, not validation of our Python pipeline.
Google documents the separate palm, landmark and gesture stages in its
[Gesture Recognizer guide](https://developers.google.com/edge/mediapipe/solutions/vision/gesture_recognizer).

## Acceptance checks

For each experiment, record the exact model version, license, SHA-256,
input preprocessing and CPU/NPU partition. Measure end-to-end FPS, inference
time, peak memory, temperatures and accuracy on representative inputs.
Check camera loss, EOF, stop/restart, thermal pacing and a multi-hour soak.
Do not equate an isolated inference benchmark with application FPS.

Models and example media belong on DigitalOcean Spaces, never Git LFS.
Keep unvalidated models out of the default install catalog.

## Model sources

Start with [NXP eIQ Model Zoo](https://github.com/NXP/eiq-model-zoo) and
its i.MX 8M Plus NNStreamer enablement matrix linked above. Prioritize
MoveNet Lightning and DeepLabV3 after the existing demos are stable.

[PINTO Model Zoo](https://github.com/PINTO0309/PINTO_model_zoo) offers
converted models, including MoveNet and body/head/hand detection. A TFLite
export alone does not establish VX delegate compatibility or NPU speed.
Check the license in each model directory: conversion-script licensing
does not replace the original model's licensing terms.

These are research candidates, not additional installed or validated demos.

## Related Guides

- [SoM Support](som-support.md): what is currently enabled, rather than proposed.
- [Model Sources and Conversion](model-conversion.md): artifact compatibility and preparation checks.
- [Validation Record](validation.md): checks already performed on the existing demos.
