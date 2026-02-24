# Batenburg Applied Technologies

This repository contains demos for the i.MX 95 (Variscite DART-MX95), organized
in execution order and complexity. All documentation is focused on what each
demo actually does, model origin, conversion context, and deployment workflow.

All 4 demos keep both model sets:

- `assets/original/` for source `.tflite`;
- `assets/converted/` for Neutron-converted `.tflite`;
- `assets/shared/` when shared metadata is required (for example `anchors.csv`).

All demos in this repository were tested on this image:

* [mx95__yocto-walnascar-6.12.20_2.0.0-v1.4__android-15.0.0_2.0.0-v1.1.wic.zst](https://variscite-public.nyc3.cdn.digitaloceanspaces.com/DART-MX95/Software/mx95__yocto-walnascar-6.12.20_2.0.0-v1.4__android-15.0.0_2.0.0-v1.1.wic.zst)

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

## Single-command Deployment (all demos)

From repository root:

```sh
./deploy-all <BOARD_IP_ADDRESS>
```

Single demo deployment example:

```sh
./deploy-all 192.168.0.10 01
```

```sh
./deploy-all 192.168.0.10 02
```

```sh
./deploy-all 192.168.0.10 03
```

```sh
./deploy-all 192.168.0.10 04
```

## Run and Test Demos on Board

```sh
cd /opt/01-hand-gesture-full && ./hand-gesture-full
```

```sh
cd /opt/02-hand-detection-only && ./hand-detection-only
```

```sh
cd /opt/03-hand-direction-tracking && ./hand-direction-tracking
```

```sh
cd /opt/04-face-detection && ./face-detection
```

All demos support camera selection and `--use-npu 0|1`.
