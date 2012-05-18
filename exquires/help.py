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

"""Print formatted help strings for exquires commands.

This module contains a formatter class which may be passed as the
formatter_class= argument to argparse's ArgumentParser constructor.

"""

import argparse
import re

def format_doc(docstring):
    """Private method to fix the module docstring for argparse."""
    # Deal with LaTeX math symbols.
    l1 = re.sub(r':\S+:', '', docstring)
    l2 = re.sub('`', '', l1)
    l3 = re.sub(r'\\ell', 'L', l2)
    l4 = re.sub(r'\\infty', 'infinity', l3)

    # Deal with list items.
    i1 = re.sub(r' \* ', u' \u2022 ', l4)

    # Deal with Sphinx bold formatting.
    b1 = re.sub(r' \*{2}', r' \033[1m', i1)
    b2 = re.sub(r'^\*{2}', r'^\033[1m', b1)
    b3 = re.sub(r'\*{2} ', r'\033[0m ', b2)
    b4 = re.sub(r'\*{2},', r'\033[0m,', b3)
    b5 = re.sub(r'\*{2}.', r'\033[0m.', b4)
    b6 = re.sub(r'\*{2}$', r'\033[0m$', b5)

    # Deal with Sphinx emphasis formatting.
    e1 = re.sub(r' \*', r' \033[4m', b6)
    e2 = re.sub(r'^\*', r'^\033[4m', e1)
    e3 = re.sub(r'\* ', r'\033[0m ', e2)
    e4 = re.sub(r'\*,', r'\033[0m,', e3)
    e5 = re.sub(r'\*.', r'\033[0m.', e4)
    return re.sub(r'\*$', r'\033[0m$', e5)

class ExquiresHelp(argparse.RawDescriptionHelpFormatter):

    """Formatter for generating usage messages and argument help strings.

    This is designed to display options in a cleaner format than the standard
    argparse help strings.

    """

    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            if action.nargs == 0:
                # If the Optional doesn't take a value, the format is:
                #    -s, --long
                parts.extend(action.option_strings)
            else:
                # If the Optional takes a value, the format is:
                #    -s, --long ARGS
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                option_strings = action.option_strings[:]
                last_option_string = option_strings.pop()
                for option_string in option_strings:
                    parts.append(option_string)
                parts.append('%s %s' % (last_option_string, args_string))

            return ', '.join(parts)

    def _fill_text(self, text, width, indent):
        return ''.join([indent + line for line in text.splitlines(True)])
