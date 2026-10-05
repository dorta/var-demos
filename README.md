# Variscite demos

Demos for i.MX 8M Plus, installed and launched through one command.
i.MX 93 and 95 support is pending; their demos are not installed.

The installer is `install.sh` at the root of the `demos` branch.
Run as root on the board:

```sh
curl -fsSL \
  https://raw.githubusercontent.com/dorta/var-demos/demos/install.sh | sh
var-demos
```

Use arrows and Enter to select; Esc returns to the menu.
Choose a category:

- AI / ML: image, video and camera classification and object detection;
  HD/Full HD video selection; experimental hand landmarks and gestures.
- Multimedia: video player with play/pause, seek, stop, volume and fullscreen.
- OpenCL: GPU vector computation with result verification.
- Installed BSP demos /opt: available fractal, render-to-texture and graphical
  OpenCL filter examples from the image's GPU SDK.

Only `var-demos` is installed as a launcher. Updates remove the old `var-ai`
and `var-media` shortcuts when they belong to this installation.
Models, videos and the player logo are downloaded from DigitalOcean Spaces
and verified with SHA-256. No Git LFS. Original `combined_videos` files have
not been recovered; the video menu contains the current replacement samples.

`catalog.toml` selects the installed categories. Other folders, including
TPM, Docker and VS Code examples, are not installed by this command.
The menu also lists selected GPU demos already present in
`/opt/imx-gpu-sdk`. These run in place; uninstall leaves them untouched.

Uninstall:

```sh
/opt/var-demos/install.sh --uninstall
```

Use `--list`, `--dry-run` or `--only ai-ml` with the installer when needed.
Re-run the same curl command to update; close the manager and demos first.
Camera demos require a supported capture device. Continuous operation needs
adequate cooling; multi-hour event stability is still under validation.
