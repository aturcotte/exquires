*********************************
About the **EXQUIRES** Test Suite
*********************************

.. image:: _images/exquires-logo.png

----

:Website: `<http://exquires.ca>`_
:PyPI:    `<http://pypi.python.org/pypi/exquires>`_
:GitHub:  `<http://github.com/aturcotte/exquires>`_
:License: `BSD 2-Clause License`_
:Authors: `Adam Turcotte`_ and `Nicolas Robidoux`_

.. _BSD 2-Clause License: http://www.opensource.org/licenses/bsd-license.php
.. _Adam Turcotte: mailto:adam.turcotte@gmail.com
.. _Nicolas Robidoux: mailto:nicolas.robidoux@gmail.com

----

=====================
What is **EXQUIRES**?
=====================

The **EXQUIRES** test suite (hereby referred to as **EXQUIRES**) is an open
source framework for assessing the accuracy of image upsampling methods.
**EXQUIRES** can also be used to compare image difference metrics, or to
measure the impact of various factors, including test image selection and
properties, downsampler choice, resizing ratio, etc.

An upsampler's performance is based on its ability to reconstruct test images
from various reduced versions. The downsampler used to reduce the images has an
influence on the re-enlargements, so any number of downsampling methods can be
used. The difference between the re-enlargements and the orginal images is
determined by using image comparison metrics. When viewing the comparison data,
it is possible to aggregate across any combination of test images,
downsamplers, and resampling ratios.

**EXQUIRES** is fully extensible: External applications can be used alongside
its own to compute downsampled and upsampled images as well as image
difference metrics. The following components of **EXQUIRES** are configurable:

* Test Images
* Resampling Ratios
* Downsampling Methods
* Upsampling Methods
* Difference Metrics

===============
Technical Notes
===============

**EXQUIRES** is written in `Python`_ (requiring version 2.7 or higher)
and makes use of several modules, including the following:

.. _Python: http://python.org/

* `argparse`_ -- command-line argument parsing
* `configobj`_ -- reading and writing :file:`.ini` files
* `curses`_ -- displaying progress information
* `fnmatch`_ -- handling wildcard characters
* `inspect`_ -- listing a class' methods
* `numpy`_ -- applying operations to lists of numbers
* `re`_ -- handling arguments with hypenated ranges
* `sqlite3`_ -- database for storing image comparison data
* `subprocess`_ -- calling external applications
* `vipsCC`_ -- Python interface for `VIPS`_

.. _argparse: http://code.google.com/p/argparse/
.. _configobj: http://www.voidspace.org.uk/python/configobj.html
.. _curses: http://docs.python.org/library/curses.html
.. _fnmatch: http://docs.python.org/library/fnmatch.html
.. _inspect: http://docs.python.org/library/inspect.html
.. _numpy: http://numpy.scipy.org/
.. _re: http://docs.python.org/library/re.html
.. _sqlite3: http://docs.python.org/library/sqlite3.html
.. _subprocess: http://docs.python.org/library/subprocess.html
.. _vipsCC: http://www.vips.ecs.soton.ac.uk/index.php?title=Python
.. _VIPS: http://www.vips.ecs.soton.ac.uk/

The following image processing applications are also used:

* `ImageMagick`_ -- resampling images
* `VIPS`_ -- computing image difference metrics

.. _ImageMagick: http://www.imagemagick.org/
.. _VIPS: http://www.vips.ecs.soton.ac.uk/
