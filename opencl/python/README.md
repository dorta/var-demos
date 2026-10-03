# Python OpenCL demo

Run from the OpenCL category in `var-demos`.

The vector-addition demo calls the installed `libOpenCL` through Python's
standard `ctypes` library. No PyOpenCL, compiler or pip install is needed.
It selects a GPU explicitly, compiles a small OpenCL kernel, verifies all
results and reports kernel profiling separately from dispatch/readback.

The original C examples remain in their folders and are not installed.
