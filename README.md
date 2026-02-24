# var-demos

This repository contains **4 production-facing demos** for i.MX95 (Variscite DART-MX95), organized in execution order and complexity.

All documentation is focused on what each demo actually does, model origin, conversion context, and deployment workflow.

## Validated BSP Image

All demos in this repository were tested on this image:

```bash
wget https://variscite-public.nyc3.cdn.digitaloceanspaces.com/DART-MX95/Software/mx95__yocto-walnascar-6.12.20_2.0.0-v1.4__android-15.0.0_2.0.0-v1.1.wic.zst
```

Image file:
- `mx95__yocto-walnascar-6.12.20_2.0.0-v1.4__android-15.0.0_2.0.0-v1.1.wic.zst`

## Demo Index

### 1) `01-hand-gesture-full`
**What it does:**
- Detects palm
- Estimates 21 hand landmarks
- Classifies gesture from landmarks

**Best for:**
- Full feature demo
- Finger/joint-aware gesture behavior

**Trade-off:**
- Highest latency among hand demos (landmark stage is heavy)

---

### 2) `02-hand-detection-only`
**What it does:**
- Detects and tracks hand region only
- Fast palm + recrop pipeline

**Best for:**
- Fast hand presence/tracking
- High FPS baseline

**Trade-off:**
- No semantic gesture labels

---

### 3) `03-hand-direction-tracking`
**What it does:**
- Detects hand region
- Outputs direction/motion labels:
  `NO_HAND`, `STILL`, `MOVE_LEFT`, `MOVE_RIGHT`, `MOVE_UP`, `MOVE_DOWN`, `WAVE`

**Best for:**
- Fast interactive directional control demo

**Trade-off:**
- Lightweight heuristic classifier (not full landmark semantics)

---

### 4) `04-face-detection`
**What it does:**
- Real-time face detection with box rendering
- Very fast Neutron path

**Best for:**
- Executive NPU speed showcase
- Stable quick demo

---

## Repository Layout

- `01-hand-gesture-full/`
- `02-hand-detection-only/`
- `03-hand-direction-tracking/`
- `04-face-detection/`
- `deploy-all` (single deploy script for all demos)

Each demo folder contains one executable entrypoint without numeric prefix:
- `01-hand-gesture-full/hand-gesture-full`
- `02-hand-detection-only/hand-detection-only`
- `03-hand-direction-tracking/hand-direction-tracking`
- `04-face-detection/face-detection`

## Single-command Deployment (all demos)

From repository root:

```bash
./deploy-all 192.168.0.10
```

This deploys to:
- `/opt/01-hand-gesture-full`
- `/opt/02-hand-detection-only`
- `/opt/03-hand-direction-tracking`
- `/opt/04-face-detection`

## Board Provisioning and Demo Validation

### 1) Download image on host PC

```bash
mkdir -p ~/imx95-image && cd ~/imx95-image
wget https://variscite-public.nyc3.cdn.digitaloceanspaces.com/DART-MX95/Software/mx95__yocto-walnascar-6.12.20_2.0.0-v1.4__android-15.0.0_2.0.0-v1.1.wic.zst
```

### 2) Flash image to SD card (Linux host)

1. Insert SD card.
2. Identify device node (`/dev/sdX`):

```bash
lsblk
```

3. Flash (replace `sdX` with the correct device, without partition suffix):

```bash
zstd -d mx95__yocto-walnascar-6.12.20_2.0.0-v1.4__android-15.0.0_2.0.0-v1.1.wic.zst -c | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync
sync
```

### 3) Boot DART-MX95

1. Insert flashed media in the board.
2. Set boot mode to SD (or your expected media boot mode).
3. Power on and complete first boot.
4. Confirm system version:

```bash
uname -a
cat /etc/os-release
```

### 4) Deploy demos from host to board

From `var-demos` repository root:

```bash
./deploy-all 192.168.0.10
```

### 5) Run and test demos on board

```bash
cd /opt/01-hand-gesture-full && ./hand-gesture-full
cd /opt/02-hand-detection-only && ./hand-detection-only
cd /opt/03-hand-direction-tracking && ./hand-direction-tracking
cd /opt/04-face-detection && ./face-detection
```

Notes:
- At startup, each demo lists available cameras and allows index selection.
- Use `--camera /dev/videoX` if you want to skip interactive selection.
- Use `--setup-mipi` when required by your MIPI pipeline.
- Use `--use-npu 1` to request Neutron delegate path.

## Run Commands on Board

```bash
cd /opt/01-hand-gesture-full && ./hand-gesture-full
cd /opt/02-hand-detection-only && ./hand-detection-only
cd /opt/03-hand-direction-tracking && ./hand-direction-tracking
cd /opt/04-face-detection && ./face-detection
```

All demos support camera selection and `--use-npu 0|1`.

## Model and Conversion Notes

Detailed model provenance and conversion context are provided in each demo's own `README.md`.

In short:
- Hand demos use palm/landmark/recrop assets previously validated in this project.
- Face detection demo uses eIQ model zoo FaceDet model, converted for Neutron.
- Conversions were done with eIQ Neutron SDK targeting `imx95`.

## Recommendation for Presentation Order

1. `04-face-detection` (fast impact)
2. `02-hand-detection-only` (fast hand tracking)
3. `03-hand-direction-tracking` (interactive behavior)
4. `01-hand-gesture-full` (most complete capabilities)
