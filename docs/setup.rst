.. _setup-label:

**********************************
Detailed Installation Instructions
**********************************

The following instructions are for Debian/Ubuntu Linux. For other platforms,
the setup is generally the same, with the exeption of installing system
dependencies.  

============
Requirements
============

**EXQUIRES** requires ImageMagick **7**, VIPS **7.24** or newer,
`Python <http://python.org>`_ **2.7**, and the Python packages
`ConfigObj <http://www.voidspace.org.uk/python/configobj.html>` and
`NumPy <http://numpy.scipy.org/>`.

The following installaton instructions are for Debian/Ubuntu Linux. For other
platforms, the setup is generally the same, with the exception of installing
system dependencies.  

==========================================
Installing ImageMagick 7 alpha from source
==========================================

* Install dependencies on Debian/Ubuntu::

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

===================
Installing EXQUIRES
===================

* Install remaining dependencies::

    $ sudo apt-get install python-pip python-configobj python-numpy python-vipscc libvips-tools
    
* Install EXQUIRES from PyPI using pip::

    $ sudo pip install -U exquires

===================================================
Installing latest EXQUIRES dev branch from git repo
===================================================

::

    pip install -e git+http://github.com/aturcotte/exquires.git#egg=exquires
