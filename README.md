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

## Support

i.MX 93 is not enabled yet. DART-MX95 supports Neutron camera classification,
camera preview, OpenCL and eight graphical BSP examples on Wrynose 6.18.20.
See [MX95 notes](ai-ml-demos/neutron-classification/) for measured performance
and the supported camera. MX95 player compatibility is still under test.
Hand gestures are experimental and enabled only on i.MX 8M Plus;
continuous operation needs cooling and further multi-hour validation.
Models and media use DigitalOcean Spaces with SHA-256 checks, not Git LFS.
See each demo's README for details and limitations.
