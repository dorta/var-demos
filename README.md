# Variscite demos

AI/ML, multimedia and GPU demos for i.MX 8M Plus.

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

## Manage

```sh
var-demos status
var-demos --list
var-demos --uninstall
```

Preview removal with `var-demos --uninstall --dry-run`.
BSP demos and unrelated files are preserved.

## Support

i.MX 93 and 95 are not enabled yet. Hand gestures are experimental;
continuous operation needs cooling and further multi-hour validation.
Models and media use DigitalOcean Spaces with SHA-256 checks, not Git LFS.
See each demo's README for details and limitations.
