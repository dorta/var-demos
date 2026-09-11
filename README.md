<!-- Copyright 2026 Variscite Ltd. -->
<!-- SPDX-License-Identifier: BSD-3-Clause -->

# Variscite demos (`dorta` fork)

This branch groups development examples by subsystem while keeping a short,
stable entry point for the i.MX 8M Plus machine-learning demos.

## Install on the target

The shortest installation works even when the target image does not include
Git:

```bash
curl -fsSL https://raw.githubusercontent.com/dorta/var-demos/imx8mp-ml-demo-suite/install.sh | bash
```

For an auditable installation, download and inspect the script first:

```bash
curl -fsSLO https://raw.githubusercontent.com/dorta/var-demos/imx8mp-ml-demo-suite/install.sh
less install.sh
bash install.sh
```

The default destination is `~/var-demos`. Use `--dir PATH` to select another
location. An existing installation is never overwritten by default;
`--force` moves it to a timestamped backup before installing the new copy.

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
that uses the PyVar API; it is not a duplicate of the direct TensorFlow Lite
demos.

The compatibility paths beneath
`machine-learning-demos/tflite/python/imx8mplus/` remain available for scripts
and automation that already use them.

## Docker

Native execution on the target is recommended. A container still needs the
matching BSP libraries, NXP GStreamer plugins, VX Delegate, device nodes, and
Wayland socket from the host. Docker can package the application but cannot
make NPU, VPU, G2D, camera, or display acceleration portable to a normal PC.

Any future container image must be versioned for a specific BSP release and
should expose only the devices and sockets required by the selected demo.

The high-resolution demo accepts any licensed H.264 MP4 through `--source`.
This is also the recommended fallback when media files from a Git LFS checkout
are only pointer text.
