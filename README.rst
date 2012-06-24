***************************************************************************
EXQUIRES: Evaluative and eXtensible QUantitative Image Re-Enlargement Suite
***************************************************************************

* Copyright: (c) 2012 `Adam Turcotte <mailto:adam.turcotte@gmail.com>`_ and
                      `Nicolas Robidoux <mailto:nicolas.robidoux@gmail.com>`_
* License: BSD 2-Clause License
* Requires: Python 2.7 or 3

----

:Web: `exquires.ca <http://exquires.ca>`_
:PyPI: `exquires <http://pypi.python.org/pypi/exquires>`_
:Dev: `exquires on GitHub <http://github.com/aturcotte/exquires>`_

----

============================
Documentation & Instructions
============================

Please visit: http://exquires.ca

===============================
Basic Installation Instructions
===============================

EXQUIRES can be installed from `PyPI <http://pypi.python.org/pypi/exquires>`_
using `pip <http://www.pip-installer.org>`_::
    
    pip install -U exquires

or download the `source distribution from PyPI <http://pypi.python.org/pypi/exquires#downloads>`_, unarchive, and run::

    python setup.py install

==================================
Detailed Installation Instructions
==================================

The following instructions are for Debian/Ubuntu/Mint Linux. For other
platforms, the setup is generally the same, with the exeption of installing
system dependencies.

------------------------------------------
Installing ImageMagick 7 alpha from source
------------------------------------------

* Install dependencies::

    $ sudo apt-get install imagemagick libmagick++-dev

* Download and untar the ImageMagick 7 alpha source::

    $ wget http://www.imagemagick.org/download/alpha/ImageMagick.tar.gz
    $ tar xvfz ImageMagick.tar.gz

* Configure, compile and install ImageMagick::

    $ cd ImageMagick-7.0.0-0
    $ ./configure CFLAGS="-fopenmp -fomit-frame-pointer -O2 -Wall -march=native -pthread" \
                  CXXFLAGS="-O2 -pthread"
    $ make
    $ sudo make install

* Configure the dynamic linker run-time bindings::

    $ sudo ldconfig /usr/local/lib

* (Optional) Ensure that the correct version is now installed::

    $ identify -version
    $ pkg-config --modversion ImageMagick

-------------------
Installing EXQUIRES
-------------------

* Install remaining dependencies::

    $ sudo apt-get install python-pip python-configobj python-dev python-numpy python-vipscc libvips-tools
    
* Install EXQUIRES from PyPI using pip::

    $ sudo pip install -U exquires

---------------------------------------------------
Installing latest EXQUIRES dev branch from git repo
---------------------------------------------------

::

    pip install -e git+http://github.com/aturcotte/exquires.git#egg=exquires

==============
Usage Overview
==============

* Obtain suitable `840x840 test images <http://www.imagemagick.org/download/image-bank/16bit840x840images/>`_
* Use ``exquires-new`` to create a new project file
* Modify the project file to suit your needs
* Use ``exquires-run`` to compute the image difference data
* Use ``exquires-update`` to compute only the new data after editing the project file
* Use ``exquires-report`` to print tables of aggregated data
* Use ``exquires-correlate`` to produce Spearman's rank cross-correlation matrices
