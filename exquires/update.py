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
import shutil
from subprocess import call, check_output

from configobj import ConfigObj

import database
import parsing
import progress
from __init__ import __version__ as VERSION


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


def main():
    """Run exquires-update."""

    # Define the command-line argument parser.
    parser = argparse.ArgumentParser(version=VERSION,
                                     description=parsing.format_doc(__doc__),
                                     formatter_class=parsing.ExquiresHelp)
    parser.add_argument('-s', '--silent', action='store_true',
                        help='do not display progress information')
    parser.add_argument('-p', '--proj', metavar='PROJECT',
                        type=str, default='project1',
                        help='name of the project (default: project1)')

    # Attempt to parse the command-line arguments.
    try:
        args = parser.parse_args()
    except argparse.ArgumentTypeError, error:
        parser.error(str(error))

    # Construct the path to the configuration and database files.
    dbase_file = '.'.join([args.proj, 'db'])
    config_file = '.'.join([args.proj, 'ini'])
    config_backup_file = '.'.join([args.proj, 'ini', 'bak'])

    # Construct the path to the generated image files.
    gen_images_path = args.proj

    # Report an error if the configuration file does not exist.
    if not os.path.isfile(config_file):
        parser.error(' '.join(['unrecognized project:', args.proj]))

    # Determine if the database can be updated.
    if not (os.path.isfile(config_backup_file) and
            os.path.isfile(dbase_file) and
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
        prg = progress.Progress(os.path.basename(__file__), args.proj, ops)
        prog = lambda *a, **k: prg.do_op(*a, **k)
        cleanup = lambda: prg.cleanup()
        complete = lambda: prg.complete()
    else:
        prog = lambda *a, **k: None
        cleanup = lambda: None
        complete = lambda: None

    # Open the database connection.
    dbase = database.Database(dbase_file)

    # Indicate that old files are being deleted.
    cleanup()

    # Remove tables that have been removed from the configuration file.
    dbase.drop_tables(images_old, downsamplers_old, ratios_old)

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
        image_path = images[image]
        master = '.'.join([os.path.join(image_dir, 'master'), 'tif'])

        # Alter tables and add new tables for the unchanged downsamplers.
        for downsampler in downsamplers_same:
            down_path = downsamplers[downsampler]
            downsampler_dir = os.path.join(image_dir, downsampler)

            # Alter tables for the unchaged ratios.
            for ratio in ratios_same:
                table = '_'.join([image, downsampler, ratio])
                table_old = '_'.join([table, 'old'])
                size = ratios[ratio]
                filename = '.'.join([ratio, 'tif'])
                small = os.path.join(downsampler_dir, filename)

                # Backup the old table.
                dbase.backup_table(table, table_old, metrics)

                # Create a directory for this ratio.
                ratio_dir = os.path.join(downsampler_dir, ratio)
                if not os.path.isdir(ratio_dir):
                    os.makedirs(ratio_dir)

                # Update the existing rows (upsamplers_same).
                for upsampler in upsamplers_same:
                    up_path = upsamplers[upsampler]
                    filename = '.'.join([upsampler, 'tif'])
                    large = os.path.join(os.path.dirname(small),
                                         ratio, filename)
                    row = dbase.get_error_data(table_old, upsampler,
                                               metrics_str)

                    # Upsample ratio.tif back to 840 using upsampler.
                    #  {0} input image path (small)
                    #  {1} output image path (large)
                    #  {2} upsampling ratio
                    #  {3} upsampled size (always 840)
                    if len(metrics_new) > 0:
                        prog(image, downsampler, ratio, upsampler)
                        call(up_path.format(small, large, ratio, 840).split())

                    for metric in metrics_new:
                        metric_path = metrics[metric][0]

                        # Compare master.tif to upsampler.tif.
                        #  {0} reference image path (master)
                        #  {1} test image path (large)
                        prog(image, downsampler, ratio, upsampler, metric)
                        cmd = metric_path.format(master, large)
                        row[metric] = float(check_output(cmd.split()))

                    dbase.insert(table, row)

                # Delete the backup table.
                dbase.drop_backup(table_old)

                # Add the new rows (upsamplers_new)
                for upsampler in upsamplers_new:
                    up_path = upsamplers[upsampler]
                    filename = '.'.join([upsampler, 'tif'])
                    large = os.path.join(os.path.dirname(small),
                                         ratio, filename)
                    row = dict(upsampler=upsampler)

                    # Upsample ratio.tif back to 840 using upsampler.
                    #  {0} input image path (small)
                    #  {1} output image path (large)
                    #  {2} upsampling ratio
                    #  {3} upsampled size (always 840)
                    prog(image, downsampler, ratio, upsampler)
                    call(up_path.format(small, large, ratio, 840).split())
                    for metric in metrics:
                        metric_path = metrics[metric][0]

                        # Compare master.tif to upsampler.tif.
                        #  {0} reference image path (master)
                        #  {1} test image path (large)
                        prog(image, downsampler, ratio, upsampler, metric)
                        cmd = metric_path.format(master, large)
                        row[metric] = float(check_output(cmd.split()))

                    # Add row to the table and delete the upsampled image.
                    dbase.insert(table, row)
                    os.remove(large)

                # Remove the directory for this ratio.
                shutil.rmtree(ratio_dir, True)

            # Create tables for unchanged images/downsamplers with new ratios.
            for ratio in ratios_new:
                table = '_'.join([image, downsampler, ratio])
                size = ratios[ratio]
                filename = '.'.join([ratio, 'tif'])
                small = os.path.join(downsampler_dir, filename)

                # Create a directory for this ratio.
                ratio_dir = os.path.join(downsampler_dir, ratio)
                if not os.path.isdir(ratio_dir):
                    os.makedirs(ratio_dir)

                # Downsample master.tif by ratio using downsampler.
                #  {0} input image path (master)
                #  {1} output image path (small)
                #  {2} downsampling ratio
                #  {3} downsampled size (width or height)
                prog(image, downsampler, ratio)
                call(down_path.format(master, small, ratio, size).split())

                # Create a new database table.
                dbase.add_table(image, downsampler, ratio, metrics)

                for upsampler in upsamplers:
                    up_path = upsamplers[upsampler]
                    filename = '.'.join([upsampler, 'tif'])
                    large = os.path.join(os.path.dirname(small),
                                         ratio, filename)
                    row = dict(upsampler=upsampler)

                    # Upsample ratio.tif back to 840 using upsampler.
                    #  {0} input image path (small)
                    #  {1} output image path (large)
                    #  {2} upsampling ratio
                    #  {3} upsampled size (always 840)
                    prog(image, downsampler, ratio, upsampler)
                    call(up_path.format(small, large, ratio, 840).split())
                    for metric in metrics:
                        metric_path = metrics[metric][0]

                        # Compare master.tif to upsampler.tif.
                        #  {0} reference image path (master)
                        #  {1} test image path (large)
                        prog(image, downsampler, ratio, upsampler, metric)
                        cmd = metric_path.format(master, large)
                        row[metric] = float(check_output(cmd.split()))

                    # Add the row to the table and delete the upsampled image.
                    dbase.insert(table, row)
                    os.remove(large)

                # Remove the directory for this ratio.
                shutil.rmtree(ratio_dir, True)

        # Create new tables for unchanged images with new downsamplers.
        for downsampler in downsamplers_new:
            down_path = downsamplers[downsampler]

            # Create a directory for this downsampler if necessary.
            downsampler_dir = os.path.join(image_dir, downsampler)
            if not os.path.exists(downsampler_dir):
                os.makedirs(downsampler_dir)

            for ratio in ratios:
                table = '_'.join([image, downsampler, ratio])
                size = ratios[ratio]
                filename = '.'.join([ratio, 'tif'])
                small = os.path.join(downsampler_dir, filename)

                # Create a directory for this ratio.
                ratio_dir = os.path.join(downsampler_dir, ratio)
                if not os.path.isdir(ratio_dir):
                    os.makedirs(ratio_dir)

                # Downsample master.tif by ratio using downsampler.
                #  {0} input image path (master)
                #  {1} output image path (small)
                #  {2} downsampling ratio
                #  {3} downsampled size (width or height)
                prog(image, downsampler, ratio)
                call(down_path.format(master, small, ratio, size).split())

                # Create a new database table.
                dbase.add_table(image, downsampler, ratio, metrics)

                for upsampler in upsamplers:
                    up_path = upsamplers[upsampler]
                    filename = '.'.join([upsampler, 'tif'])
                    large = os.path.join(os.path.dirname(small),
                                         ratio, filename)
                    row = dict(upsampler=upsampler)

                    # Upsample ratio.tif back to 840 using upsampler.
                    #  {0} input image path (small)
                    #  {1} output image path (large)
                    #  {2} upsampling ratio
                    #  {3} upsampled size (always 840)
                    prog(image, downsampler, ratio, upsampler)
                    call(up_path.format(small, large, ratio, 840).split())
                    for metric in metrics:
                        metric_path = metrics[metric][0]

                        # Compare master.tif to upsampler.tif.
                        #  {0} reference image path (master)
                        #  {1} test image path (large)
                        prog(image, downsampler, ratio, upsampler, metric)
                        cmd = metric_path.format(master, large)
                        row[metric] = float(check_output(cmd.split()))

                    # Add the row to the table and delete the upsampled image.
                    dbase.insert(table, row)
                    os.remove(large)

                # Remove the directory for this ratio.
                shutil.rmtree(ratio_dir, True)

    # Create the new error tables for the new images.
    for image in images_new:
        image_dir = os.path.join(gen_images_path, image)
        image_path = images_new[image]
        master = os.path.join(image_dir, 'master.tif')

        # Create a new directory for this image if it does not exist.
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        # Make a copy of the test image.
        shutil.copyfile(image_path, master)
        for downsampler in downsamplers:
            down_path = downsamplers[downsampler]

            # Create a directory for this downsampler if necessary.
            downsampler_dir = os.path.join(image_dir, downsampler)
            if not os.path.exists(downsampler_dir):
                os.makedirs(downsampler_dir)

            for ratio in ratios:
                table = '_'.join([image, downsampler, ratio])
                size = ratios[ratio]
                filename = '.'.join([ratio, 'tif'])
                small = os.path.join(downsampler_dir, filename)

                # Create a directory for this ratio.
                ratio_dir = os.path.join(downsampler_dir, ratio)
                if not os.path.isdir(ratio_dir):
                    os.makedirs(ratio_dir)

                # Downsample master.tif by ratio using downsampler.
                #  {0} input image path (master)
                #  {1} output image path (small)
                #  {2} downsampling ratio
                #  {3} downsampled size (width or height)
                prog(image, downsampler, ratio)
                call(down_path.format(master, small, ratio, size).split())

                # Create a new database table.
                dbase.add_table(image, downsampler, ratio, metrics)

                for upsampler in upsamplers:
                    up_path = upsamplers[upsampler]
                    filename = '.'.join([upsampler, 'tif'])
                    large = os.path.join(os.path.dirname(small),
                                         ratio, filename)
                    row = dict(upsampler=upsampler)

                    # Upsample ratio.tif back to 840 using upsampler.
                    #  {0} input image path (small)
                    #  {1} output image path (large)
                    #  {2} upsampling ratio
                    #  {3} upsampled size (always 840)
                    prog(image, downsampler, ratio, upsampler)
                    call(up_path.format(small, large, ratio, 840).split())
                    for metric in metrics:
                        metric_path = metrics[metric][0]

                        # Compare master.tif to upsampler.tif.
                        #  {0} reference image path (master)
                        #  {1} test image path (large)
                        prog(image, downsampler, ratio, upsampler, metric)
                        cmd = metric_path.format(master, large)
                        row[metric] = float(check_output(cmd.split()))

                    # Add the row to the table and delete the upsampled image.
                    dbase.insert(table, row)
                    os.remove(large)

                # Remove the directory for this ratio.
                shutil.rmtree(ratio_dir, True)

    # Backup the configuration file and close the database connection.
    shutil.copyfile(config_file, config_backup_file)
    dbase.close()
    complete()

if __name__ == '__main__':
    main()
