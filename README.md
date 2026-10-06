# Variscite demos

One installer and terminal menu for i.MX 8M Plus, VAR-SOM-MX93 and DART-MX95.

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

The installer detects the board and selects compatible models and demos.

| Feature | i.MX 8M Plus | VAR-SOM-MX93 | DART-MX95 |
| --- | --- | --- | --- |
| NPU backend | VX | Ethos-U65 / Vela | Neutron |
| Camera preview | Tested | Tested | Tested |
| Camera classification | Tested | Tested | Tested |
| Object detection | Tested | Tested | Tested |
| HD / Full HD detection | Available | MJPEG / CPU decoding | H.264 / hardware decoding |
| Hand gestures | Experimental | Not enabled | Not enabled |
| Video player | Tested / G2D | Tested / PXP | Tested / EGL |
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
| MX95 / SSD-Lite camera, 12 seconds | 1280x720 | 5.83 | 3.72 ms |
| MX93 / buildings A video, 12 seconds | MJPEG 1280x720 | 18.51 | 9.16 ms |
| MX93 / buildings A video, 12 seconds | MJPEG 1920x1080 | 11.28 | 9.03 ms |

Benchmarks time inference only, not decoding, capture or drawing. These
different models and test durations are not a like-for-like board ranking.
HD describes the source video, not the model's input resolution.
Short tests do not establish multi-hour stability; cooling is required.
The MX95 Full HD test reached 81.92 C and paused to cool: 40 frames over
30.07 seconds (1.33 FPS including cooling), despite 3.67 ms inference.
Do not interpret fast NPU inference as sustained video throughput.
The MX93 camera test peaked at 59.85 C on `cpu-thermal`; this is the
reported CPU thermal zone, not a separate NPU temperature sensor.

[Model conversion](CONVERTING_MODELS.md) explains the three NPU paths.
See [camera/video notes](ai-ml-demos/camera-vision/) for capture limitations.
Models and media use DigitalOcean Spaces with SHA-256 checks, not Git LFS.

The video selector includes both High-rise buildings clips in 720p and
1080p; 720p is the default. MX93 uses MJPEG copies at the same resolution
and frame rate because this image lacks an H.264 decoder. Encoding differs,
so these are not equivalent decoder or image-quality benchmarks.
