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


def _remove_duplicates(input_list):
    """Remove duplicate entries from a list.

    .. note::

        This is a private function called by :meth:`ListAction.__call__`
        and :meth:`RatioAction.__call__`.

    :param input_list: list to remove duplicate entries from
    :type input_list:  `list of values`

    :return:           list with duplicate entries removed
    :rtype:            `list of values`

    """
    unique = set()
    return [x for x in input_list if x not in unique and not unique.add(x)]


def _format_doc(docstring):
    """Parse the module docstring and re-format all `reST` markup.

    .. note::

        This is a private function called when creating a new
        :class:`ExquiresParser` object.

    :param docstring: docstring to format
    :type docstring:  `string`

    :return:          formatted docstring
    :rtype:           `string`

    """
    # Deal with directives and LaTeX math symbols.
    dir1 = re.sub(r':file:`', r'\033[4m', docstring)
    dir2 = re.sub(r':\S+:`', r'\033[1m', dir1)
    dir3 = re.sub('`', r'\033[0m', dir2)
    dir4 = re.sub(r'\\infty', 'infinity', re.sub(r'\\ell', 'L', dir3))

    # Deal with list items.
    item1 = re.sub(r'    \* ', u'    \u2022 ', dir4)

    # Deal with bold formatting.
    bold1 = re.sub(r' \*{2}', r' \033[1m', item1)
    bold2 = re.sub(r'^\*{2}', r'^\033[1m', bold1)
    bold3 = re.sub(r'\*{2} ', r'\033[0m ', bold2)
    bold4 = re.sub(r'\*{2},', r'\033[0m,', bold3)
    bold5 = re.sub(r'\*{2}.', r'\033[0m.', bold4)
    return re.sub(r'\*{2}$', r'\033[0m$', bold5)


class ExquiresParser(argparse.ArgumentParser):

    """Generic **EXQUIRES** parser.

    :param description: docstring from the calling program
    :type description:  `string`

    """

    def __init__(self, description):
        """Create a new ExquiresParser object."""
        super(ExquiresParser, self).__init__(
            version=VERSION, description=_format_doc(description),
            formatter_class=lambda prog: ExquiresHelp(prog,
                                                      max_help_position=36)
        )

    def parse_args(self, args=None, namespace=None):
        """Parse command-line arguments.

        :param args:      the command-line arguments
        :param namespace: the namespace
        :type args:       `string`
        :type namespace:  :class:`argparse.Namespace`

        :return:          the parsed arguments
        :rtype:           :class:`argparse.Namespace`

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

    """Parser used by :ref:`exquires-run` and :ref:`exquires-update`.

    :param description: docstring from the calling program
    :param update:      `True` if called by :ref:`exquires-update`
    :type description:  `string`
    :type update:       `boolean`

    """

    def __init__(self, description, update=False):
        """Create a new OperationsParser object."""
        super(OperationsParser, self).__init__(description)
        self.add_argument('-s', '--silent', action='store_true',
                          help='do not display progress information')
        self.add_argument('-p', '--proj', metavar='PROJECT',
                          type=str, default='project1',
                          help='name of the project (default: project1)')
        self.update = update

    def parse_args(self, args=None, namespace=None):
        """Parse the received arguments.

        This method parses the arguments received by  :ref:`exquires-run` or
        :ref`exquires-update`.

        :param args:      the command-line arguments
        :param namespace: the namespace
        :type args:       `string`
        :type namespace:  :class:`argparse.Namespace`

        :return:          the parsed arguments
        :rtype:           :class:`argparse.Namespace`

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

    """Parser used by :ref:`exquires-report` and :ref:`exquires-correlate`.

    :param description: docstring from the calling program
    :param correlate:   `True` if using :ref:`exquires-correlate`
    :type description:  `string`
    :type correlate:    `boolean`

    """

    def __init__(self, description, correlate=False):
        """Create a new StatsParser object."""
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

        if correlate:
            # Anchor option (sorting for exquires-correlate).
            self.add_argument('-a', '--anchor', metavar='ANCHOR', type=str,
                              action=AnchorAction, default=None,
                              help='sort using this anchor (default: none)')
        else:
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

    def parse_args(self, args=sys.argv[1:], namespace=None):
        """Parse the received arguments.

        This method parses the arguments received by :ref:`exquires-report` or
        :ref:`exquires-correlate`.

        :param args:      the command-line arguments
        :param namespace: the namespace
        :type args:       `string`
        :type namespace:  :class:`argparse.Namespace`

        :return:          the parsed arguments
        :rtype:           :class:`argparse.Namespace`

        """
        # Deal with the -h/--help  and -v/--version options.
        help_or_version = False
        for arg in args:
            if arg in ('-h', '--help', '-v', '--version'):
                help_or_version = True
                break

        if not help_or_version:
            # Deal with the -p/--proj option.
            proj = False
            for i, arg in enumerate(args, 1):
                if arg in ('-p', '--proj'):
                    args.insert(0, args.pop(i))
                    args.insert(0, args.pop(i))
                    proj = True
                    break
            if not proj:
                args.insert(0, 'project1')
                args.insert(0, '--proj')

        # Setup the arguments to be parsed last.
        if self.correlate:
            # Make -a/--anchor the rightmost option.
            flags = ('-a', '--anchor')
        else:
            # Make -s/--sort the rightmost option.
            flags = ('-s', '--sort')
        for i, arg in enumerate(args):
            if arg in flags:
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
        """Format the string describing the invocation of the specified action.

        :param action: the parsing action
        :type action:  :class:`argparse.Action`

        :return:       the formatted action invocation
        :rtype:        `string`

        """
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
        """Fill action text with whitespace.

        :param text:   the text to display
        :param width:  line width
        :param indent: indentation printed before the text
        :type text:    `string`
        :type width:   `integer`
        :type indent:  `string`

        :return:       the formatted text
        :rtype:        `string`

        """
        return ''.join([indent + line for line in text.splitlines(True)])


class ProjectAction(argparse.Action):

    """Parser action to read a project file based on the specified name."""

    def __call__(self, parser, args, value, option_string=None):
        """Parse the :option:`-p`/:option:`--project` option.

        :param parser:        the parser calling this action
        :param args:          arguments
        :param values:        values
        :param option_string: command-line option string
        :type parser:         :class:`ExquiresParser`
        :type args:           :class:`argparse.Namespace`
        :type values:         `list of values`
        :type option_string:  `string`

        :raises:              :class:`argparse.ArgumentError`

        """
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

        # Set the default correlation key in case an anchor is specified.
        args.key = 'metric'


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
        """Parse any option that supports lists with wildcard characters.

        :param parser:        the parser calling this action
        :param args:          arguments
        :param values:        values
        :param option_string: command-line option string
        :type parser:         :class:`ExquiresParser`
        :type args:           :class:`argparse.Namespace`
        :type values:         `list of values`
        :type option_string:  `string`

        :raises:              :class:`argparse.ArgumentError`

        """
        value_list = getattr(args, self.dest)
        matches = []
        for value in values:
            results = fnmatch.filter(value_list, value)
            if not results:
                tup = value, ', '.join([repr(val) for val in value_list])
                msg = 'invalid choice: %r (choose from %s)' % tup
                raise argparse.ArgumentError(self, msg)
            matches.extend(results)

        # Set the argument and possibly set the correlation key.
        setattr(args, self.dest, _remove_duplicates(matches))
        if self.dest is not 'up':
            args.key = self.dest


class RatioAction(argparse.Action):

    """Parser action to deal with ratio ranges."""

    def __call__(self, parser, args, values, option_string=None):
        """Parse the :option:`-r`/:option:`--ratio` option.

        :param parser:        the parser calling this action
        :param args:          arguments
        :param values:        values
        :param option_string: command-line option string
        :type parser:         :class:`ExquiresParser`
        :type args:           :class:`argparse.Namespace`
        :type values:         `list of values`
        :type option_string:  `string`

        :raises:              :class:`argparse.ArgumentError`

        """
        matches = []
        for value in values:
            # Detect range.
            nums = value.split('-')
            if len(nums) == 1:
                if nums[0] not in args.ratio:
                    tup = value, ', '.join([repr(val) for val in args.ratio])
                    msg = 'invalid choice: %r (choose from %s)' % tup
                    raise argparse.ArgumentError(self, msg)
                matches.append(int(nums[0]))
            elif len(nums) == 2:
                value_range = range(int(nums[0]), int(nums[1]) + 1)
                for num in value_range:
                    if str(num) not in args.ratio:
                        tup = value, ', '.join([
                            repr(val) for val in args.ratio
                        ])
                        msg = 'invalid choice: %r (choose from %s)' % tup
                        raise argparse.ArgumentError(self, msg)
                matches.extend(value_range)
            else:
                msg = 'format error in {}'.format(value)
                raise argparse.ArgumentError(self, msg)

        # Set the argument and correlation key.
        setattr(args, self.dest, _remove_duplicates(matches))
        args.key = self.dest


class AnchorAction(argparse.Action):

    """Parser action to sort the correlation matrix."""

    def __call__(self, parser, args, value, option_string=None):
        """Parse the :option:`-a`/:option:`--anchor` option.

        :param parser:        the parser calling this action
        :param args:          arguments
        :param values:        values
        :param option_string: command-line option string
        :type parser:         :class:`ExquiresParser`
        :type args:           :class:`argparse.Namespace`
        :type values:         `list of values`
        :type option_string:  `string`

        :raises:              :class:`argparse.ArgumentError`

        """
        group = getattr(args, args.key)
        if value not in group:
            tup = value, ', '.join([repr(val) for val in group])
            msg = 'invalid choice: %r (choose from %s)' % tup
            raise argparse.ArgumentError(self, msg)
        setattr(args, self.dest, value)


class SortAction(argparse.Action):

    """Parser action to sort the data by the appropriate metric."""

    def __call__(self, parser, args, value, option_string=None):
        """Parse the :option:`-s`/:option:`--sort` option.

        :param parser:        the parser calling this action
        :param args:          arguments
        :param values:        values
        :param option_string: command-line option string
        :type parser:         :class:`ExquiresParser`
        :type args:           :class:`argparse.Namespace`
        :type values:         `list of values`
        :type option_string:  `string`

        :raises:              :class:`argparse.ArgumentError`

        """
        if value not in args.metrics:
            tup = value, ', '.join([repr(val) for val in args.metrics])
            msg = 'invalid choice: %r (choose from %s)' % tup
            raise argparse.ArgumentError(self, msg)
        setattr(args, self.dest, value)
