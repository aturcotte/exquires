#!/usr/bin/env python
# coding: utf-8
#
#  Copyright (c) 2012, Adam Turcotte (adam.turcotte@gmail.com)
#                      Nicolas Robidoux (nicolas.robidoux@gmail.com)
#  License: BSD 2-Clause License
#
#  This file is part of the
#  EXQUIRES (EXtensible QUantitative Image RESampling) suite
#

"""Compute new error data for changes to the user-specified project file.

The project file is inspected to determine which changes have been made. Items
that have been removed will result in entries being removed from the database.
Items that have been changed or added will result in new data being computed
and added to the database file. If no changes have been made to the project
file, the database will not be updated.

If you wish to recompute all data based on your project file rather than simply
updating it with the changes, use **exquires-run**.

To view aggregated error data, use **exquires-report**.

"""

import argparse

from configobj import ConfigObj

import exquires.operations as operations
import exquires.parsing as parsing


def _subtract(dict1, dict2):
    """Private method to subtract dictionary dict2 from dict1.

    :param dict1: The dictionary to subtract from.
    :param dict2: The dictionary to subtract.
    :return: The resulting dictionary.

    """
    result = {}
    for key in dict1.keys():
        if not key in dict2 or dict1[key] != dict2[key]:
            result[key] = dict1[key]
    return result


def _get_namespaces(config_file, config_bak):
    """Private method to get all necessary configuration namespaces.

    :param config_file: The current configuration file.
    :param config_bak: The previous configuration file.
    :return: The current, new, old, and same namespaces.

    """

    # Read the current configuration file.
    current = argparse.Namespace()
    config_current = ConfigObj(config_file)
    current.images = config_current['Images']
    current.ratios = config_current['Ratios']
    current.downsamplers = config_current['Downsamplers']
    current.upsamplers = config_current['Upsamplers']
    current.metrics = config_current['Metrics']

    # Read the configuration file last used to update the database.
    previous = argparse.Namespace()
    config_previous = ConfigObj(config_bak)
    previous.images = config_previous['Images']
    previous.ratios = config_previous['Ratios']
    previous.downsamplers = config_previous['Downsamplers']
    previous.upsamplers = config_previous['Upsamplers']
    previous.metrics = config_previous['Metrics']

    # Construct dictionaries from the current and previous configurations.
    new = argparse.Namespace()
    new.images = _subtract(current.images, previous.images)
    new.ratios = _subtract(current.ratios, previous.ratios)
    new.downsamplers = _subtract(current.downsamplers, previous.downsamplers)
    new.upsamplers = _subtract(current.upsamplers, previous.upsamplers)
    new.metrics = _subtract(current.metrics, previous.metrics)
    old = argparse.Namespace()
    old.images = _subtract(previous.images, current.images)
    old.ratios = _subtract(previous.ratios, current.ratios)
    old.downsamplers = _subtract(previous.downsamplers, current.downsamplers)
    same = argparse.Namespace()
    same.images = _subtract(current.images, new.images)
    same.ratios = _subtract(current.ratios, new.ratios)
    same.downsamplers = _subtract(current.downsamplers, new.downsamplers)
    same.upsamplers = _subtract(current.upsamplers, new.upsamplers)
    same.metrics = _subtract(current.metrics, new.metrics)

    # Return the namespaces.
    return current, new, old, same


def _update(args):
    """Update the database.

    :param args.config_file: The current configuration file.
    :param args.config_bak: The previous configuration file.

    """
    # Get the various namespaces for this project update.
    current, new, old, same = _get_namespaces(args.config_file,
                                              args.config_bak)
    args.met_same = same.metrics
    args.metrics = current.metrics

    # Define operations.
    same.up_obj = operations.Upsamplers(same.upsamplers, new.metrics, True)
    new.up_obj = operations.Upsamplers(new.upsamplers, current.metrics)
    current.up_obj = operations.Upsamplers(current.upsamplers, current.metrics)
    same.rat_obj = operations.Ratios(same.ratios,
                                     [same.up_obj, new.up_obj], True)
    new.rat_obj = operations.Ratios(new.ratios, [current.up_obj])
    current.rat_obj = operations.Ratios(current.ratios, [current.up_obj])
    same.down_obj = operations.Downsamplers(same.downsamplers,
                                            [same.rat_obj, new.rat_obj], True)
    new.down_obj = operations.Downsamplers(new.downsamplers, [current.rat_obj])
    current.down_obj = operations.Downsamplers(current.downsamplers,
                                               [current.rat_obj])
    same.img_obj = operations.Images(same.images,
                                     [same.down_obj, new.down_obj], True)
    new.img_obj = operations.Images(new.images, [current.down_obj])
    operations.Operations([same.img_obj, new.img_obj]).compute(args, old)


def main():
    """Run exquires-update.

    Update the project database based on changes to the project file.

    """
    _update(parsing.OperationsParser(__doc__, True).parse_args())

if __name__ == '__main__':
    main()
