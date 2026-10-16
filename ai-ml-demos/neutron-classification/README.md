# Neutron camera classification

Historical camera-only implementation for DART-MX95 / Sonata, Wrynose
6.18.20 v1.2, CSI0 OV5640. It is no longer selected by the installer.
Use [camera-vision](../camera-vision/README.md) for the current Neutron
camera/video classification and detection demos in `var-demos`.

The demo configures the CSI0 media graph at each launch. Other cameras are
not supported yet. Esc returns to the menu; the launcher can also stop it.

MobileNet V1 uses a compiled Neutron graph and refuses a non-delegated model.
Softmax and output dequantization remain outside the NPU graph. This is
whole-image classification, not object detection or gesture recognition.

Initial measurements: about 1.4 ms Python inference and 6 FPS camera capture
at 1280 x 720. Capture, not inference, currently limits throughput. The
compiled-model benchmark measured about 1.2 ms; neither value is a guarantee
for other models. Multi-hour stability has not been validated.

Temperature is read from `ana-thermal`, the analog thermal zone; it is not
presented as a measured NPU temperature.
The current camera-vision implementation reads `a55-thermal` for its CPU
temperature display and includes both zones in thermal protection.

## Assets

Model and labels come from the matching [NXP BSP assets](https://github.com/nxp-imx-support/nxp-demo-experience-assets/tree/lf-6.18.20_2.0.0/models).
They are mirrored on DigitalOcean Spaces and SHA-256 checked at install.
The original MobileNet model is Apache-2.0; its license is installed beside
the model. No models or media are stored in Git.
