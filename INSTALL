***********************
Installing **EXQUIRES**
***********************

===============================
Basic Installation Instructions
===============================

**EXQUIRES** can be installed from `PyPI <http://pypi.python.org/pypi/exquires>`_
using `pip <http://www.pip-installer.org>`_::
    
    pip install -U exquires

Alternatively, download the `source distribution from PyPI
<http://pypi.python.org/pypi/exquires#downloads>`_, unarchive, and run::

    python setup.py install

=============================================
Detailed Installation Instructions for Debian
=============================================

The following instructions are for Debian/Ubuntu/Mint Linux. For other
platforms, the setup is generally the same, with the exception of installing
system dependencies.

------------
Requirements
------------

**EXQUIRES** requires `ImageMagick <http://www.imagemagick.org>`_ 6.8.0-2 or
newer, `VIPS <http://www.vips.ecs.soton.ac.uk/>`_ 7.24 or newer,
`Python <http://python.org>`_ 2.7, and the Python packages
`ConfigObj <http://www.voidspace.org.uk/python/configobj.html>`_ and
`NumPy <http://numpy.scipy.org/>`_.

----------------------------------
Installing ImageMagick from source
----------------------------------

* Install dependencies on Debian/Ubuntu/Mint:

.. code-block:: console

    $ sudo apt-get install imagemagick libmagick++-dev subversion

* Download and extract the ImageMagick source:

.. code-block:: console

    $ wget http://www.imagemagick.org/download/ImageMagick.tar.gz
    $ tar -zxvf ImageMagick.tar.gz

* Configure, compile and install ImageMagick:

.. code-block:: console

    $ cd ImageMagick-6.8.X-X
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

    $ cd ImageMagick-6.8.X-X
    $ sudo make uninstall
    $ make clean
    $ svn update
    $ CFLAGS="-march=native -O2" CXXFLAGS="-march=native -O2" ./configure --enable-hdri
    $ make
    $ sudo make install
    $ sudo ldconfig /usr/local/lib

-----------------------
Installing **EXQUIRES**
-----------------------

* Install remaining dependencies:

.. code-block:: console

    $ sudo apt-get install python-pip python-configobj python-dev python-numpy python-vipscc libvips-tools
    
* Install **EXQUIRES** from PyPI using pip:

.. code-block:: console

    $ sudo pip install -U exquires

-------------------------------------------------
Installing latest **EXQUIRES** development branch
-------------------------------------------------

* The latest development version can be installed from the GitHub repository:

.. code-block:: console

    sudo pip install -e git+http://github.com/aturcotte/exquires.git#egg=exquires
