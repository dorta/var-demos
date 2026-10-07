<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://nyc3.digitaloceanspaces.com/variscite-marketing/demos/branding/v1/variscite-logo-white.png">
  <img src="https://nyc3.digitaloceanspaces.com/variscite-marketing/demos/branding/v1/variscite-logo-black.png" alt="Variscite" width="320">
</picture>

**Demos for Variscite System on Modules**

## Installing Variscite Demos

Download the Linux image for your SoM, flash it to an SD card, boot the
system and connect it to the internet. Then run this command in its terminal:

```sh
curl -fsSL https://raw.githubusercontent.com/dorta/var-demos/demos/install.sh | sh
```

The SoM is detected automatically. To update, close the demos and repeat
the command.

## Running Variscite Demos

Open the demo manager with the command below, then choose demos to try:

```sh
var-demos
```

Arrows to select, Enter to launch, Esc to return.

Choose a demo, then select the video or camera resolution when prompted.

For videos, choose **HD (720p)** or **Full HD (1080p)**, then **Buildings A**
or **Buildings B**. AI demos and the player use the same [two Freepik clips](docs/video-sources.md),
with identical choices on all three SoMs.

## Supported System on Modules

| SoM | Photo | CPU | GPU / Image Engine | NPU |
| --- | :---: | --- | --- | --- |
| [DART-MX8M-PLUS](docs/hardware.md#dart-mx8m-plus) | <img src="https://dev.variscite.com/static/assets/dart-family/DART-MX8M-PLUS_wiki.png" alt="DART-MX8M-PLUS" width="130"> | 4× Cortex-A53<br>Up to 1.8 GHz | Vivante GC7000UL (3D)<br>GC520L (2D) | [VIP8000](docs/npus/vip8000.md) |
| [VAR-SOM-MX93](docs/hardware.md#var-som-mx93) | <img src="https://dev.variscite.com/static/assets/som-family/VAR-SOM-MX93_wiki.png" alt="VAR-SOM-MX93" width="130"> | 2× Cortex-A55<br>Up to 1.7 GHz | No 3D GPU<br>PXP image engine | [Ethos-U65](docs/npus/ethos-u65.md) |
| [DART-MX95](docs/hardware.md#dart-mx95) | <img src="https://dev.variscite.com/static/assets/dart-family/DART-MX95_wiki.png" alt="DART-MX95" width="130"> | Up to 6× Cortex-A55<br>Up to 2.0 GHz | Arm Mali-G310 (3D)<br>2D acceleration | [Neutron](docs/npus/neutron.md) |

Photos and product specifications come from the Variscite Developer Center
and its linked product pages. See [hardware details and sources](docs/hardware.md)
and [SoM Support](docs/som-support.md). Maximum CPU specifications depend on SKU.

| Category | Demos |
| --- | --- |
| [AI / ML](ai-ml-demos/) | Classification, detection and hand gestures |
| [Multimedia](multimedia-demos/) | Video player |
| [OpenCL](opencl/python/) | GPU computation |
| BSP | Graphical examples already installed in `/opt` |

## Documentation

| Guide | Contents |
| --- | --- |
| [SoM Support](docs/som-support.md) | Available demos, NPUs and camera resolutions |
| [Hardware](docs/hardware.md) | CPU, GPU, NPU specifications and official sources |
| [NPU Guides](docs/npus/README.md) | Per-NPU requirements, preparation, startup and hardware/software flows |
| [Models and Processing Flows](docs/models.md) | Model origins, data types, classification and detection diagrams |
| [Model Sources and Conversion](docs/model-conversion.md) | Source links, checksums, quantization and compiler commands |
| [Video Sources](docs/video-sources.md) | Freepik clips, formats and board-specific video conversion |
| [Demo Benchmarks](docs/performance.md) | Our measured demo results, test conditions and limitations |
| [Validation Record](docs/validation.md) | Test conditions, playback fixes and thermal behavior |

See the [documentation index](docs/README.md) for all guides.
