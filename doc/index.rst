***************************************************************************
EXQUIRES: Evaluative and eXtensible QUantitative Image Re-Enlargement Suite
***************************************************************************

.. image:: assets/exquires-420.png

----

:Web: `exquires.rivetsforbreakfast.com <http://exquires.rivetsforbreakfast.com>`_
:PyPI: `exquires package <http://pypi.python.org/pypi/exquires>`_
:Dev: `exquires on GitHub <http://github.com/aturcotte/exquires>`_
:License: `BSD 2-Clause License <http://www.opensource.org/licenses/bsd-license.php>`_
:Authors: `Adam Turcotte <mailto:adam.turcotte@gmail.com>`_ and
          `Nicolas Robidoux <mailto:nicolas.robidoux@gmail.com>`_

----

============
Introduction
============

**EXQUIRES** is an open source framework for assessing the performance of image
upsampling methods. An upsampler's performance is based on its ability to
reconstruct test images from various reduced versions. The downsampler used to
reduce the images has an influence on the re-enlargements, so any number of
downsampling methods can be used. The difference between the re-enlargements
and the orginal images is determined by using image comparison metrics. When
viewing the comparison data, it is possible to aggregate across any combination
of test images, downsamplers, and resampling ratios.

The following components of **EXQUIRES** are fully configurable:

* Test Images
* Resampling Ratios
* Downsampling Methods
* Upsampling Methods
* Difference Metrics

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

* Obtain suitable `840x840 test images <http://exquires.rivetsforbreakfast.com/downloads/840x840images.zip>`_
* Use ``exquires-new`` to create a new project file
* Modify the project file to suit your needs
* Use ``exquires-run`` to compute the image difference data
* Use ``exquires-update`` to compute only the new data after editing the project file
* Use ``exquires-report`` to print tables of aggregated data

For more information on using **EXQUIRES**, see :ref:`usage-label`.
