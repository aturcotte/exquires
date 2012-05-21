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
import os
import re
import shutil
from subprocess import call, check_output

from configobj import ConfigObj

from database import Database
from progress import Progress
from parsing import format_doc, ExquiresHelp
from __init__ import __version__ as VERSION


def _subtract(d1, d2):
    """Private method to subtract dictionary d2 from d1.

    :param d1: The dictionary to subtract from.
    :param d2: The dictionary to subtract.
    :return: The resulting dictionary.

    """
    result = {}
    for key in d1.keys():
        if not key in d2 or d1[key] != d2[key]:
            result[key] = d1[key]
    return result

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
    config_file = '.'.join([args.proj, 'ini'])
    config_backup_file = '.'.join([args.proj, 'ini', 'bak'])

    # Construct the path to the generated image files.
    gen_images_path = args.proj

    # Report an error if the configuration file does not exist.
    if not os.path.isfile(config_file):
        parser.error(' '.join(['unrecognized project:', args.proj]))

    # Determine if the database can be updated.
    if not (os.path.isfile(config_backup_file) and
            os.path.isfile(db_file) and
            os.path.isdir(args.proj)):
        parser.error(' '.join([args.proj, 'has not been run']))

    # Read the configuration file.
    config = ConfigObj(config_file)
    images = config['Images']
    ratios = config['Ratios']
    downsamplers = config['Downsamplers']
    upsamplers = config['Upsamplers']
    metrics = config['Metrics']

    # Read the configuration file last used to update the database.
    config_previous = ConfigObj(config_backup_file)
    images_previous = config_previous['Images']
    ratios_previous = config_previous['Ratios']
    downsamplers_previous = config_previous['Downsamplers']
    upsamplers_previous = config_previous['Upsamplers']
    metrics_previous = config_previous['Metrics']

    # Construct dictionaries from the current and previous configurations.
    images_new = _subtract(images, images_previous)
    images_old = _subtract(images_previous, images)
    images_same = _subtract(images, images_new)
    ratios_new = _subtract(ratios, ratios_previous)
    ratios_old = _subtract(ratios_previous, ratios)
    ratios_same = _subtract(ratios, ratios_new)
    downsamplers_new = _subtract(downsamplers, downsamplers_previous)
    downsamplers_old = _subtract(downsamplers_previous, downsamplers)
    downsamplers_same = _subtract(downsamplers, downsamplers_new)
    upsamplers_new = _subtract(upsamplers, upsamplers_previous)
    upsamplers_same = _subtract(upsamplers, upsamplers_new)
    metrics_new = _subtract(metrics, metrics_previous)
    metrics_same = _subtract(metrics, metrics_new)

    # Create a string version of the unchanged metric names.
    metrics_str = ','.join(metrics_same)

    # Count number of operations and exit if there are none.
    downsamples = (len(images_same) *
                      (len(downsamplers_same) * len(ratios_new) +
                       len(downsamplers_new) * len(ratios)) +
                   len(images_new) * len(downsamplers) * len(ratios))
    upsamples_same = (len(images_same) * len(downsamplers_same) *
                      len(ratios_same) * len(upsamplers_same))
    upsamples = (len(images) * len(downsamplers) *
                 len(ratios) * len(upsamplers) -
                 upsamples_same)
    compares = upsamples * len(metrics)
    if len(metrics_new):
        upsamples += upsamples_same
        compares += upsamples_same * len(metrics_new)
    ops = downsamples + upsamples + compares
    if not ops:
        return

    # Setup progress indicator.
    if not args.silent:
        from progress import Progress
        p = Progress(os.path.basename(__file__), args.proj, ops)
        def prog(image, downsampler, ratio, upsampler=None, metric=None):
            p.do_op(image, downsampler, ratio, upsampler, metric)
        def cleanup():
            p.cleanup()
        def complete():
            p.complete()
    else:
        prog = lambda *a: None
        cleanup = lambda *a: None
        complete = lambda *a: None

    # Open the database connection.
    db = Database(db_file)

    # Indicate that old files are being deleted.
    cleanup()

    # Remove tables that have been removed from the configuration file.
    db.drop_tables(images_old, downsamplers_old, ratios_old)

    # Delete all images and directories that are no longer needed.
    for image in images_old:
        image_dir = os.path.join(gen_images_path, image)
        shutil.rmtree(image_dir, True)
    for image in images_same:
        image_dir = os.path.join(gen_images_path, image)
        for downsampler in downsamplers_old:
            downsampler_dir = os.path.join(image_dir, downsampler)
            shutil.rmtree(downsampler_dir, True)
        for downsampler in downsamplers_same:
            downsampler_dir = os.path.join(image_dir, downsampler)
            for ratio in ratios_old:
                ratio_file = '.'.join([ratio, 'tif'])
                os.remove(os.path.join(downsampler_dir, ratio_file))

    # Alter tables and add new tables for the unchanged images.
    for image in images_same:
        image_dir = os.path.join(gen_images_path, image)
        IMAGE = images[image]
        MASTER = '.'.join([os.path.join(image_dir, 'master'), 'tif'])

        # Alter tables and add new tables for the unchanged downsamplers.
        for downsampler in downsamplers_same:
            DOWN = downsamplers[downsampler]
            downsampler_dir = os.path.join(image_dir, downsampler)

            # Alter tables for the unchaged ratios.
            for ratio in ratios_same:
                TABLE = '_'.join([image, downsampler, ratio])
                TABLE_OLD = '_'.join([TABLE, 'old'])
                SIZE = ratios[ratio]
                filename = '.'.join([ratio, 'tif'])
                SMALL = os.path.join(downsampler_dir, filename)

                # Backup the old table.
                db.backup_table(TABLE, TABLE_OLD, metrics)

                # Create a directory for this ratio.
                ratio_dir = os.path.join(downsampler_dir, ratio)
                if not os.path.isdir(ratio_dir):
                    os.makedirs(ratio_dir)

                # Update the existing rows (upsamplers_same).
                for upsampler in upsamplers_same:
                    UP = upsamplers[upsampler]
                    filename = '.'.join([upsampler, 'tif'])
                    LARGE = os.path.join(os.path.dirname(SMALL),
                                         ratio, filename)
                    ROW = db.get_error_data(TABLE_OLD, upsampler, metrics_str)

                    # Upsample ratio.tif back to 840 using upsampler.
                    #  {0} INPUT_IMAGE (SMALL)
                    #  {1} OUTPUT_IMAGE (LARGE)
                    #  {2} UPSAMPLING RATIO
                    #  {3} UPSAMPLED_SIZE (always 840)
                    if len(metrics_new) > 0:
                        prog(image, downsampler, ratio, upsampler)
                        call(UP.format(SMALL, LARGE, ratio, 840).split())

                    for metric in metrics_new:
                        METRIC = metrics[metric][0]

                        # Compare master.tif to upsampler.tif.
                        #  {0} REFERENCE_IMAGE (MASTER)
                        #  {1} TEST_IMAGE (LARGE)
                        prog(image, downsampler, ratio, upsampler, metric)
                        cmd = METRIC.format(MASTER, LARGE)
                        ROW[metric] = float(check_output(cmd.split()))

                    db.insert(TABLE, ROW)

                # Delete the backup table.
                db.drop_backup(TABLE_OLD)

                # Add the new rows (upsamplers_new)
                for upsampler in upsamplers_new:
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

                    # Add row to the table and delete the upsampled image.
                    db.insert(TABLE, ROW)
                    os.remove(LARGE)

                # Remove the directory for this ratio.
                shutil.rmtree(ratio_dir, True)

            # Create tables for unchanged images/downsamplers with new ratios.
            for ratio in ratios_new:
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
                db.add_table(image, downsampler, ratio, metrics)

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

        # Create new tables for unchanged images with new downsamplers.
        for downsampler in downsamplers_new:
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
                db.add_table(image, downsampler, ratio, metrics)

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

    # Create the new error tables for the new images.
    for image in images_new:
        image_dir = os.path.join(gen_images_path, image)
        IMAGE = images_new[image]
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
                db.add_table(image, downsampler, ratio, metrics)

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
