***********************************************************************
EANBQH: Exact Area image upsizing with Natural BiQuadratic Histosplines
***********************************************************************

============
Introduction
============

EANBQH is an image resampling method that is well-suited for enlarging images.

For more details regarding this method, see Fast Exact Area Image Upsampling
with Natural Biquadratic Histosplines by Nicolas Robidoux, Adam Turcotte,
Minglun Gong and Annie Tousignant pp.85-96 of Image Analysis and Recognition,
5th International Conference, ICIAR 2008, Póvoa de Varzim, Portugal, June 25-27,
2008. Proceedings, Aurelio C. Campilho, Mohamed S. Kamel (Eds.).
Lecture Notes in Computer Science 5112, Springer 2008, ISBN 978-3-540-69811-1.

**Note:** Currently, only binary-mode PPM (P6) files are supported.


===========
Compilation
===========

* For the version that supports PPM files with 8-bit samples, type::

     gcc -o eanbqh8 eanbqh8.c -fomit-frame-pointer -O2 -Wall -march=native -lm

* For the version that supports PPM files with 16-bit samples, type::

     gcc -o eanbqh16 eanbqh16.c -fomit-frame-pointer -O2 -Wall -march=native -lm


=====
Usage
=====

1. Specify output width::

    eanbqh8  input.ppm output.ppm width
    eanbqh16 input.ppm output.ppm width

2. Specify output height::

    eanbqh8  input.ppm output.ppm -h height
    eanbqh16 input.ppm output.ppm -h height

3. Specify output dimensions::

    eanbqh8  input.ppm output.ppm -d width height
    eanbqh16 input.ppm output.ppm -d width height

4. Specify the scaling factor::

    eanbqh8  input.ppm output.ppm -s scale
    eanbqh16 input.ppm output.ppm -s scale

5. Specify the scaling factor as a percentage::

    eanbqh8  input.ppm output.ppm -p percentage
    eanbqh16 input.ppm output.ppm -p percentage


=======================
EXQUIRES Python Wrapper
=======================

EXQUIRES is designed to work with sRGB TIFF images with 16 bits per sample
(48 bits per pixel) and a width and height of 840 pixels. The eanbqh16 program
is designed to work with binary PPM images with 16 bits per sample
(maxval=65535).

An example of bridging this gap is found in eanbqh.py, which uses ImageMagick
to manage the conversions between the two image formats.
