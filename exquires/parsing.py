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

"""Classes and methods used for parsing arguments and formatting help text."""

import argparse
import fnmatch
import re


def format_doc(docstring):
    """Parse the module docstring and re-format all reST markup.

    :param docstring: The module docstring to format.

    """
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

    This class is designed to display options in a cleaner format than the
    standard argparse help strings.

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


class ProjectParser(argparse.Action):

    """Parser action to read a project file based on the specified name."""

    def __call__(self, parser, args, value, option_string=None):
        # Construct the path to the configuation and database files.
        proj_file = '.'.join([value, 'ini', 'bak'])
        db_file = '.'.join([value, 'db'])
        setattr(args, 'db_file', db_file)

        # Exit with an error if one of these files is missing.
        if not (os.path.isfile(proj_file) and os.path.isfile(db_file)):
            msg = ' '.join(['do \'exquires-run -p', value, '\' first'])
            raise argparse.ArgumentTypeError(msg)

        # Read the configuration file last used to update the database.
        config = ConfigObj(proj_file)
        setattr(args, 'proj', proj_file)
        setattr(args, 'image', config['Images'].keys())
        setattr(args, 'down', config['Downsamplers'].keys())
        setattr(args, 'ratio', config['Ratios'].keys())
        setattr(args, 'up', config['Upsamplers'].keys())
        setattr(args, 'metrics_d', config['Metrics'])
        setattr(args, 'metrics', getattr(args, 'metrics_d').keys())
        setattr(args, 'metric', getattr(args, 'metrics'))
        setattr(args, 'sort', None)
        setattr(args, 'show_sort', True)


class ListParser(argparse.Action):

    """Parser action to handle wildcards for options that support them.

    When specifying aggregation options with exquires-report, this class
    expands any wildcards passed in arguments for the following options:

    * Images
    * Downsamplers
    * Upsamplers
    * Metrics

    """

    def __call__(self, parser, args, values, option_string=None):
        value_list = getattr(args, self.dest)
        matches = set()
        for value in values:
            results = fnmatch.filter(value_list, value)
            if not results:
                tup = value, ', '.join(map(repr, value_list))
                msg = 'invalid choice: %r (choose from %s)' % tup
                raise argparse.ArgumentError(self, msg)
            matches.update(results)
        setattr(args, self.dest, [x for x in value_list if x in matches])


class RatioParser(argparse.Action):

    """Parser action to deal with ratio ranges."""

    def __call__(self, parser, args, values, option_string=None):
        #value_list = getattr(args, self.dest)
        value_list = range(0, 20)
        matches = set()
        for value in values:
            # first, figure out if it's a range
            # if so, replace with ' '.join(range(start, end+1))
            nums = value.split('-')
            if len(nums) == 1:
                if int(nums[0]) not in value_list:
                    tup = value, ', '.join(map(repr, value_list))
                    msg = 'invalid choice: %r (choose from %s)' % tup
                    raise argparse.ArgumentError(self, msg)
                matches.add(int(nums[0]))
            elif len(nums) == 2:
                value_range = range(int(nums[0]), int(nums[1]) + 1)
                for num in value_range:
                    if int(num) not in value_range:
                        tup = value, ', '.join(map(repr, value_list))
                        msg = 'invalid choice: %r (choose from %s)' % tup
                        raise argparse.ArgumentError(self, msg)
                matches.update(value_range)
            else:
                msg = 'format error in {}'.format(value)
                raise argparse.ArgumentError(self, msg)
        setattr(args, self.dest, [x for x in value_list if x in matches])


class SortParser(argparse.Action):

    """Parser action to sort the data by the appropriate metric."""

    def __call__(self, parser, args, value, option_string=None):
        value_list = getattr(args, 'metrics')
        if value not in value_list:
            tup = value, ', '.join(map(repr, value_list))
            msg = 'invalid choice: %r (choose from %s)' % tup
            raise argparse.ArgumentError(self, msg)
        metric = getattr(args, 'metric')
        if value not in metric:
            metric.insert(0, value)
            setattr(args, 'metric', metric)
            setattr(args, 'show_sort', False)
        setattr(args, self.dest, value)
