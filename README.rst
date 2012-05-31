***************************************************************************
EXQUIRES: Evaluative and eXtensible QUantitative Image Re-Enlargement Suite
***************************************************************************

* Copyright: (c) 2012 `Adam Turcotte <mailto:adam.turcotte@gmail.com>`_ and `Nicolas Robidoux <mailto:nicolas.robidoux@gmail.com>`_
* License: BSD 2-Clause License
* Requires: Python 2.7 or 3

----

:Web: `exquires.rivetsforbreakfast.com <http://exquires.rivetsforbreakfast.com>`_
:PyPI: `exquires <http://pypi.python.org/pypi/exquires>`_
:Dev: `git repo <http://github.com/aturcotte/exquires>`_

----

============================
Documentation & Instructions
============================

Please visit: http://exquires.rivetsforbreakfast.com

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

These instructions are for Debian/Ubuntu/Mint Linux.  For other platforms, the
setup is generally the same, with the exception of installing system
dependencies.  

------------------------------------------
Installing ImageMagick 7 alpha from source
------------------------------------------

* Install dependencies on Debian/Ubuntu/Mint::

    $ sudo apt-get install imagemagick libmagick++-dev

* download and untar the ImageMagick 7 alpha source::

    $ wget http://www.imagemagick.org/download/alpha/ImageMagick.tar.gz
    $ tar xvfz ImageMagick.tar.gz

* configure, compile and install ImageMagick::

    $ cd ImageMagick-7.0.0-0
    $ ./configure CFLAGS="-fopenmp -fomit-frame-pointer -O2 -Wall -march=native -pthread" \
                  CXXFLAGS="-O2 -pthread"
    $ make
    $ sudo make install

* configure the dynamic linker run-time bindings::

    $ sudo ldconfig /usr/local/lib

* (optional) ensure that the correct version is now installed::

    $ identify -version
    $ pkg-config --modversion ImageMagick

-------------------
Installing EXQUIRES
-------------------

* install dependencies::

    $ sudo apt-get install python-pip python-configobj python-numpy python-vipscc libvips-tools
    
* install EXQUIRES from PyPI using pip::

    $ sudo pip install -U exquires

---------------------------------------------------
Installing latest EXQUIRES dev branch from git repo
---------------------------------------------------

::

    pip install -e git+http://github.com/aturcotte/exquires.git#egg=exquires

==============
Usage Overview
==============

* Use ``exquires-new`` to create a new project file
* Modify the project file to suit your needs
* Use ``exquires-run`` to compute the image difference data
* Use ``exquires-update`` to compute only the new data after editing the project file
* Use ``exquires-report`` to print tables of aggregated data
