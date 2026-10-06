# Python OpenCL demo

Use the [root installer](../../README.md), then run from the **OpenCL**
category in `var-demos`.

The vector-addition demo calls the installed `libOpenCL` through Python's
standard `ctypes` library. No PyOpenCL, compiler or pip install is needed.
It selects a GPU explicitly, compiles a small OpenCL kernel, verifies all
results and reports kernel profiling separately from dispatch/readback.

Tested on i.MX 8M Plus and DART-MX95 (Mali-G310). The MX95 smoke test verified
262,144 additions with a 0.368 ms kernel and 1.973 ms dispatch/readback.
These measurements are not a sustained-performance guarantee.

The original C examples remain in their folders and are not installed.
For graphical OpenCL output, the **Installed BSP demos /opt** category offers
the SDK Gaussian filter when its executable is present. BSP files are not
installed, updated or removed by our installer.
