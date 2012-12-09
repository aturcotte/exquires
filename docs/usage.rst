.. _usage:

******************
Using **EXQUIRES**
******************

.. _ImageMagick: http://www.imagemagick.org
.. _VIPS: http://www.vips.ecs.soton.ac.uk

==============
Usage Overview
==============

* Obtain suitable `16 bit 840x840 test images`_
* Use :ref:`exquires-new` to create a new project file
* Modify the project file to suit your needs
* Use :ref:`exquires-run` to compute the image difference data
* Use :ref:`exquires-update` to compute only the new data after editing the project file
* Use :ref:`exquires-report` to produce tables of aggregated data
* Use :ref:`exquires-correlate` to produce Spearman's rank cross-correlation matrices

.. _16 bit 840x840 test images: http://www.imagemagick.org/download/image-bank/16bit840x840images/

==================
Usage Instructions
==================

**EXQUIRES** comes with several :ref:`programs`, each including a
:option:`-h`/:option:`--help` option to display usage information and a
:option:`-v`/:option:`--version` option to display the version number.

These five main programs can be used to create and maintain a project,
which can be specified with the :option:`-p`/:option:`--proj` option:

* :ref:`exquires-new`
* :ref:`exquires-run`
* :ref:`exquires-update`
* :ref:`exquires-report`
* :ref:`exquires-correlate`

These two programs are responsible for computing image differences
and aggregating the results:

* :ref:`exquires-compare`
* :ref:`exquires-aggregate`

The following sections will explain how to make use of these programs to
compute data and view aggregated results and cross-correlation matrices.


.. _test-images:

------------------------------
Obtaining suitable test images
------------------------------

**EXQUIRES** is designed to use sRGB TIFF images with 16 bits per sample
(48 bits per pixel) and a width and height of 840 pixels. One image
(:download:`wave.tif <../exquires/wave.tif>`) is included as a default
selection.

A separate distribution of test images converted from RAW is available at
`<http://www.imagemagick.org/download/image-bank/16bit840x840images/>`_.
The examples in this section make use of several images from this collection.

The easiest way to obtain a copy of the image bank is as follows:

.. code-block:: console

    $ wget -r -nH --cut-dirs=3 ftp://ftp.imagemagick.org/pub/ImageMagick/image-bank/16bit840x840images/


.. _new-project:

---------------------------
Creating a new project file
---------------------------

A project file is a :file:`.ini` file that tells **EXQUIRES** which of the
following to use:

* Images
* Resampling Ratios
* Downsamplers
* Upsamplers
* Difference Metrics

The basic syntax to create a new project using :ref:`exquires-new` is:

.. code-block:: console

    $ exquires-new

which will create the project file :file:`project1.ini` and include the image
`wave.tif <http://www.imagemagick.org/download/image-bank/16bit840x840images/images/wave.tif>`_
along with a default collection of ratios, downsamplers, upsamplers, and
metrics.

In order to specify a project name and a set of test images, type one of the
following:

.. code-block:: console

    $ exquires-new -p my_project -I my_images
    $ exquires-new --proj my_project --image my_images

where :file:`my_project` is a name to identify your project and
:file:`my_images` is a list (wildcards are supported) of images with the
following properties:

:File Format: TIFF
:Colour Space: sRGB
:Bit Depth: 16 bits/sample (48 bits/pixel)
:Size: 840x840 pixels

To demonstrate, we will create a new project :command:`example_proj` using the
`16bit840x840images <http://www.imagemagick.org/download/image-bank/16bit840x840images/>`_
collection:

.. code-block:: console

    $ exquires-new -p example_proj -I /path/to/16bit840x840images/images/*


.. _custom-project:

----------------------------
Customizing the project file
----------------------------

Once a project file has been generated, you can manually edit it to suit your
needs. For our example project :command:`example_proj`, we have a project file
:file:`example_proj.ini` and we will look at each section in detail.


^^^^^^
Images
^^^^^^

This section lists the paths to the test images that will be used. We will keep
this example project small by removing all but two of the
`16bit840x840images <http://www.imagemagick.org/download/image-bank/16bit840x840images/>`_,
:file:`apartments.tif` and :file:`cabins.tif`.

.. code-block:: ini

    # TEST IMAGES
    # Images are 16-bit sRGB TIFFs with a width and height of 840 pixels.
    # Any images that are added must conform to this standard.
    [Images]
    apartments = /path/to/16bit840x840images/images/apartments.tif
    cabins = /path/to/16bit840x840images/images/cabins.tif

Notice that **EXQUIRES** has also assigned default names for these images,
which you can also modify.


^^^^^^
Ratios
^^^^^^

This section lists the resampling ratios and specifies the width and
height of the downsampled image for each ratio. Here are the default ratios:

.. code-block:: ini

    # RESAMPLING RATIOS
    # The test images are downsampled to the specified sizes.
    # Each size is obtained by dividing 840 by the ratio.
    [Ratios]
    2 = 420
    3 = 280
    4 = 210
    5 = 168
    6 = 140
    7 = 120
    8 = 105


^^^^^^^^^^^^
Downsamplers
^^^^^^^^^^^^

This section lists the downsampling methods that will be used to reduce each of
the test images. We have edited our example project to include a small subset
of the defaults.

.. code-block:: ini

    # DOWNSAMPLING COMMANDS
    # To add a downsampler, provide the command to execute it.
    # The command can make use of the following replacement fields:
    #     {0} = input image
    #     {1} = output image
    #     {2} = downsampling ratio
    #     {3} = downsampled size (width or height)
    # WARNING: Be sure to use a unique name for each downsampler.
    [Downsamplers]
    box_srgb = magick {0} -filter Box -resize {3}x{3} -strip {1}
    box_linear = magick {0} -colorspace RGB -filter Box -resize {3}x{3} -colorspace sRGB -strip {1}
    nearest_srgb = magick {0} -filter Point -resize {3}x{3} -strip {1}
    nearest_linear = magick {0} -colorspace RGB -filter Point -resize {3}x{3} -colorspace sRGB -strip {1}

Note that the `ImageMagick`_ commands in this example make use of numbered
replacement fields to denote the command-line arguments. If you wish to add
your own downsampling method, you must use :command:`{0}` and :command:`{1}`
to specify the input and output images, and either :command:`{2}` or
:command:`{3}` (or both) to specify the size of the reduced image.

Also note that the methods suffixed with :command:`_srgb` do not apply
gamma correction, meaning that the sRGB images are downsampled using linear
averaging even though sRGB is a non-linear colour space.
The methods suffixed with :command:`_linear` convert the input image to linear
RGB with sRGB primaries before downsampling, then convert the result back to
sRGB, using the `ImageMagick`_ command :command:`-colorspace`. Such suffixes
are useful because they allow one to separately aggregate the results of only
downsampling or upsampling using the two main "tracks" without having to list
the methods individually. In the same spirit if, for example, you were to
program downsamplers or upsamplers that convert into and out of sRGB using ICC
profiles, we would suggest that you use something like the :command:`_icc`
suffix; if you were to go through the XYZ colourspace, we would suggest
:command:`_xyz`.


^^^^^^^^^^
Upsamplers
^^^^^^^^^^

This section lists the upsampling methods that will be used to re-enlarge
each of the downsampled images, and makes use of the same replacement fields as
the Downsamplers section.

Since the purpose of **EXQUIRES** is to assess the accuracy of upsampling
methods, you may wish to add your own method to see how it ranks alongside
pre-existing methods. For example, we can compare the Nohalo method with
several Lanczos variations.

.. code-block:: ini

    # UPSAMPLING COMMANDS
    # To add an upsampler, provide the command to execute it.
    # The command can make use of the following replacement fields:
    #     {0} = input image
    #     {1} = output image
    #     {2} = upsampling ratio
    #     {3} = upsampled size (always 840)
    [Upsamplers]
    lanczos2_srgb = magick {0} -filter Lanczos2 -resize {3}x{3} -strip {1}
    lanczos2_linear = magick {0} -colorspace RGB -filter Lanczos2 -resize {3}x{3} -colorspace sRGB -strip {1}
    lanczos3_srgb = magick {0} -filter Lanczos -resize {3}x{3} -strip {1}
    lanczos3_linear = magick {0} -colorspace RGB -filter Lanczos -resize {3}x{3} -colorspace sRGB -strip {1}
    nohalo_srgb = nohalo {0} {1} {2} 0
    nohalo_linear = nohalo {0} {1} {2} 1

The :program:`nohalo` program is found in
:download:`nohalo.cpp <../exquires/examples/nohalo.cpp>`,
which uses `VIPS`_ to resample the image (using a trick to produce a result
that conforms to the proper pixel alignment convention). For more information
on this method, see :ref:`example`.

^^^^^^^
Metrics
^^^^^^^

This section lists the image comparison metrics that will be used to assess
the accuracy of the re-enlarged images. Each metric is associated with an
aggregator and a best-to-worst ordering, as seen in the default settings.

.. code-block:: ini

    # IMAGE DIFFERENCE METRICS AND AGGREGATORS
    # Each metric must be associated with a data aggregation method.
    # To add a metric, you must provide the following three items:
    #     1. Error metric command, using the following replacement fields:
    #         {0} = reference image
    #         {1} = test image
    #     2. Aggregator command, using the following replacement field:
    #         {0} = list of error data to aggregate
    #     3. Best-to-worst ordering, given as a 0 or 1:
    #         0 = ascending
    #         1 = descending
    [Metrics]
    srgb_1 = exquires-compare srgb_1 {0} {1}, exquires-aggregate l_1 {0}, 0
    srgb_2 = exquires-compare srgb_2 {0} {1}, exquires-aggregate l_2 {0}, 0
    srgb_4 = exquires-compare srgb_4 {0} {1}, exquires-aggregate l_4 {0}, 0
    srgb_inf = exquires-compare srgb_inf {0} {1}, exquires-aggregate l_inf {0}, 0
    cmc_1 = exquires-compare cmc_1 {0} {1}, exquires-aggregate l_1 {0}, 0
    cmc_2 = exquires-compare cmc_2 {0} {1}, exquires-aggregate l_2 {0}, 0
    cmc_4 = exquires-compare cmc_4 {0} {1}, exquires-aggregate l_4 {0}, 0
    cmc_inf = exquires-compare cmc_inf {0} {1}, exquires-aggregate l_inf {0}, 0
    xyz_1 = exquires-compare xyz_1 {0} {1}, exquires-aggregate l_1 {0}, 0
    xyz_2 = exquires-compare xyz_2 {0} {1}, exquires-aggregate l_2 {0}, 0
    xyz_4 = exquires-compare xyz_4 {0} {1}, exquires-aggregate l_4 {0}, 0
    xyz_inf = exquires-compare xyz_inf {0} {1}, exquires-aggregate l_inf {0}, 0
    blur_1 = exquires-compare blur_1 {0} {1}, exquires-aggregate l_1 {0}, 0
    blur_2 = exquires-compare blur_2 {0} {1}, exquires-aggregate l_2 {0}, 0
    blur_4 = exquires-compare blur_4 {0} {1}, exquires-aggregate l_4 {0}, 0
    blur_inf = exquires-compare blur_inf {0} {1}, exquires-aggregate l_inf {0}, 0
    mssim = exquires-compare mssim {0} {1}, exquires-aggregate l_1 {0}, 1

Note that these default metric definitions make use of
:ref:`exquires-compare` and :ref:`exquires-aggregate`. Also note that
most of the metrics return an error measure, meaning that a lower result is
better. MSSIM, on the other hand, is a similarity index, meaning that a higher
result is better.

For more information on the default metrics, see :mod:`compare`.

For more information on the aggregation methods, see :mod:`aggregate`.


.. _run:

-----------------------------------
Computing the image comparison data
-----------------------------------

The basic syntax to run a project using :ref:`exquires-run` is:

.. code-block:: console

    $ exquires-run

which will read the project file :file:`project1.ini`, downsample the images
by each ratio using each downsampler, re-enlarge the downsampled images using
each upsampler, and compute the difference using each metric.

You can specify the project name using one of the following:

.. code-block:: console

    $ exquires-run -p my_project
    $ exquires-run --proj my_project

where :file:`my_project` is a name to identify your project.

By default, :ref:`exquires-run` displays progress information.
You can disable this output using one of the following:

.. code-block:: console

    $ exquires-run -s
    $ exquires-run --silent

.. warning::

    With large project files, this program can take an *extremely* long time to
    run. For slower machines, it is recommended to start with a small set of
    test images. You can add additional images later and call
    :ref:`exquires-update` to compute the new data.


.. _update:

----------------------------------
Updating the image comparison data
----------------------------------

If you make changes to the project file after calling :ref:`exquires-run`,
running it again will compute all data, including data for unchanged entries
in the project file. To compute only the new data rather than recomputing the
entire data set, use :ref:`exquires-update`, which supports the same
options as :ref:`exquires-run`.

See :ref:`run` for more information.


.. _report:

------------------------------------------------------
Generating a table of aggregate image comparison table
------------------------------------------------------

Once the image difference data has been computed, you can generate various
aggregations of the data and either display it in the terminal or write it to
a file.

The basic syntax to print aggregated data using :ref:`exquires-report` is:

.. code-block:: console

    $ exquires-report

which will read a backup of the project file :file:`project1.ini` that was
created the last time :ref:`exquires-run` or :ref:`exquires-update` was
called, select the appropriate values from the database, aggregate the data,
and print the results in tabular format to standard output.

As with the other programs, you can specify the project name using one of
the following:

.. code-block:: console

    $ exquires-report -p my_project
    $ exquires-report --proj my_project

where :file:`my_project` is a name to identify your project.

Normally, :ref:`exquires-report` prints the data as a plaintext table.
You may wish to include the results in a LaTeX document instead, which can be
done using one of the following:

.. code-block:: console

    $ exquires-report -l
    $ exquires-report --latex

Likewise, :ref:`exquires-report` normally shows the aggregated data when it
prints the table. You can instead show the Spearman (fractional) ranks for each
upsampling method by using one of the following:

.. code-block:: console

    $ exquires-report -r
    $ exquires-report --rank

Furthermore, you can instead merge the Spearman (fractional) ranks across
all specified metrics by using one of the following:

.. code-block:: console

    $ exquires-report -m
    $ exquires-report --merge

Whether you display aggregated data or ranks, by default the upsamplers in the
printed table will be sorted from best-to-worst according to the first metric
specified. If you wish to sort according to a different metric (including
those that are not selected to be displayed), use one of the following:

.. code-block:: console

    $ exquires-report -s my_metric
    $ exquires-report --sort my_metric

where :file:`my_metric` is one of the metrics defined in the project file.

By default, :ref:`exquires-report` prints the aggregated data to standard
output. You can write the aggregated data to a file by using one of the
following:

.. code-block:: console

    $ exquires-report -f my_file
    $ exquires-report --file my_file

where :file:`my_file` is the file you wish to write the data to.

When producing tables, :ref:`exquires-report` will display 4 digits by
default. You can select any number of digits between 1 and 16. For example, you
can change the number of digits to to 6 using one of the following:

.. code-block:: console

    $ exquires-report -d 6
    $ exquires-report --digits 6

There are three components that determine which database tables to aggregate
across: images, ratios, and downsamplers. By default, the image comparison data
is aggregated across all images, ratios, and downsampler. If you wish to
aggregate over a subset of the database, use the following options.

You can specify the images to aggregate across by using one of the following:

.. code-block:: console

    $ exquires-report -I my_images
    $ exquires-report --image my_images

where :file:`my_images` is a list of images defined in the project file.

.. note::

    The arguments passed to the :option:`-I`/:option:`--image` option support
    wildcard characters.

You can specify the downsamplers to aggregate across by using one of the
following:

.. code-block:: console

    $ exquires-report -D my_downsamplers
    $ exquires-report --down my_downsamplers

where :file:`my_downsamplers` is a list of downsamplers defined in the
project file.

.. note::

    The arguments passed to the :option:`-D`/:option:`--down` option support
    wildcard characters.

You can specify the ratios to aggregate across by using one of the following:

.. code-block:: console

    $ exquires-report -R my_ratios
    $ exquires-report --ratio my_ratios


where :file:`my_ratios` is a list of images defined in the project file.

.. note::

    The arguments passed to the :option:`-R`/:option:`--ratio` option support
    hyphenated ranges.

For example, to aggregate over the ratios 2 through 4 and 6, type:

.. code-block:: console

    $ exquires-report -R 2-4 6

Regardless of which images, downsamplers, and ratios the data is aggregated
across, the default behaviour is to display data for each upsampler and
metric, with each row representing an upsampler and each column representing
a metric. If you wish to display only certain rows and columns, use the
following options.

You can specify the metrics (columns) to display by using one of the following:

.. code-block:: console

    $ exquires-report -M my_metrics
    $ exquires-report --metric my_metrics

where :file:`my_metrics` is a list of metrics defined in the project file.

.. note::

    The arguments passed to the :option:`-M`/:option:`--metric` option support
    wildcard characters.

For example, to only display data for the metrics prefixed with
:command:`xyz_`, type:

.. code-block:: console

    $ exquires-report -M xyz_*

You can specify the upsamplers (rows) to display by using one of the following:

.. code-block:: console

    $ exquires-report -U my_upsamplers
    $ exquires-report --up my_upsamplers

where :file:`my_upsamplers` is a list of upsamplers defined in the project
file.

.. note::

    The arguments passed to the :option:`-U`/:option:`--up` option support
    wildcard characters.

For example, to only display data for the upsamplers suffixed with
:command:`_srgb`, type:

.. code-block:: console

    $ exquires-report -U *_srgb


.. _correlate:

-----------------------------------------------------
Generating a Spearman's rank cross-correlation matrix
-----------------------------------------------------

In addition to using :ref:`exquires-report` with the
:option:`-r`/:option:`--rank` or :option:`-m`/:option:`--merge` options, which
produce tables of Spearman (fractional) ranks, you can use
:ref:`exquires-correlate` to compute Spearman's rank cross-correlation matrices
for several different groups.

The basic syntax to print a cross-correlation matrix using
:ref:`exquires-correlate` is:

.. code-block:: console

    $ exquires-correlate

which will read a backup of the project file :file:`project1.ini` that was
created the last time :ref:`exquires-run` or :ref:`exquires-update` was
called, select the appropriate values from the database, aggregate the data,
and print the cross-correlation matrix for all comparison metrics to standard
output.

You can select which upsamplers to consider when computing the matrix
by using the :option:`-U`/:option:`--up` option.

By default, the :option:`-M`/:option:`--metric` option is selected. You can
select one of the following cross-correlation groups:

* :option:`-I`/:option:`--image`
* :option:`-D`/:option:`--down`
* :option:`-R`/:option:`--ratio`
* :option:`-M`/:option:`--metric`

As with the other programs, you can specify the project name using one of the
following:

.. code-block:: console

    $ exquires-correlate -p my_project
    $ exquires-correlate --proj my_project


Normally, :ref:`exquires-correlate` prints the cross-correlation matrix as
a plaintext table. You may wish to include the results in a LaTeX document
instead, which can be done using one of the following:

.. code-block:: console

    $ exquires-correlate -l
    $ exquires-correlate --latex

By default, :ref:`exquires-correlate` prints the cross-correlation matrix
to standard output. You can write the matrix to a file by using one of the
following:

.. code-block:: console

    $ exquires-correlate -f my_file
    $ exquires-correlate --file my_file

where :file:`my_file` is the file you wish to write the data to.

When producing a matrix, :ref:`exquires-correlate` will display 4 digits by
default. You can select any number of digits between 1 and 16. For example,
you can change the number of digits to to 6 using one of the following:

.. code-block:: console

    $ exquires-correlate -d 6
    $ exquires-correlate --digits 6

By default, the order of the rows and columns of the correlation matrix
corresponds to the order they were passed to :ref:`exquires-correlate`. It is
often useful to sort the coefficients from best to worst based on a
specific anchor row/column. You can specify the anchor using one of the
following:

.. code-block:: console

    $ exquires-correlate -a my_anchor
    $ exquires-correlate --anchor my_anchor

where :file:`my_anchor` is the anchor you wish to use.

You can specify the upsamplers (rows) to consider in the computation by using
one of the following:

.. code-block:: console

    $ exquires-correlate -U my_upsamplers
    $ exquires-correlate --up my_upsamplers

where :file:`my_upsamplers` is a list of upsamplers defined in the project
file.

.. note::

    The arguments passed to the :option:`-U`/:option:`--up` option support
    wildcard characters.

For example, to only consider data for the upsamplers suffixed with
:command:`_srgb`, type:

.. code-block:: console

    $ exquires-correlate -U *_srgb


.. _compare:

-------------------------
Manually comparing images
-------------------------

The :ref:`exquires-run` and :ref:`exquires-update` programs compute
data to be inserted into the database by calling :ref:`exquires-compare`
(see :ref:`compare-module`).

You can call :ref:`exquires-compare` directly on any pair of images with the
same dimensions by using:

.. code-block:: console

    $ exquires-compare my_metric my_image1 my_image2

where :file:`my_image1` and :file:`my_image2` are the images to compare and
:file:`my_metric` is one of the metrics described in :ref:`compare-module`.

By default, :ref:`exquires-compare` expects images with 16 bits per sample:
each value is between 0 and 65535. You can change the maximum value from 65535
to anything you like. For example, to support images with 8 bits per sample
(values between 0 and 255), type one of the following:

.. code-block:: console

    $ exquires-compare my_metric my_image1 my_image2 -m 255
    $ exquires-compare my_metric my_image1 my_image2 --maxval 255


.. _aggregate:

-------------------------
Manually aggregating data
-------------------------

The :ref:`exquires-report` program aggregates the image comparison data
before printing it to standard output or writing it to a file by calling
:ref:`exquires-aggregate`.

You can call :ref:`exquires-aggregate` directly on any list of numbers by
using:

.. code-block:: console

    $ exquires-aggregate my_method my_numbers

where :file:`my_numbers` is a list of numbers separated by spaces and
:file:`my_method` is one of the aggregation methods described in
:ref:`aggregate-module`.

For example, to return the average of a list of numbers, type:

.. code-block:: console

    $ exquires-aggregate l_1 1.2 2.4 3.6 4.8
    3.000000000000000

and to find the maximum, type:

.. code-block:: console

    $ exquires-aggregate l_inf 1.2 2.4 3.6 4.8
    4.800000000000000
