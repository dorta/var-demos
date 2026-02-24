#!/usr/bin/env python3
import argparse
import json
import os
import statistics
import time
from pathlib import Path

import numpy as np
import tflite_runtime.interpreter as tflite


def make_input_array(detail):
    shape = [d if d > 0 else 1 for d in detail["shape"]]
    dtype = np.dtype(detail["dtype"])

    if np.issubdtype(dtype, np.integer):
        q = detail.get("quantization", (0.0, 0))
        scale = q[0] if isinstance(q, (tuple, list)) and len(q) > 0 else 0.0
        zp = q[1] if isinstance(q, (tuple, list)) and len(q) > 1 else 0
        if scale and scale > 0:
            arr = np.zeros(shape, dtype=dtype)
            arr.fill(int(zp))
            return arr
        if dtype == np.uint8:
            return np.full(shape, 127, dtype=dtype)
        return np.zeros(shape, dtype=dtype)

    if dtype == np.float16:
        return np.zeros(shape, dtype=np.float16)
    return np.zeros(shape, dtype=np.float32)


def run_bench(model_path, delegate_path, warmup, loops):
    delegates = None
    if delegate_path:
        delegates = [tflite.load_delegate(delegate_path)]
    interp = tflite.Interpreter(model_path=str(model_path), experimental_delegates=delegates)
    interp.allocate_tensors()

    in_details = interp.get_input_details()
    out_details = interp.get_output_details()

    prepared = []
    for d in in_details:
        arr = make_input_array(d)
        interp.set_tensor(d["index"], arr)
        prepared.append({
            "name": d.get("name", ""),
            "shape": [int(x) for x in arr.shape],
            "dtype": str(arr.dtype),
            "quant": list(d.get("quantization", (0.0, 0))),
        })

    for _ in range(warmup):
        interp.invoke()

    lat_ms = []
    for _ in range(loops):
        t0 = time.perf_counter()
        interp.invoke()
        t1 = time.perf_counter()
        lat_ms.append((t1 - t0) * 1000.0)

    p50 = statistics.median(lat_ms)
    p90 = sorted(lat_ms)[int(len(lat_ms) * 0.9) - 1]
    p99 = sorted(lat_ms)[max(int(len(lat_ms) * 0.99) - 1, 0)]

    return {
        "model": str(model_path),
        "delegate": delegate_path or "CPU",
        "warmup": warmup,
        "loops": loops,
        "inputs": prepared,
        "outputs": [{"name": d.get("name", ""), "shape": [int(x) for x in d["shape"]], "dtype": str(d["dtype"])} for d in out_details],
        "latency_ms": {
            "min": min(lat_ms),
            "max": max(lat_ms),
            "avg": sum(lat_ms) / len(lat_ms),
            "p50": p50,
            "p90": p90,
            "p99": p99,
        },
    }


def main():
    ap = argparse.ArgumentParser(description="TFLite benchmark helper for i.MX95 NPU/CPU")
    ap.add_argument("--model", required=True)
    ap.add_argument("--delegate", default="")
    ap.add_argument("--warmup", type=int, default=10)
    ap.add_argument("--loops", type=int, default=100)
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    result = run_bench(Path(args.model), args.delegate, args.warmup, args.loops)
    print(json.dumps(result, indent=2))

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
