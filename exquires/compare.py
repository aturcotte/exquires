#!/usr/bin/env python
# coding: utf-8
#
#  Copyright (c) 2012, Adam Turcotte (adam.turcotte@gmail.com)
#                      Nicolas Robidoux (nicolas.robidoux@gmail.com)
#  License: BSD 2-Clause License
#
#  This file is part of
#  EXQUIRES | Evaluative and eXtensible QUantitative Image Re-Enlargement Suite
#

"""Print the result of calling a difference metric on two image files.

    -------------
    Error Metrics
    -------------

    ==========   =====================================================
     NAME         DESCRIPTION
    ==========   =====================================================
     l_1          :math:`\ell_1` norm, aka Average Absolute Error (AAE)
     l_2          :math:`\ell_2` norm, aka Root Mean Squared Error (RMSE)
     l_4          :math:`\ell_4` norm
     l_inf        :math:`\ell_\infty` norm, aka Maximum Absolute Error (MAE)
     cmc_1        :math:`\ell_1` norm in CMC(1:1) colour space
     cmc_2        :math:`\ell_2` norm in CMC(1:1) colour space
     cmc_4        :math:`\ell_4` norm in CMC(1:1) colour space
     cmc_inf      :math:`\ell_\infty` norm in CMC(1:1) colour space
     xyz_1        :math:`\ell_1` norm in XYZ colour space
     xyz_2        :math:`\ell_2` norm in XYZ colour space
     xyz_4        :math:`\ell_4` norm in XYZ colour space
     xyz_inf      :math:`\ell_\infty` norm in XYZ colour space
     blur_1       MSSIM-inspired :math:`\ell_1` norm
     blur_2       MSSIM-inspired :math:`\ell_2` norm
     blur_4       MSSIM-inspired :math:`\ell_4` norm
     blur_inf     MSSIM-inspired :math:`\ell_\infty` norm
     mssim        Mean Structural Similarity Index (MSSIM)
    ==========   =====================================================

"""

import argparse
import inspect
import os
import sys

from parsing import format_doc, ExquiresHelp
from __init__ import __version__ as VERSION


class Metrics(object):

    """This class contains error metrics to be used on sRGB images.

    The :math:`\ell_1`, :math:`\ell_2`, :math:`\ell_4`, and :math:`\ell_\infty`
    metrics are normalized by L, the largest possible pixel value of the input
    images (the lowest is assumed to be 0). The range of output for these
    metrics is [0, 100].

    The MSSIM metric produces output in the range [-1, 1], but it is unlikely
    that a negative value will be produced, as the image features must differ
    greatly. For instance, a pure white image compared with a pure black image
    produces a result slightly greater than 0.

    The CMC and XYZ errors can be slightly outside the range [0, 100], but this
    will not occur for most image pairs.

    """

    def __init__(self, image1, image2, L=65535):
        """This constructor creates a new Metrics object.

        By default, a Metrics object is configured to operate on 16-bit images.

        :param image1: The first image to compare (reference image).
        :param image2: The second image to compare (test image).
        :param L: The highest possible pixel value (default=65535).

        """
        from vipsCC import VImage
        self.i1 = VImage.VImage(image1)
        self.i2 = VImage.VImage(image2)
        self.L = L
        sRGB_file = 'sRGB_IEC61966-2-1_black_scaled.icc'
        self.sRGB_profile = os.path.join(os.path.dirname(__file__), sRGB_file)
        self.intent = 1    # IM_INTENT_RELATIVE_COLORIMETRIC

    def l_1(self):
        """Compute :math:`\ell_1` error, aka Average Absolute Error (AAE).

        The equation for the :math:`\ell_1` error is

        .. math::

            AAE(x,y) = \\frac{1}{N} \sum_{i=1}^{N} |x_i - y_i|

        where :math:`x` and :math:`y` are the images to compare.

        :return: :math:`\ell_1` error

        """
        from vipsCC import VImage
        return (self.i1.subtract(self.i2).abs().avg() / self.L) * 100

    def l_2(self):
        """Compute :math:`\ell_2` error, aka Root Mean Squared Error (RMSE).

        The equation for the :math:`\ell_2` error is

        .. math::

            RMSE(x,y) = \sqrt{\\frac{1}{N} \sum_{i=1}^{N} (x_i - y_i)^2}

        where :math:`x` and :math:`y` are the images to compare.

        :return: :math:`\ell_2` error

        """
        from vipsCC import VImage
        return (self.i1.subtract(self.i2).pow(2).avg() ** 0.5 / self.L) * 100

    def l_4(self):
        """Compute :math:`\ell_4` error.

        The equation for the :math:`\ell_4` error is

        .. math::

            \ell_4(x,y) = \sqrt[4]{\\frac{1}{N} \sum_{i=1}^{N} (x_i - y_i)^4}

        where :math:`x` and :math:`y` are the images to compare.

        :return: :math:`\ell_4` error

        """
        from vipsCC import VImage
        return (self.i1.subtract(self.i2).pow(4).avg() ** 0.25 / self.L) * 100

    def l_inf(self):
        """Compute :math:`\ell_\infty` error, aka Maximum Absolute Error (MAE).

        The equation for the :math:`\ell_\infty` error is

        .. math::

            MAE(x,y) = \max_{1 \le i \le N} |x_i - y_i|

        where :math:`x` and :math:`y` are the images to compare.

        :return: :math:`\ell_\infty` error

        """
        from vipsCC import VImage
        return (self.i1.subtract(self.i2).abs().max() / self.L) * 100

    def mssim(self):
        """Compute the Mean Structural Similarity Index (MSSIM).

        The equation for SSIM is

        .. math::

            SSIM(x,y) = \\frac{(2\mu_x\mu_y + C_1)(2\sigma_{xy} + C_2)}
                    {(\mu_x^2 + \mu_y^2 + C_1)(\sigma_x^2 + \sigma_y^2 + C_2)}

        where :math:`\mu_x` and :math:`\mu_y` are the sample means,
        :math:`\sigma_x` and :math:`\sigma_y` are the standard deviations, and
        :math:`\sigma_{xy}` is the correlation coefficient between images
        :math:`x` and :math:`y`.

        Note that the image is converted to grayscale. ELABORATE.

        Once the SSIM map is computed, the border is trimmed by 5 pixels and
        the mean is returned.

        This version is slightly more efficient than the method proposed by
        Wang et. al. because it reduces the number of Gaussian blurs from 5 to
        4.

        :return: Mean SSIM

        """
        from vipsCC import VImage, VMask

        # Compute the SSIM constants from the highest possible pixel value.
        C1 = (0.01 * self.L) ** 2
        C2 = (0.03 * self.L) ** 2
        Csum = C1 + C2

        # Create the Gaussian blur mask.
        blur = VMask.VDMask(11, 1, 1.0, 0, _get_blurlist())

        # Compute a mask for converting the image to grayscale.
        # Note that the result is equivalent to the Y channel of YIQ.
        rgb2gray = VMask.VDMask(3, 1, 0, 0, [0.299, 0.587, 0.114])

        # Convert the image to grayscale using Matlab's approach.
        x = self.i1.recomb(rgb2gray)
        y = self.i2.recomb(rgb2gray)

        # Apply Gaussian blur to the grayscale images.
        a = x.convsep(blur)
        b = y.convsep(blur)

        # Compute the SSIM map.
        c = x.multiply(y).convsep(blur).lin(2, Csum)
        d = x.pow(2).add(y.pow(2)).convsep(blur).lin(1, Csum)
        e = a.multiply(b).lin(2, C1)
        f = b.subtract(a).pow(2).add(e)
        g = e.multiply(c.subtract(e)).divide(d.subtract(f).multiply(f))

        # Crop the SSIM map and return the average.
        return g.extract_area(5, 5, x.Xsize() - 10, x.Ysize() - 10).avg()

    def blur_1(self):
        """Compute MSSIM-inspired :math:`\ell_1` error.

        This method performs the same greyscale conversion, Gaussian blur, and
        cropping as MSSIM, but returns the :math:`\ell_1` error of the cropped
        image.

        :return: MSSIM-inspired :math:`\ell_1` error.

        """
        from vipsCC import VImage, VMask

        # Create the Gaussian blur mask.
        blur = VMask.VDMask(11, 1, 1.0, 0, _get_blurlist())

        # Compute a mask for converting the image to grayscale.
        # Note that the result is equivalent to the Y channel of YIQ.
        rgb2gray = VMask.VDMask(3, 1, 0, 0, [0.299, 0.587, 0.114])

        # Convert the image to grayscale using Matlab's approach.
        x = self.i1.recomb(rgb2gray)
        y = self.i2.recomb(rgb2gray)

        # Apply Gaussian blur to the grayscale images.
        a = x.convsep(blur)
        b = y.convsep(blur)

        # Crop the difference and return the l_1 error.
        crop = a.subtract(b).extract_area(5, 5, x.Xsize() - 10, x.Ysize() - 10)
        return (crop.abs().avg() / self.L) * 100

    def blur_2(self):
        """Compute MSSIM-inspired :math:`\ell_2` error.

        This method performs the same greyscale conversion, Gaussian blur, and
        cropping as MSSIM, but returns the :math:`\ell_2` error of the cropped
        image.

        :return: MSSIM-inspired :math:`\ell_2` error.

        """
        from vipsCC import VImage, VMask

        # Create the Gaussian blur mask.
        blur = VMask.VDMask(11, 1, 1.0, 0, _get_blurlist())

        # Compute a mask for converting the image to grayscale.
        # Note that the result is equivalent to the Y channel of YIQ.
        rgb2gray = VMask.VDMask(3, 1, 0, 0, [0.299, 0.587, 0.114])

        # Convert the image to grayscale using Matlab's approach.
        x = self.i1.recomb(rgb2gray)
        y = self.i2.recomb(rgb2gray)

        # Apply Gaussian blur to the grayscale images.
        a = x.convsep(blur)
        b = y.convsep(blur)

        # Crop the difference and return the l_2 error.
        crop = a.subtract(b).extract_area(5, 5, x.Xsize() - 10, x.Ysize() - 10)
        return (crop.pow(2).avg() ** 0.5 / self.L) * 100

    def blur_4(self):
        """Compute MSSIM-inspired :math:`\ell_4` error.

        This method performs the same greyscale conversion, Gaussian blur, and
        cropping as MSSIM, but returns the :math:`\ell_4` error of the cropped
        image.

        :return: MSSIM-inspired :math:`\ell_4` error.

        """
        from vipsCC import VImage, VMask

        # Create the Gaussian blur mask.
        blur = VMask.VDMask(11, 1, 1.0, 0, _get_blurlist())

        # Compute a mask for converting the image to grayscale.
        # Note that the result is equivalent to the Y channel of YIQ.
        rgb2gray = VMask.VDMask(3, 1, 0, 0, [0.299, 0.587, 0.114])

        # Convert the image to grayscale using Matlab's approach.
        x = self.i1.recomb(rgb2gray)
        y = self.i2.recomb(rgb2gray)

        # Apply Gaussian blur to the grayscale images.
        a = x.convsep(blur)
        b = y.convsep(blur)

        # Crop the difference and return the l_4 error.
        crop = a.subtract(b).extract_area(5, 5, x.Xsize() - 10, x.Ysize() - 10)
        return (crop.pow(4).avg() ** 0.25 / self.L) * 100

    def blur_inf(self):
        """Compute MSSIM-inspired :math:`\ell_\infty` error.

        This method performs the same greyscale conversion, Gaussian blur, and
        cropping as MSSIM, but returns the :math:`\ell_\infty` error of the
        cropped image.

        :return: MSSIM-inspired :math:`\ell_\infty` error.

        """
        from vipsCC import VImage, VMask

        # Create the Gaussian blur mask.
        blur = VMask.VDMask(11, 1, 1.0, 0, _get_blurlist())

        # Compute a mask for converting the image to grayscale.
        # Note that the result is equivalent to the Y channel of YIQ.
        rgb2gray = VMask.VDMask(3, 1, 0, 0, [0.299, 0.587, 0.114])

        # Convert the image to grayscale using Matlab's approach.
        x = self.i1.recomb(rgb2gray)
        y = self.i2.recomb(rgb2gray)

        # Apply Gaussian blur to the grayscale images.
        a = x.convsep(blur)
        b = y.convsep(blur)

        # Crop the difference and return the l_1 error.
        crop = a.subtract(b).extract_area(5, 5, x.Xsize() - 10, x.Ysize() - 10)
        return (crop.abs().max() / self.L) * 100

    def cmc_1(self):
        """Compute :math:`\ell_1` error in Uniform Colour Space (UCS).

        This method imports the images into Lab colour space, then calculates
        delta-E CMC(1:1) and returns the average.

        :return: :math:`\ell_1` error in Uniform Colour Space (UCS).

        """
        from vipsCC import VImage
        lab1 = self.i1.icc_import(self.sRGB_profile, self.intent)
        lab2 = self.i2.icc_import(self.sRGB_profile, self.intent)
        return lab1.dECMC_fromLab(lab2).avg()

    def cmc_2(self):
        """Compute :math:`\ell_2` error in Uniform Colour Space (UCS).

        This method imports the images into Lab colour space, then calculates
        delta-E CMC(1:1) and returns the :math:`\ell_2` norm.

        :return: :math:`\ell_2` error in Uniform Colour Space (UCS).

        """
        from vipsCC import VImage
        lab1 = self.i1.icc_import(self.sRGB_profile, self.intent)
        lab2 = self.i2.icc_import(self.sRGB_profile, self.intent)
        return lab1.dECMC_fromLab(lab2).pow(2).avg() ** 0.5

    def cmc_4(self):
        """Compute :math:`\ell_4` error in Uniform Colour Space (UCS).

        This method imports the images into Lab colour space, then calculates
        delta-E CMC(1:1) and returns the :math:`\ell_4` norm.

        :return: :math:`\ell_4` error in Uniform Colour Space (UCS).

        """
        from vipsCC import VImage
        lab1 = self.i1.icc_import(self.sRGB_profile, self.intent)
        lab2 = self.i2.icc_import(self.sRGB_profile, self.intent)
        return lab1.dECMC_fromLab(lab2).pow(4).avg() ** 0.25

    def cmc_inf(self):
        """Compute :math:`\ell_\infty` error in Uniform Colour Space (UCS).

        This method imports the images into Lab colour space, then calculates
        delta-E CMC(1:1) and returns the :math:`\ell_\infty` norm.

        :return: :math:`\ell_\infty` error in Uniform Colour Space (UCS).

        """
        from vipsCC import VImage
        lab1 = self.i1.icc_import(self.sRGB_profile, self.intent)
        lab2 = self.i2.icc_import(self.sRGB_profile, self.intent)
        return lab1.dECMC_fromLab(lab2).max()

    def xyz_1(self):
        """Compute :math:`\ell_1` error in XYZ Colour Space.

        This method imports the images into XYZ colour space, then calculates
        the :math:`\ell_1` error.

        :return: :math:`\ell_1` error in XYZ Colour Space.

        """
        from vipsCC import VImage
        xyz1 = self.i1.icc_import(self.sRGB_profile, self.intent).Lab2XYZ()
        xyz2 = self.i2.icc_import(self.sRGB_profile, self.intent).Lab2XYZ()
        return xyz1.subtract(xyz2).abs().avg()

    def xyz_2(self):
        """Compute :math:`\ell_2` error in XYZ Colour Space.

        This method imports the images into XYZ colour space, then calculates
        the :math:`\ell_2` error.

        :return: :math:`\ell_2` error in XYZ Colour Space.

        """
        from vipsCC import VImage
        xyz1 = self.i1.icc_import(self.sRGB_profile, self.intent).Lab2XYZ()
        xyz2 = self.i2.icc_import(self.sRGB_profile, self.intent).Lab2XYZ()
        return xyz1.subtract(xyz2).pow(2).avg() ** 0.5

    def xyz_4(self):
        """Compute :math:`\ell_4` error in XYZ Colour Space.

        This method imports the images into XYZ colour space, then calculates
        the :math:`\ell_4` error.

        :return: :math:`\ell_4` error in XYZ Colour Space.

        """
        from vipsCC import VImage
        xyz1 = self.i1.icc_import(self.sRGB_profile, self.intent).Lab2XYZ()
        xyz2 = self.i2.icc_import(self.sRGB_profile, self.intent).Lab2XYZ()
        return xyz1.subtract(xyz2).pow(4).avg() ** 0.25

    def xyz_inf(self):
        """Compute :math:`\ell_\infty` error in XYZ Colour Space.

        This method imports the images into XYZ colour space, then calculates
        the :math:`\ell_\infty` error.

        :return: :math:`\ell_\infty` error in XYZ Colour Space.

        """
        from vipsCC import VImage
        xyz1 = self.i1.icc_import(self.sRGB_profile, self.intent).Lab2XYZ()
        xyz2 = self.i2.icc_import(self.sRGB_profile, self.intent).Lab2XYZ()
        return xyz1.subtract(xyz2).abs().max()


def _get_blurlist():
    """Private method to return a Gaussian blur mask."""
    from math import exp

    # Compute the raw Gaussian blur coefficients.
    blurSigma = 1.5
    blurDivisor = 2 * blurSigma * blurSigma
    rawblur1 = exp(-1 / blurDivisor)
    rawblur2 = exp(-4 / blurDivisor)
    rawblur3 = exp(-9 / blurDivisor)
    rawblur4 = exp(-16 / blurDivisor)
    rawblur5 = exp(-25 / blurDivisor)

    # Normalize the raw Gaussian blur coefficients.
    rawblursum = rawblur1 + rawblur2 + rawblur3 + rawblur4 + rawblur5
    blurNormalizer = 2 * rawblursum + 1
    blur0 = 1 / blurNormalizer
    blur1 = rawblur1 / blurNormalizer
    blur2 = rawblur2 / blurNormalizer
    blur3 = rawblur3 / blurNormalizer
    blur4 = rawblur4 / blurNormalizer
    blur5 = rawblur5 / blurNormalizer

    # Return the Gaussian blur mask as a list.
    return [blur5, blur4, blur3, blur2, blur1,
            blur0, blur1, blur2, blur3, blur4, blur5]


def main():
    # Obtain a list of error metrics that can be called.
    metrics = []
    methods = inspect.getmembers(Metrics, predicate=inspect.ismethod)
    for method in methods[1:]:
        metrics.append(method[0])

    # Define the command-line argument parser.
    parser = argparse.ArgumentParser(version=VERSION,
                                     description=format_doc(__doc__),
                                     formatter_class=ExquiresHelp)
    parser.add_argument('metric', type=str, metavar='METRIC', choices=metrics,
                        help='the error metric to use')
    parser.add_argument('image1', type=str, metavar='IMAGE_1',
                        help='the first image to compare')
    parser.add_argument('image2', type=str, metavar='IMAGE_2',
                        help='the second image to compare')
    parser.add_argument('-L', type=int, metavar='MAX_LEVEL', default=65535,
                        help='the maximum pixel value (default=65535)')

    # Attempt to parse the command-line arguments.
    try:
        args = parser.parse_args()
    except Exception, e:
        parser.error(str(e))

    # Attempt to call the chosen metric on the specified images.
    from vipsCC import VError
    try:
        # Print the result with 15 digits after the decimal.
        m = Metrics(args.image1, args.image2, args.L)
        print '%.15f' % getattr(m, args.metric)()
    except VError.VError, e:
        parser.error(str(e))

if __name__ == '__main__':
    main()
