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

"""A collection of methods for producing statistical output."""

from operator import itemgetter
from subprocess import check_output

import numpy


def _format_cell(cell, digits):
    """Return a formatted version of this cell of the data table.

    .. note::

        This is a private function called by :func:`print_normal`
        and :func:`print_latex`.

    :param cell:   cell to format
    :param digits: maximum number of digits to display
    :type cell:    `string`
    :type digits:  `integer`

    :return:       the formatted cell
    :rtype:        `string`

    """
    try:
        value = str(float(cell))
        if value[0] is '0':
            return value[1:digits + 2]
        elif value[0] is '-':
            if value[1] is '0':
                return ''.join(['-', value[2:digits + 3]])
            return value[:digits + 2]
        return value[:digits + 1]
    except ValueError:
        # Cell is not a float.
        return cell


def print_normal(printdata, args, header, matrix=False):
    """Print the processed data table with normal formatting.

    :param printdata:   table of data to print
    :param args:        arguments
    :param args.file:   path to write the aggregated error table
    :param args.digits: maximum number of digits to display
    :param header:      table headings
    :param matrix:      `True` if printing a correlation matrix
    :type printdata:    `list of lists`
    :type args:         :class:`argparse.Namespace`
    :type args.file:    `path`
    :type args.digits:  `integer`
    :type header:       `list of strings`
    :type matrix:       `boolean`

    """
    # Print the header.
    if matrix:
        index = 0
        pad = [max((len(head) for head in header))]
        print >> args.file, ''.ljust(pad[0]),
    else:
        index = 1
        pad = [max(len(header[0]), max(len(str(row[0])) for row in printdata))]
        print >> args.file, header[0].ljust(pad[0]),
    pad[1:] = [max(args.digits + 2, len(head)) for head in header[index:]]
    for i, heading in enumerate(header[index:], 1):
        print >> args.file, heading.rjust(pad[i] + 1),
    print >> args.file

    # Print the remaining rows.
    for j, row in enumerate(printdata):
        # Print the cell for the left column.
        if matrix:
            print >> args.file, header[j].ljust(pad[0]),
        else:
            print >> args.file, str(row[0]).ljust(pad[0]),

        # Print the cells for the remaining columns.
        for i, cell in enumerate(row[index:], 1):
            print >> args.file, _format_cell(
                    cell, args.digits).rjust(pad[i] + 1),
        print >> args.file


def print_latex(printdata, args, header, matrix=False):
    """Print the processed data table with LaTeX formatting.

    :param printdata:   table of data to print
    :param args:        arguments
    :param args.file:   path to write the aggregated error table
    :param args.digits: maximum number of digits to display
    :param header:      table headings
    :param matrix:      `True` if printing a correlation matrix
    :type printdata:    `list of lists`
    :type args:         :class:`argparse.Namespace`
    :type args.file:    `path`
    :type args.digits:  `integer`
    :type header:       `list of strings`
    :type matrix:       `boolean`

    """
    # No padding is necessary since this is a LaTeX table.
    print >> args.file, '\\begin{table}[t]'
    print >> args.file, '\\centering'
    print >> args.file, '\\begin{tabular}{|l||',
    for dummy in range(len(printdata[0]) - 1):
        print >> args.file, 'r|',
    print >> args.file, '}'
    print >> args.file, '\\hline'

    # Print the header.
    if matrix:
        index = 0
    else:
        index = 1
        print >> args.file, header[0],
    for heading in header[index:]:
        print >> args.file, ' & {}'.format(heading),
    print >> args.file, '\\\\'
    print >> args.file, '\\hline'

    # Print the remaining rows.
    for j, row in enumerate(printdata):
        # Print the cell for the left column.
        if matrix:
            print >> args.file, header[j],
        else:
            print >> args.file, row[0],

        # Print the cells for the remaining columns.
        for cell in row[index:]:
            print >> args.file, ' & {}'.format(
                    _format_cell(cell, args.digits)
            ),
        print >> args.file, '\\\\'

    print >> args.file, '\\hline'
    print >> args.file, '\\end{{tabular}}'
    print >> args.file, '\\caption{{Insert a caption}}'
    print >> args.file, '\\label{{tab:table1}}'
    print >> args.file, '\\end{{table}}'


def get_ranks(printdata, metrics_desc, sort_index):
    """Return a table of Spearman (Fractional) ranks based on a data table.

    :param printdata:    table of data to print
    :param metrics_desc: list of 0s and 1s (where 1 is 'descending')
    :param sort_index:   index of the column to sort by
    :type printdata:     `list of lists`
    :type metrics_desc:  `list of integers`
    :type sort_index:    `integer`

    :return:             table of ranks
    :rtype:              `list of lists`

    """
    data = [x[:] for x in printdata]
    for j in range(1, len(printdata[0])):
        data.sort(key=itemgetter(j), reverse=metrics_desc[j - 1])
        i = 0
        end = len(printdata) - 1
        while i <= end:
            if i == end or data[i][j] != data[i + 1][j]:
                data[i][j] = i + 1
                i += 1
            else:  # We have at least one tie.
                matches = 1
                for k in range(i + 2, len(printdata)):
                    if data[i][j] != data[k][j]:
                        break
                    matches += 1
                rank = i + 1 + matches * 0.5
                for k in range(i, i + 1 + matches):
                    data[k][j] = rank
                i += matches + 1

    data.sort(key=itemgetter(sort_index))
    return data


def get_merged_ranks(printdata, metrics_desc, sort_index):
    """Return a table of merged Spearman ranks based on a data table.

    :param printdata:    table of data to print
    :param metrics_desc: list of 0s and 1s (where 1 is 'descending')
    :param sort_index:   index of the column to sort by
    :type printdata:     `list of lists`
    :type metrics_desc:  `list of integers`
    :type sort_index:    `integer`

    :return:             table of merged ranks
    :rtype:              `list of lists`

    """
    # Get the Spearman (Fractional) ranks.
    data = get_ranks(printdata, metrics_desc, sort_index)

    # Combine the ranks into a single column.
    for row in data:
        row[1:] = [numpy.average(row[1:])]

    # Convert the averages back into ranks.
    return get_ranks(data, [0], sort_index)


def get_aggregate_table(dbase, upsamplers, metrics_d, tables):
    """Return a table of aggregate image difference data.

    :param dbase:      connected database
    :param upsamplers: upsamplers (rows) of the table
    :param metrics_d:  metrics (columns) of the table in dictionary form
    :param tables:     names of database tables to aggregate across
    :type dbase:       :class:`database.Database`
    :type upsamplers:  `list of strings`
    :type metrics_d:   `dict`
    :type tables:      `list of strings`

    :return:           table of aggregate image difference data
    :rtype:            `list of lists`

    """
    metrics = metrics_d.keys()
    metrics_str = ','.join(metrics)
    aggregate_table = []
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
        aggregate_table.append(datarow)

    # Return the table of aggregate image difference data.
    return aggregate_table
