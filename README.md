<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://nyc3.digitaloceanspaces.com/variscite-marketing/demos/branding/v1/variscite-logo-white.png">
  <img src="https://nyc3.digitaloceanspaces.com/variscite-marketing/demos/branding/v1/variscite-logo-black.png" alt="Variscite" width="320">
</picture>

**Demos for Variscite System on Modules**

## Install

Run as root on the board:

```sh
curl -fsSL https://raw.githubusercontent.com/dorta/var-demos/demos/install.sh | sh
```

The board is detected automatically. To update, close the demos and repeat
the command.

## Run

```sh
var-demos
```

Arrows to select, Enter to launch, Esc to return.

| Category | Demos |
| --- | --- |
| [AI / ML](ai-ml-demos/) | Classification, detection and hand gestures |
| [Multimedia](multimedia-demos/) | Video player |
| [OpenCL](opencl/python/) | GPU computation |
| BSP | Graphical examples already installed in `/opt` |

## Board support

| Demo | i.MX 8M Plus | i.MX 93 | i.MX 95 |
| --- | :---: | :---: | :---: |
| NPU | VX | Ethos-U65 | Neutron |
| Camera classification | ✓ | ✓ | ✓ |
| Camera detection | ✓ | ✓ | ✓ |
| 720p / 1080p detection | ✓ | ✓ | ✓ |
| Video player | ✓ | ✓ | ✓ |
| OpenCL / GPU examples | ✓ | — | ✓ |
| Hand gestures | Experimental | — | — |

✓ Tested on the connected boards; — not enabled. This does not certify
continuous operation. MX93 uses CPU-decoded MJPEG, not H.264.
Both buildings clips are available in 720p and 1080p; 720p is the default.

## Performance

The same four scenarios are listed for every SoM:

- **Measured:** a recorded run with FPS and inference timing.
- **Functional:** opened and processed frames; timing is not reported here.
- **—:** no recorded measurement, not a failed or unsupported demo.

**FPS** is the processed frame rate. **Inference** is model execution time
only; it excludes capture, decoding and drawing. Video resolution describes
the source, not the resized image passed to the model.

### i.MX 8M Plus

VX NPU · MobileNet V1 classification · SSD MobileNet V1 detection.

| Scenario | Source | Validation | Duration | FPS | Inference |
| --- | --- | --- | --- | ---: | ---: |
| Camera classification | Camera | Functional | — | — | — |
| Camera detection | 720×480 | Measured | 10 min | 15.76 | 9.00 ms |
| 720p video detection | 720p H.264 | Functional | — | — | — |
| 1080p video detection | 1080p H.264 | Functional | — | — | — |

### VAR-SOM-MX93

Ethos-U65 NPU · MobileNet V1 classification · SSD MobileNet V1 detection.

| Scenario | Source | Validation | Duration | FPS | Inference |
| --- | --- | --- | --- | ---: | ---: |
| Camera classification | 640×480 | Measured | 60 s | 29.98 | 4.12 ms |
| Camera detection | 640×480 | Measured | 60 s | 29.97 | 8.64 ms |
| 720p video detection | 720p MJPEG | Measured | 12 s | 18.51 | 9.16 ms |
| 1080p video detection | 1080p MJPEG | Measured | 12 s | 11.28 | 9.03 ms |

MJPEG is decoded on the CPU; this BSP has no H.264 decoder.

### DART-MX95

Neutron NPU · MobileNet V1 classification · SSD-Lite V2 detection.

| Scenario | Source | Validation | Duration | FPS | Inference |
| --- | --- | --- | --- | ---: | ---: |
| Camera classification | 1280×720 | Measured | 10 s | 5.90 | 1.40 ms |
| Camera detection | 1280×720 | Measured | 12 s | 5.83 | 3.72 ms |
| 720p video detection | 720p H.264 | Functional | — | — | — |
| 1080p video detection | 1080p H.264 | Measured | 30 s | 1.33 | 3.67 ms |

The Full HD run reached 81.92 °C and paused to cool. Its FPS includes that
pause; camera throughput is currently limited by capture.

These are existing validation results, not one standardized benchmark.
Different camera resolutions, models, codecs, durations and temperatures
prevent a fair speed ranking. Uniform-duration comparative measurements
are still pending; multi-hour stability is not certified.

[Camera and video details](ai-ml-demos/camera-vision/) ·
[Model conversion](CONVERTING_MODELS.md)

Models and media are stored on DigitalOcean Spaces and verified with
SHA-256. No Git LFS.
