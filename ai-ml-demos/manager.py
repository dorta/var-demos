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
from runtime import clock_is_limited, temperature, StartupProgress


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
    if launcher.get('terminal_output'):
        print('  Results will appear in the terminal when finished.')
    else:
        print("  The demo opens on the board's display.")
    print("  Ctrl+C: stop and return\n")
    stopped = False
    with tempfile.NamedTemporaryFile(
        prefix='var-ai-', suffix='.log', delete=False
    ) as log:
        process = subprocess.Popen(
            command,
            cwd=directory,
            env=environment_for(launcher),
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        started = time.monotonic()
        last_elapsed = -1
        cooling = False
        progress = StartupProgress(launcher.get('startup_progress', False))
        try:
            while process.poll() is None:
                elapsed = int(time.monotonic() - started)
                if elapsed != last_elapsed:
                    soc = SOC_TEMPERATURE.read()
                    soc_text = '--' if soc is None else f'{soc:.1f}'
                    peak = temperature()
                    limited = clock_is_limited()
                    inference_demo = launcher.get('group', 'ai-ml') == 'ai-ml'
                    if inference_demo and (limited or (
                            peak is not None and peak >= 82)):
                        cooling = True
                    elif peak is not None and peak < 78:
                        cooling = False
                    progress.read(log.name)
                    state = ('Cooling' if cooling else 'Running'
                             if progress.ready else 'Preparing')
                    print(
                        f"\r  {state:<7}  {elapsed // 60:02d}:"
                        f"{elapsed % 60:02d}  |  SoC {soc_text} C    ",
                        end='', flush=True,
                    )
                    last_elapsed = elapsed
                    if not progress.ready:
                        print(f'\n  {progress.message}', flush=True)
                time.sleep(0.1)
        except KeyboardInterrupt:
            stopped = True
        finally:
            stop_process(process)

    if stopped:
        print('\r  Stopped.                                       ')
    elif process.returncode == 0:
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
    if stopped or process.returncode == 0:
        try:
            from terminal_ui import log_tail, summary_lines
            lines = (log_tail(log.name) if launcher.get('terminal_output') else
                     summary_lines(log.name, time.monotonic() - started))
        except ImportError:
            # The plain interface remains usable on images without curses.
            with open(log.name, 'rb') as output:
                output.seek(0, 2)
                output.seek(max(0, output.tell() - 65536))
                lines = output.read().decode('utf-8', errors='replace').splitlines()[-8:]
        for line in lines:
            line = ''.join(character for character in line
                           if character.isprintable())
            print(f'  {line}')
    return 0 if stopped else process.returncode


def prepare_launch(catalog, launcher, video=None):
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

    if video is not None:
        launcher = dict(launcher, title=video['title'])
    return launcher, command, directory


def environment_for(launcher):
    environment = display_environment()
    if launcher.get('native_wayland'):
        environment['GDK_BACKEND'] = 'wayland'
        runtime = Path(environment['XDG_RUNTIME_DIR'])
        sockets = sorted(path for path in runtime.glob('wayland-*')
                         if path.is_socket())
        if not sockets:
            raise RuntimeError(f'No Wayland display socket in {runtime}')
        environment['WAYLAND_DISPLAY'] = sockets[0].name
    return environment


def run_launcher(catalog, launcher, dashboard=True, video=None):
    launcher, command, directory = prepare_launch(catalog, launcher, video)
    if dashboard and sys.stdout.isatty():
        return run_with_dashboard(launcher, command, directory)
    return subprocess.run(
        command,
        cwd=directory,
        env=environment_for(launcher),
        check=False,
    ).returncode


def show_menu(platform, launchers, back=False, suite=False):
    clear_screen()
    print('VARISCITE DEMOS' if suite else 'VARISCITE AI/ML DEMOS')
    print(f"Platform: {platform}")
    category = None
    for index, launcher in enumerate(launchers, start=1):
        if launcher.get("category") != category:
            category = launcher.get("category")
            if category:
                print(category)
        title = launcher.get("menu_title", launcher["title"])
        description = launcher.get("description", "")
        print(f"  {index}. {title:<9} {description}")
    print('\n  q. Back' if back else '\n  q. Quit')
    print("Demos open fullscreen. Press Esc to close the display.")


def interactive(catalog, platform, launchers):
    all_launchers = launchers
    groups = [group for group in catalog.get('groups', []) if any(
        item.get('group') == group['id'] for item in launchers)]
    selected_group = None
    while True:
        if groups and selected_group is None:
            clear_screen()
            print(f'VARISCITE DEMOS | {platform}\n')
            for index, group in enumerate(groups, 1):
                print(f"  {index}. {group['title']}")
            print('\n  q. Quit')
            try:
                choice = input('Choose a category: ').strip().lower()
            except (EOFError, KeyboardInterrupt):
                return 0
            if choice in {'q', 'quit', 'exit'}:
                return 0
            try:
                index = int(choice) - 1
                if not 0 <= index < len(groups):
                    continue
                selected_group = groups[index]
            except ValueError:
                continue
            launchers = [item for item in all_launchers
                         if item.get('group') == selected_group['id']]
        show_menu(platform, launchers, back=bool(groups), suite=bool(groups))
        try:
            choice = input(
                f"\nSelect a demo [1-{len(launchers)}]: "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if choice in {"q", "quit", "exit"}:
            if groups:
                selected_group = None
                continue
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
    parser.add_argument("--plain", action="store_true",
                        help="use the simple text interface")
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

    if (not args.plain and sys.stdin.isatty() and sys.stdout.isatty()
            and os.environ.get('TERM', 'dumb') != 'dumb'):
        try:
            import curses
            from terminal_ui import TerminalUI, serial_console
        except ImportError:
            return interactive(catalog, platform, launchers)
        try:
            if serial_console():
                # The serial login defaults to Linux-console capabilities,
                # but minicom emulates VT100, not the Linux console.
                os.environ['TERM'] = 'vt100'
            return curses.wrapper(
                lambda screen: TerminalUI(
                    screen, catalog, platform, launchers,
                    sys.modules[__name__],
                ).main()
            )
        except curses.error as error:
            print(f'Terminal UI unavailable: {error}; using text mode.')
        except KeyboardInterrupt:
            return 0
    return interactive(catalog, platform, launchers)


if __name__ == "__main__":
    sys.exit(main())
