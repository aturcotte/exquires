#!/usr/bin/env python
# coding: utf-8
#
#  Copyright (c) 2012, Adam Turcotte (adam.turcotte@gmail.com)
#                      Nicolas Robidoux (nicolas.robidoux@gmail.com)
#  License: BSD 2-Clause License
#
#  This file is part of
#  EXQUIRES | EXtensible QUantitative Image Re-Enlargement Suite
#

"""Produce a Spearman's rank cross-correlation matrix for the specified group.

By default, the -M/--metric option is selected. You can select one of the
following cross-correlation groups:

 * -I/--image
 * -D/--down
 * -R/--ratio
 * -M/--metric

You can also select which upsamplers to consider when computing the matrix
by using the -U/--up option.

"""

import argparse

import numpy

from exquires import database, parsing, stats


def _get_group_and_ranks(args):
    """Private method to get the group and ranks.

    :param args.dbase_file: The database file.
    :param args.image: The list of selected image names.
    :param args.down: The list of selected downsampler names.
    :param args.ratio: The list of selected ratios in string form.
    :param args.up: The list of selected upsampler names.
    :param args.metric: The list of selected metric names.
    :param args.metrics_d: The dictionary of all metrics.
    :param args.file: The name of the output file.
    :param args.digits: The number of digits to print.
    :param args.latex: If true, print a LaTeX-formatted table.
    :param args.key: The key for the correlation group.

    """
    # Create a list of the sorting options for each metric.
    metrics_desc = []
    for metric in args.metric:
        metrics_desc.append(int(args.metrics_d[metric][2]))

    # See if the config file has been poorly edited by the user.
    if not (len(args.image) or len(args.down) or
            len(args.ratio) or len(args.up) or len(args.metric)):
        return

    # Open the database connection.
    dbase = database.Database(args.dbase_file)

    # Determine which cross-correlation to perform.
    group = getattr(args, args.key)
    ranks = []
    if args.key in ('image', 'down', 'ratio'):
        # Setup table arguments.
        table_args = argparse.Namespace()
        table_args.image = None
        table_args.down = None
        table_args.ratio = None

        for item in group:
            # Setup the tables to access.
            setattr(table_args, args.key, [item])
            agg_table = stats.get_aggregate_table(
                dbase, args.up, args.metrics_d, dbase.get_tables(table_args)
            )

            if ranks:
                col = stats.get_merged_ranks(agg_table, metrics_desc, 0)
                for i in range(0, len(args.up)):
                    ranks[i].append(col[i][1])
            else:
                ranks = stats.get_merged_ranks(agg_table, metrics_desc, 0)

    else:  # Cross-correlation group is 'metric'
        # Get the rank table.
        agg_table = stats.get_aggregate_table(
            dbase, args.up, args.metrics_d, dbase.get_tables(args)
        )
        ranks = stats.get_ranks(agg_table, metrics_desc, 0)

    # Close the database connection.
    dbase.close()

    # Return the group and ranks.
    return group, ranks


def _print_matrix(args):
    """Print a cross-correlation matrix from aggregate image comparison data.

    :param args.dbase_file: The database file.
    :param args.image: The list of selected image names.
    :param args.down: The list of selected downsampler names.
    :param args.ratio: The list of selected ratios in string form.
    :param args.up: The list of selected upsampler names.
    :param args.metric: The list of selected metric names.
    :param args.metrics_d: The dictionary of all metrics.
    :param args.file: The name of the output file.
    :param args.digits: The number of digits to print.
    :param args.latex: If true, print a LaTeX-formatted table.
    :param args.key: The key for the correlation group.
    :param args.anchor: The row/col to order the matrix by.

    """
    # Get the correlation group and ranks table.
    group, ranks = _get_group_and_ranks(args)

    # Compute the correlation coefficient matrix.
    matrix = numpy.identity(len(group))
    xbar = (len(args.up) + 1) * 0.5
    for i, mrow1 in enumerate(matrix):
        for j, mrow2 in enumerate(matrix[i + 1:], i + 1):
            # Compute the numerator and denominator.
            coeff = [0, 0, 0]
            for row in [rank_row[1:] for rank_row in ranks]:
                coeff[0] += (row[i] - xbar) * (row[j] - xbar)
                coeff[1] += (row[i] - xbar) ** 2
                coeff[2] += (row[j] - xbar) ** 2

            # Compute the correlation coefficient.
            mrow1[j] = mrow2[i] = (
                    coeff[0] / ((coeff[1] * coeff[2]) ** 0.5)
            )

    # Deal with -a/--anchor option.
    if args.anchor:
        sort_order = matrix[group.index(args.anchor)].argsort()[::-1]
        group = [group[i] for i in sort_order]
        matrix_sorted = numpy.identity(len(group))
        for i, row in enumerate(sort_order):
            for j, col in enumerate(sort_order):
                matrix_sorted[i, j] = matrix[row, col]
        matrix = matrix_sorted

    # Pass the coefficient matrix to the appropriate table printer.
    if args.latex:
        stats.print_latex(matrix, args, group, True)
    else:
        stats.print_normal(matrix, args, group, True)


def main():
    """Run exquires-correlate.

    Parse the command-line arguments and print the cross-correlation matrix.

    """
    _print_matrix(parsing.StatsParser(__doc__, True).parse_args())

if __name__ == '__main__':
    main()
