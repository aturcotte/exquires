.. _usage-label:

******************
Usage Instructions
******************

**EXQUIRES** comes with several programs, each of which include a
:file:`-h/--help` option to display usage information and a
:file:`-v/--version` option to display the version number.

These five main programs can be used to create and maintain a project,
which can be specified with the :file:`-p/--proj` option:

* :program:`exquires-new` (see :ref:`exquires-new-label`)
* :program:`exquires-run` (see :ref:`exquires-run-label`)
* :program:`exquires-update` (see :ref:`exquires-update-label`)
* :program:`exquires-report` (see :ref:`exquires-report-label`)
* :program:`exquires-correlate` (see :ref:`exquires-correlate-label`)

These two programs are responsible for computing image differences
and aggregating the results:

* :program:`exquires-compare` (see :ref:`exquires-compare-label`)
* :program:`exquires-aggregate` (see :ref:`exquires-aggregate-label`)

The following sections will explain how to make use of these programs to
compute data and view aggregated results and cross-correlation matrices.


===========================
Obtain suitable test images
===========================

**EXQUIRES** is designed to use sRGB TIFF images with 16 bits per sample
(48 bits per pixel) and a width and height of 840 pixels. One image
(`wave.tif <http://www.imagemagick.org/download/image-bank/16bit840x840images/images/wave.tif>`_)
is included as a default selection.

A separate distribution of test images converted from RAW is available
`here <http://www.imagemagick.org/download/image-bank/16bit840x840images/>`_.
The examples in this section make use of several images from this collection.

The easiest way to obtain a copy of the image bank is as follows:

.. code-block:: console

    $ wget -r -nH --cut-dirs=3 ftp://ftp.imagemagick.org/pub/ImageMagick/image-bank/16bit840x840images/


.. _exquires-new-label:

=========================
Create a new project file
=========================

A project file is a :file`.ini` file that tells **EXQUIRES** which of the following
to use:

* Images
* Resampling Ratios
* Downsamplers
* Upsamplers
* Difference Metrics

The basic syntax to create a new project is:

.. code-block:: console

    $ exquires-new

which will create the project file :file:`project1.ini` and include the image
`wave.tif <http://www.imagemagick.org/download/image-bank/16bit840x840images/images/wave.tif>`_
along with a default collection of ratios, downsamplers, upsamplers, and
metrics.

In order to specify a project name and a set of test images, type:

.. code-block:: console

    $ exquires-new -p my_project -I my_images

or:

.. code-block:: console

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

==========================
Customize the project file
==========================

Once a project file has been generated, you can manually edit it to suit your
needs. For our example project :command:`example_proj`, we have a project file
:file:`example_proj.ini` and we will look at each section in detail.

------
Images
------

This section lists the paths to the test images that will be used. We will keep
this example project small by removing all but two of the
`16bit840x840images <http://www.imagemagick.org/download/image-bank/16bit840x840images/>`_,
:file:`apartments.tif` and :file:`cabins.tif`.

.. code-block:: ini

    # TEST IMAGES
    # Images are 16-bit sRGB TIFFs with a width and height of 840 pixels.
    # Any images that are added must conform to this standard.
    [Images]
    apartments = /path/to/user/16bit840x840images/images/apartments.tif
    cabins = /path/to/16bit840x840images/images/cabins.tif

Notice that **EXQUIRES** has also assigned default names for these images,
which you can also modify.

------
Ratios
------

This section lists the resampling ratios and specifies the width and
height of the downsampled image for each ratio. Here are the default ratios:

.. code-block:: ini

    # RESAMPLING RATIOS
    # The test images are downsampled to the specified sizes.
    # Each size is obtained by dividing 840 by the ratio.
    [Ratios]
    2 = 420
    3 = 280
    4 = 240
    5 = 168
    6 = 140
    7 = 120
    8 = 105

------------
Downsamplers
------------

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

Note that the **ImageMagick** commands in this example make use of numbered
replacement fields to denote the command-line arguments. If you wish to add
your own downsampling method, you must use :command:`{0}` and :command:`{1}`
to specify the input and output images, and either :command:`{2}` or
:command:`{3}` (or both) to specify the size of the reduced image.

Also note that the methods suffixed with :command:`_srgb` do not apply
gamma correction, meaning that the sRGB images are downsampled using linear
averaging even though sRGB is a non-linear colour space.
The methods suffixed with :command:`_linear` convert the input image to linear RGB
with sRGB primaries before downsampling, then convert the result back to sRGB,
using the **ImageMagick** command :command:`-colorspace`. Such suffixes are
useful because they allow one to separately aggregate the
results of only downsampling or upsampling using the two main "tracks" without
having to list the methods individually. In the same spirit if, for example,
you were to program downsamplers or upsamplers that convert into and out of
sRGB using ICC profiles, we would suggest that you use something like the
:command:`_icc` suffix; if you were to go through the XYZ colourspace, we would
suggest :command:`_xyz`.

----------
Upsamplers
----------

This section lists the upsampling methods that will be used to re-enlarge
each of the downsampled images, and makes use of the same replacement fields as
the Downsamplers section.

Since the purpose of **EXQUIRES** is to assess the accuracy of upsampling
methods, you may wish to add your own method to see how it ranks alongside
pre-existing methods. For example, we can compare our own implementation of
the EANBQH (Exact Area image upsizing with Natural BiQuadratic Histosplines)
method with several Lanczos variations.

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
    lanczos4_srgb = magick {0} -filter Lanczos -define filter:lobes=4 -resize {3}x{3} -strip {1}
    lanczos4_linear = magick {0} -colorspace RGB -filter Lanczos -define filter:lobes=4 -resize {3}x{3} -colorspace sRGB -strip {1}
    eanbqh_srgb = python eanbqh.py {0} {1} {3}
    eanbqh_linear = python eanbqh.py --linear {0} {1} {3}

Your upsampling program may not be equipped to handle the TIFF formatted images
used by **EXQUIRES**. Likewise, the :program:`eanbqh16` program is only
compatible with binary-mode PPM images. An example of bridging this gap is
found in :file:`eanbqh.py`, which uses ImageMagick to manage the conversions
between the two image formats.

-------
Metrics
-------

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
    l_1 = exquires-compare l_1 {0} {1}, exquires-aggregate l_1 {0}, 0
    l_2 = exquires-compare l_2 {0} {1}, exquires-aggregate l_2 {0}, 0
    l_4 = exquires-compare l_4 {0} {1}, exquires-aggregate l_4 {0}, 0
    l_inf = exquires-compare l_inf {0} {1}, exquires-aggregate l_inf {0}, 0
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
:program:`exquires-compare` and :program:`exquires-aggregate`. Also note that
most of the metrics return an error measure, meaning that a lower result is
better. MSSIM, on the other hand, is a similarity index, meaning that a higher
result is better.

For more information on the default metrics, see :ref:`compare-module`.

For more information on the aggregation methods, see :ref:`aggregate-module`.


.. _exquires-run-label:

=================================
Compute the image difference data
=================================

The basic syntax to run a project is:

.. code-block:: console

    $ exquires-run

which will read the project file :file:`project1.ini`, downsample the images
by each ratio using each downsampler, re-enlarge the downsampled images using
each upsampler, and compute the difference using each metric.

You can specify the project name using:

.. code-block:: console

    $ exquires-run -p my_project

or:

.. code-block:: console

    $ exquires-run --proj my_project

By default, :program:`exquires-run` displays progress information.
You can disable this output using:

.. code-block:: console

    $ exquires-run -s

or:

.. code-block:: console

    $ exquires-run --silent

.. warning::

    With large project files, this program can take an *extremely* long time to
    run. For slower machines, it is recommended to start with a small set of
    test images. You can add additional images later and call
    :program:`exquires-update` to compute the new data.


.. _exquires-update-label:

================================
Update the image difference data
================================

If you make changes to the project file after calling :program:`exquires-run`,
running it again will compute all data, including data for unchanged entries
in the project file. To compute only the new data rather than recomputing the
entire data set, use :program:`exquires-update`, which supports the same
options as :program:`exquires-run`.


.. _exquires-report-label:

========================================
Generate a table of aggregate error data
========================================

Once the image difference data has been computed, you can generate various
aggregations of the data and either display it in the terminal or write it to
a file.

The basic syntax to print aggregated data is:

.. code-block:: console

    $ exquires-report

which will read a backup of the project file :file:`project1.ini` that was
created the last time :program:`exquires-run` or :program:`exquires-update` was
called, select the appropriate values from the database, aggregate the data,
and print the results in tabular format to standard output.

As with the other programs, you can specify the project name using:

.. code-block:: console

    $ exquires-report -p my_project

or:

.. code-block:: console

    $ exquires-report --proj my_project


Normally, :program:`exquires-report` prints the data as a plaintext table.
You may wish to include the results in a LaTeX document instead, which can be
done using:

.. code-block:: console

    $ exquires-report -l

or:

.. code-block:: console

    $ exquires-report --latex

Likewise, :program:`exquires-report` normally shows the aggregated data when it
prints the table. You can instead show the Spearman (fractional) ranks for each
upsampling method by using:

.. code-block:: console

    $ exquires-report -r

or:

.. code-block:: console

    $ exquires-report --rank

Furthermore, you can instead merge the Spearman (fractional) ranks across
all specified metrics by using:

.. code-block:: console

    $ exquires-report -m

or:

.. code-block:: console

    $ exquires-report --merge

Whether you display aggregated data or ranks, by default the upsamplers in the
printed table will be sorted from best-to-worst according to the first metric
specified. If you wish to sort according to a different metric (including
those that are not selected to be displayed), use:

.. code-block:: console

    $ exquires-report -s my_metric

or:

.. code-block:: console

    $ exquires-report --sort my_metric

where :file:`my_metric` is one of the metrics defined in the project file.

By default, :program:`exquires-report` prints the aggregated data to standard
output. You can write the aggregated data to a file by using:

.. code-block:: console

    $ exquires-report -f my_file

or:

.. code-block:: console

    $ exquires-report --file my_file

where :file:`my_file` is the file you wish to write the data to.

When producing tables, :program:`exquires-report` will display 4 digits by
default. You can select any number of digits between 1 and 16. For example, you
can change the number of digits to to 6 using:

.. code-block:: console

    $ exquires-report -d 6

or:

.. code-block:: console

    $ exquires-report --digits 6

There are three components that determine which database tables to aggregate
across: images, ratios, and downsamplers. By default, the image comparison data
is aggregated across all images, ratios, and downsampler. If you wish to
aggregate over a subset of the database, use the following options.

You can specify the images to aggregate across by using:

.. code-block:: console

    $ exquires-report -I my_images

or:

.. code-block:: console

    $ exquires-report --image my_images

where :file:`my_images` is a list of images defined in the project file.

.. note::

    The arguments passed to the :file:`-I/--image` option support wildcard
    characters.

You can specify the downsamplers to aggregate across by using:

.. code-block:: console

    $ exquires-report -D my_downsamplers

or:

.. code-block:: console

    $ exquires-report --down my_downsamplers

where :file:`my_downsamplers` is a list of downsamplers defined in the
project file.

.. note::

    The arguments passed to the :file:`-D/--down` option support wildcard
    characters.

You can specify the ratios to aggregate across by using:

.. code-block:: console

    $ exquires-report -R my_ratios

or:

.. code-block:: console

    $ exquires-report --ratio my_ratios


where :file:`my_ratios` is a list of images defined in the project file.

.. note::

    The arguments passed to the :file:`-R/--ratio` option support hyphenated
    ranges.

For example, to aggregate over the ratios **1**, **2**, **3**, **4**, and **6**,
type:

.. code-block:: console

    $ exquires-report -R 1-4 6

Regardless of which images, downsamplers, and ratios the data is aggregated
across, the default behaviour is to display data for each upsampler and
metric, with each row representing an upsampler and each column representing
a metric. If you wish to display only certain rows and columns, use the
following options.

You can specify the metrics (columns) to display by using:

.. code-block:: console

    $ exquires-report -M my_metrics

or:

.. code-block:: console

    $ exquires-report --metric my_metrics

where :file:`my_metrics` is a list of metrics defined in the project file.

.. note::

    The arguments passed to the :file:`-M/--metric` option support wildcard
    characters.

For example, to only display data for the metrics prefixed with
:command:`xyz_`, type:

.. code-block:: console

    $ exquires-report -M xyz_*

You can specify the upsamplers (rows) to display by using:

.. code-block:: console

    $ exquires-report -U my_upsamplers

or:

.. code-block:: console

    $ exquires-report --up my_upsamplers

where :file:`my_upsamplers` is a list of upsamplers defined in the project
file.

.. note::

    The arguments passed to the :file:`-U/--up` option support wildcard
    characters.

For example, to only display data for the upsamplers suffixed with
:command:`_srgb`, type:

.. code-block:: console

    $ exquires-report -U *_srgb


.. _exquires-correlate-label:

===================================================
Generate a Spearman's rank cross-correlation matrix
===================================================

In addition to producing a table of Spearman (fractional) ranks, 

The basic syntax to print a cross-correlation matrix is:

.. code-block:: console

    $ exquires-correlate

which will read a backup of the project file :file:`project1.ini` that was
created the last time :program:`exquires-run` or :program:`exquires-update` was
called, select the appropriate values from the database, aggregate the data,
and print the cross-correlation matrix for all comparison metrics to standard
output.

You can select which upsamplers to consider when computing the matrix
by using the :file:`-U/--up` option.

By default, the :file:`-M/--metric` option is selected. You can select one of
the following cross-correlation groups:

* :file:`-I/--image`
* :file:`-D/--down`
* :file:`-R/--ratio`
* :file:`-M/--metric`

As with the other programs, you can specify the project name using:

.. code-block:: console

    $ exquires-correlate -p my_project

or:

.. code-block:: console

    $ exquires-correlate --proj my_project


Normally, :program:`exquires-correlate` prints the cross-correlation matrix as
a plaintext table. You may wish to include the results in a LaTeX document
instead, which can be done using:

.. code-block:: console

    $ exquires-correlate -l

or:

.. code-block:: console

    $ exquires-correlate --latex

By default, :program:`exquires-correlate` prints the cross-correlation matrix
to standard output. You can write the matrix to a file by using:

.. code-block:: console

    $ exquires-correlate -f my_file

or:

.. code-block:: console

    $ exquires-correlate --file my_file

where :file:`my_file` is the file you wish to write the data to.

When producing a matrix, :program:`exquires-correlate` will display 4 digits by
default. You can select any number of digits between 1 and 16. For example,
you can change the number of digits to to 6 using:

.. code-block:: console

    $ exquires-correlate -d 6

or:

.. code-block:: console

    $ exquires-correlate --digits 6

You can specify the upsamplers (rows) to consider in the computation by using:

.. code-block:: console

    $ exquires-correlate -U my_upsamplers

or:

.. code-block:: console

    $ exquires-correlate --up my_upsamplers

where :file:`my_upsamplers` is a list of upsamplers defined in the project file.

.. note::

    The arguments passed to the :file:`-U/--up` option support wildcard
    characters.

For example, to only consider data for the upsamplers suffixed with
:command:`_srgb`, type:

.. code-block:: console

    $ exquires-correlate -U *_srgb


.. _exquires-compare-label:

=========================
Manually comparing images
=========================

The :program:`exquires-run` and :program:`exquires-update` programs compute
data to be inserted into the database by calling :program:`exquires-compare`
(see :ref:`compare-module`).

You can call :program:`exquires-compare` directly on any pair of images with the
same dimensions by using:

.. code-block:: console

    $ exquires-compare my_metric my_image1 my_image2

where :file:`my_image1` and :file:`my_image2` are the images to compare and
:file:`my_metric` is one of the metrics described in :ref:`compare-module`.

By default, :program:`exquires-compare` expects images with 16 bits per sample:
each value is between 0 and 65535. You can change the maximum value from 65535
to anything you like. For example, to support images with 8 bits per sample
(values between 0 and 255), type:

.. code-block:: console

    $ exquires-compare my_metric my_image1 my_image2 -m 255

or:

.. code-block:: console

    $ exquires-compare my_metric my_image1 my_image2 --maxval 255


.. _exquires-aggregate-label:

=========================
Manually aggregating data
=========================

The :program:`exquires-report` program aggregates the image comparison data
before printing it to standard output or writing it to a file by calling
:program:`exquires-aggregate` (see :ref:`aggregate-module`).

You can call :program:`exquires-aggregate` directly on any list of numbers by
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
