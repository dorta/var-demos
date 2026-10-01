#!/usr/bin/env python3

# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

import argparse
from collections import deque
import os
from pathlib import Path
import queue
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
import tomllib


ROOT = Path(__file__).resolve().parent


def load_catalog():
    with (ROOT / "catalog.toml").open("rb") as catalog_file:
        return tomllib.load(catalog_file)


def detect_platform(catalog):
    compatible_path = Path("/proc/device-tree/compatible")
    if not compatible_path.is_file():
        raise RuntimeError("Device Tree compatible string is unavailable")

    compatible = compatible_path.read_bytes().split(b"\0")
    values = {value.decode(errors="replace") for value in compatible if value}
    for platform_id, platform in catalog["platforms"].items():
        if values.intersection(platform.get("compatible", [])):
            if platform.get("status") != "validated":
                status = platform.get("status", "unknown")
                raise RuntimeError(
                    f"{platform_id} support is {status}"
                )
            return platform_id
    raise RuntimeError("unsupported platform")


def find_demo(catalog, demo_id):
    return next(demo for demo in catalog["demos"] if demo["id"] == demo_id)


def launchers_for(catalog, platform):
    supported = {
        demo["id"]
        for demo in catalog["demos"]
        if platform in demo.get("platforms", [])
    }
    return [
        launcher
        for launcher in catalog.get("launchers", [])
        if launcher["demo"] in supported
    ]


def detect_camera():
    nodes = sorted(Path("/sys/class/video4linux").glob("video*"))
    for node in nodes:
        name_file = node / "name"
        name = name_file.read_text(errors="replace").strip().lower()
        if "capture" in name:
            return f"/dev/{node.name}"

    if shutil.which("v4l2-ctl"):
        for node in nodes:
            device = f"/dev/{node.name}"
            result = subprocess.run(
                ["v4l2-ctl", "--device", device, "--all"],
                capture_output=True,
                text=True,
                check=False,
            )
            output = f"{result.stdout}\n{result.stderr}"
            if "Video Capture" in output and "Memory-to-Memory" not in output:
                return device
    raise RuntimeError("no V4L2 capture device was found")


def command_for(launcher):
    camera = None
    command = []
    for argument in launcher["command"]:
        if argument == "{camera}":
            if camera is None:
                camera = detect_camera()
            command.append(camera)
        else:
            command.append(argument)
    return command


def display_environment():
    environment = os.environ.copy()
    environment.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    environment.setdefault("DISPLAY", ":0")
    environment.pop("WAYLAND_DISPLAY", None)
    environment.pop("QT_QPA_PLATFORM", None)
    return environment


def clear_screen():
    if sys.stdout.isatty():
        print("\033[2J\033[H", end="")


def render_running(launcher, command, process, started, lines):
    clear_screen()
    elapsed = int(time.monotonic() - started)
    print("VARISCITE AI/ML DEMOS")
    print("=" * 50)
    print(f"Running : {launcher['title']}")
    print(f"Elapsed : {elapsed // 60:02d}:{elapsed % 60:02d}")
    print(f"PID     : {process.pid}")
    print(f"Command : {shlex.join(command)}")
    print("\nPress Ctrl+C to stop this demo and return to the menu.")
    print("\nLatest output")
    print("-" * 50)
    for line in lines:
        print(line)
    sys.stdout.flush()


def collect_output(stream, messages):
    for line in iter(stream.readline, ""):
        messages.put(line.rstrip())
    stream.close()


def stop_process(process):
    if process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def run_with_dashboard(launcher, command, directory):
    messages = queue.Queue()
    lines = deque(maxlen=14)
    process = subprocess.Popen(
        command,
        cwd=directory,
        env=display_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True,
    )
    reader = threading.Thread(
        target=collect_output,
        args=(process.stdout, messages),
        daemon=True,
    )
    reader.start()
    started = time.monotonic()

    try:
        while process.poll() is None:
            while True:
                try:
                    lines.append(messages.get_nowait())
                except queue.Empty:
                    break
            render_running(
                launcher, command, process, started, lines
            )
            time.sleep(0.25)
    except KeyboardInterrupt:
        lines.append("Stopping demo...")
        stop_process(process)

    reader.join(timeout=1)
    while not messages.empty():
        lines.append(messages.get_nowait())
    render_running(launcher, command, process, started, lines)
    return process.returncode


def run_launcher(catalog, launcher, dashboard=True):
    demo = find_demo(catalog, launcher["demo"])
    directory = ROOT / demo["path"]
    if not directory.is_dir():
        raise RuntimeError(f"demo is not installed: {demo['id']}")
    command = command_for(launcher)

    if dashboard and sys.stdout.isatty():
        return run_with_dashboard(launcher, command, directory)
    return subprocess.run(
        command,
        cwd=directory,
        env=display_environment(),
        check=False,
    ).returncode


def show_menu(platform, launchers):
    clear_screen()
    print("VARISCITE AI/ML DEMOS")
    print(f"Platform: {platform}")
    category = None
    for index, launcher in enumerate(launchers, start=1):
        if launcher.get("category") != category:
            category = launcher.get("category")
            print(f"\n{category}")
        title = launcher.get("menu_title", launcher["title"])
        description = launcher.get("description", "")
        print(f"  {index}. {title:<9} {description}")
    print("\n  q. Quit")
    print("\nDemos open fullscreen. Press Esc to close the display.")


def interactive(catalog, platform, launchers):
    while True:
        show_menu(platform, launchers)
        try:
            choice = input("\nSelect a demo [1-7]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if choice in {"q", "quit", "exit"}:
            return 0
        try:
            launcher = launchers[int(choice) - 1]
        except (ValueError, IndexError):
            continue

        try:
            result = run_launcher(catalog, launcher)
            print(f"\nDemo exited with status {result}.")
        except (OSError, RuntimeError) as error:
            print(f"\nError: {error}")
        try:
            input("Press Enter to return to the menu...")
        except (EOFError, KeyboardInterrupt):
            print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--run", metavar="LAUNCHER")
    parser.add_argument("--platform")
    args = parser.parse_args()

    catalog = load_catalog()
    platform = args.platform or detect_platform(catalog)
    launchers = launchers_for(catalog, platform)

    if args.list:
        for launcher in launchers:
            print(f"{launcher['id']}\t{launcher['title']}")
        return 0

    if args.run:
        try:
            launcher = next(
                item for item in launchers if item["id"] == args.run
            )
        except StopIteration as error:
            raise SystemExit(f"unknown launcher: {args.run}") from error
        return run_launcher(catalog, launcher)

    return interactive(catalog, platform, launchers)


if __name__ == "__main__":
    sys.exit(main())
