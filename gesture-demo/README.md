# Gesture Demo - DART-MX95 (Walnascar 6.12.20_2.0.0)

Real-time hand gesture demo for i.MX 95 (Variscite DART-MX95), supporting both
USB (UVC) and MIPI/CSI cameras through `/dev/videoX`.

## Main files

- `main.py`: single entrypoint (camera listing, optional MIPI media setup, demo run)
- `hand_tracker.py`: palm + landmark pipeline (based on eIQ example)
- `gesture_classifier.py`: gesture classifier from hand landmarks
- `deploy`: deploy script for the board

## Assets

- `assets/original/`
  - `palm_detection_builtin_256_integer_quant.tflite`
  - `hand_landmark_3d_256_integer_quant.tflite`
- `assets/shared/`
  - `anchors.csv` (used by both original and converted pipelines)
- `assets/converted/`
  - `palm_detection_builtin_256_integer_quant_neutron.tflite`
  - `hand_landmark_3d_256_integer_quant_neutron.tflite`
  - `libneutron_delegate_sdk3.so`

## Model roles (palm vs landmark)

- `palm_detection...`: first-stage hand detector (finds hand region/box).
- `hand_landmark...`: second-stage hand pose model (predicts 21 keypoints).

Pipeline: **palm -> landmark -> gesture classification**.

## Before vs after eIQ conversion

- Before: original models only, CPU fallback dominant.
- After: converted models available from eIQ Neutron SDK.
- Current default strategy:
  - Converted `palm` on NPU for major latency improvement.
  - Original `landmark` on CPU for better quality/stability.

## Usage (single entrypoint)

### 1) Recommended (no arguments)

```bash
python3 main.py
```

Behavior:

- Lists all detected `/dev/video*` devices (USB and/or MIPI/CSI).
- Prompts for camera index selection.
- If a MIPI/CSI device is selected, asks whether to apply `media-ctl` setup.

### 2) List available cameras only

```bash
python3 main.py --list-cameras
```

### 3) Run with explicit camera

```bash
python3 main.py --camera /dev/video13 --use-npu 1      # USB example
python3 main.py --camera /dev/video0 --use-npu 1       # MIPI example
python3 main.py --camera /dev/video13 --use-npu 0      # CPU-only
```

### 4) Select converted/original model mix

```bash
python3 main.py --camera /dev/video13 --use-npu 1 --use-neutron-palm 1 --use-neutron-landmark 0
```

Default is `--use-neutron-palm 1 --use-neutron-landmark 0`.

## Optional MIPI media-ctl setup (inside demo)

When required, apply media pipeline setup before capture:
```bash
python3 main.py --camera /dev/video0 --setup-mipi --mipi-csi-index 0 --camera-width 640 --camera-height 480 --use-npu 1
```

Useful options:

- `--mipi-csi-index 0|1`
- `--media-dev /dev/media0` (optional, auto-detected by default)
- `--camera-fmt UYVY8_1X16` (default)

## eIQ conversion details

SDK used:
- `eiq-neutron-sdk-linux-3.0.0.zip`

Conversion commands:

```bash
export SDK=/home/dorta/pier/tools/eiq-neutron-sdk-linux-3.0.0
export LD_LIBRARY_PATH="$SDK/lib:${LD_LIBRARY_PATH:-}"

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

## Deploy

IP/host is mandatory.

```bash
./deploy <board_ip_or_host> [remote_dir]
```

Examples:

```bash
./deploy 192.168.0.10
./deploy 192.168.0.10 /opt/gesture-demo
```