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

"""Compute error data for the entries in the specified project file.

The project file is read to determine which images, downsamplers, ratios,
upsamplers, and metrics to use. If a database file already exists for this
project, it will be backed up and a new one will be created.

Each image will be downsampled by each of the ratios using each of the
downsamplers. The downsampled images will then be upsampled back to their
original size (840x840) using each of the upsamplers. The upsampled images will
be compared to the original images using each of the metrics and the results
will be stored in the database file.

If you make changes to the project file and wish to only compute data for these
changes rather than recomputing everything, use **exquires-update**.

To view aggregated error data, use **exquires-report**.

"""

from configobj import ConfigObj

from exquires import operations, parsing


def _run(args):
    """Create a new project database.

    :param args.config_file: The current configuration file.

    """
    # Read the configuration file.
    config = ConfigObj(args.config_file)
    args.metrics = config['Metrics']

    # Define operations.
    operations.Operations(
        [operations.Images(config['Images'],
            [operations.Downsamplers(config['Downsamplers'],
                [operations.Ratios(config['Ratios'],
                    [operations.Upsamplers(config['Upsamplers'],
                        args.metrics)])])])]
    )

    # Perform operations.
    operations.Operations(
            [operations.Images(config['Images'],
            [operations.Downsamplers(config['Downsamplers'],
            [operations.Ratios(config['Ratios'],
            [operations.Upsamplers(config['Upsamplers'], args.metrics)])])])]
    ).compute(args)


def main():
    """Run exquires-run.

    Create a project database based on the project file.

    """
    _run(parsing.OperationsParser(__doc__).parse_args())

if __name__ == '__main__':
    main()
