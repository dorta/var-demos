#!/usr/bin/env python3

# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

import argparse
from collections import deque
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import tomllib

from telemetry import SOC_TEMPERATURE
from runtime import clock_is_limited, temperature


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


def stop_process(process):
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def run_with_dashboard(launcher, command, directory):
    print(f"\n  {launcher['title']}")
    print("  The demo opens on the board's display.")
    print("  Esc: close display  |  Ctrl+C: stop and return\n")
    stopped = False
    with tempfile.NamedTemporaryFile(
        prefix='var-ai-', suffix='.log', delete=False
    ) as log:
        process = subprocess.Popen(
            command,
            cwd=directory,
            env=display_environment(),
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        started = time.monotonic()
        last_elapsed = -1
        cooling = False
        try:
            while process.poll() is None:
                elapsed = int(time.monotonic() - started)
                if elapsed != last_elapsed:
                    soc = SOC_TEMPERATURE.read()
                    soc_text = '--' if soc is None else f'{soc:.1f}'
                    peak = temperature()
                    limited = clock_is_limited()
                    if limited or (
                        peak is not None and peak >= 82
                    ):
                        cooling = True
                    elif peak is not None and peak < 78:
                        cooling = False
                    state = 'Cooling' if cooling else 'Running'
                    print(
                        f"\r  {state:<7}  {elapsed // 60:02d}:"
                        f"{elapsed % 60:02d}  |  SoC {soc_text} C    ",
                        end='', flush=True,
                    )
                    last_elapsed = elapsed
                time.sleep(0.1)
        except KeyboardInterrupt:
            stopped = True
        finally:
            stop_process(process)

    if stopped:
        print('\r  Stopped.                                       ')
        return 0
    if process.returncode == 0:
        print('\r  Finished.                                      ')
    else:
        print(f'\n  Demo failed (exit {process.returncode}).')
        print(f'  Diagnostic log: {log.name}')
        with open(log.name, encoding='utf-8', errors='replace') as output:
            # Keep failure details visible without dumping startup chatter.
            tail = deque(output, maxlen=8)
        for line in tail:
            line = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', line)
            line = ''.join(
                character for character in line.rstrip()
                if character.isprintable() or character == '\t'
            )
            print(f'  {line}')
    return process.returncode


def run_launcher(catalog, launcher, dashboard=True, video=None):
    demo = find_demo(catalog, launcher["demo"])
    directory = ROOT / demo["path"]
    if not directory.is_dir():
        raise RuntimeError(f"demo is not installed: {demo['id']}")
    command = command_for(launcher)
    if video is not None:
        video_path = directory / video['path']
        if not video_path.is_file():
            raise RuntimeError(f"video is not installed: {video['title']}")
        command.extend(['--video', str(video_path)])
        if '--combination' in command:
            index = command.index('--combination') + 1
            command[index] = str(video['combination'])

    if dashboard and sys.stdout.isatty():
        if video is not None:
            launcher = dict(launcher, title=video['title'])
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
            print(category)
        title = launcher.get("menu_title", launcher["title"])
        description = launcher.get("description", "")
        print(f"  {index}. {title:<9} {description}")
    print("\n  q. Quit")
    print("Demos open fullscreen. Press Esc to close the display.")


def interactive(catalog, platform, launchers):
    while True:
        show_menu(platform, launchers)
        try:
            choice = input(
                f"\nSelect a demo [1-{len(launchers)}]: "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if choice in {"q", "quit", "exit"}:
            return 0
        try:
            if int(choice) < 1:
                continue
            launcher = launchers[int(choice) - 1]
        except (ValueError, IndexError):
            continue

        try:
            video = None
            if launcher.get('select_video'):
                video = select_video(catalog, launcher['demo'])
                if video is None:
                    continue
            result = run_launcher(catalog, launcher, video=video)
            if result != 0:
                print(f"\nThe demo could not finish (exit {result}).")
        except (OSError, RuntimeError) as error:
            print(f"\nError: {error}")
        try:
            input("Press Enter to return to the menu...")
        except (EOFError, KeyboardInterrupt):
            print()


def select_video(catalog, demo_id):
    videos = [
        video for video in catalog.get('videos', [])
        if video['demo'] == demo_id
    ]
    if not videos:
        raise RuntimeError('no videos are configured for this demo')
    while True:
        print('\nChoose a video:')
        for index, video in enumerate(videos, start=1):
            print(f"  {index}. {video['title']}")
        print('  b. Back')
        try:
            choice = input('Video: ').strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if choice in {'b', 'q'}:
            return None
        try:
            index = int(choice) - 1
            if 0 <= index < len(videos):
                return videos[index]
        except ValueError:
            pass


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
