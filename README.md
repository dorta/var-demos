<!-- Copyright 2026 Variscite Ltd. -->
<!-- SPDX-License-Identifier: BSD-3-Clause -->

# Variscite demos (`dorta` fork)

This branch groups development examples by subsystem while keeping a short,
stable entry point for the i.MX 8M Plus machine-learning demos.

## Quick start

Run `./ml-demo --help` from the repository root. The launcher selects the
correct application directory, so users do not need to type or depend on the
internal Python path.

```bash
./ml-demo classify --headless --output-frame /tmp/classification.png
./ml-demo detect --headless --output-frame /tmp/detection.png
./ml-demo hd --combination 1 --source /path/to/1280x720-video.mp4 \
  --headless --max-frames 1 --output-frame /tmp/hd-result.png
```

Remove `--headless` to use the interactive OpenCV window. The HD command also
supports Full HD sources; use combination 13 for a 1920x1080 validation.

## Repository map

| Area | Purpose |
| --- | --- |
| `machine-learning-demos/` | TensorFlow Lite and accelerator examples |
| `machine-learning-demos/tflite/python/imx8mplus/assets/` | Shared test media and models |
| `demo-loop/` | Prepared GStreamer playback loop |
| `docker-demos/` | Container examples |
| `opencl/` | OpenCL examples |
| `tpm-demos/` | TPM examples |
| `vscode-demos/` | VS Code integration examples |

The `pyvar_examples/` directory is retained as an alternative implementation
that uses the PyVar API; it is not a duplicate of the direct TensorFlow Lite demos.

The compatibility paths beneath
`machine-learning-demos/tflite/python/imx8mplus/` remain available for scripts
and automation that already use them.

The high-resolution demo accepts any licensed H.264 MP4 through `--source`.
This is also the recommended fallback when media files from a Git LFS checkout
are only pointer text.
