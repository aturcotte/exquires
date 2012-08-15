**************************
**EXQUIRES** Documentation
**************************

====================
Online Documentation
====================

The documentation for the latest release version of **EXQUIRES** can be
viewed online at `<http://exquires.ca>`_.

==========================
Building the Documentation
==========================

The **EXQUIRES** documentation/website is built using `Sphinx`_.

.. _Sphinx: http://sphinx.pocoo.org/

Before building the documentation, you must first perform the following tasks:

* Install Sphinx (``$ sudo apt-get install python-sphinx``)
* Install **EXQUIRES**

To produce the HTML documentation (same as the online documentation):

* From the ``docs`` directory, run: ``$ make html``
* This will produce HTML documentation in the ``_build/html/`` directory
* Open ``_build/html/index.html`` with your browser

To produce the PDF manual:

* From the ``docs`` directory, run: ``$ make latexpdf``
* This will produce LaTeX files in the ``_build/latex`` directory and run them
  through pdflatex
* Open ``exquires.pdf`` to view the manual.
