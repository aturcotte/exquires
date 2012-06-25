.. _setup-label:

**********************************
Detailed Installation Instructions
**********************************

The following instructions are for Debian/Ubuntu/Mint Linux. For other
platforms, the setup is generally the same, with the exeption of installing
system dependencies.

============
Requirements
============

**EXQUIRES** requires `ImageMagick <http://www.imagemagick.org>`_ **7** from
May 13, 2012 or later (due to changes to the Kaiser filter),
`VIPS <http://www.vips.ecs.soton.ac.uk/>`_ **7.24** or newer,
`Python <http://python.org>`_ **2.7**, and the Python packages
`ConfigObj <http://www.voidspace.org.uk/python/configobj.html>`_ and
`NumPy <http://numpy.scipy.org/>`_.

==========================================
Installing ImageMagick 7 alpha from source
==========================================

* Install dependencies on Debian/Ubuntu/Mint:

.. code-block:: console

    $ sudo apt-get install imagemagick libmagick++-dev subversion

* Download the ImageMagick 7 development source:

.. code-block:: console

    $ svn co https://subversion.imagemagick.org/subversion/ImageMagick-Windows/trunk/ ImageMagick

* Configure, compile and install ImageMagick:

.. code-block:: console

    $ cd ImageMagick/ImageMagick
    $ CFLAGS="-march=native -O2" CXXFLAGS="-march=native -O2" ./configure --enable-hdri
    $ make
    $ sudo make install

* Configure the dynamic linker run-time bindings:

.. code-block:: console

    $ sudo ldconfig /usr/local/lib

* (Optional) Ensure that the correct version is now installed:

.. code-block:: console

    $ identify -version
    $ pkg-config --modversion ImageMagick

* Updating ImageMagick development version:

.. code-block:: console

    $ cd ImageMagick/ImageMagick
    $ sudo make uninstall
    $ make clean
    $ svn update
    $ CFLAGS="-march=native -O2" CXXFLAGS="-march=native -O2" ./configure --enable-hdri
    $ make
    $ sudo make install

===================
Installing EXQUIRES
===================

* Install remaining dependencies:

.. code-block:: console

    $ sudo apt-get install python-pip python-configobj python-dev python-numpy python-vipscc libvips-tools
    
* Install **EXQUIRES** from PyPI using pip:

.. code-block:: console

    $ sudo pip install -U exquires

===================================================
Installing latest EXQUIRES dev branch from git repo
===================================================

.. code-block:: console

    sudo pip install -e git+http://github.com/aturcotte/exquires.git#egg=exquires
