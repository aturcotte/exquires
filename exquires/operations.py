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

"""A collection of methods to compute image difference data."""

import os
import shutil
from subprocess import call, check_output

from exquires import database, progress, tools

# pylint: disable-msg=R0903


class Operations(object):

    """This class is responsible for calling all operations."""

    def __init__(self, images):
        """This constructor creates a new Operations object.

        :param images: A list of Images objects.
        :param old: Namespace of old database elements.

        """
        self.images = images
        self.len = sum(len(image) for image in self.images)

    def __len__(self):
        """Return the length of this Operations object.

        The length of an Operations object is the total number of operations
        (downsampling, upsampling, and comparing) to be performed.

        """
        return self.len

    def compute(self, args, old=None):
        """Perform all operations.

        :param args.prog: The name of the calling program.
        :param args.dbase_file: The database file.
        :param args.proj: The name of the current project.
        :param args.silent: True if using silent mode, else false.
        :param args.met_same: The dictionary of unchanged metrics.
        :param args.metrics: The dictionary of current metrics.
        :param args.config_file: The current configuration file.
        :param args.config_bak: The previous configuration file.

        """
        # Setup verbose mode.
        if not args.silent:
            prg = progress.Progress(args.prog, args.proj, len(self))
            args.do_op = prg.do_op
            cleanup = prg.cleanup
            complete = prg.complete
        else:
            args.do_op = lambda *a, **k: None
            cleanup = lambda: None
            complete = lambda: None

        # Open the database connection.
        args.dbase = database.Database(args.dbase_file)

        # Remove old database tables.
        if old:
            cleanup()
            args.dbase.drop_tables(old.images, old.downsamplers, old.ratios)

        # Create the project folder if it does not exist.
        tools.create_dir(args.proj)

        # Compute for all images.
        for image in self.images:
            image.compute(args)

        # Remove the project directory and close the database.
        shutil.rmtree(args.proj, True)
        args.dbase.close()

        # Backup the project file and indicate completion.
        shutil.copyfile(args.config_file, args.config_bak)
        complete()


class Images(object):

    """This class calls operations for a particular set of images."""

    def __init__(self, images, downsamplers, same=False):
        """This constructor creates a new Images object.

        :param images: A dictionary of images.
        :param downsamplers: A list of Downsamplers objects.

        """
        self.images = images
        self.downsamplers = downsamplers
        self.same = same
        self.len = (len(self.images) *
                    sum(len(down) + down.ops for down in self.downsamplers))

    def __len__(self):
        """Return the length of this Images object.

        The length of an Images object is the number of images times
        the sum of the lengths and the number of upsampling and comparison
        operations of each Downsamplers object.

        """
        return self.len

    def compute(self, args):
        """Perform all operations for this set of images.

        :param args.dbase_file: The database file.
        :param args.dbase: The connected database.
        :param args.proj: The name of the current project.
        :param args.silent: True if using silent mode, else false.
        :param args.met_same: The dictionary of unchanged metrics.
        :param args.metrics: The dictionary of current metrics.
        :param args.do_op: The function to update the displayed progress.

        """
        if len(self):
            # Compute for all images.
            for args.image in self.images:
                args.image_dir = tools.create_dir(args.proj, args.image)
                args.master = os.path.join(args.image_dir, 'master.tif')

                # Make a copy of the test image.
                shutil.copyfile(self.images[args.image], args.master)

                # Compute for all downsamplers.
                for downsampler in self.downsamplers:
                    downsampler.compute(args, self.same)

                # Remove the directory for this image.
                shutil.rmtree(args.image_dir, True)


class Downsamplers(object):

    """This class calls operations for a particular set of downsamplers."""

    def __init__(self, downsamplers, ratios, same=False):
        """This constructor creates a new Downsamplers object.

        :param downsamplers: A dictionary of downsamplers.
        :param ratios: A list of Ratios objects.

        """
        self.downsamplers = downsamplers
        self.ratios = ratios
        self.same = same
        self.ops = len(self.downsamplers) * sum(rat.ops for rat in self.ratios)
        self.len = (len(self.downsamplers) *
                    sum(len(rat) for rat in self.ratios)) if self.ops else 0

    def __len__(self):
        """Return the length of this Downsamplers object.

        The length of a Downsamplers object is the number of downsamplers times
        the sum of the lengths of each Ratios object.

        """
        return self.len

    def compute(self, args, same):
        """Perform all operations for this set of downsamplers.

        :param args.dbase_file: The database file.
        :param args.dbase: The connected database.
        :param args.proj: The name of the current project.
        :param args.silent: True if using silent mode, else false.
        :param args.met_same: The dictionary of unchanged metrics.
        :param args.metrics: The dictionary of current metrics.
        :param args.do_op: The function to update the displayed progress.
        :param args.image: The name of the image.
        :param args.image_dir: The directory to store results for this image.
        :param args.master: The image to downsample.
        :param same: True if possibly accessing an existing table.

        """
        if len(self):
            # Compute for all downsamplers.
            for args.downsampler in self.downsamplers:
                # Create a directory for this downsampler if necessary.
                args.downsampler_dir = tools.create_dir(args.image_dir,
                                                        args.downsampler)

                # Compute for all ratios.
                for ratio in self.ratios:
                    ratio.compute(args, self.downsamplers, self.same and same)

                # Remove the directory for this downsampler.
                shutil.rmtree(args.downsampler_dir, True)


class Ratios(object):

    """This class calls operations for a particular set of ratios."""

    def __init__(self, ratios, upsamplers, same=False):
        """This constructor creates a new Ratios object.

        :param ratios: A dictionary of ratios.
        :param upsamplers: A list of Upsamplers objects.

        """
        self.ratios = ratios
        self.upsamplers = upsamplers
        self.same = same
        self.ops = len(self.ratios) * sum(len(ups) for ups in self.upsamplers)
        self.len = len(self.ratios) if self.ops else 0

    def __len__(self):
        """Return the length of this Ratios object.

        The length of a Ratios object is the number of ratios.

        """
        return self.len

    def compute(self, args, downsamplers, same):
        """Perform all operations for this set of ratios.

        :param args.dbase_file: The database file.
        :param args.dbase: The connected database.
        :param args.proj: The name of the current project.
        :param args.silent: True if using silent mode, else false.
        :param args.met_same: The dictionary of unchanged metrics.
        :param args.metrics: The dictionary of current metrics.
        :param args.do_op: The function to update the displayed progress.
        :param args.image: The name of the image.
        :param args.image_dir: The directory to store results for this image.
        :param args.master: The image to downsample.
        :param args.downsampler: The name of the downsampler.
        :param args.downsampler_dir: The directory to store reduced images.
        :param downsamplers: The dictionary of downsamplers.
        :param same: True if possibly accessing an existing table.

        """
        if len(self):
            # Compute for all ratios.
            for args.ratio in self.ratios:
                args.small = os.path.join(args.downsampler_dir,
                                          '.'.join([args.ratio, 'tif']))

                # Create a directory for this ratio.
                ratio_dir = tools.create_dir(args.downsampler_dir, args.ratio)

                # Downsample master.tif by ratio using downsampler.
                #  {0} input image path (master)
                #  {1} output image path (small)
                #  {2} downsampling ratio
                #  {3} downsampled size (width or height)
                args.do_op(args)
                call(
                    downsamplers[args.downsampler].format(
                        args.master, args.small,
                        args.ratio, self.ratios[args.ratio]
                    ).split()
                )

                is_same = self.same and same
                if is_same:
                    # Access the existing database table.
                    args.table = '_'.join([args.image,
                                           args.downsampler, args.ratio])
                    args.table_bak = args.dbase.backup_table(args.table,
                                                             args.metrics)

                else:
                    # Create a new database table.
                    args.table = args.dbase.add_table(
                        args.image, args.downsampler, args.ratio, args.metrics)

                # Compute for all upsamplers.
                for upsampler in self.upsamplers:
                    upsampler.compute(args, is_same)

                # Remove the directory for this ratio.
                shutil.rmtree(ratio_dir, True)

                # Delete the backup table.
                if is_same:
                    args.dbase.drop_backup(args.table_bak)


class Upsamplers(object):

    """This class upsamples an image and compares with its master image."""

    def __init__(self, upsamplers, metrics, same=False):
        """This constructor creates a new Upsamplers object.

        :param upsamplers: A dictionary of upsamplers.
        :param metrics: A dictionary of metrics.

        """
        self.upsamplers = upsamplers
        self.metrics = metrics
        self.same = same
        ops = len(self.metrics)
        self.len = len(self.upsamplers) * (ops + 1) if ops else 0

    def __len__(self):
        """Return the length of this Upsamplers object.

        The length of an Upsamplers object is the number of upsampling and
        comparing operations to perform.

        """
        return self.len

    def compute(self, args, same):
        """Perform all operations for this set of ratios.

        :param args.dbase_file: The database file.
        :param args.dbase: The connected database.
        :param args.proj: The name of the current project.
        :param args.silent: True if using silent mode, else false.
        :param args.metrics: The dictionary of metrics.
        :param args.do_op: The function to update the displayed progress.
        :param args.image: The name of the image.
        :param args.image_dir: The directory to store results for this image.
        :param args.master: The image to downsample.
        :param args.downsampler: The name of the downsampler.
        :param args.downsampler_dir: The directory to store reduced images.
        :param args.ratio: The ratio.
        :param args.small: The path of the downsampled image.
        :param args.table: The name of the table to insert the row.
        :param args.table_bak: The name of the backup table if it exists.
        :param same: True if accessing an existing table.

        """
        is_same = self.same and same and args.met_same

        # Compute for all upsamplers.
        for upsampler in self.upsamplers:
            row = {}
            if is_same:
                # Access the existing table row.
                row = args.dbase.get_error_data(args.table_bak, upsampler,
                                                ','.join(args.met_same))

            if len(self):
                if not is_same:
                    # Start creating a new table row.
                    row['upsampler'] = upsampler

                # Construct the path to the upsampled image.
                large = os.path.join(
                    os.path.dirname(args.small), args.ratio,
                    '.'.join([upsampler, 'tif'])
                )

                # Upsample ratio.tif back to 840 using upsampler.
                #  {0} input image path (small)
                #  {1} output image path (large)
                #  {2} upsampling ratio
                #  {3} upsampled size (always 840)
                args.do_op(args, upsampler)
                call(self.upsamplers[upsampler].format(
                        args.small, large, args.ratio, 840).split())

                # Compute for all metrics.
                for metric in self.metrics:
                    # Compare master.tif to upsampler.tif.
                    #  {0} reference image path (master)
                    #  {1} test image path (large)
                    args.do_op(args, upsampler, metric)
                    row[metric] = float(
                        check_output(
                            self.metrics[metric][0].format(args.master,
                                                           large).split()
                        )
                    )

                # Remove the upsampled image.
                os.remove(large)

            # Add the new row to the table.
            if row:
                args.dbase.insert(args.table, row)
