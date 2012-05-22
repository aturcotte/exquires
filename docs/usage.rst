.. _usage-label:

******************
Usage Instructions
******************

=========================
Create a new project file
=========================

A project file is an *ini* file that tells EXQUIRES which of the following
to use:

* Images
* Downsamplers
* Resampling Ratios
* Upsamplers
* Difference Metrics

In order to create a default project file for a specific set of images, type::

    $ exquires-new -p my_project -I my_images

or::

    $ exquires-new --proj my_project --image my_images

where ``my_project`` is a name to identify your project and ``my_images`` is
a list (wildcards are supported) of images with the following properties:

:File Format: TIFF
:Colour Space: sRGB
:Bit Depth: 16 bits/sample (48 bits/pixel)
:Size: 840x840 pixels

If you do not include the ``-p``/``--proj`` or ``-I``/``--image`` options,
like so::

    $ exquires-new

the project name **project1** and the image
`wave.tif <http://exquires.rivetsforbreakfast.com/downloads/wave/wave.tif>`_
will be used to generate the project file ``project1.ini``.

==========================
Customize the project file
==========================

Once a project file has been generated, you can manually edit it to suit your
needs. If you called your project ``my_project``, as we did in the example, the
project file is called **my_project.ini** and you can use your favourite editor
to customize it to suit your needs.

We will look at each section of the project file using a simple example.

* Images::

    # TEST IMAGES
    # Images are 16-bit sRGB TIFFs with a width and height of 840 pixels.
    # Any images that are added must conform to this standard.
    [Images]
    apartments = /home/me/840x840images/apartments.tif
    cabins = /home/me/840x840images/cabins.tif

* Ratios::

    # RESAMPLING RATIOS
    # The test images are downsampled to the specified sizes.
    # Each size is obtained by dividing 840 by the ratio.
    [Ratios]
    2 = 420
    3 = 280
    4 = 240

* Downsamplers::

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

* Upsamplers::

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

* Metrics::

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
    l_1 = compare.py l_1 {0} {1}, aggregate.py l_1 {0}, 0
    l_2 = compare.py l_2 {0} {1}, aggregate.py l_2 {0}, 0
    l_inf = compare.py l_inf {0} {1}, aggregate.py l_inf {0}, 0
    mssim = compare.py mssim {0} {1}, aggregate.py l_1 {0}, 1

=================================
Compute the image difference data
=================================

Once the project file contains the desired configuration, you can compute the
image difference data using::

    $ exquires-run -p my_project

or::

    $ exquires-run --proj my_project

Once again, if you leave out the ``-p``/``--proj`` option, ``exquires-run`` will
look for a project called **project1**.

By default, ``exquires-run`` displays progress information as it computes the
image difference data. If you wish do disable this feature, use the
``-s``/``--silent`` option::

    $ exquires-run -p my_project -s

or::

    $ exquires-run --proj my_project --silent

================================
Update the image difference data
================================

If you make changes to the project file after calling ``exquires-run`` and you
wish to compute only the new data rather than recomputing the entire data set,
use ``exquires-update``, which supports the same options as ``exquires-run``.

========================================
Generate a table of aggregate error data
========================================

Once the image difference data has been computed, you can generate various
aggreagations of the data and either display it in the terminal or write it to
a file.

::

    $ exquires-report -p my_project
