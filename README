===========================================================================
EXQUIRES: Evaluative and eXtensible QUantitative Image Re-Enlargement Suite
===========================================================================

* Copyright: (c) 2012 Adam Turcotte (adam.turcotte@gmail.com) and Nicolas Robidoux (nicolas.robidoux@gmail.com)
* License: BSD 2-Clause License
* Requires: Python 2.7 or 3

----

:Web: `exquires.rivetsforbreakfast.com <http://exquires.rivetsforbreakfast.com>`_
:PyPI: `exquires <http://pypi.python.org/pypi/exquires>`_
:Dev: `git repo <http://github.com/aturcotte/exquires>`_

----

*******************
Docs / Instructions
*******************

please visit: http://exquires.rivetsforbreakfast.com

***************
Install / Setup
***************

EXQUIRES can be installed from `PyPI <http://pypi.python.org/pypi/exquires>`_ using `pip <http://www.pip-installer.org>`_::
    
    pip install -U exquires

... or download the `source distribution from PyPI <http://pypi.python.org/pypi/exquires#downloads>`_, unarchive, and run::

    python setup.py install

... then use ``exquires-new`` to create a new project file, modify it to suit
your needs, then use ``exquires-run`` to compute the image difference data, and
``exquires-report`` to print tables of aggregated data. If you make changes to
the project file and wish to only compute the new data as opposed to the entire
data set, use ``exquires-update``.

************************
Detailed Install / Setup
************************

These instructions are for Debian/Ubuntu Linux.  For other platforms, the setup
is generally the same, with the exception of installing system dependencies.  

----------------------------------------------
    installing ImageMagick 7 alpha from source
----------------------------------------------

* install dependencies on Debian/Ubuntu::

    $ sudo apt-get install imagemagick libmagick++-dev

* download and untar the ImageMagick 7 alpha source::

    $ wget http://www.imagemagick.org/download/alpha/ImageMagick.tar.gz
    $ tar xvfz ImageMagick.tar.gz

* configure, compile and install ImageMagick::

    $ cd ImageMagick-7.0.0-0
    $ ./configure CFLAGS="-fopenmp -fomit-frame-pointer -O2 -Wall -march=native -pthread" CXXFLAGS="-O2 -pthread"
    $ make
    $ sudo make install

* configure the dynamic linker run-time bindings::

    $ sudo ldconfig /usr/local/lib

* (optional) ensure that the correct version is now installed::

    $ identify -version
    $ pkg-config --modversion ImageMagick

-----------------------------------
    installing exquires system-wide
-----------------------------------

* install dependencies on Debian/Ubuntu::

    $ sudo apt-get install python-pip python-configobj python-numpy python-vipscc libvips-tools
    
* install exquires from PyPI using Pip::

    $ sudo pip install -U exquires


***********
Basic Usage
***********

* create a new project file::

    $ exquires-new -p my_project -I my_images

... where ``my_project`` is a name to identify your project and ``my_images`` is
a list (wildcards are supported) of 840x840 TIFF images with the following
properties:

    * *File Format:* TIFF
    * *Colour Space:* sRGB
    * *Depth:* 16 bits/sample (48 bits/pixel)
    * *Size:* 840x840 pixels

If you do not include the **-p** or **-I** options, like so::

    $ exquires-new

... the project name **project1** and the image
`wave.tif <http://exquires.rivetsforbreakfast.com/downloads/wave/wave.tif>`_
will be used to generate the project file ``project1.ini``.

* compute the image similarity data::

    $ exquires-compute my_test

* print a table of the aggregate error data:

    $ exquires-print my_test
