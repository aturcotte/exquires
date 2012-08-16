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

"""A collection of classes used to compute image difference data.

The hierarchy of classes is as follows:

    * :class:`Operations` encapsulate a list of :class:`Images`
    * :class:`Images` encapsulate a `dict` of images
      and a list of :class:`Downsamplers`
    * :class:`Downsamplers` encapsulate a `dict` of downsamplers
      and a list of :class:`Ratios`
    * :class:`Ratios` encapsulate a `dict` of ratios and a list :class:`Images`
    * :class:`Images` encapsulate a `dict` of images and a `dict` of metrics

These classes work together to downsample the master images, upsample the
downsampled images, and compare the upsampled images to the master images.
To perform the operations, call :meth:`Operations.compute`.

"""

import os
import shutil
from subprocess import call, check_output

from exquires import database, progress, tools

# pylint: disable-msg=R0903


class Operations(object):

    """A collection of Image objects to compute data with.

    This class is responsible for calling all operations defined in the
    specified project file when using :ref:`exquires-run` or
    :ref:`exquires-update`.

    :param images: images to downsample
    :type images:  list of :class:`Images`

    """

    def __init__(self, images):
        """Create a new :class:`Operations` object."""
        self.images = images
        self.len = sum(len(image) for image in self.images)

    def __len__(self):
        """Return the length of this :class:`Operations` object.

        The length of an :class:`Operations` object is the total number of
        operations (downsampling, upsampling, and comparing) to be performed.

        :return: length of this :class:`Operations` object
        :rtype:  `integer`

        """
        return self.len

    def compute(self, args, old=None):
        """Perform all operations.

        :param args:             arguments
        :param args.prog:        name of the calling program
        :param args.dbase_file:  database file
        :param args.proj:        name of the current project
        :param args.silent:      `True` if using silent mode
        :param args.met_same:    unchanged metrics
        :param args.metrics:     current metrics
        :param args.config_file: current configuration file
        :param args.config_bak:  previous configuration file
        :param old:              old configuration entries to be removed
        :type args:              :class:`argparse.Namespace`
        :type args.prog:         `string`
        :type args.dbase_file:   `path`
        :type args.proj:         `string`
        :type args.silent:       `boolean`
        :type args.met_same:     `dict`
        :type args.metrics:      `dict`
        :type args.config_file:  `path`
        :type args.config_bak:   `path`
        :type old:               :class:`argparse.Namespace`

        """
        # Setup verbose mode.
        if not args.silent:
            prg = progress.Progress(args.prog, args.proj, len(self))
            args.do_op = prg.do_op
            cleanup = prg.cleanup
            complete = prg.complete
        else:
            prg = []
            args.do_op = lambda *a, **k: None
            cleanup = lambda: None
            complete = lambda: None

        # Backup any existing database file.
        dbase_bak = '.'.join([args.dbase_file, 'bak'])
        if os.path.isfile(args.dbase_file):
            shutil.copyfile(args.dbase_file, dbase_bak)

        # Open the database connection.
        args.dbase = database.Database(args.dbase_file)

        success = True
        try:
            # Remove old database tables.
            if old:
                cleanup()
                args.dbase.drop_tables(old.images,
                                       old.downsamplers, old.ratios)

            # Create the project folder if it does not exist.
            tools.create_dir(args.proj)

            # Compute for all images.
            for image in self.images:
                image.compute(args)
        except StandardError as std_err:
            success = False
            error = std_err
        finally:
            # Remove the project directory and close the database.
            shutil.rmtree(args.proj, True)
            args.dbase.close()

            if success:
                # Backup the project file.
                shutil.copyfile(args.config_file, args.config_bak)

                # Delete the database backup.
                if os.path.isfile(dbase_bak):
                    os.remove(dbase_bak)

                # Indicate completion and restore the console.
                complete()
                del prg
            else:
                # Restore the previous database file.
                os.remove(args.dbase_file)
                if os.path.isfile(dbase_bak):
                    shutil.move(dbase_bak, args.dbase_file)

                # Restore the console
                del prg

                # Print an error message.
                print error


class Images(object):

    """This class calls operations for a particular set of images.

    :param images:       images to downsample
    :param downsamplers: downsamplers to use
    :param same:        `True` if using unchanged images
    :type images:        `dict`
    :type downsamplers:  list of :class:`Downsamplers`
    :type same:          `boolean`

    """

    def __init__(self, images, downsamplers, same=False):
        """Create a new :class:`Images` object."""
        self.images = images
        self.downsamplers = downsamplers
        self.same = same
        self.len = (len(self.images) *
                    sum(len(down) + down.ops for down in self.downsamplers))

    def __len__(self):
        """Return the length of this :class:`Images` object.

        The length of an :class:`Images` object is the number of images times
        the sum of the lengths and the number of upsampling and comparison
        operations of each :class:`Downsamplers` object.

        :return: length of this :class:`Images` object
        :rtype:  `integer`

        """
        return self.len

    def compute(self, args):
        """Perform all operations for this set of images.

        :param args:            arguments
        :param args.dbase_file: database file
        :param args.dbase:      connected database
        :param args.proj:       name of the current project
        :param args.silent:     `True` if using silent mode
        :param args.met_same:   unchanged metrics
        :param args.metrics:    current metrics
        :param args.do_op:      updates the displayed progress
        :type args:             :class:`argparse.Namespace`
        :type args.dbase_file:  `path`
        :type args.dbase:       :class:`database.Database`
        :type args.proj:        `string`
        :type args.silent:      `boolean`
        :type args.met_same:    `dict`
        :type args.metrics:     `dict`
        :type args.do_op:       `function`

        """
        # Compute for all images.
        for args.image in self.images:
            # Make a copy of the test image.
            if len(self):
                args.image_dir = tools.create_dir(args.proj, args.image)
                args.master = os.path.join(args.image_dir, 'master.tif')
                shutil.copyfile(self.images[args.image], args.master)

            # Compute for all downsamplers.
            for downsampler in self.downsamplers:
                downsampler.compute(args, self.same)

            # Remove the directory for this image.
            if len(self):
                shutil.rmtree(args.image_dir, True)


class Downsamplers(object):

    """This class calls operations for a particular set of downsamplers.

    :param downsamplers: downsamplers to use
    :param ratios:       ratios to downsample by
    :param same:         `True` if using unchanged downsamplers
    :type downsamplers:  `dict`
    :type ratios:        list of :class:`Ratios`
    :type same:          `boolean`

    """

    def __init__(self, downsamplers, ratios, same=False):
        """Create a new :class:`Downsamplers` object."""
        self.downsamplers = downsamplers
        self.ratios = ratios
        self.same = same
        self.ops = len(self.downsamplers) * sum(rat.ops for rat in self.ratios)
        self.len = (len(self.downsamplers) *
                    sum(len(rat) for rat in self.ratios)) if self.ops else 0

    def __len__(self):
        """Return the length of this :class:`Downsamplers` object.

        The length of a :class:`Downsamplers` object is the number of
        downsamplers times the sum of the lengths of each :class:`Ratios`
        object.

        :return: length of this :class:`Downsamplers` object
        :rtype:  `integer`

        """
        return self.len

    def compute(self, args, same):
        """Perform all operations for this set of downsamplers.

        :param args:            arguments
        :param args.dbase_file: database file
        :param args.dbase:      connected database
        :param args.proj:       name of the current project
        :param args.silent:     `True` if using silent mode
        :param args.met_same:   unchanged metrics
        :param args.metrics:    current metrics
        :param args.do_op:      updates the displayed progress
        :param args.image:      name of the image
        :param args.image_dir:  directory to store results for this image
        :param args.master:     master image to downsample
        :param same:            `True` if possibly accessing an existing table
        :type args:             :class:`argparse.Namespace`
        :type args.dbase_file:  `path`
        :type args.dbase:       :class:`database.Database`
        :type args.proj:        `string`
        :type args.silent:      `boolean`
        :type args.met_same:    `dict`
        :type args.metrics:     `dict`
        :type args.do_op:       `function`
        :type args.image:       `string`
        :type args.image_dir:   `path`
        :type args.master:      `path`
        :type same:             `boolean`

        """
        is_same = self.same and same

        # Compute for all downsamplers.
        for args.downsampler in self.downsamplers:
            # Create a directory for this downsampler if necessary.
            if len(self):
                args.downsampler_dir = tools.create_dir(args.image_dir,
                                                        args.downsampler)

            # Compute for all ratios.
            for ratio in self.ratios:
                ratio.compute(args, self.downsamplers, is_same)

            # Remove the directory for this downsampler.
            if len(self):
                shutil.rmtree(args.downsampler_dir, True)


class Ratios(object):

    """This class calls operations for a particular set of ratios.

    :param ratios:     ratios to downsample by
    :param upsamplers: upsamplers to use
    :param same:       `True` if using unchanged ratios
    :type ratios:      `dict`
    :type upsamplers:  list of :class:`Upsamplers`
    :type same:        `boolean`

    """

    def __init__(self, ratios, upsamplers, same=False):
        """Create a new :class:`Ratios` object."""
        self.ratios = ratios
        self.upsamplers = upsamplers
        self.same = same
        self.ops = len(self.ratios) * sum(len(ups) for ups in self.upsamplers)
        self.len = len(self.ratios) if self.ops else 0

    def __len__(self):
        """Return the length of this :class:`Ratios` object.

        The length of a :class:`Ratios` object is the number of ratios.

        :return: length of this :class:`Ratios` object
        :rtype:  `integer`

        """
        return self.len

    def compute(self, args, downsamplers, same):
        """Perform all operations for this set of ratios.

        :param args:                 arguments
        :param args.dbase_file:      database file
        :param args.dbase:           connected database
        :param args.proj:            name of the current project
        :param args.silent:          `True` if using silent mode
        :param args.met_same:        unchanged metrics
        :param args.metrics:         current metrics
        :param args.do_op:           updates the displayed progress
        :param args.image:           name of the image
        :param args.image_dir:       directory to store results for this image
        :param args.master:          master image to downsample
        :param args.downsampler:     name of the downsampler
        :param args.downsampler_dir: directory to store dowsampled images
        :param downsamplers:         downsamplers to use
        :param same:                 `True` if accessing an existing table
        :type args:                  :class:`argparse.Namespace`
        :type args.dbase_file:       `path`
        :type args.dbase:            :class:`database.Database`
        :type args.proj:             `string`
        :type args.silent:           `boolean`
        :type args.met_same:         `dict`
        :type args.metrics:          `dict`
        :type args.do_op:            `function`
        :type args.image:            `string`
        :type args.image_dir:        `path`
        :type args.master:           `path`
        :type args.downsampler:      `string`
        :type args.downsampler_dir:  `path`
        :type downsamplers:          `dict`
        :type same:                  `boolean`

        """
        is_same = self.same and same

        # Compute for all ratios.
        for args.ratio in self.ratios:
            if len(self):
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
            if len(self):
                shutil.rmtree(ratio_dir, True)

            # Delete the backup table.
            if is_same:
                args.dbase.drop_backup(args.table_bak)


class Upsamplers(object):

    """This class upsamples an image and compares with its master image.

    :param upsamplers: upsamplers to use
    :param metrics:    metrics to compare with
    :param same:       `True` if using unchanged upsamplers
    :type upsamplers:  `dict`
    :type metrics:     `dict`
    :type same:        `boolean`

    """

    def __init__(self, upsamplers, metrics, same=False):
        """Create a new :class:`Upsamplers` object."""
        self.upsamplers = upsamplers
        self.metrics = metrics
        self.same = same
        ops = len(self.metrics)
        self.len = len(self.upsamplers) * (ops + 1) if ops else 0

    def __len__(self):
        """Return the length of this :class:`Upsamplers` object.

        The length of an :class:`Upsamplers` object is the number of upsampling
        and comparison operations to perform.

        :return: length of this :class:`Upsamplers` object
        :rtype:  `integer`

        """
        return self.len

    def compute(self, args, same):
        """Perform all operations for this set of ratios.

        :param args:                 arguments
        :param args.dbase_file:      database file
        :param args.dbase:           connected database
        :param args.proj:            name of the current project
        :param args.silent:          `True` if using silent mode
        :param args.met_same:        unchanged metrics
        :param args.metrics:         current metrics
        :param args.do_op:           updates the displayed progress
        :param args.image:           name of the image
        :param args.image_dir:       directory to store results for this image
        :param args.master:          master image to downsample
        :param args.downsampler:     name of the downsampler
        :param args.downsampler_dir: directory to store dowsampled images
        :param args.ratio:           resampling ratio
        :param args.small:           downsampled image
        :param args.table:           name of the table to insert the row into
        :param args.table_bak:       name of the backup table (if it exists)
        :param same:                 `True` if accessing an existing table
        :type args:                  :class:`argparse.Namespace`
        :type args.dbase_file:       `path`
        :type args.dbase:            :class:`database.Database`
        :type args.proj:             `string`
        :type args.silent:           `boolean`
        :type args.met_same:         `dict`
        :type args.metrics:          `dict`
        :type args.do_op:            `function`
        :type args.image:            `string`
        :type args.image_dir:        `path`
        :type args.master:           `path`
        :type args.downsampler:      `string`
        :type args.downsampler_dir:  `path`
        :type args.ratio:            `string`
        :type args.small:            `path`
        :type args.table:            `string`
        :type args.table_bak:        `string`
        :type same:                  `boolean`

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
