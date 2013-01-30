*************************************************************************
Extensibility Example (Nohalo Image Resampling with LBB Finishing Scheme)
*************************************************************************

============
Introduction
============

Nohalo is a resampler with a mission: smoothly straightening oblique lines
without undesirable side-effects. In particular, without much blurring and with
no added haloing.

In this program, one Nohalo subdivision is performed. The interpolation is
finished with LBB (Locally Bounded Bicubic).

This program is a wrapper around the Nohalo implementation found in VIPS.
Unfortunately, VIPS does not conform to the pixel alignment convention used in
the **EXQUIRES** test suite. In order to alleviate this problem, the leftmost
column of the image is duplicated and the topmost row of the resulting image is
duplicated before performing the resampling step.

.. note::

    This program is designed to enlarge images in a way that preserves the
    aspect ratio of the image.

For more information about Nohalo (a prototype version with bilinear finish
instead of LBB), see:

    CPU, SMP and GPU implementations of Nohalo level 1, a fast co-convex
    antialiasing image resampler by Nicolas Robidoux, Minglun Gong,
    John Cupitt, Adam Turcotte, and Kirk Martinez, in C3S2E '09: Proceedings
    of the 2nd Canadian Conference on Computer Science and Software
    Engineering, p. 185--195, ACM, New York, NY, USA, 2009.
    `<http://doi.acm.org/10.1145/1557626.1557657>`_.


===========================
Installing VIPS from source
===========================

This program requires VIPS 7.30 or later, which is not available through a 
package manager as of this writing. Follow these instructions to install VIPS
from source.

* Install dependencies on Debian/Ubuntu/Mint:

.. code-block:: console

    $ sudo apt-get install gobject-introspection gtk-doc-tools libvips-dev swig

* Download and extract the VIPS source:

.. code-block:: console

    $ wget http://www.vips.ecs.soton.ac.uk/supported/current/vips-7.30.6.tar.gz
    $ tar xvfz vips-7.30.6.tar.gz

* Configure, compile and install VIPS:

.. code-block:: console

    $ cd vips-7.30.6.tar.gz
    $ ./configure
    $ make
    $ sudo make install

* Configure the dynamic linker run-time bindings:

.. code-block:: console

    $ sudo ldconfig /usr/local/lib


=============
Configuration
=============

The Nohalo program relies on an external sRGB profile. A valid profile is
included with the **EXQUIRES** test suite. Before compiling `nohalo.cpp`
you must configure the `profile` variable to point to a valid sRGB profile. If
you have installed **EXQUIRES** for Python 2.7, you should find a valid profile
here::

    /usr/local/lib/python2.7/dist-packages/exquires/sRGB_IEC61966-2-1_black_scaled.icc

If you find the profile at this location, you do not need to configure the
Nohalo program, and can move on to compilation.


===========
Compilation
===========

* The basic syntax to compile the Nohalo image resampler is::

     g++ -Wall -o nohalo -g nohalo.cpp `pkg-config vipsCC --cflags --libs`

* If you have installed **EXQUIRES** for Python 2.7 and wish to install
  Nohalo system-wide for use in the test suite, type::

    sudo g++ -Wall -o /usr/local/bin/nohalo -g \
    /usr/local/lib/python2.7/dist-packages/exquires/examples/nohalo.cpp \
    `pkg-config vipsCC --cflags --libs`


=====
Usage
=====

---------------------
From the command line
---------------------

* To use the Nohalo image resampler with the sRGB colour space, type::

    nohalo input.tif output.tif enlargement_factor 0

* To use the Nohalo image resampler with the linear XYZ colour space, type::

    nohalo input.tif output.tif enlargement_factor 1


---------------------------------
Adding to an **EXQUIRES** project
---------------------------------

* In order to add the sRGB version to an EXQUIRES project file, add the
  following to the `[Upsamplers]` section::

    nohalo {0} {1} {2} 0

* In order to add the linear version to an EXQUIRES project file,, add the
  following to the `[Upsamplers]` section::

    nohalo {0} {1} {2} 1

