# Variscite demos

AI/ML and GPU demos for i.MX 8M Plus and DART-MX95.
The multimedia player is currently enabled only on i.MX 8M Plus.

## Install

Run as root on the board:

```sh
curl -fsSL \
  https://raw.githubusercontent.com/dorta/var-demos/demos/install.sh | sh
```

The installer lives at the root of the `demos` branch. Run the same command
to update, with the manager and demos closed.

## Run

```sh
var-demos
```

Use arrows and Enter to choose; Esc stops the demo and returns to the menu.

- [AI / ML](ai-ml-demos/): classification, detection, HD video and hand gestures.
- [Multimedia](multimedia-demos/): video player with playback controls.
- [OpenCL](opencl/python/): GPU computation with verified results.
- **Installed BSP demos:** selected graphical examples found in `/opt`.

The BSP menu includes fractals, render-to-texture, a Gaussian filter,
particles, bloom lighting, a skybox, a 3D model viewer, Verlet physics and
spring animation. Entries appear only when their executables are installed
with the board image. These use the GPU, not the AI inference NPU.

## Manage

```sh
var-demos status
var-demos --list
var-demos --uninstall
```

Preview removal with `var-demos --uninstall --dry-run`.
BSP demos and unrelated files are preserved.

## Board support

Only validated options are enabled in the installer. Hardware tests on
MX93 are in progress; its installer support is not enabled yet.

| Feature | i.MX 8M Plus | VAR-SOM-MX93 | DART-MX95 |
| --- | --- | --- | --- |
| NPU backend | VX | Ethos-U65 / Vela | Neutron |
| Camera preview | Tested | Tested | Tested |
| Camera classification | Available | Integration pending | Available |
| Object detection | Available | Model benchmark passed | Model benchmark passed |
| HD / Full HD detection | Available | H.264 decoder missing | Pending |
| Hand gestures | Experimental | Not enabled | Not enabled |
| Video player | Available | Not enabled | Under test |
| OpenCL / GPU examples | Available | Not enabled | Available |

### Measured performance

| Board / test | Camera input | Output FPS | Mean inference |
| --- | --- | --- | --- |
| 8M Plus / SSD, 10 minutes | 720x480 | 15.76 | 9.00 ms |
| MX93 / preview, 7 seconds | 640x480 | 27.55 | No inference |
| MX93 / MobileNet V1 benchmark | Model input 224x224 | Not measured | 3.92 ms |
| MX93 / MobileNet V1 camera, 60 seconds | 640x480 | 29.98 | 4.12 ms |
| MX93 / SSD benchmark | Model input 300x300 | Not measured | 9.23 ms |
| MX93 / SSD camera, 60 seconds | 640x480 | 29.97 | 8.64 ms |
| MX95 / MobileNet V1 camera, 10 seconds | 1280x720 | 5.9 | 1.4 ms |
| MX95 / SSD-Lite benchmark | Model input 300x300 | Not measured | 3.80 ms |

Benchmarks time inference only, not decoding, capture or drawing. These
different models and test durations are not a like-for-like board ranking.
HD describes the source video, not the model's input resolution.
Short tests do not establish multi-hour stability; cooling is required.
The MX93 camera test peaked at 59.85 C on `cpu-thermal`; this is the
reported CPU thermal zone, not a separate NPU temperature sensor.

[Model conversion](CONVERTING_MODELS.md) explains the three NPU paths.
See [MX95 notes](ai-ml-demos/neutron-classification/) for camera limitations.
Models and media use DigitalOcean Spaces with SHA-256 checks, not Git LFS.
