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

### i.MX 8M Plus

| Demo | Input | Test | FPS | Inference |
| --- | --- | --- | ---: | ---: |
| SSD camera detection | 720×480 | 10 min | 15.76 | 9.00 ms |

### VAR-SOM-MX93

| Demo | Input | Test | FPS | Inference |
| --- | --- | --- | ---: | ---: |
| MobileNet camera classification | 640×480 | 60 s | 29.98 | 4.12 ms |
| SSD camera detection | 640×480 | 60 s | 29.97 | 8.64 ms |
| SSD video detection | 720p MJPEG | 12 s | 18.51 | 9.16 ms |
| SSD video detection | 1080p MJPEG | 12 s | 11.28 | 9.03 ms |

### DART-MX95

| Demo | Input | Test | FPS | Inference |
| --- | --- | --- | ---: | ---: |
| MobileNet camera classification | 1280×720 | 10 s | 5.9 | 1.4 ms |
| SSD-Lite camera detection | 1280×720 | 12 s | 5.83 | 3.72 ms |
| SSD-Lite video detection | 1080p H.264 | 30 s | 1.33 | 3.67 ms |

The Full HD run reached 81.92 °C and paused to cool. Its FPS includes that
pause; camera throughput is currently limited by capture.

Inference times exclude capture, decoding and drawing. Models, encodings
and test durations differ; these results are not a board ranking or a
multi-hour stability guarantee. Adequate cooling is required.

[Camera and video details](ai-ml-demos/camera-vision/) ·
[Model conversion](CONVERTING_MODELS.md)

Models and media are stored on DigitalOcean Spaces and verified with
SHA-256. No Git LFS.
