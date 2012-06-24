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
import os
import fnmatch
import re
import sys

from configobj import ConfigObj

from exquires import tools
from exquires import __version__ as VERSION

# pylint: disable-msg=R0903


def _format_doc(docstring):
    """Parse the module docstring and re-format all reST markup.

    :param docstring: The module docstring to format.

    """
    # Deal with LaTeX math symbols.
    latex1 = re.sub('`', '', re.sub(r':\S+:', '', docstring))
    latex2 = re.sub(r'\\infty', 'infinity', re.sub(r'\\ell', 'L', latex1))

    # Deal with list items.
    item1 = re.sub(r' \* ', u' \u2022 ', latex2)

    # Deal with Sphinx bold formatting.
    bold1 = re.sub(r' \*{2}', r' \033[1m', item1)
    bold2 = re.sub(r'^\*{2}', r'^\033[1m', bold1)
    bold3 = re.sub(r'\*{2} ', r'\033[0m ', bold2)
    bold4 = re.sub(r'\*{2},', r'\033[0m,', bold3)
    bold5 = re.sub(r'\*{2}.', r'\033[0m.', bold4)
    bold6 = re.sub(r'\*{2}$', r'\033[0m$', bold5)

    # Deal with Sphinx emphasis formatting.
    emph1 = re.sub(r'^\*', r'^\033[4m', re.sub(r' \*', r' \033[4m', bold6))
    emph2 = re.sub(r'\*,', r'\033[0m,', re.sub(r'\* ', r'\033[0m ', emph1))
    return re.sub(r'\*$', r'\033[0m$', re.sub(r'\*.', r'\033[0m.', emph2))


class ExquiresParser(argparse.ArgumentParser):

    """Generic EXQUIRES parser."""

    def __init__(self, description):
        """This constructor creates a new ExquiresParser object.

        :param description: The docstring from the calling program.

        """
        super(ExquiresParser, self).__init__(
            version=VERSION, description=_format_doc(description),
            formatter_class=lambda prog: ExquiresHelp(prog,
                                                      max_help_position=36)
        )

    def parse_args(self, args=None, namespace=None):
        """Parse command-line arguments.

        :param args: The command-line arguments.
        :param namespace: The namespace.

        """
        # Get the raw command-line arguments
        if args is None:
            args = sys.argv[1:]

        # Attempt to parse the command-line arguments.
        try:
            args = super(ExquiresParser, self).parse_args(args, namespace)
        except argparse.ArgumentTypeError, error:
            self.error(str(error))

        # Return the parsed arguments.
        return args


class OperationsParser(ExquiresParser):

    """Parser for exquires-run and exquires-update."""

    def __init__(self, description, update=False):
        """This constructor creates a new OperationsParser object.

        :param description: The docstring from the calling program.

        """
        super(OperationsParser, self).__init__(description)
        self.add_argument('-s', '--silent', action='store_true',
                          help='do not display progress information')
        self.add_argument('-p', '--proj', metavar='PROJECT',
                          type=str, default='project1',
                          help='name of the project (default: project1)')
        self.update = update

    def parse_args(self, args=None, namespace=None):
        """Parse arguments for exquires-run or exquires-update.

        :param args: The command-line arguments.
        :param namespace: The namespace.

        """
        # Get the raw command-line arguments
        if args is None:
            args = sys.argv[1:]

        # Attempt to parse the command-line arguments.
        args = super(OperationsParser, self).parse_args(args, namespace)

        # Construct the path to the configuration and database files.
        args.dbase_file = '.'.join([args.proj, 'db'])
        args.config_file = '.'.join([args.proj, 'ini'])
        args.config_bak = '.'.join([args.config_file, 'bak'])
        args.prog = self.prog

        # Report an error if the configuration file does not exist.
        if not os.path.isfile(args.config_file):
            self.error(' '.join(['unrecognized project:', args.proj]))

        if self.update:
            # Determine if the database can be updated.
            if not (os.path.isfile(args.config_bak) and
                    os.path.isfile(args.dbase_file)):
                self.error(' '.join([args.proj, 'has not been run']))
        else:
            # Create a new database file, backing up any that already exists.
            if os.path.isfile(args.dbase_file):
                os.rename(args.dbase_file, '.'.join([args.proj, 'db', 'bak']))

        # Return the parsed arguments.
        return args


class StatsParser(ExquiresParser):

    """Parser for exquires-report and exquires-correlate."""

    def __init__(self, description, correlate=False):
        """This constructor creates a new StatsParser object.

        :param description: The docstring from the calling program.

        """
        super(StatsParser, self).__init__(description)
        self.correlate = correlate

        # Output options.
        self.add_argument('-l', '--latex', action='store_true',
                          help='print a LaTeX formatted table')

        if not correlate:
            group = self.add_mutually_exclusive_group()
            group.add_argument('-r', '--rank', action='store_true',
                               help='print Spearman (fractional) ranks')
            group.add_argument('-m', '--merge', action='store_true',
                               help='print merged Spearman ranks')

        self.add_argument('-p', '--proj', metavar='PROJECT', type=str,
                          action=ProjectAction,
                          help='name of the project (default: project1)')
        self.add_argument('-f', '--file', metavar='FILE',
                          type=argparse.FileType('w'), default=sys.stdout,
                          help='output to file (default: sys.stdout)')
        self.add_argument('-d', '--digits', metavar='DIGITS',
                          type=int, choices=range(1, 16), default=4,
                          help='total number of digits (default: 4)')

        if not correlate:
            # Sort option.
            self.add_argument('-s', '--sort', metavar='METRIC', type=str,
                              action=SortAction, default=None,
                              help='sort using this metric (default: first)')

        # Upsampler selection.
        self.add_argument('-U', '--up', metavar='METHOD',
                          type=str, nargs='+', action=ListAction,
                          help='upsamplers to consider (default: all)')

        # Determine if using exquires-report or exquires-correlate.
        if correlate:
            group = self.add_mutually_exclusive_group()
        else:
            group = self

        # Aggregation/correlation options.
        group.add_argument('-I', '--image', metavar='IMAGE',
                           type=str, nargs='+', action=ListAction,
                           help='images to consider (default: all)')
        group.add_argument('-D', '--down', metavar='METHOD',
                           type=str, nargs='+', action=ListAction,
                           help='downsamplers to consider (default: all)')
        group.add_argument('-R', '--ratio', metavar='RATIO',
                           type=str, nargs='+', action=RatioAction,
                           help='ratios to consider (default: all)')
        group.add_argument('-M', '--metric', metavar='METRIC',
                           type=str, nargs='+', action=ListAction,
                           help='metrics to consider (default: all)')

    def parse_args(self, args=None, namespace=None):
        """Parse arguments for exquires-report or exquires-correlate.

        :param args: The command-line arguments.
        :param namespace: The namespace.

        """
        # Get the raw command-line arguments
        if args is None:
            args = sys.argv[1:]

        # Deal with the -h/--help  and -v/--version options.
        help_or_version = False
        for arg in args:
            if arg in ('-h', '--help', '-v', '--version'):
                help_or_version = True
                break

        if not help_or_version:
            # Deal with the -p/--proj option.
            proj = False
            for i in range(0, len(args) - 1):
                if args[i] == '-p' or args[i] == '--proj':
                    args.insert(0, args.pop(i + 1))
                    args.insert(0, args.pop(i + 1))
                    proj = True
                    break
            if not proj:
                args.insert(0, 'project1')
                args.insert(0, '--proj')

        # Make --sort the rightmost option.
        for i in range(2, len(args) - 1):
            if args[i] == '--sort':
                args.append(args.pop(i))
                args.append(args.pop(i))
                break

        # Attempt to parse the command-line arguments.
        args = super(StatsParser, self).parse_args(args, namespace)

        # Default to sorting by the leftmost column.
        if not args.sort:
            args.sort = args.metric[0]

        # Deal with the sort/metric options.
        if not (self.correlate or args.merge) and args.sort not in args.metric:
            args.metric.insert(0, args.sort)
            args.show_sort = False

        # Construct the path to the database file.
        args.dbase_file = '.'.join([args.proj, 'db'])

        # Need to prune the dict first so it matches the argument list.
        args.metrics_d = tools.prune_metrics(args.metric, args.metrics_d)

        # Return the parsed arguments.
        return args


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


class ProjectAction(argparse.Action):

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
        setattr(args, self.dest, value)
        args.image = config['Images'].keys()
        args.down = config['Downsamplers'].keys()
        args.ratio = config['Ratios'].keys()
        args.up = config['Upsamplers'].keys()
        args.metrics_d = config['Metrics']
        args.metrics = config['Metrics'].keys()
        args.metric = config['Metrics'].keys()
        args.sort = None
        args.show_sort = True
        args.merge = False
        args.rank = False

        # Set the "flags" to False.
        args.image_flag = False
        args.down_flag = False
        args.ratio_flag = False
        args.metric_flag = False
        args.up_flag = False


class ListAction(argparse.Action):

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
                tup = value, ', '.join([repr(val) for val in value_list])
                msg = 'invalid choice: %r (choose from %s)' % tup
                raise argparse.ArgumentError(self, msg)
            matches.update(results)
        setattr(args, self.dest, [x for x in value_list if x in matches])
        setattr(args, '_'.join([self.dest, 'flag']), True)


class RatioAction(argparse.Action):

    """Parser action to deal with ratio ranges."""

    def __call__(self, parser, args, values, option_string=None):
        matches = set()
        for value in values:
            # first, figure out if it's a range
            # if so, replace with ' '.join(range(start, end+1))
            nums = value.split('-')
            if len(nums) == 1:
                if nums[0] not in args.ratio:
                    tup = value, ', '.join([repr(val) for val in args.ratio])
                    msg = 'invalid choice: %r (choose from %s)' % tup
                    raise argparse.ArgumentError(self, msg)
                matches.add(int(nums[0]))
            elif len(nums) == 2:
                value_range = range(int(nums[0]), int(nums[1]) + 1)
                for num in value_range:
                    if str(num) not in args.ratio:
                        tup = value, ', '.join([
                            repr(val) for val in args.ratio
                        ])
                        msg = 'invalid choice: %r (choose from %s)' % tup
                        raise argparse.ArgumentError(self, msg)
                matches.update(value_range)
            else:
                msg = 'format error in {}'.format(value)
                raise argparse.ArgumentError(self, msg)
        args.ratio = [x for x in args.ratio if int(x) in matches]
        args.ratio_flag = True


class SortAction(argparse.Action):

    """Parser action to sort the data by the appropriate metric."""

    def __call__(self, parser, args, value, option_string=None):
        if value not in args.metrics:
            tup = value, ', '.join([repr(val) for val in args.metrics])
            msg = 'invalid choice: %r (choose from %s)' % tup
            raise argparse.ArgumentError(self, msg)
        setattr(args, self.dest, value)
