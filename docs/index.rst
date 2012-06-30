***************************************************************************
EXQUIRES: Evaluative and eXtensible QUantitative Image Re-Enlargement Suite
***************************************************************************

.. image:: _images/exquires-logo.png

----

:Web: `exquires.ca <http://exquires.ca>`_
:PyPI: `exquires package <http://pypi.python.org/pypi/exquires>`_
:Dev: `exquires on GitHub <http://github.com/aturcotte/exquires>`_
:License: `BSD 2-Clause License <http://www.opensource.org/licenses/bsd-license.php>`_
:Authors: `Adam Turcotte <mailto:adam.turcotte@gmail.com>`_ and
          `Nicolas Robidoux <mailto:nicolas.robidoux@gmail.com>`_

----

============
Introduction
============

**EXQUIRES** is an open source framework for assessing the accuracy of image
upsampling methods. **EXQUIRES** can also be used to compare image difference
metrics, or to measure the impact of various factors, including test image
selection and properties, downsampler choice, resizing ratio, etc.

An upsampler's performance is based on its ability to
reconstruct test images from various reduced versions. The downsampler used to
reduce the images has an influence on the re-enlargements, so any number of
downsampling methods can be used. The difference between the re-enlargements
and the orginal images is determined by using image comparison metrics. When
viewing the comparison data, it is possible to aggregate across any combination
of test images, downsamplers, and resampling ratios.

**EXQUIRES** is fully extensible: External applications can be used alongside
its own to compute downsampled and upsampled images as well as image
difference metrics. The following components of **EXQUIRES** are configurable:

* Test Images
* Resampling Ratios
* Downsampling Methods
* Upsampling Methods
* Difference Metrics

**EXQUIRES** is written in `Python <http://python.org>`_ and makes use of
several modules, including the following:

* `argparse <http://code.google.com/p/argparse/>`_ (handle command-line arguments)
* `configobj <http://www.voidspace.org.uk/python/configobj.html>`_ (create and read :file:`.ini` files)
* `curses <http://docs.python.org/library/curses.html>`_ (display progress information)
* `fnmatch <http://docs.python.org/library/fnmatch.html>`_ (handle wildcard characters)
* `inspect <http://docs.python.org/library/inspect.html>`_ (get a list of methods for a class)
* `numpy <http://numpy.scipy.org/>`_ (apply operations to lists of numbers)
* `re <http://docs.python.org/library/re.html>`_ (handle arguments with hypenated ranges)
* `sqlite3 <http://docs.python.org/library/sqlite3.html>`_ (database to store image comparison data)
* `subprocess <http://docs.python.org/library/subprocess.html>`_ (call external applications)
* `vipsCC <http://www.vips.ecs.soton.ac.uk/index.php?title=Python>`_ (Python interface to `VIPS <http://www.vips.ecs.soton.ac.uk/>`_)

The following image processing applications are also used:

* `ImageMagick <http://www.imagemagick.org>`_ (resample images)
* `VIPS <http://www.vips.ecs.soton.ac.uk/>`_ (compute image difference metrics)

=========
Resources
=========

.. toctree::
    :maxdepth: 1
    
    setup
    usage
    modules
    changelog
    
==================
Basic Installation
==================

**EXQUIRES** can be installed from `PyPI <http://pypi.python.org/pypi/exquires>`_
using `pip <http://www.pip-installer.org>`_::
    
    pip install -U exquires

Alternatively, download the
`source distribution from PyPI <http://pypi.python.org/pypi/exquires#downloads>`_,
unarchive, and run::

    python setup.py install

For more information on installing **EXQUIRES** and its dependencies,
see :ref:`setup-label`.

==============
Usage Overview
==============

* Obtain suitable `16 bit 840x840 test images <http://www.imagemagick.org/download/image-bank/16bit840x840images/>`_
* Use :program:`exquires-new` to create a new project file
* Modify the project file to suit your needs
* Use :program:`exquires-run` to compute the image difference data
* Use :program:`exquires-update` to compute only the new data after editing the project file
* Use :program:`exquires-report` to produce tables of aggregated data
* Use :program:`exquires-correlate` to produce Spearman's rank cross-correlation matrices

For more information on using **EXQUIRES**, see :ref:`usage-label`.
