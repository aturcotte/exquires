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

"""Print a formatted table of aggregate image difference data.

Each database table in the current project contains data for a single image,
downsampler, and ratio. Each row represents an upsampler and each column
represents a difference metric. By default, the data across all rows and
columns of all tables is aggregated. Use the appropriate option flags to
aggregate across a subset of the database.

--------
Features
--------

 * -R/--ratio supports hyphenated ranges (ex. '1-3 5' gives '1 2 3 5')
 * -I/--image, -D/--downsampler, -U/--upsampler & -M/--metric support wildcards

"""

import argparse
import sys
from collections import OrderedDict
from math import fabs
from operator import itemgetter
from subprocess import check_output

import database
import parsing
from __init__ import __version__ as VERSION


def _prune_metrics(keys, metrics_d):
    """Prune a dictionary of metrics using a list of keys.

    :param keys: A list of keys to retain.
    :param metrics_d: A dictionary of metric names to prune.
    :return: The pruned dictionary.

    """
    result = OrderedDict()
    for key in keys:
        result[key] = metrics_d[key]
    return result


def _format_cell(cell, digits):
    """Return a formatted version of this cell of the data table.

    :param cell: The cell to format.
    :param digits: The number of digits to display.
    :return: The formatted cell.

    """
    try:
        value = float(cell)
        if fabs(value) < 1:
            return str(cell)[1:digits + 2]
        return str(cell)[:digits + 1]
    except ValueError:
        # Cell is not a float.
        return cell


def _get_max_width(printdata, index, digits):
    """Return the width of a column.

    :param printdata: A list of lists, defining the table to print.
    :param index: The cell index.
    :param digits: The number of digits to display.
    :return: The width of this column.

    """
    if digits is 0:
        return max(len(printdata[0][index]), len(str(len(printdata) - 1)))
    return max(len(printdata[0][index]), digits + 1)


def _get_ranks(printdata, metrics_desc, sort_index):
    """Return a rank table based on a data table.

    :param printdata: A list of lists, defining the table to print.
    :param metrics_desc: A list of 0s and 1s (where 1 is 'descending').
    :param sort_index: Index of the column to sort by.
    :return: A table of ranks.

    """
    li1 = [x[:] for x in printdata]
    li2 = [x[:] for x in printdata]
    for j in range(1, len(printdata[0])):
        li1.sort(key=itemgetter(j), reverse=metrics_desc[j - 1])
        li2.sort(key=itemgetter(j), reverse=metrics_desc[j - 1])
        li2[0][j] = 1
        for i in range(1, len(printdata)):
            li2[i][j] = li2[i - 1][j] if li1[i][j] == li1[i - 1][j] else i + 1

    li2.sort(key=itemgetter(sort_index))
    return li2


def _print_normal(printdata, outfile, digits):
    """Print the processed data table with normal formatting.

    :param printdata: A list of lists, defining the table to print.
    :param outfile: The path to write the aggregated error table.
    :param digits: The number of digits to display after the decimal point.

    """
    col_pad = []

    for i in range(len(printdata[0])):
        col_pad.append(_get_max_width(printdata, i, digits))

    for row in printdata:
        # Print the cell for the left column (upsamplers).
        print >> outfile, row[0].ljust(col_pad[0]),

        # Print the cells for the remaining columns.
        for i in range(1, len(row)):
            cell = _format_cell(row[i], digits).rjust(col_pad[i] + 1)
            print >> outfile, cell,
        print >> outfile


def _print_latex(printdata, outfile, digits):
    """Print the processed data table with LaTeX formatting.

    :param printdata: A list of lists, defining the table to print.
    :param outfile: The path to write the aggregated data table.
    :param digits: The number of digits to display.

    """
    #no padding necessary since this is a LaTeX table
    print >> outfile, '\\begin{table}[t]'
    print >> outfile, '\\centering'
    print >> outfile, '\\begin{tabular}{|l||',
    for dummy in range(len(printdata[0]) - 1):
        print >> outfile, 'r|',
    print >> outfile, '}'
    print >> outfile, '\\hline'

    #headings are found in the first row of printdata
    headings = printdata[0]
    print >> outfile, headings[0],
    for heading in headings[1:]:
        print >> outfile, ' & {}'.format(heading),
    print >> outfile, '\\\\'
    print >> outfile, '\\hline'

    for row in printdata[1:]:
        print >> outfile, row[0],
        for col in row[1:]:
            value = _format_cell(col, digits)
            print >> outfile, ' & {}'.format(value),
        print >> outfile, '\\\\'

    print >> outfile, '\\hline'
    print >> outfile, '\\end{{tabular}}'
    print >> outfile, '\\caption{{Insert a caption}}'
    print >> outfile, '\\label{{tab:table1}}'
    print >> outfile, '\\end{{table}}'


def _print_table(dbase, **kwargs):
    """Print a table of aggregate image comparison data.

    Since the database contains error data for several images, downsamplers,
    ratios, upsamplers, and metrics, it is convenient to be able to specify
    which of these to consider. This method aggregates the data for each
    relevant column in the appropriate tables.

    :param dbase: The database file.
    :param images: The list of image names.
    :param downsamplers: The list of downsampler names.
    :param ratios: The list of ratios in string form.
    :param upsamplers: The list of upsampler names.
    :param metrics_d: The dictionary of metrics.
    :param outfile: The name of the output file.
    :param digits: The number of digits to print.
    :param latex: If true, print a LaTeX-formatted table.
    :param rank: If true, print ranks instead of data.
    :param sort: The metric to sort by.
    :param show_sort: True if the sort column should be displayed.

    """
    # Get keyword arguments.
    images = kwargs.get('images', None)
    downsamplers = kwargs.get('downsamplers', None)
    ratios = kwargs.get('ratios', None)
    upsamplers = kwargs.get('upsamplers', None)
    metrics_d = kwargs.get('metrics_d', None)
    outfile = kwargs.get('outfile', None)
    digits = kwargs.get('digits', None)
    latex = kwargs.get('latex', False)
    rank = kwargs.get('rank', False)
    sort = kwargs.get('sort', None)
    show_sort = kwargs.get('show_sort', True)

    # Create list and string versions of the metric names.
    metrics = metrics_d.keys()
    metrics_str = ','.join(metrics)

    # Create a list of the sorting options for each metric.
    metrics_desc = []
    for metric in metrics:
        metrics_desc.append(int(metrics_d[metric][2]))

    # Determine the sort index.
    reverse_index = metrics.index(sort)
    sort_index = reverse_index + 1

    # See if the config file has been poorly edited by the user.
    if not (len(images) or len(downsamplers) or
            len(ratios) or len(upsamplers) or len(metrics)):
        return

    # Assemble a SELECT on TABLEDATA that returns table names to aggregate.
    query = 'SELECT name FROM TABLEDATA WHERE ('
    for image in images:
        query = ' '.join([query, 'image = \'{}\' OR'.format(image)])
    query = ''.join([query.rstrip(' OR'), ') AND ('])
    for downsampler in downsamplers:
        downsampler_str = 'downsampler = \'{}\' OR'.format(downsampler)
        query = ' '.join([query, downsampler_str])
    query = ''.join([query.rstrip(' OR'), ') AND ('])
    for ratio in ratios:
        query = ' '.join([query, 'ratio = \'{}\' OR'.format(ratio)])
    query = ''.join([query.rstrip(' OR'), ')'])
    tables = [table[0] for table in dbase.sql_fetchall(query)]

    # Setup a data structure (list of lists) to store aggregated data.
    header = ['upsampler']
    for metric in metrics:
        header.append(metric)
    printdata = []

    for upsampler in upsamplers:
        datarow = [upsampler]

        # Create a new dictionary.
        metric_lists = {}
        for metric in metrics:
            metric_lists[metric] = []
        for table in tables:
            row = dbase.get_error_data(table, upsampler, metrics_str)
            for metric in metrics:
                metric_lists[metric].append(row[metric])
        for metric in metrics:
            # Aggregate the error data using the appropriate method.
            metric_list = ' '.join(str(x) for x in metric_lists[metric])
            met = metrics_d[metric][1].format(metric_list).split()
            datarow.append(float(check_output(met)))
        printdata.append(datarow)

    if rank:
        # Modify the table so it contains ranks instead of data.
        printdata = _get_ranks(printdata, metrics_desc, sort_index)
        digits = 0
    else:
        # Sort by the specified index in the appropriate order.
        printdata.sort(
            key=itemgetter(sort_index),
            reverse=metrics_desc[reverse_index]
        )

    # Add the table headers.
    printdata.insert(0, header)

    # Remove the sort column if necessary.
    if not show_sort:
        for row in printdata:
            row.pop(sort_index)

    # Pass the printdata to the appropriate table printer.
    if latex:
        _print_latex(printdata, outfile, digits)
    else:
        _print_normal(printdata, outfile, digits)


def main():
    """Run exquires-report."""

    # Define the command-line argument parser.
    parser = argparse.ArgumentParser(
        version=VERSION,
        description=parsing.format_doc(__doc__),
        formatter_class=lambda prog: parsing.ExquiresHelp(prog,
                                                          max_help_position=36)
    )

    # Output options.
    parser.add_argument('-l', '--latex', action='store_true',
                        help='print a LaTeX formatted table')
    parser.add_argument('-r', '--rank', action='store_true',
                        help='display ranks instead of values')
    parser.add_argument('-p', '--proj', metavar='PROJECT', type=str,
                        action=parsing.ProjectParser,
                        help='name of the project (default: project1)')
    parser.add_argument('-s', '--sort', metavar='METRIC', type=str,
                        action=parsing.SortParser, default=None,
                        help='sort using this metric (default: first)')
    parser.add_argument('-d', '--digits', metavar='DIGITS',
                        type=int, choices=range(1, 16), default=4,
                        help='total number of digits (default: 4)')
    parser.add_argument('-f', '--file', metavar='FILE',
                        type=argparse.FileType('w'), default=sys.stdout,
                        help='output to file (default: sys.stdout)')

    # Aggregation options.
    parser.add_argument('-I', '--image', metavar='IMAGE',
                        type=str, nargs='+', action=parsing.ListParser,
                        help='images to consider (default: all)')
    parser.add_argument('-D', '--down', metavar='METHOD',
                        type=str, nargs='+', action=parsing.ListParser,
                        help='downsamplers to consider (default: all)')
    parser.add_argument('-R', '--ratio', metavar='RATIO',
                        type=str, nargs='+', action=parsing.RatioParser,
                        help='ratios to consider (default: all)')
    parser.add_argument('-U', '--up', metavar='METHOD',
                        type=str, nargs='+', action=parsing.ListParser,
                        help='upsamplers to consider (default: all)')
    parser.add_argument('-M', '--metric', metavar='METRIC',
                        type=str, nargs='+', action=parsing.ListParser,
                        help='metrics to consider (default: all)')

    # Pre-parse the command-line arguments.
    preparsed_args = sys.argv[1:]

    # Deal with the -h/--help  and -v/--version options.
    help_or_version = False
    for arg in preparsed_args:
        if arg == '-h' or arg == '--help' or arg == '-v' or arg == '--version':
            help_or_version = True
            break

    # Deal with the -p/--proj option.
    if not help_or_version:
        proj = False
        for i in range(0, len(preparsed_args) - 1):
            if preparsed_args[i] == '-p' or preparsed_args[i] == '--proj':
                preparsed_args.insert(0, preparsed_args.pop(i + 1))
                preparsed_args.insert(0, preparsed_args.pop(i + 1))
                proj = True
                break
        if not proj:
            preparsed_args.insert(0, 'project1')
            preparsed_args.insert(0, '--proj')

    # Make --sort the rightmost option.
    for i in range(2, len(preparsed_args) - 1):
        if preparsed_args[i] == '--sort':
            preparsed_args.append(preparsed_args.pop(i))
            preparsed_args.append(preparsed_args.pop(i))
            break

    # Attempt to parse the command-line arguments.
    try:
        args = parser.parse_args(preparsed_args)
    except argparse.ArgumentTypeError, error:
        parser.error(str(error))

    if not args.sort:
        args.sort = args.metric[0]

    # Everything is passed as a list except metrics, which is a dictionary.
    # Need to prune the dict first so it matches the argument list.
    met_d = _prune_metrics(args.metric, args.metrics_d)

    # Open the database connection.
    dbase = database.Database(args.dbase_file)

    # Print the aggregate data table.
    _print_table(dbase, images=args.image, downsamplers=args.down,
                 ratios=args.ratio, upsamplers=args.up, metrics_d=met_d,
                 outfile=args.file, digits=args.digits, latex=args.latex,
                 rank=args.rank, sort=args.sort, show_sort=args.show_sort)

    # Close the database connection.
    dbase.close()

if __name__ == '__main__':
    main()
