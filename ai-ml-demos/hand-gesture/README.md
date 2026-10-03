# Hand and gesture recognition experiment

Status: proposed. No runnable demo or validated i.MX 8M Plus model yet.

NXP documents an NPU hand-gesture demo on the i.MX 8M Plus in
[AN14272](https://www.nxp.com/docs/en/application-note/AN14272.pdf).
Its approximately 41 ms model-inference result is not application FPS or a
measurement on our board. Evaluate its platform-specific INT8 models first.

The proposed pipeline detects a palm, crops the hand, estimates landmarks
and recognizes a gesture. Candidate outputs include open palm, closed fist,
thumbs up/down, pointing and victory. These are model categories, not a sign
language translator. See Google's
[Gesture Recognizer](https://developers.google.com/edge/mediapipe/solutions/vision/gesture_recognizer).

Validate model operators, quantization, preprocessing and CPU/NPU partition
on the MPlus before adding the demo to `catalog.toml`. MediaPipe model
availability does not imply an installable MediaPipe runtime on this Yocto
image. Measure the complete pipeline and stabilize results across frames.

A later experiment can map a stable gesture to player controls. Initially,
recognition should only display results, without executing external actions.
