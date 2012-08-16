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

"""Print a formatted table of aggregate image difference data.

Each database table in the current project contains data for a single image,
downsampler, and ratio. Each row represents an upsampler and each column
represents a difference metric. By default, the data across all rows and
columns of all tables is aggregated. Use the appropriate option flags to
aggregate across a subset of the database.

  **Features:**

    * :option:`-R`/:option`--ratio` supports hyphenated ranges
      (for example, '1-3 5' gives '1 2 3 5')
    * :option:`-U`/:option:`--up`, :option:`-I`/:option:`--image`,
      :option:`-D`/:option:`--down` and :option:`-M`/:option:`--metric`
      support wildcard characters

"""

from operator import itemgetter

from exquires import database, parsing, stats


def _print_table(args):
    """Print a table of aggregate image comparison data.

    Since the database contains error data for several images, downsamplers,
    ratios, upsamplers, and metrics, it is convenient to be able to specify
    which of these to consider. This method aggregates the data for each
    relevant column in the appropriate tables.

    .. note::

        This is a private function called by :func:`main`.

    :param args:            arguments
    :param args.dbase_file: database file
    :param args.image:      selected image names
    :param args.down:       selected downsampler names
    :param args.ratio:      selected ratios
    :param args.up:         selected upsampler names
    :param args.metric:     selected metric names
    :param args.metrics_d:  all metric names
    :param args.file:       output file
    :param args.digits:     number of digits to print
    :param args.latex:      `True` if printing a LaTeX-formatted table
    :param args.rank:       `True` if printing Spearman (fractional) ranks
    :param args.merge:      `True` if printing merged Spearman ranks
    :param args.sort:       metric to sort by
    :param args.show_sort:  `True` if the sort column should be displayed
    :type args:             :class:`argparse.Namespace`
    :type args.dbase_file:  `path`
    :type args.image:       `list of strings`
    :type args.down:        `list of strings`
    :type args.ratio:       `list of strings`
    :type args.up:          `list of strings`
    :type args.metric:      `list of strings`
    :type args.metrics_d:   `dict`
    :type args.file:        `path`
    :type args.digits:      `integer`
    :type args.latex:       `boolean`
    :type args.rank:        `boolean`
    :type args.merge:       `boolean`
    :type args.sort:        `string`
    :type args.show_sort:   `boolean`

    """
    # Create a list of the sorting options for each metric.
    metrics_desc = []
    for metric in args.metric:
        metrics_desc.append(int(args.metrics_d[metric][2]))

    # Determine the sort index.
    reverse_index = args.metric.index(args.sort)
    sort_index = reverse_index + 1

    # See if the config file has been poorly edited by the user.
    if not (len(args.image) or len(args.down) or
            len(args.ratio) or len(args.up) or len(args.metric)):
        return

    # Open the database connection.
    dbase = database.Database(args.dbase_file)

    # Get a list of table names to aggregate across.
    tables = dbase.get_tables(args)

    # Get the table (list of lists) of aggregate image difference data.
    printdata = stats.get_aggregate_table(dbase, args.up,
                                          args.metrics_d, tables)

    # Close the database connection.
    dbase.close()

    if args.rank:
        # Modify the table so it contains Spearman ranks instead of data.
        printdata = stats.get_ranks(printdata, metrics_desc, sort_index)
    elif args.merge:
        # Modify the table so it contains merged ranks instead of data.
        printdata = stats.get_merged_ranks(printdata, metrics_desc, 1)
    else:
        # Sort by the specified index in the appropriate order.
        printdata.sort(key=itemgetter(sort_index),
                       reverse=metrics_desc[reverse_index])

    # Add the table headers.
    if args.merge:
        header = ['upsampler', 'rank']
    else:
        header = ['upsampler']
        for metric in args.metric:
            header.append(metric)

        # Remove the sort column if necessary.
        if not args.show_sort:
            header.pop(1)
            for row in printdata:
                row.pop(sort_index)

    # Pass the printdata to the appropriate table printer.
    if args.latex:
        stats.print_latex(printdata, args, header)
    else:
        stats.print_normal(printdata, args, header)


def main():
    """Run :ref:`exquires-report`.

    Parse the command-line arguments and print the aggregate data table.

    """
    _print_table(parsing.StatsParser(__doc__).parse_args())

if __name__ == '__main__':
    main()
