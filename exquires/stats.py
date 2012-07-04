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

"""A collection of methods for producing statistical output."""

from math import fabs
from operator import itemgetter
from subprocess import check_output

import numpy


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


def print_normal(printdata, args, header, matrix=False):
    """Print the processed data table with normal formatting.

    :param printdata: A list of lists, defining the table to print.
    :param args.file: The path to write the aggregated error table.
    :param args.digits: The maximum number of digits to display.
    :param header: A list of table headings.
    :param matrix: True if printing a correlation matrix.

    """
    # Compute the column widths (padding).
    pad = [max(len(header[0]), max(len(row[0]) for row in printdata))]
    pad[1:] = [max(args.digits + 1, len(head)) for head in header[1:]]

    # Print the header.
    if matrix:
        index = 0
        print >> args.file, ''.ljust(pad[0]),
    else:
        index = 1
        print >> args.file, header[0].ljust(pad[0]),
    for i, heading in enumerate(header[index:], index):
        print >> args.file, heading.rjust(pad[i] + 1),
    print >> args.file

    # Print the remaining rows.
    for j, row in enumerate(printdata):
        # Print the cell for the left column.
        if matrix:
            print >> args.file, header[j].ljust(pad[0]),
        else:
            print >> args.file, row[0].ljust(pad[0]),

        # Print the cells for the remaining columns.
        for i, cell in enumerate(row[index:], index):
            print >> args.file, _format_cell(
                    cell, args.digits).rjust(pad[i] + 1),
        print >> args.file


def print_latex(printdata, args, header, matrix=False):
    """Print the processed data table with LaTeX formatting.

    :param printdata: A list of lists, defining the table to print.
    :param args.file: The path to write the aggregated data table.
    :param args.digits: The number of digits to display.
    :param header: A list of table headings.

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

    :param printdata: A list of lists, defining the table to print.
    :param metrics_desc: A list of 0s and 1s (where 1 is 'descending').
    :param sort_index: Index of the column to sort by.
    :return: A table of ranks.

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

    :param printdata: A list of lists, defining the table to print.
    :param metrics_desc: A list of 0s and 1s (where 1 is 'descending').
    :param sort_index: Index of the column to sort by (0 or 1).
    :return: A table of ranks.

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

    :param upsamplers: The upsamplers (rows) of the table.
    :param metrics_d: The metrics (columns) of the table in dictionary form.
    :param tables: The database tables to aggregate across.
    :return: The table of aggregate image difference data.

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
