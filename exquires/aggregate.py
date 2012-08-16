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

"""Aggregate a list of numbers using the specified method.

  **Aggregators:**

    ====== ==============================================
    NAME   DESCRIPTION
    ====== ==============================================
    l_1    return the average
    l_2    average the squares and return the square root
    l_4    average the quads and return the fourth root
    l_inf  return the maximum
    ====== ==============================================

"""

import inspect

import numpy

from exquires import parsing


class Aggregate(object):

    """This class provide various ways of aggregating error data.

    :param values: numbers to aggregate
    :type values:  `list of numbers`

    """

    def __init__(self, values):
        """Create a new :class:`Aggregate` object."""
        self.values = values

    def l_1(self):
        """Return the average.

        :return: the average
        :rtype:  `float`

        """
        return numpy.average(self.values)

    def l_2(self):
        """Average the squares and return the square root.

        :return: the square root of the average of the squares
        :rtype:  `float`

        """
        return numpy.average(numpy.power(self.values, 2)) ** 0.5

    def l_4(self):
        """Average the quads and return the fourth root.

        :return: the fourth root of the average of the quads
        :rtype:  `float`

        """
        return numpy.average(numpy.power(self.values, 4)) ** 0.25

    def l_inf(self):
        """Return the maximum.

        :return: the maximum
        :rtype:  `float`

        """
        return max(self.values)


def main():
    """Run :ref:`exquires-aggregate`."""

    # Obtain a list of aggregation methods that can be called.
    aggregators = []
    methods = inspect.getmembers(Aggregate, predicate=inspect.ismethod)
    for method in methods[1:]:
        aggregators.append(method[0])

    # Define the command-line argument parser.
    parser = parsing.ExquiresParser(description=__doc__)
    parser.add_argument('method', metavar='METHOD', choices=aggregators,
                        help='the type of aggregation to use')
    parser.add_argument('values', metavar='NUM', type=float, nargs='+',
                         help='number to include in aggregation')

    # Attempt to parse the command-line arguments.
    args = parser.parse_args()

    # Print the result with 15 digits after the decimal.
    aggregation = Aggregate(args.values)
    print '%.15f' % getattr(aggregation, args.method)()

if __name__ == '__main__':
    main()
