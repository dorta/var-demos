<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://nyc3.digitaloceanspaces.com/variscite-marketing/demos/branding/v1/variscite-logo-white.png">
  <img src="https://nyc3.digitaloceanspaces.com/variscite-marketing/demos/branding/v1/variscite-logo-black.png" alt="Variscite" width="320">
</picture>

**Demos for Variscite System on Modules**

# Install

Run as root on the board:

```sh
curl -fsSL https://raw.githubusercontent.com/dorta/var-demos/demos/install.sh | sh
```

The board is detected automatically. To update, close the demos and repeat
the command.

Installation and removal show the board, demo and asset counts, current
task, completed-step progress and elapsed time in one terminal dashboard.
The latest three assets appear with readable names and download/verification
status; assets are SHA-256 verified. Failures point
to a diagnostic log. ANSI terminals redraw in place; redirected output and
`TERM=dumb` use plain status lines. `NO_COLOR=1` disables colors.

# Run

```sh
var-demos
```

Arrows to select, Enter to launch, Esc to return.

The AI menu uses the same order on every SoM: classification (image,
video, camera), then detection (image, video, camera), followed by optional
extras. Demos open fullscreen. Video selection includes 720p and 1080p;
camera selection offers the connected OV5640's configured resolutions.
Display resolution and model input dimensions do not change with that choice.

| Category | Demos |
| --- | --- |
| [AI / ML](ai-ml-demos/) | Classification, detection and hand gestures |
| [Multimedia](multimedia-demos/) | Video player |
| [OpenCL](opencl/python/) | GPU computation |
| BSP | Graphical examples already installed in `/opt` |

## Board support

| Demo | i.MX 8M Plus | i.MX 93 | i.MX 95 |
| --- | :---: | :---: | :---: |
| NPU | VIP8000 / VX | Ethos-U65 | Neutron |
| Camera classification | ✓ | ✓ | ✓ |
| Camera detection | ✓ | ✓ | ✓ |
| Image classification / detection | ✓ | ✓ | ✓ |
| 720p / 1080p classification | ✓ | ✓ | ✓ |
| 720p / 1080p detection | ✓ | ✓ | ✓ |
| Video player | ✓ | ✓ | ✓ |
| OpenCL / GPU examples | ✓ | — | ✓ |
| Hand gestures | Experimental | — | — |

✓ Tested on the connected boards; — not enabled. This does not certify
continuous operation. MX93 uses CPU-decoded MJPEG, not H.264.
Both buildings clips are available in 720p and 1080p; 720p is the default.

| Camera capture choice | i.MX 8M Plus | i.MX 93 | i.MX 95 |
| --- | :---: | :---: | :---: |
| VGA 640×480 | ✓ | ✓ (default) | ✓ |
| SD 720×480 | ✓ (default) | — | — |
| HD 1280×720 | ✓ | ✓ | ✓ (default) |
| Full HD 1920×1080 | ✓ | ✓ | ✓ |

These choices were checked with the connected OV5640 cameras for both
classification and detection. They are capture modes, not a promise of
30 FPS at every resolution or compatibility with other sensors.

## Models and conversion

These are **8-bit quantized models, not universally signed INT8 models**.
The installed models all accept RGB **UINT8** tensors; their output types
and quantization parameters differ. Source video resolution (720p/1080p)
does not change the model's input dimensions.

| SoM | NPU / delegate | Classification | Detection | Preparation / origin |
| --- | --- | --- | --- | --- |
| i.MX 8M Plus | VeriSilicon VIP8000 / VX | MobileNet V1 1.0, 224×224; UINT8 input/output | SSD MobileNet V1, 300×300; UINT8 input, FLOAT32 detection outputs | Original Variscite demo artifacts; VX prepares the graph at runtime |
| VAR-SOM-MX93 | Arm Ethos-U65-256 / Ethos-U | MobileNet V1 1.0, 224×224; UINT8 input/output | SSD MobileNet V1, 300×300; UINT8 input, FLOAT32 detection outputs | Same MPlus source models, compiled with Vela 3.12.0; verified by SHA-256 |
| DART-MX95 | NXP Neutron / Neutron delegate | MobileNet V1 1.0, 224×224; UINT8 input, FLOAT32 output | SSD-Lite MobileNet V2, 300×300; UINT8 input, FLOAT32 raw boxes/scores | Already compiled NXP artifacts from `lf-6.18.20_2.0.0`; not converted locally with the current SDK |

**Not the same detector on all three:** MPlus and MX93 use SSD MobileNet
V1; MX95 uses SSD-Lite MobileNet V2, with matching COCO labels, anchors and
CPU box decoding/NMS. The classifiers share an architecture; this alone
does not prove identical weights or preprocessing. In particular, MX95
uses a different input scale/zero point. Recompiling the MPlus classifier
with Vela reproduced the installed MX93 classifier byte-for-byte.

See [model provenance and conversion](CONVERTING_MODELS.md) for source links,
artifact filenames and checksums, tensor quantization, compiler options,
runtime compatibility and the limits of what was actually reproduced.

## Performance

Every demo in the support matrix is listed for every SoM. Video detection
has separate 720p and 1080p rows; the NPU is identified above each table.

- **Measured:** a recorded run with FPS and inference timing.
- **Functional:** ran successfully; timing is not reported here.
- **Experimental:** available, but still needs representative validation.
- **Not enabled:** not installed or offered on this SoM.
- **—:** no recorded measurement, not a failed or unsupported demo.

**FPS** is the processed frame rate. **Inference** is model execution time
only; it excludes capture, decoding and drawing. Video resolution describes
the source, not the resized image passed to the model.

### i.MX 8M Plus

VX NPU · MobileNet V1 classification · SSD MobileNet V1 detection.

| Scenario | Source | Validation | Duration | FPS | Inference |
| --- | --- | --- | --- | ---: | ---: |
| Image classification | Sample image | Functional | — | — | — |
| Image detection | Sample image | Functional | — | — | — |
| 720p video classification | 720p H.264 | Functional | — | — | — |
| 1080p video classification | 1080p H.264 | Functional | — | — | — |
| Camera classification | Camera | Functional | — | — | — |
| Camera detection | 720×480 | Measured | 10 min | 15.76 | 9.00 ms |
| 720p video detection | 720p H.264 | Functional | — | — | — |
| 1080p video detection | 1080p H.264 | Functional | — | — | — |
| Video player | 720p H.264 | Functional | — | — | — |
| OpenCL / GPU examples | GPU | Functional | — | — | — |
| Hand gestures | Camera | Experimental | — | — | — |

### VAR-SOM-MX93

Ethos-U65 NPU · MobileNet V1 classification · SSD MobileNet V1 detection.

| Scenario | Source | Validation | Duration | FPS | Inference |
| --- | --- | --- | --- | ---: | ---: |
| Image classification | Sample image | Functional | — | — | — |
| Image detection | Sample image | Functional | — | — | — |
| 720p video classification | 720p MJPEG | Functional | — | — | — |
| 1080p video classification | 1080p MJPEG | Functional | — | — | — |
| Camera classification | 640×480 | Measured | 60 s | 29.98 | 4.12 ms |
| Camera detection | 640×480 | Measured | 60 s | 29.97 | 8.64 ms |
| 720p video detection | 720p MJPEG | Measured | 12 s | 18.51 | 9.16 ms |
| 1080p video detection | 1080p MJPEG | Measured | 12 s | 11.28 | 9.03 ms |
| Video player | 720p MJPEG | Functional | — | — | — |
| OpenCL / GPU examples | — | Not enabled | — | — | — |
| Hand gestures | — | Not enabled | — | — | — |

MJPEG is decoded on the CPU; this BSP has no H.264 decoder.

### DART-MX95

Neutron NPU · MobileNet V1 classification · SSD-Lite V2 detection.

| Scenario | Source | Validation | Duration | FPS | Inference |
| --- | --- | --- | --- | ---: | ---: |
| Image classification | Sample image | Functional | — | — | — |
| Image detection | Sample image | Functional | — | — | — |
| 720p video classification | 720p H.264 | Functional | — | — | — |
| 1080p video classification | 1080p H.264 | Functional | — | — | — |
| Camera classification | 1280×720 | Measured | 10 s | 5.90 | 1.40 ms |
| Camera detection | 1280×720 | Measured | 12 s | 5.83 | 3.72 ms |
| 720p video detection | 720p H.264 | Functional | — | — | — |
| 1080p video detection | 1080p H.264 | Functional | — | — | — |
| Video player | 720p H.264 | Functional | — | — | — |
| OpenCL / GPU examples | GPU | Functional | — | — | — |
| Hand gestures | — | Not enabled | — | — | — |

The previous Full HD timing was withdrawn: its GL conversion delivered
black frames. The corrected path was checked with visible detections;
representative sustained video timings must be measured again. Thermal
pauses still occur around 82 °C; camera throughput is limited by capture.
The final video path explicitly uses MMAP decoder buffers before GPU
conversion; automatic DMA_DRM import produced out-of-order image content
even with increasing timestamps. See the [validation record](ai-ml-demos/VALIDATION.md).

These are existing validation results, not one standardized benchmark.
Different camera resolutions, models, codecs, durations and temperatures
prevent a fair speed ranking. Uniform-duration comparative measurements
are still pending; multi-hour stability is not certified.

[Camera and video details](ai-ml-demos/camera-vision/) ·
[Model conversion](CONVERTING_MODELS.md)

Models and media are stored on DigitalOcean Spaces and verified with
SHA-256. No Git LFS.
