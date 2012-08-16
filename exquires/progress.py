#!/usr/bin/env python
# coding: utf-8
#
#  Copyright (c) 2012, Adam Turcotte (adam.turcotte@gmail.com)
#                      Nicolas Robidoux (nicolas.robidoux@gmail.com)
#  License: BSD 2-Clause License
#
#  This file is part of the
#  EXQUIRES (EXtensible QUantitative Image RESampling) test suite
#

"""Display progress info for :ref:`exquires-run` and :ref:`exquires-update`.

When the :option:`-s`/:option:`--silent` option is not selected in
:ref:`exquires-run` or :ref:`exquires-update`, the Progress class is used to
display the appropriate information.

"""

import curses
import time


# pylint: disable-msg=E1101
class Progress(object):

    """This class contains methods for displaying progress in exquires.

    When :ref:`exquires-run` and :ref:`exquires-update` are used without silent
    mode enabled, this class is responsible for displaying information about
    the downsampling, upsampling, and comparison steps and the total progress.

    :param program:   name of the program that is running
    :param proj:      name of the project being used
    :param total_ops: total number of operations
    :type program:    `string`
    :type proj:       `string`
    :type total_ops:  `integer`

    """

    def __init__(self, program, proj, total_ops):
        """Create a new Progress object."""
        self.scr = curses.initscr()
        curses.cbreak()
        curses.noecho()
        curses.curs_set(0)
        self.program = program
        self.proj = proj
        self.total_ops = total_ops
        self.num_ops = 0

    def __del__(self):
        """Destruct this Progress object and restore the console."""
        self.scr.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()

    def __table_top(self, line, label, content):
        """Draw the top row of the progress table.

        This method draws the first row of the progress table, which
        displays the project name. Three lines are used to draw this section
        of the table.

        .. note::

            This is a private method called by
            :meth:`cleanup`, :meth:`complete`, and :meth:`do_op`.

        .. warning::

            To display the updated progress table, the screen must be
            refreshed by calling :meth:`self.scr.refresh`.

        :param line:    line number to start drawing at
        :param label:   label for this table entry
        :param content: content for this table entry
        :type line:     `integer`
        :type label:    `string`
        :type content:  `string`

        """
        # Top line.
        self.scr.addch(line, 1, curses.ACS_ULCORNER)
        for column in range(2, 14):
            self.scr.addch(line, column, curses.ACS_HLINE)
        self.scr.addch(line, 14, curses.ACS_TTEE)
        for column in range(15, 56):
            self.scr.addch(line, column, curses.ACS_HLINE)
        self.scr.addch(line, 56, curses.ACS_URCORNER)

        # Content line.
        self.scr.addch(line + 1, 1, curses.ACS_VLINE)
        self.scr.addstr(line + 1, 2, label)
        self.scr.addch(line + 1, 14, curses.ACS_VLINE)
        self.scr.addstr(line + 1, 16, content)
        self.scr.addch(line + 1, 56, curses.ACS_VLINE)

        # Bottom line.
        self.scr.addch(line + 2, 1, curses.ACS_LTEE)
        for column in range(2, 14):
            self.scr.addch(line + 2, column, curses.ACS_HLINE)
        self.scr.addch(line + 2, 14, curses.ACS_PLUS)
        for column in range(15, 56):
            self.scr.addch(line + 2, column, curses.ACS_HLINE)
        self.scr.addch(line + 2, 56, curses.ACS_RTEE)

    def __table_middle(self, line, label, content):
        """Draw one of the middle rows of the progress table.

        This method draws one of the middle rows of the progress table.
        Two lines are used to draw this section of the table.

        .. note::

            This is a private method called by
            :meth:`cleanup`, :meth:`complete`, and :meth:`do_op`.

        .. warning::

            To display the updated progress table, the screen must be
            refreshed by calling :meth:`self.scr.refresh`.

        :param line:    line number to start drawing at
        :param label:   label for this table entry
        :param content: content for this table entry
        :type line:     `integer`
        :type label:    `string`
        :type content:  `string`

        """
        # Content line.
        self.scr.addch(line, 1, curses.ACS_VLINE)
        self.scr.addstr(line, 2, label)
        self.scr.addch(line, 14, curses.ACS_VLINE)
        self.scr.addstr(line, 16, content)
        self.scr.addch(line, 56, curses.ACS_VLINE)

        # Bottom line.
        self.scr.addch(line + 1, 1, curses.ACS_LTEE)
        for column in range(2, 14):
            self.scr.addch(line + 1, column, curses.ACS_HLINE)
        self.scr.addch(line + 1, 14, curses.ACS_PLUS)
        for column in range(15, 56):
            self.scr.addch(line + 1, column, curses.ACS_HLINE)
        self.scr.addch(line + 1, 56, curses.ACS_RTEE)

    def __table_bottom(self, line, label, content):
        """Draw the bottom row of the progress table.

        This method draws one of the middle rows of the progress table.
        Two lines are used to draw this section of the table.

        .. note::

            This is a private method called by
            :meth:`cleanup`, :meth:`complete`, and :meth:`do_op`.

        .. warning::

            To display the updated progress table, the screen must be
            refreshed by calling :meth:`self.scr.refresh`.

        :param line:    line number to start drawing at
        :param label:   label for this table entry
        :param content: content for this table entry
        :type line:     `integer`
        :type label:    `string`
        :type content:  `string`

        """
        # Content line.
        self.scr.addch(line, 1, curses.ACS_VLINE)
        self.scr.addstr(line, 2, label)
        self.scr.addch(line, 14, curses.ACS_VLINE)
        self.scr.addstr(line, 16, content)
        self.scr.addch(line, 56, curses.ACS_VLINE)

        # Bottom line.
        self.scr.addch(line + 1, 1, curses.ACS_LLCORNER)
        for column in range(2, 14):
            self.scr.addch(line + 1, column, curses.ACS_HLINE)
        self.scr.addch(line + 1, 14, curses.ACS_BTEE)
        for column in range(15, 56):
            self.scr.addch(line + 1, column, curses.ACS_HLINE)
        self.scr.addch(line + 1, 56, curses.ACS_LRCORNER)

    def cleanup(self):
        """Indicate that files are being deleted."""
        self.scr.clear()
        self.scr.addstr(1, 1, self.program, curses.A_BOLD)
        self.__table_top(3, 'PROJECT', self.proj)
        self.__table_middle(6, 'PROGRESS', '0%')
        self.__table_bottom(8, 'STATUS', 'DELETING OLD FILES')
        self.scr.refresh()

    def do_op(self, args, upsampler=None, metric=None):
        """Update the progress indicator.

        * If no upsampler is specified, `operation=downsampling`
        * If an upsampler is specified, but no metric, `operation=upsampling`
        * If an upsampler and metric are specified, `operation=comparing`

        :param args:             arguments
        :param args.image:       image being processed
        :param args.downsampler: downsampler being used
        :param args.ratio:       resampling ratio being used
        :param upsampler:        upsampler being used
        :param metric:           metric being used
        :type args:              :class:`argparse.Namespace`
        :type args.image:        `string`
        :type args.downsampler:  `string`
        :type args.ratio:        `string`
        :type upsampler:         `string`
        :type metric:            `string`

        """
        percent = int(self.num_ops * 100 / self.total_ops)
        self.num_ops += 1
        self.scr.clear()
        self.scr.addstr(1, 1, self.program, curses.A_BOLD)
        self.__table_top(3, 'PROJECT', self.proj)
        self.__table_middle(6, 'PROGRESS', '{}%'.format(percent))

        if metric:
            self.__table_middle(8, 'STATUS', 'COMPARING')
        elif upsampler:
            self.__table_middle(8, 'STATUS', 'UPSAMPLING')
        else:
            self.__table_middle(8, 'STATUS', 'DOWNSAMPLING')

        self.__table_middle(10, 'IMAGE', args.image)
        self.__table_middle(12, 'DOWNSAMPLER', args.downsampler)

        if metric:
            self.__table_middle(14, 'RATIO', args.ratio)
            self.__table_middle(16, 'UPSAMPLER', upsampler)
            self.__table_bottom(18, 'METRIC', metric)
        elif upsampler:
            self.__table_middle(14, 'RATIO', args.ratio)
            self.__table_bottom(16, 'UPSAMPLER', upsampler)
        else:
            self.__table_bottom(14, 'RATIO', args.ratio)

        self.scr.refresh()

    def complete(self):
        """Complete the progress indicator.

        Call this method to indicate success once all operations have been
        performed.

        .. note::

            The completion screen is displayed for a half second.

        .. warning::

            To restore the terminal after completion, destruct the
            :class:`Progress` object by calling `del prg`
            (where `prg` is the object to destruct).

        """
        self.scr.clear()
        self.scr.addstr(1, 1, self.program, curses.A_BOLD)
        self.__table_top(3, 'PROJECT', self.proj)
        self.__table_middle(6, 'PROGRESS', '100%')
        self.__table_bottom(8, 'STATUS', 'COMPLETE')
        self.scr.refresh()
        time.sleep(0.5)
