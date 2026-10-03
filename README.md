# Variscite demos

AI/ML, multimedia and OpenCL demos, selected for the connected board.
Currently validated on i.MX 8M Plus; i.MX 93 and 95 are pending.

Run as root on the board:

```sh
curl -fsSL \
  https://raw.githubusercontent.com/dorta/var-demos/demos/install.sh | sh
var-demos
```

Use arrows and Enter to select; Esc returns to the menu. `var-ai` remains
an AI/ML shortcut. Models and media come from DigitalOcean Spaces, with
SHA-256 verification. No Git LFS.

`catalog.toml` selects the installed categories. Other folders, including
TPM, Docker and VS Code examples, are not installed by this command.
The menu also lists selected GPU demos already present in
`/opt/imx-gpu-sdk`. These run in place; uninstall leaves them untouched.

Uninstall:

```sh
/opt/var-demos/install.sh --uninstall
```

Use `--list`, `--dry-run` or `--only ai-ml` with the installer when needed.
