.. _programs:

********
Programs
********

.. _exquires-new:

============
exquires-new
============

**Syntax:**

::

    exquires-new [-h] [-v] [-p PROJECT] [-I IMAGE [IMAGE ...]]


**Description:**

Generate a new project file to use with :ref:`exquires-run`.

The project file is used to specify the following components of the suite:

    * Images ( sRGB TIFF | 16 bits/sample (48/pixel) | 840x840 pixels )
    * Downsamplers
    * Resampling Ratios
    * Upsamplers
    * Difference Metrics

For the specified project name and list of images, a default project file will
be created with the name :file:`PROJECT.ini`, where :file:`PROJECT` is a name
specified using the :option:`-p`\:option:`--proj` option. If a name is not
specified, the default name is :file:`project1`.

Use the :option:`-I`\:option:`--image` option to provide a list of images to
include in the project file. If no images are specified, a default image
(:download:`wave.tif <../exquires/wave.tif>`) is included in the project file.

Manually edit this file to customize your project.


**Optional Arguments:**

================ =================== =================== ============================================
SHORT FLAG       LONG FLAG           ARGUMENTS           DESCRIPTION
================ =================== =================== ============================================
:option:`-h`     :option:`--help`                        show this help message and exit
:option:`-v`     :option:`--version`                     show program's version number and exit
:option:`-p`     :option:`--proj`    `PROJECT`           name of the project (default: `project1`)
:option:`-I`     :option:`--image`   `IMAGE [IMAGE ...]` the test images to use (default: :download:`wave.tif <../exquires/wave.tif>`)
================ =================== =================== ============================================


For additional usage instructions, see :ref:`test-images`, :ref:`new-project`,
and :ref:`custom-project`.

For technical information, see :mod:`new`.


.. _exquires-run:

============
exquires-run
============

**Syntax:**

::

    exquires-run [-h] [-v] [-s] [-p PROJECT]


**Description:**

Compute error data for the entries in the specified project file.

The project file is read to determine which images, downsamplers, ratios,
upsamplers, and metrics to use. If a database file already exists for this
project, it will be backed up and a new one will be created.

Each image will be downsampled by each of the ratios using each of the
downsamplers. The downsampled images will then be upsampled back to their
original size (840x840) using each of the upsamplers. The upsampled images will
be compared to the original images using each of the metrics and the results
will be stored in the database file.

If you make changes to the project file and wish to only compute data for these
changes rather than recomputing everything, use :ref:`exquires-update`.

To view aggregated error data, use :ref:`exquires-report`.


**Optional Arguments:**

================ =================== =================== =========================================
SHORT FLAG       LONG FLAG           ARGUMENTS           DESCRIPTION
================ =================== =================== =========================================
:option:`-h`     :option:`--help`                        show this help message and exit
:option:`-v`     :option:`--version`                     show program's version number and exit
:option:`-s`     :option:`--silent`                      do not display progress information
:option:`-p`     :option:`--proj`    `PROJECT`           name of the project (default: `project1`)
================ =================== =================== =========================================


For additional usage instructions, see :ref:`run`.

For technical information, see :mod:`run`.


.. _exquires-update:

===============
exquires-update
===============

**Syntax:**

::

    exquires-update [-h] [-v] [-s] [-p PROJECT]


**Description:**

Compute new error data for changes to the user-specified project file.

The project file is inspected to determine which changes have been made. Items
that have been removed will result in entries being removed from the database.
Items that have been changed or added will result in new data being computed
and added to the database file. If no changes have been made to the project
file, the database will not be updated.

If you wish to recompute all data based on your project file rather than simply
updating it with the changes, use :ref:`exquires-run`.

To view aggregated error data, use :ref:`exquires-report`.


**Optional Arguments:**

================ =================== =================== =========================================
SHORT FLAG       LONG FLAG           ARGUMENTS           DESCRIPTION
================ =================== =================== =========================================
:option:`-h`     :option:`--help`                        show this help message and exit
:option:`-v`     :option:`--version`                     show program's version number and exit
:option:`-s`     :option:`--silent`                      do not display progress information
:option:`-p`     :option:`--proj`    `PROJECT`           name of the project (default: `project1`)
================ =================== =================== =========================================


For additional usage instructions, see :ref:`update`.

For technical information, see :mod:`update`.


.. _exquires-report:

===============
exquires-report
===============

**Syntax:**

::

    exquires-report [-h] [-v] [-l] [-r | -m] [-p PROJECT] [-f FILE]
                    [-d DIGITS] [-s METRIC] [-U METHOD [METHOD ...]]
                    [-I IMAGE [IMAGE ...]] [-D METHOD [METHOD ...]]
                    [-R RATIO [RATIO ...]] [-M METRIC [METRIC ...]]


**Description:**

Print a formatted table of aggregate image difference data.

Each database table in the current project contains data for a single image,
downsampler, and ratio. Each row represents an upsampler and each column
represents a difference metric. By default, the data across all rows and
columns of all tables is aggregated. Use the appropriate option flags to
aggregate across a subset of the database.


**Optional Arguments:**

================ =================== ===================== =========================================
SHORT FLAG       LONG FLAG           ARGUMENTS             DESCRIPTION
================ =================== ===================== =========================================
:option:`-h`     :option:`--help`                          show this help message and exit
:option:`-v`     :option:`--version`                       show program's version number and exit
:option:`-l`     :option:`--latex`                         print a LaTeX formatted table
:option:`-r`     :option:`--rank`                          print Spearman (fractional) ranks
:option:`-m`     :option:`--merge`                         print merged Spearman ranks
:option:`-p`     :option:`--proj`    `PROJECT`             name of the project (default: `project1`)
:option:`-f`     :option:`--file`    `FILE`                output to file (default: `sys.stdout`)
:option:`-d`     :option:`--digits`  `DIGITS`              total number of digits (default: `4`)
:option:`-s`     :option:`--sort`    `METRIC`              sort using this metric (default: `first`)
:option:`-U`     :option:`--up`      `METHOD [METHOD ...]` upsamplers to consider (default: `all`)
:option:`-I`     :option:`--image`   `IMAGE [IMAGE ...]`   images to consider (default: `all`)
:option:`-D`     :option:`--down`    `METHOD [METHOD ...]` downsamplers to consider (default: `all`)
:option:`-R`     :option:`--ratio`   `RATIO [RATIO ...]`   ratios to consider (default: `all`)
:option:`-M`     :option:`--metric`  `METRIC [METRIC ...]` metrics to consider (default: `all`)
================ =================== ===================== =========================================


**Features:**

 * :option:`-R`/:option:`--ratio` supports hyphenated ranges
   (ex. '2-4 6' gives '2 3 4 6')
 * :option:`-U`/:option:`--up`, :option:`-I`/:option:`--image`,
   :option:`-D`/:option:`--down` and :option:`-M`/:option:`--metric`
   support wildcards


For additional usage instructions, see :ref:`report`.

For technical information, see :mod:`report`.


.. _exquires-correlate:

==================
exquires-correlate
==================

**Syntax:**

::

    exquires-correlate [-h] [-v] [-l] [-p PROJECT] [-f FILE] [-d DIGITS]
                       [-U METHOD [METHOD ...]] [-I IMAGE [IMAGE ...] | -D
                       METHOD [METHOD ...] | -R RATIO [RATIO ...] | -M
                       METRIC [METRIC ...]]


**Description:**

Produce a Spearman's rank cross-correlation matrix for the specified group.

By default, the :option:`-M`/:option:`--metric` option is selected. You can
select one of the following cross-correlation groups:

    * :option:`-I`/:option:`--image`
    * :option:`-D`/:option:`--down`
    * :option:`-R`/:option:`--ratio`
    * :option:`-M`/:option:`--metric`

You can also select which upsamplers to consider when computing the matrix
by using the :option:`-U`/:option:`--up` option.


**Optional Arguments:**

================ =================== ===================== =========================================
SHORT FLAG       LONG FLAG           ARGUMENTS             DESCRIPTION
================ =================== ===================== =========================================
:option:`-h`     :option:`--help`                          show this help message and exit
:option:`-v`     :option:`--version`                       show program's version number and exit
:option:`-l`     :option:`--latex`                         print a LaTeX formatted table
:option:`-p`     :option:`--proj`    `PROJECT`             name of the project (default: `project1`)
:option:`-f`     :option:`--file`    `FILE`                output to file (default: `sys.stdout`)
:option:`-d`     :option:`--digits`  `DIGITS`              total number of digits (default: `4`)
:option:`-a`     :option:`--anchor`  `ANCHOR`              sort using this anchor (default: `none`)
:option:`-U`     :option:`--up`      `METHOD [METHOD ...]` upsamplers to consider (default: `all`)
:option:`-I`     :option:`--image`   `IMAGE [IMAGE ...]`   images to consider (default: `all`)
:option:`-D`     :option:`--down`    `METHOD [METHOD ...]` downsamplers to consider (default: `all`)
:option:`-R`     :option:`--ratio`   `RATIO [RATIO ...]`   ratios to consider (default: `all`)
:option:`-M`     :option:`--metric`  `METRIC [METRIC ...]` metrics to consider (default: `all`)
================ =================== ===================== =========================================


For additional usage instructions, see :ref:`correlate`.

For technical information, see :mod:`correlate`.


.. _exquires-compare:

================
exquires-compare
================

**Syntax:**

::

    exquires-compare [-h] [-v] [-m MAX_LEVEL] METRIC IMAGE_1 IMAGE_2


**Description:**

Print the result of calling a difference metric on two image files.


**Difference Metrics:**

============================================ ==================================================
NAME                                         DESCRIPTION
============================================ ==================================================
:meth:`srgb_1 <~compare.Metrics.srgb_1>`     :math:`\ell_1` norm in sRGB colour space
:meth:`srgb_2 <~compare.Metrics.srgb_2>`     :math:`\ell_2` norm in sRGB colour space
:meth:`srgb_4 <~compare.Metrics.srgb_4>`     :math:`\ell_4` norm in sRGB colour space
:meth:`srgb_inf <~compare.Metrics.srgb_inf>` :math:`\ell_\infty` norm in sRGB colour space
:meth:`cmc_1 <~compare.Metrics.cmc_1>`       :math:`\ell_1` norm in CMC(1:1) colour space
:meth:`cmc_2 <~compare.Metrics.cmc_2>`       :math:`\ell_2` norm in CMC(1:1) colour space
:meth:`cmc_4 <~compare.Metrics.cmc_4>`       :math:`\ell_4` norm in CMC(1:1) colour space
:meth:`cmc_inf <~compare.Metrics.cmc_inf>`   :math:`\ell_\infty` norm in CMC(1:1) colour space
:meth:`xyz_1 <~compare.Metrics.xyz_1>`       :math:`\ell_1` norm in XYZ colour space
:meth:`xyz_2 <~compare.Metrics.xyz_2>`       :math:`\ell_2` norm in XYZ colour space
:meth:`xyz_4 <~compare.Metrics.xyz_4>`       :math:`\ell_4` norm in XYZ colour space
:meth:`xyz_inf <~compare.Metrics.xyz_inf>`   :math:`\ell_\infty` norm in XYZ colour space
:meth:`blur_1 <~compare.Metrics.blur_1>`     MSSIM-inspired :math:`\ell_1` norm
:meth:`blur_2 <~compare.Metrics.blur_2>`     MSSIM-inspired :math:`\ell_2` norm
:meth:`blur_4 <~compare.Metrics.blur_4>`     MSSIM-inspired :math:`\ell_4` norm
:meth:`blur_inf <~compare.Metrics.blur_inf>` MSSIM-inspired :math:`\ell_\infty` norm
:meth:`mssim <~compare.Metrics.mssim>`       Mean Structural Similarity Index (MSSIM)
============================================ ==================================================


**Positional Arguments:**

============== ============================
ARGUMENT       DESCRIPTION
============== ============================
`METRIC`       the difference metric to use
`IMAGE_1`      the first image to compare
`IMAGE_2`      the second image to compare
============== ============================


**Optional Arguments:**

================ =================== ================ ==========================================
SHORT FLAG       LONG FLAG           ARGUMENTS        DESCRIPTION
================ =================== ================ ========================================== 
:option:`-h`     :option:`--help`                     show this help message and exit
:option:`-v`     :option:`--version`                  show program's version number and exit
:option:`-m`     :option:`--maxval`  `MAX_LEVEL`      the maximum pixel value (default: `65535`)
================ =================== ================ ==========================================


For additional usage instructions, see :ref:`compare`.

For technical information, see :mod:`compare`.


.. _exquires-aggregate:

==================
exquires-aggregate
==================

**Syntax:**

::

    exquires-aggregate [-h] [-v] METHOD NUM [NUM ...]


**Description:**

Aggregate a list of values using the selected method.


**Aggregators:**

========================================== ==============================================
NAME                                       DESCRIPTION
========================================== ==============================================
:meth:`l_1 <~aggregate.Aggregate.l_1>`     return the average
:meth:`l_2 <~aggregate.Aggregate.l_2>`     average the squares and return the square root
:meth:`l_4 <~aggregate.Aggregate.l_4>`     average the quads and return the fourth root
:meth:`l_inf <~aggregate.Aggregate.l_inf>` return the maximum
========================================== ==============================================


**Positional Arguments:**

============== ================================
ARGUMENT       DESCRIPTION
============== ================================
`METHOD`       the type of aggregation to use
`NUM`          number to include in aggregation
============== ================================


**Optional Arguments:**

================ =================== ==========================================
SHORT FLAG       LONG FLAG           DESCRIPTION
================ =================== ==========================================
:option:`-h`     :option:`--help`    show the help message and exit
:option:`-v`     :option:`--version` show the program's version number and exit
================ =================== ==========================================


For additional usage instructions, see :ref:`compare`.

For technical information, see :mod:`compare`.

