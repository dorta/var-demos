# Copyright 2026 Variscite Ltd.
# SPDX-License-Identifier: BSD-3-Clause

import curses
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from terminal_ui import TerminalUI, navigate, safe_text


class TerminalTests(unittest.TestCase):
    def make_ui(self, keys, size=(24, 80)):
        screen = Mock()
        screen.getmaxyx.return_value = size
        screen.getch.side_effect = keys
        with patch('terminal_ui.curses.has_colors', return_value=False), \
                patch('terminal_ui.curses.curs_set'):
            ui = TerminalUI(screen, {}, 'imx8mplus', [], Mock())
        return ui

    def test_navigation_wraps(self):
        self.assertEqual(navigate(curses.KEY_UP, 0, 3), 2)
        self.assertEqual(navigate(curses.KEY_DOWN, 2, 3), 0)
        self.assertEqual(navigate(curses.KEY_DOWN, 0, 0), 0)

    @patch('terminal_ui.curses.doupdate')
    @patch('terminal_ui.SOC_TEMPERATURE.read', return_value=70)
    def test_select_and_cancel(self, *_):
        items = [{'title': 'One'}, {'title': 'Two'}]
        ui = self.make_ui([curses.KEY_DOWN, 10])
        self.assertEqual(ui.choose('Demos', items), items[1])
        ui = self.make_ui([27])
        self.assertIsNone(ui.choose('Demos', items))

    @patch('terminal_ui.curses.doupdate')
    def test_small_terminal_can_exit(self, *_):
        ui = self.make_ui([27], (8, 20))
        self.assertIsNone(ui.choose('Demos', [{'title': 'One'}]))

    @patch('terminal_ui.curses.doupdate')
    @patch('terminal_ui.SOC_TEMPERATURE.read', return_value=70)
    @patch('terminal_ui.clock_is_limited', return_value=False)
    @patch('terminal_ui.temperature', return_value=70)
    @patch('terminal_ui.subprocess.Popen')
    def test_escape_releases_process(self, popen, *_):
        ui = self.make_ui([27])
        launcher = {'title': 'Camera'}
        ui.api.prepare_launch.return_value = (launcher, ['demo'], '/tmp')
        process = popen.return_value
        process.poll.return_value = None
        ui.run(launcher)
        ui.api.stop_process.assert_called_once_with(process)
        self.assertIn('stopped', ui.notice)

    def test_control_characters_are_removed(self):
        self.assertEqual(safe_text('hello\n\x00world'), 'helloworld')


if __name__ == '__main__':
    unittest.main()
