# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

from collections import deque
import curses
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import time

from telemetry import SOC_TEMPERATURE
from runtime import clock_is_limited, temperature


def navigate(key, selected, count):
    if not count:
        return 0
    if key in (curses.KEY_UP, ord('k')):
        return (selected - 1) % count
    if key in (curses.KEY_DOWN, ord('j')):
        return (selected + 1) % count
    return selected


def safe_text(text):
    return ''.join(character for character in str(text)
                   if character.isprintable())


def serial_console():
    try:
        device = os.ttyname(sys.stdin.fileno())
    except (OSError, ValueError):
        return False
    return device.startswith(('/dev/ttymxc', '/dev/ttyS', '/dev/ttyAMA',
                              '/dev/ttyUSB', '/dev/ttyACM'))


def log_tail(path):
    with Path(path).open(encoding='utf-8', errors='replace') as output:
        return [safe_text(line) for line in deque(output, maxlen=8)]


def summary_lines(path, elapsed):
    lines = [f'Elapsed: {elapsed:.1f} seconds']
    with Path(path).open('rb') as output:
        output.seek(0, 2)
        output.seek(max(0, output.tell() - 65536))
        tail = output.read().decode('utf-8', errors='replace')
    for line in reversed(tail.splitlines()):
        if not line.startswith('VAR_AI_STATS '):
            continue
        try:
            stats = json.loads(line.removeprefix('VAR_AI_STATS '))
            lines.append(f"Frames with inference: {int(stats['frames'])}")
            for key, label, unit in (
                ('processing_fps', 'Average processing rate', 'FPS'),
                ('inference_ms', 'Average inference', 'ms'),
                ('soc_peak_c', 'Peak sampled SoC temperature', 'C'),
            ):
                value = stats.get(key)
                if isinstance(value, (int, float)):
                    lines.append(f'{label}: {value:.1f} {unit}')
            break
        except (ValueError, TypeError, KeyError):
            continue
    if len(lines) == 1:
        lines.append('Processing statistics unavailable for this run.')
    return lines


class TerminalUI:
    def __init__(self, screen, catalog, platform, launchers, api):
        self.screen = screen
        self.catalog = catalog
        self.platform = platform
        self.launchers = launchers
        self.api = api
        self.notice = ''
        self.serial = serial_console()
        self.view = None
        self.full_refresh = True
        if self.serial:
            # Serial links do not propagate the emulator's window size.
            height, width = screen.getmaxyx()
            curses.resizeterm(min(height, 24), min(width, 80))
        self.accent = curses.A_BOLD
        self.selected_style = curses.A_REVERSE | curses.A_BOLD
        screen.keypad(True)
        screen.timeout(200)
        screen.idcok(False)
        screen.idlok(False)
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        if not self.serial and curses.has_colors():
            curses.start_color()
            background = curses.COLOR_BLACK
            try:
                curses.use_default_colors()
                background = -1
            except curses.error:
                pass
            curses.init_pair(1, curses.COLOR_CYAN, background)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
            self.accent = curses.color_pair(1) | curses.A_BOLD
            self.selected_style = curses.color_pair(2) | curses.A_BOLD

    def text(self, row, column, text, style=0):
        text = safe_text(text)
        if self.serial:
            text = text.replace('\u2014', '-').replace('\u2013', '-')
            text = text.encode('ascii', errors='replace').decode('ascii')
        height, width = self.screen.getmaxyx()
        if 0 <= row < height and 0 <= column < width - 1:
            try:
                self.screen.addnstr(
                    row, column, text, width - column - 1, style
                )
            except curses.error:
                pass

    def header(self, title):
        view = (title, self.screen.getmaxyx())
        if view != self.view:
            self.full_refresh = True
            self.view = view
        self.screen.erase()
        height, width = self.screen.getmaxyx()
        if height < 12 or width < 45:
            self.text(0, 0, 'Resize terminal to at least 45 x 12.')
            self.text(1, 0, 'Esc / q: back or stop')
            return False
        self.text(1, 2, 'VARISCITE  /  AI + ML', self.accent)
        value = SOC_TEMPERATURE.read()
        thermal = 'SoC --.- C' if value is None else f'SoC {value:.1f} C'
        self.text(1, width - len(thermal) - 3, thermal, curses.A_BOLD)
        self.text(2, 2, f'{self.platform}  |  {title}', curses.A_DIM)
        self.text(4, 2, '-' * (width - 5), curses.A_DIM)
        return True

    def footer(self, text):
        height, _ = self.screen.getmaxyx()
        self.text(height - 2, 2, text, self.accent)
        # curses sends changed cells only; no full-screen clear per refresh.
        if self.full_refresh:
            self.screen.clearok(True)
            self.screen.refresh()
            self.full_refresh = False
        else:
            self.screen.noutrefresh()
            curses.doupdate()

    def choose(self, title, items, back_label='Back'):
        if not items:
            self.message('No compatible demos are available.')
            return None
        selected = 0
        previous = None
        while True:
            state = (selected, int(time.monotonic()),
                     self.screen.getmaxyx())
            if state != previous:
                if self.header(title):
                    height, width = self.screen.getmaxyx()
                    page_size = max(1, height - 12)
                    start = (selected // page_size) * page_size
                    for index in range(start, min(len(items), start + page_size)):
                        item = items[index]
                        label = f" {index + 1:>2}  {item['title']} "
                        style = self.selected_style if index == selected else 0
                        self.text(5 + index - start, 2,
                                  label.ljust(width - 5), style)
                    description = items[selected].get('description', '')
                    lines = textwrap.wrap(description, max(1, width - 5))
                    self.text(height - 6, 2, lines[0] if lines else '',
                              curses.A_DIM)
                    self.text(height - 5, 2, self.notice)
                self.footer(f'Up/Down: select  Enter: open  Esc/q: {back_label}')
                previous = state
            key = self.screen.getch()
            if key in (27, ord('q')):
                return None
            selected = navigate(key, selected, len(items))
            if key in (10, 13, curses.KEY_ENTER):
                return items[selected]
            if ord('1') <= key <= ord('9'):
                index = key - ord('1')
                if index < len(items):
                    return items[index]

    def message(self, title, lines=()):
        while True:
            if self.header(title):
                height, _ = self.screen.getmaxyx()
                for index, line in enumerate(lines[:max(0, height - 8)]):
                    self.text(5 + index, 2, line)
            self.footer('Enter / Esc: return')
            if self.screen.getch() in (10, 13, 27, ord('q')):
                return

    def run(self, launcher, video=None):
        launcher, command, directory = self.api.prepare_launch(
            self.catalog, launcher, video
        )
        stopped = False
        show_logs = False
        cooling = False
        with tempfile.NamedTemporaryFile(
            prefix='var-ai-', suffix='.log', delete=False
        ) as log:
            process = subprocess.Popen(
                command, cwd=directory, env=self.api.display_environment(),
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
            )
            started = time.monotonic()
            previous = None
            try:
                while process.poll() is None:
                    elapsed = int(time.monotonic() - started)
                    state = (elapsed, show_logs, self.screen.getmaxyx())
                    if state != previous:
                        peak = temperature()
                        if clock_is_limited() or (peak is not None and peak >= 82):
                            cooling = True
                        elif peak is not None and peak < 78:
                            cooling = False
                        if self.header('Demo running'):
                            self.text(5, 2, launcher['title'], curses.A_BOLD)
                            status = 'Cooling - inference paused' if cooling else 'Running'
                            self.text(7, 2, status, self.accent)
                            self.text(8, 2,
                                      f'Elapsed  {elapsed // 60:02d}:{elapsed % 60:02d}')
                            self.text(10, 2, 'Video output: board display', curses.A_DIM)
                            if show_logs:
                                height, _ = self.screen.getmaxyx()
                                for index, line in enumerate(log_tail(log.name)):
                                    if 12 + index < height - 3:
                                        self.text(12 + index, 2, line, curses.A_DIM)
                        self.footer('Esc/s: stop and return  l: toggle diagnostic log')
                        previous = state
                    key = self.screen.getch()
                    if key in (27, ord('s'), ord('q')):
                        stopped = True
                        break
                    if key == ord('l'):
                        show_logs = not show_logs
            except KeyboardInterrupt:
                stopped = True
            finally:
                self.api.stop_process(process)
        if stopped:
            self.notice = 'Demo stopped. Camera and display resources released.'
        elif process.returncode == 0:
            self.notice = 'Demo finished.'
        else:
            self.notice = f'Demo failed (exit {process.returncode}).'
            self.message(self.notice, log_tail(log.name) + [f'Log: {log.name}'])
            return
        self.message(self.notice, summary_lines(
            log.name, time.monotonic() - started
        ))

    def main(self):
        while True:
            launcher = self.choose('Choose a demo', self.launchers, 'Quit')
            if launcher is None:
                return 0
            try:
                video = None
                if launcher.get('select_video'):
                    videos = [item for item in self.catalog.get('videos', [])
                              if item['demo'] == launcher['demo']]
                    video = self.choose('Choose a video', videos)
                    if video is None:
                        continue
                self.run(launcher, video)
            except (OSError, RuntimeError) as error:
                self.message('Cannot start demo', [str(error)])
