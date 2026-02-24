# var-demos

This repository contains **4 production-facing demos** for i.MX95 (Variscite DART-MX95), organized in execution order and complexity.

All documentation is focused on what each demo actually does, model origin, conversion context, and deployment workflow.

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

## Run Commands on Board

```bash
cd /opt/01-hand-gesture-full && python3 main.py
cd /opt/02-hand-detection-only && python3 main.py
cd /opt/03-hand-direction-tracking && python3 main.py
cd /opt/04-face-detection && python3 main.py
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
