# Python OpenCL demo

Use the [root installer](../../README.md), then run from the **OpenCL**
category in `var-demos`.

The vector-addition demo calls the installed `libOpenCL` through Python's
standard `ctypes` library. No PyOpenCL, compiler or pip install is needed.
It selects a GPU explicitly, compiles a small OpenCL kernel, verifies all
results and reports kernel profiling separately from dispatch/readback.

The original C examples remain in their folders and are not installed.
For graphical OpenCL output, the **Installed BSP demos /opt** category offers
the SDK Gaussian filter when its executable is present. BSP files are not
installed, updated or removed by our installer.
