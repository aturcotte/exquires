#!/usr/bin/env python
# coding: utf-8
#
#  Copyright (c) 2012, Adam Turcotte (adam.turcotte@gmail.com)
#                      Nicolas Robidoux (nicolas.robidoux@gmail.com)
#  License: BSD 2-Clause License
#
#  This file is part of
#  EXQUIRES | Evaluative and eXtensible QUantitative Image Re-Enlargement Suite
#

"""Display progress information for **exquires-run** and **exquires-update**.

When the '--silent' option is not selected in **exquires-run** or
**exquires-update**, the Progress class is used to display the appropriate
information.

"""

import curses
import os
import time


class Progress(object):

    """This class contains methods for displaying progress in exquires.

    When **exquires-run** and **exquires-update** are used without silent
    mode enabled, this class is responsible for displaying information about
    the downsampling, upsampling, and comparison steps and the total progress.

    """

    def __init__(self, prg, proj, num_operations):
        """This constructor creates a new Progress object.

        :param prg: The name of the program that is running.
        :param proj: The name of the project being used.
        :param num_operations: The total number of operations.

        """
        self.scr = curses.initscr()
        curses.cbreak()
        curses.noecho()
        curses.curs_set(0)
        self.prg = prg
        self.proj = proj
        self.num_operations = num_operations
        self.op = 0

    def __table_top(self, y, label, content):
        """Private method to create the top row of a table.

        :param y: The line number to start drawing.
        :param label: The label for this table entry.
        :param content: The content for this table entry.

        """
        # Top line.
        self.scr.addch(y, 1, curses.ACS_ULCORNER)
        for x in range(2, 14):
            self.scr.addch(y, x, curses.ACS_HLINE)
        self.scr.addch(y, 14, curses.ACS_TTEE)
        for x in range(15, 56):
            self.scr.addch(y, x, curses.ACS_HLINE)
        self.scr.addch(y, 56, curses.ACS_URCORNER)

        # Content line.
        self.scr.addch(y + 1, 1, curses.ACS_VLINE)
        self.scr.addstr(y + 1, 2, label)
        self.scr.addch(y + 1, 14, curses.ACS_VLINE)
        self.scr.addstr(y + 1, 16, content)
        self.scr.addch(y + 1, 56, curses.ACS_VLINE)

        # Bottom line.
        self.scr.addch(y + 2, 1, curses.ACS_LTEE)
        for x in range(2, 14):
            self.scr.addch(y + 2, x, curses.ACS_HLINE)
        self.scr.addch(y + 2, 14, curses.ACS_PLUS)
        for x in range(15, 56):
            self.scr.addch(y + 2, x, curses.ACS_HLINE)
        self.scr.addch(y + 2, 56, curses.ACS_RTEE)

    def __table_middle(self, y, label, content):
        """Private method to create the middle row of a table.

        :param y: The line number to start drawing.
        :param label: The label for this table entry.
        :param content: The content for this table entry.

        """
        # Content line.
        self.scr.addch(y, 1, curses.ACS_VLINE)
        self.scr.addstr(y, 2, label)
        self.scr.addch(y, 14, curses.ACS_VLINE)
        self.scr.addstr(y, 16, content)
        self.scr.addch(y, 56, curses.ACS_VLINE)

        # Bottom line.
        self.scr.addch(y + 1, 1, curses.ACS_LTEE)
        for x in range(2, 14):
            self.scr.addch(y + 1, x, curses.ACS_HLINE)
        self.scr.addch(y + 1, 14, curses.ACS_PLUS)
        for x in range(15, 56):
            self.scr.addch(y + 1, x, curses.ACS_HLINE)
        self.scr.addch(y + 1, 56, curses.ACS_RTEE)

    def __table_bottom(self, y, label, content):
        """Private method to create the bottom row of a table.

        :param y: The line number to start drawing.
        :param label: The label for this table entry.
        :param content: The content for this table entry.

        """
        # Content line.
        self.scr.addch(y, 1, curses.ACS_VLINE)
        self.scr.addstr(y, 2, label)
        self.scr.addch(y, 14, curses.ACS_VLINE)
        self.scr.addstr(y, 16, content)
        self.scr.addch(y, 56, curses.ACS_VLINE)

        #Bottom line.
        self.scr.addch(y + 1, 1, curses.ACS_LLCORNER)
        for x in range(2, 14):
            self.scr.addch(y + 1, x, curses.ACS_HLINE)
        self.scr.addch(y + 1, 14, curses.ACS_BTEE)
        for x in range(15, 56):
            self.scr.addch(y + 1, x, curses.ACS_HLINE)
        self.scr.addch(y + 1, 56, curses.ACS_LRCORNER)

    def cleanup(self):
        """Indicate that files are being deleted."""
        self.scr.clear()
        self.scr.addstr(1, 1, self.prg, curses.A_BOLD)
        self.__table_top(3, 'PROJECT', self.proj)
        self.__table_middle(6, 'PROGRESS', '0%')
        self.__table_bottom(8, 'STATUS', 'DELETING OLD FILES')
        self.scr.refresh()

    def do_op(self, image, downsampler, ratio, upsampler=None, metric=None):
        """Update the progress indicator.

        If no upsampler is specified, operation=downsampling.
        If an upsampler is specified, but no metric, operation=upsampling.
        If an upsampler and metric are specified, operation=comparing.

        :param image: The image being processed.
        :param downsampler: The downsampler being used.
        :param ratio: The resampling ratio being used.
        :param upsampler: The upsampler being used.
        :param metric: The metric being used.

        """
        percent = int(self.op * 100 / self.num_operations)
        self.op += 1
        self.scr.clear()
        self.scr.addstr(1, 1, self.prg, curses.A_BOLD)
        self.__table_top(3, 'PROJECT', self.proj)
        self.__table_middle(6, 'PROGRESS', '{}%'.format(percent))

        if metric:
            self.__table_middle(8, 'STATUS', 'COMPARING')
        elif upsampler:
            self.__table_middle(8, 'STATUS', 'UPSAMPLING')
        else:
            self.__table_middle(8, 'STATUS', 'DOWNSAMPLING')

        self.__table_middle(10, 'IMAGE', image)
        self.__table_middle(12, 'DOWNSAMPLER', downsampler)

        if metric:
            self.__table_middle(14, 'RATIO', ratio)
            self.__table_middle(16, 'UPSAMPLER', upsampler)
            self.__table_bottom(18, 'METRIC', metric)
        elif upsampler:
            self.__table_middle(14, 'RATIO', ratio)
            self.__table_bottom(16, 'UPSAMPLER', upsampler)
        else:
            self.__table_bottom(14, 'RATIO', ratio)

        self.scr.refresh()

    def complete(self):
        """Complete the progress indicator."""
        self.scr.clear()
        self.scr.addstr(1, 1, self.prg, curses.A_BOLD)
        self.__table_top(3, 'PROJECT', self.proj)
        self.__table_middle(6, 'PROGRESS', '100%')
        self.__table_bottom(8, 'STATUS', 'COMPLETE')
        self.scr.refresh()
        time.sleep(0.5)
        curses.nocbreak()
        self.scr.keypad(0)
        curses.echo()
        curses.curs_set(1)
        curses.endwin()
