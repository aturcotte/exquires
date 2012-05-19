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

import argparse
import os
import shutil
from subprocess import call, check_output

from configobj import ConfigObj

from database import Database
from help import format_doc, ExquiresHelp
from __init__ import __version__ as VERSION


def main():
    # Define the command-line argument parser.
    parser = argparse.ArgumentParser(version=VERSION,
                                     description=format_doc(__doc__),
                                     formatter_class=ExquiresHelp)
    parser.add_argument('-s', '--silent', action='store_true',
                        help='do not display progress information')
    parser.add_argument('-p', '--proj', metavar='PROJECT',
                        type=str, default='project1',
                        help='name of the project (default: project1)')

    # Attempt to parse the command-line arguments.
    try:
        args = parser.parse_args()
    except Exception, e:
        parser.error(str(e))

    # Construct the path to the configuration and database files.
    db_file = '.'.join([args.proj, 'db'])
    db_backup_file = '.'.join([args.proj, 'db', 'bak'])
    config_file = '.'.join([args.proj, 'cfg'])
    config_backup_file = '.'.join([args.proj, 'cfg', 'bak'])

    # Construct the path to the generated image files.
    gen_images_path = args.proj

    # Report an error if the configuration file does not exist.
    if not os.path.isfile(config_file):
        parser.error(' '.join(['unrecognized project:', args.proj]))

    # Create the project folder if it does not exist.
    if not os.path.isdir(args.proj):
        os.makedirs(gen_images_path)

    # Read the configuration file.
    config = ConfigObj(config_file)
    images = config['Images']
    ratios = config['Ratios']
    downsamplers = config['Downsamplers']
    upsamplers = config['Upsamplers']
    metrics = config['Metrics']

    # Count number of operations and exit if there are none.
    downsamples = len(images) * len(downsamplers) * len(ratios)
    upsamples = downsamples * len(upsamplers)
    compares = upsamples * len(metrics)
    ops = downsamples + upsamples + compares
    if not ops:
        return

    # Setup verbose mode.
    if not args.silent:
        from progress import Progress
        p = Progress(os.path.basename(__file__), args.proj, ops)
        def prog(image, downsampler, ratio, upsampler=None, metric=None):
            p.do_op(image, downsampler, ratio, upsampler, metric)
        def complete():
            p.complete()
    else:
        prog = lambda *a: None
        complete = lambda *a: None

    # Create a new database file, backing up any that already exists.
    if os.path.isfile(db_file):
        os.rename(db_file, db_backup_file)
    db = Database(db_file)

    # Create the new error tables.
    for image in images:
        image_dir = os.path.join(gen_images_path, image)
        IMAGE = images[image]
        MASTER = os.path.join(image_dir, 'master.tif')

        # Create a new directory for this image if it does not exist.
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        # Make a copy of the test image.
        shutil.copyfile(IMAGE, MASTER)

        for downsampler in downsamplers:
            DOWN = downsamplers[downsampler]

            # Create a directory for this downsampler if necessary.
            downsampler_dir = os.path.join(image_dir, downsampler)
            if not os.path.exists(downsampler_dir):
                os.makedirs(downsampler_dir)

            for ratio in ratios:
                TABLE = '_'.join([image, downsampler, ratio])
                SIZE = ratios[ratio]
                filename = '.'.join([ratio, 'tif'])
                SMALL = os.path.join(downsampler_dir, filename)

                # Create a directory for this ratio.
                ratio_dir = os.path.join(downsampler_dir, ratio)
                if not os.path.isdir(ratio_dir):
                    os.makedirs(ratio_dir)

                # Downsample master.tif by ratio using downsampler.
                #  {0} INPUT_IMAGE (MASTER)
                #  {1} OUTPUT_IMAGE (SMALL)
                #  {2} DOWNSAMPLING RATIO
                #  {3} DOWNSAMPLED SIZE (width or height)
                prog(image, downsampler, ratio)
                call(DOWN.format(MASTER, SMALL, ratio, SIZE).split())

                # Create a new database table.
                name = db.add_table(image, downsampler, ratio, metrics)

                for upsampler in upsamplers:
                    UP = upsamplers[upsampler]
                    filename = '.'.join([upsampler, 'tif'])
                    LARGE = os.path.join(os.path.dirname(SMALL),
                                         ratio, filename)
                    ROW = dict(upsampler=upsampler)

                    # Upsample ratio.tif back to 840 using upsampler.
                    #  {0} INPUT_IMAGE (SMALL)
                    #  {1} OUTPUT_IMAGE (LARGE)
                    #  {2} UPSAMPLING RATIO
                    #  {3} UPSAMPLED_SIZE (always 840)
                    prog(image, downsampler, ratio, upsampler)
                    call(UP.format(SMALL, LARGE, ratio, 840).split())

                    for metric in metrics:
                        METRIC = metrics[metric][0]

                        # Compare master.tif to upsampler.tif.
                        #  {0} REFERENCE_IMAGE (MASTER)
                        #  {1} TEST_IMAGE (LARGE)
                        prog(image, downsampler, ratio, upsampler, metric)
                        cmd = METRIC.format(MASTER, LARGE)
                        ROW[metric] = float(check_output(cmd.split()))

                    # Add the row to the table and delete the upsampled image.
                    db.insert(TABLE, ROW)
                    os.remove(LARGE)

                # Remove the directory for this ratio.
                shutil.rmtree(ratio_dir, True)

    # Backup the configuration file and close the database connection.
    shutil.copyfile(config_file, config_backup_file)
    db.close()
    complete()

if __name__ == '__main__':
    main()
