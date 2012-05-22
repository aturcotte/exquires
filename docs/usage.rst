.. _usage-label:

******************
Usage Instructions
******************

===========================
Obtain suitable test images
===========================

**EXQUIRES** is designed to use sRGB TIFF images with 16 bits per sample
(48 bits per pixel) and a width and height of 840 pixels. One image
(`wave.tif <http://exquires.rivetsforbreakfast.com/downloads/wave/wave.tif>`_)
is included as a default selection.

A separate distribution of test images converted from RAW is available
`here <http://exquires.rivetsforbreakfast.com/downloads/840x840images.zip>`.
The examples in this section make use of several images from this collection.

=========================
Create a new project file
=========================

A project file is a *.ini* file that tells **EXQUIRES** which of the following
to use:

* Images
* Resampling Ratios
* Downsamplers
* Upsamplers
* Difference Metrics

The basic syntax to create a new project is::

    $ exquires-new

which will create the project file ``project1.ini`` and include the image
`wave.tif <http://exquires.rivetsforbreakfast.com/downloads/wave/wave.tif>`_
along with a default collection of ratios, downsamplers, upsamplers, and
metrics.

In order to specify a project name and a set of test images, type::

    $ exquires-new -p my_project -I my_images

or::

    $ exquires-new --proj my_project --image my_images

where ``my_project`` is a name to identify your project and ``my_images`` is
a list (wildcards are supported) of images with the following properties:

:File Format: TIFF
:Colour Space: sRGB
:Bit Depth: 16 bits/sample (48 bits/pixel)
:Size: 840x840 pixels

To demonstrate, we will create a new project ``example_proj`` using the
`840x840images <http://exquires.rivetsforbreakfast.com/downloads/840x840images.zip>`
collection.

    $ exquires-new -p example_proj -I 840x840images/images/*

==========================
Customize the project file
==========================

Once a project file has been generated, you can manually edit it to suit your
needs. For our example project ``example_proj``, we have a project file
**example_proj.ini** and we will look at each section in detail.

------
Images
------

This section lists the paths to the test images that will be used. We will keep
this example project small by removing all but two of the
`840x840images <http://exquires.rivetsforbreakfast.com/downloads/840x840images.zip>`,
**apartments.tif** and **cabins.tif**::

    # TEST IMAGES
    # Images are 16-bit sRGB TIFFs with a width and height of 840 pixels.
    # Any images that are added must conform to this standard.
    [Images]
    apartments = /home/user/840x840images/images/apartments.tif
    cabins = /home/user/840x840images/images/cabins.tif

Notice that **EXQUIRES** has also assigned default names for these images,
which you can also modify.

------
Ratios
------

This section lists the resampling ratios and specifies the width and
height of the downsampled image for each ratio. Here are the default ratios::

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
of the defaults::

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
your own downsampling method, you must use ``{0}`` and ``{1}`` to specify the
input and output images, and either ``{2}`` or ``{3}`` (or both) to specify
the size of the reduced image.

Also note that the methods suffixed with ``_srgb`` do not apply gamma
correction, meaning that the sRGB images are downsampled using linear averaging
even though sRGB is a non-linear colour space.
The methods suffixed with ``_linear`` convert the input image to linear RGB
before downsampling, then convert the result back to sRGB.

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
method with several Lanczos variations::

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
    eanbqh = python eanbqh.py {0} {1} {3}

Your upsampling program may not be equipped to handle the TIFF formatted images
used by **EXQUIRES**. Likewise, the ``eanbqh16`` program is only compatible
with binary-mode PPM images. An example of bridging this gap is found in
``eanbqh.py``, which uses ImageMagick to manage the conversions between the two
image formats.

-------
Metrics
-------

::

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
