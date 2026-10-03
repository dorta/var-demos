# Hand and gestures

Experimental single-hand demo for i.MX 8M Plus. Palm detection and 21 hand
landmarks use TensorFlow Lite with the VX NPU delegate. Gesture labels use
geometric rules, not a trained classifier: open hand, closed fist, pointing
and victory. Other poses show `Unknown`. Labels settle for 350 ms; landmarks
use light temporal smoothing. Losing the hand clears both immediately.
No external actions are executed.

Launch from `var-demos` or `var-ai`. Esc stops and returns to the manager.
Fullscreen fills the display using a central crop; use `--windowed` to
retain the entire camera image. First inference includes model preparation
and can take tens of seconds. Both models prepare before camera capture,
avoiding a delayed stall when the first hand enters the scene. The video
window opens after a valid frame.

Developer checks, from the installed demo directory:

```sh
python3 check_on_board.py
python3 demo.py --sample --headless --duration 60
python3 demo.py --camera /dev/video4 --headless --duration 600
```

CPU and NPU agree on open-hand labels for the NXP reference image and its
mirror; empty images produce no hand. Landmark differences measured on
those inputs were 5.67/8.77 px maximum and 1.87/2.94 px RMS. This is a
regression check, not an accuracy benchmark for arbitrary gestures.

The legacy landmark model's `output_handflag` returned the same 0.210898
value for hand and blank crops on both CPU and NPU. It is not used as a
confidence probability. Presence uses the palm detector's 0.95 threshold.
The models' expected RGB normalization is `(pixel - 128) / 128`.

The demo uses bounded capture buffers, stop/restart cleanup, shared thermal
pacing and SoC temperature telemetry. Multi-hour operation and all gestures
still require representative hardware validation. See [THIRD_PARTY.md](THIRD_PARTY.md)
for model origins and licenses. Assets are external, verified by SHA-256;
no Git LFS or MediaPipe Python package is needed.

The initial 10-minute headless camera run completed 8,268 inferences without
a crash. Most frames contained no hand: 24 ms palm inference, about 15 FPS
when warm, 13.78 FPS over the whole run including compilation and cooling.
Peak sampled SoC temperature was 81 C; hardware clock scale remained 64 at
checks. Memory stabilized near 623 MiB after both models were prepared.
This run motivated preparing both models before capture; it is not a
multi-hour or all-gesture certification of the final graphical version.
