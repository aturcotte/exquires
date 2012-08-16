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

"""A collection of convenience methods."""

from collections import OrderedDict
import os


def prune_metrics(keys, metrics_d):
    """Prune a dictionary of metrics using a list of keys.

    :param keys:      keys to retain
    :param metrics_d: metrics to prune
    :type keys:       `list of strings`
    :type metrics_d:  `dict`

    :return:          pruned metrics
    :rtype:           `dict`

    """
    result = OrderedDict()
    for key in keys:
        result[key] = metrics_d[key]
    return result


def create_dir(base_dir, relative_dir=''):
    """Create a directory if it doesn't already exist and return it.

    :param base_dir:     base directory within which to create the directory
    :param relative_dir: directory to create inside the base directory
    :type base_dir:      `path`
    :type relative_dir:  `path`

    :return:             the created directory
    :rtype:              `path`

    """
    directory = os.path.join(base_dir, relative_dir)
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory
