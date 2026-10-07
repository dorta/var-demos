# Documentation

[Project Overview](../README.md)

Start with SoM support, then follow the model diagrams to understand how
images, videos and camera frames are processed.

## Find Your Answer

- **Which demos can my board run?** Open [SoM Support](som-support.md).
- **Are the models the same on all boards?** See [model origins](models.md#where-the-models-come-from).
- **How does classification or detection work?** Follow the [classification](models.md#classification-flow) and [detection](models.md#detection-flow) diagrams.
- **Where did the models come from, and how were they compiled?** Open [Model Sources and Conversion](model-conversion.md).
- **Why does MX93 use AVI and PXP?** See the [input processing flow](models.md#image-video-and-camera-input-flow) and [video formats](video-sources.md).
- **What FPS was measured, and under which conditions?** Read [Performance](performance.md), then the [Validation Record](validation.md).

## Complete Guides

| Guide | What You Will Find |
| --- | --- |
| [SoM Support](som-support.md) | Demo availability, NPUs and tested camera modes |
| [Hardware](hardware.md) | Official CPU/GPU/NPU specifications, photos and source links |
| [NPU Guides](npus/README.md) | What each NPU expects and per-SoM startup, classification and detection flows |
| [Models and Processing Flows](models.md) | Model comparison, origins and preparation, classification and detection flows |
| [Model Sources and Conversion](model-conversion.md) | Exact artifacts, source links, SHA-256, tensor interfaces and compiler commands |
| [Video Sources](video-sources.md) | Supplied clips, codecs, conversion and license limitations |
| [Demo Benchmarks](performance.md) | Our measured per-SoM results, FPS versus inference time and benchmark limitations |
| [Validation Record](validation.md) | Historical checks, decoder fixes and thermal/performance tests |
| [Experiment Ideas](ideas.md) | Research candidates, not installed or validated demos |

## Component Guides

| Component | Guide |
| --- | --- |
| AI / ML | [Overview](../ai-ml-demos/README.adoc) |
| Camera and Video Inference | [Runtime Details](../ai-ml-demos/camera-vision/README.md) |
| Video Player | [Playback and Controls](../multimedia-demos/README.md) |
| OpenCL | [GPU Computation](../opencl/python/README.md) |
| Hand Gestures | [Experimental Demo](../ai-ml-demos/hand-gesture/README.md) |

Internal navigation uses relative paths. External model sources and asset
downloads retain their upstream URLs; the installation command requires
a complete download URL.
