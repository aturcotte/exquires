#!/usr/bin/env python
# coding: utf-8
#
#  Copyright (c) 2012, Adam Turcotte (adam.turcotte@gmail.com)
#                      Nicolas Robidoux (nicolas.robidoux@gmail.com)
#  License: BSD 2-Clause License
#
#  This file is part of the
#  EXQUIRES (EXtensible QUantitative Image RESampling) test suite
#

"""Print the result of calling a difference metric on two image files.

  **Difference Metrics:**

    =========== =================================================
    NAME        DESCRIPTION
    =========== =================================================
    srgb_1      :math:`\ell_1` norm in sRGB colour space
    srgb_2      :math:`\ell_2` norm in sRGB colour space
    srgb_4      :math:`\ell_4` norm in sRGB colour space
    srgb_inf    :math:`\ell_\infty` norm in sRGB colour space
    cmc_1       :math:`\ell_1` norm using the CMC(1:1) colour difference
    cmc_2       :math:`\ell_2` norm using the CMC(1:1) colour difference
    cmc_4       :math:`\ell_4` norm using the CMC(1:1) colour difference
    cmc_inf     :math:`\ell_\infty` norm using the CMC(1:1) colour difference
    xyz_1       :math:`\ell_1` norm in XYZ colour space
    xyz_2       :math:`\ell_2` norm in XYZ colour space
    xyz_4       :math:`\ell_4` norm in XYZ colour space
    xyz_inf     :math:`\ell_\infty` norm in XYZ colour space
    blur_1      MSSIM-inspired :math:`\ell_1` norm
    blur_2      MSSIM-inspired :math:`\ell_2` norm
    blur_4      MSSIM-inspired :math:`\ell_4` norm
    blur_inf    MSSIM-inspired :math:`\ell_\infty` norm
    mssim       Mean Structural Similarity Index (MSSIM)
    =========== =================================================

"""

import inspect
import os
from math import exp

from exquires import parsing


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

    .. note::

        By default, a :class:`Metrics` object is configured to operate on
        16-bit images.

    :param image1: first image to compare (reference image)
    :param image2: second image to compare (test image)
    :param L:      highest possible pixel value (default=65535)
    :type image1:  `path`
    :type image2:  `path`
    :type L:       `integer`

    """

    def __init__(self, image1, image2, maxval=65535):
        """Create a new :class:`Metrics` object."""
        vipscc = __import__('vipsCC', globals(), locals(),
                           ['VImage', 'VMask'], -1)
        self.vmask = vipscc.VMask
        self.im1 = vipscc.VImage.VImage(image1)
        self.im2 = vipscc.VImage.VImage(image2)
        self.maxval = maxval
        self.srgb_profile = os.path.join(os.path.dirname(__file__),
                                         'sRGB_IEC61966-2-1_black_scaled.icc')
        self.intent = 1    # IM_INTENT_RELATIVE_COLORIMETRIC

    def srgb_1(self):
        """Compute :math:`\ell_1` error in sRGB colour space.

        The equation for the :math:`\ell_1` error, aka Average Absolute Error
        (AAE), is

        .. math::
            :label: l_1

            \ell_1(x,y) = \\frac{1}{N} \sum_{i=1}^{N} |x_i - y_i|

        where :math:`x` and :math:`y` are the images to compare, each
        consisting of :math:`N` pixels.

        :return: :math:`\ell_1` error
        :rtype:  `float`

        """
        diff = self.im1.subtract(self.im2).abs().avg() / self.maxval
        return diff * 100

    def srgb_2(self):
        """Compute :math:`\ell_2` error in sRGB colour space.

        The equation for the :math:`\ell_2` error, aka Root Mean Squared Error
        (RMSE), is

        .. math::
            :label: l_2

            \ell_2(x,y) = \sqrt{\\frac{1}{N} \sum_{i=1}^{N} (x_i - y_i)^2}

        where :math:`x` and :math:`y` are the images to compare, each
        consisting of :math:`N` pixels.

        :return: :math:`\ell_2` error
        :rtype:  `float`

        """
        diff = self.im1.subtract(self.im2).pow(2).avg() ** 0.5 / self.maxval
        return diff * 100

    def srgb_4(self):
        """Compute :math:`\ell_4` error in sRGB colour space.

        The equation for the :math:`\ell_4` error is

        .. math::
            :label: l_4

            \ell_4(x,y) = \sqrt[4]{\\frac{1}{N} \sum_{i=1}^{N} (x_i - y_i)^4}

        where :math:`x` and :math:`y` are the images to compare, each
        consisting of :math:`N` pixels.

        :return: :math:`\ell_4` error
        :rtype:  `float`

        """
        diff = self.im1.subtract(self.im2).pow(4).avg() ** 0.25 / self.maxval
        return diff * 100

    def srgb_inf(self):
        """Compute :math:`\ell_\infty` error in sRGB colour space.

        The equation for the :math:`\ell_\infty` error, aka Maximum Absolute
        Error (MAE), is

        .. math::
            :label: l_inf

            \ell_\infty(x,y) = \max_{1 \le i \le N} |x_i - y_i|

        where :math:`x` and :math:`y` are the images to compare, each
        consisting of :math:`N` pixels.

        :return: :math:`\ell_\infty` error
        :rtype:  `float`

        """
        diff = self.im1.subtract(self.im2).abs().max() / self.maxval
        return diff * 100

    def mssim(self):
        """Compute the Mean Structural Similarity Index (MSSIM).

        The equation for SSIM is

        .. math::
            :label: ssim

            SSIM(x,y) = \\frac{(2\mu_x\mu_y + C_1)(2\sigma_{xy} + C_2)}
                    {(\mu_x^2 + \mu_y^2 + C_1)(\sigma_x^2 + \sigma_y^2 + C_2)}

        where :math:`\mu_x` and :math:`\mu_y` are the sample means,
        :math:`\sigma_x` and :math:`\sigma_y` are the standard deviations, and
        :math:`\sigma_{xy}` is the correlation coefficient between images
        :math:`x` and :math:`y`.

        Once the SSIM map is computed, the border is trimmed by 5 pixels and
        the mean is returned.

        This version is slightly more efficient than the method proposed by
        Wang et. al. because it reduces the number of Gaussian blurs from 5 to
        4.

        .. note::

            The images are converted to grayscale before applying
            Gaussian blur. The grayscale conversion is equivalent to taking
            the Y channel in YIQ colour space.

        :return: mean SSIM
        :rtype:  `float`

        """
        # Compute the SSIM constants from the highest possible pixel value.
        const1 = (0.01 * self.maxval) ** 2
        const_sum = const1 + (0.03 * self.maxval) ** 2

        # Create the Gaussian blur mask.
        blur = self.vmask.VDMask(11, 1, 1.0, 0, _get_blurlist())

        # Compute a mask for converting the image to grayscale.
        # Note that the result is equivalent to the Y channel of YIQ.
        rgb2gray = self.vmask.VDMask(3, 1, 1, 0, [0.299, 0.587, 0.114])

        # Convert the image to grayscale using Matlab's approach.
        im1_g = self.im1.recomb(rgb2gray)
        im2_g = self.im2.recomb(rgb2gray)

        # Apply Gaussian blur to the grayscale images.
        im1_b = im1_g.convsep(blur)
        im2_b = im2_g.convsep(blur)

        # Compute the SSIM map.
        tmp1 = im1_g.multiply(im2_g).convsep(blur).lin(2, const_sum)
        tmp2 = im1_g.pow(2).add(im2_g.pow(2)).convsep(blur).lin(1, const_sum)
        tmp3 = im1_b.multiply(im2_b).lin(2, const1)
        tmp4 = im2_b.subtract(im1_b).pow(2).add(tmp3)
        tmp5 = tmp3.multiply(tmp1.subtract(tmp3))
        ssim = tmp5.divide(tmp2.subtract(tmp4).multiply(tmp4))

        # Crop the SSIM map and return the average.
        return ssim.extract_area(5, 5,
                                 im1_g.Xsize() - 10, im1_g.Ysize() - 10).avg()

    def blur_1(self):
        """Compute MSSIM-inspired :math:`\ell_1` error.

        This method performs the same greyscale conversion, Gaussian blur, and
        cropping as MSSIM, but returns the :math:`\ell_1` error of the cropped
        image.

        See :eq:`l_1` for details on how the blurred images are compared.

        .. note::

            The images are converted to grayscale before applying
            Gaussian blur. The grayscale conversion is equivalent to taking
            the Y channel in YIQ colour space.

        :return: MSSIM-inspired :math:`\ell_1` error
        :rtype:  `float`

        """

        # Create the Gaussian blur mask.
        blur = self.vmask.VDMask(11, 1, 1.0, 0, _get_blurlist())

        # Compute a mask for converting the image to grayscale.
        # Note that the result is equivalent to the Y channel of YIQ.
        rgb2gray = self.vmask.VDMask(3, 1, 1, 0, [0.299, 0.587, 0.114])

        # Convert the image to grayscale using Matlab's approach.
        im1_g = self.im1.recomb(rgb2gray)
        im2_g = self.im2.recomb(rgb2gray)

        # Apply Gaussian blur, crop the difference and return the l_1 error.
        diff = im1_g.convsep(blur).subtract(im2_g.convsep(blur))
        crop = diff.extract_area(5, 5, im1_g.Xsize() - 10, im1_g.Ysize() - 10)
        return (crop.abs().avg() / self.maxval) * 100

    def blur_2(self):
        """Compute MSSIM-inspired :math:`\ell_2` error.

        This method performs the same greyscale conversion, Gaussian blur, and
        cropping as MSSIM, but returns the :math:`\ell_2` error of the cropped
        image.

        See :eq:`l_2` for details on how the blurred images are compared.

        .. note::

            The images are converted to grayscale before applying
            Gaussian blur. The grayscale conversion is equivalent to taking
            the Y channel in YIQ colour space.

        :return: MSSIM-inspired :math:`\ell_2` error
        :rtype:  `float`

        """

        # Create the Gaussian blur mask.
        blur = self.vmask.VDMask(11, 1, 1.0, 0, _get_blurlist())

        # Compute a mask for converting the image to grayscale.
        # Note that the result is equivalent to the Y channel of YIQ.
        rgb2gray = self.vmask.VDMask(3, 1, 1, 0, [0.299, 0.587, 0.114])

        # Convert the image to grayscale using Matlab's approach.
        im1_g = self.im1.recomb(rgb2gray)
        im2_g = self.im2.recomb(rgb2gray)

        # Apply Gaussian blur, crop the difference and return the l_2 error.
        diff = im1_g.convsep(blur).subtract(im2_g.convsep(blur))
        crop = diff.extract_area(5, 5, im1_g.Xsize() - 10, im1_g.Ysize() - 10)
        return (crop.pow(2).avg() ** 0.5 / self.maxval) * 100

    def blur_4(self):
        """Compute MSSIM-inspired :math:`\ell_4` error.

        This method performs the same greyscale conversion, Gaussian blur, and
        cropping as MSSIM, but returns the :math:`\ell_4` error of the cropped
        image.

        See :eq:`l_4` for details on how the blurred images are compared.

        .. note::

            The images are converted to grayscale before applying
            Gaussian blur. The grayscale conversion is equivalent to taking
            the Y channel in YIQ colour space.

        :return: MSSIM-inspired :math:`\ell_4` error
        :rtype:  `float`

        """

        # Create the Gaussian blur mask.
        blur = self.vmask.VDMask(11, 1, 1.0, 0, _get_blurlist())

        # Compute a mask for converting the image to grayscale.
        # Note that the result is equivalent to the Y channel of YIQ.
        rgb2gray = self.vmask.VDMask(3, 1, 1, 0, [0.299, 0.587, 0.114])

        # Convert the image to grayscale using Matlab's approach.
        im1_g = self.im1.recomb(rgb2gray)
        im2_g = self.im2.recomb(rgb2gray)

        # Apply Gaussian blur, crop the difference and return the l_4 error.
        diff = im1_g.convsep(blur).subtract(im2_g.convsep(blur))
        crop = diff.extract_area(5, 5, im1_g.Xsize() - 10, im1_g.Ysize() - 10)
        return (crop.pow(4).avg() ** 0.25 / self.maxval) * 100

    def blur_inf(self):
        """Compute MSSIM-inspired :math:`\ell_\infty` error.

        This method performs the same greyscale conversion, Gaussian blur, and
        cropping as MSSIM, but returns the :math:`\ell_\infty` error of the
        cropped image.

        See :eq:`l_inf` for details on how the blurred images are compared.

        .. note::

            The images are converted to grayscale before applying
            Gaussian blur. The grayscale conversion is equivalent to taking
            the Y channel in YIQ colour space.

        :return: MSSIM-inspired :math:`\ell_\infty` error
        :rtype:  `float`

        """

        # Create the Gaussian blur mask.
        blur = self.vmask.VDMask(11, 1, 1.0, 0, _get_blurlist())

        # Compute a mask for converting the image to grayscale.
        # Note that the result is equivalent to the Y channel of YIQ.
        rgb2gray = self.vmask.VDMask(3, 1, 1, 0, [0.299, 0.587, 0.114])

        # Convert the image to grayscale using Matlab's approach.
        im1_g = self.im1.recomb(rgb2gray)
        im2_g = self.im2.recomb(rgb2gray)

        # Apply Gaussian blur, crop the difference and return the l_inf error.
        diff = im1_g.convsep(blur).subtract(im2_g.convsep(blur))
        crop = diff.extract_area(5, 5, im1_g.Xsize() - 10, im1_g.Ysize() - 10)
        return (crop.abs().max() / self.maxval) * 100

    def cmc_1(self):
        """Compute :math:`\ell_1` error in Uniform Colour Space (UCS).

        This method imports the images into Lab colour space, then calculates
        delta-E CMC(1:1) and returns the average.

        See :eq:`l_1` for details on how the standard :math:`\ell_1` norm is
        computed.

        :return: :math:`\ell_1` error in Uniform Colour Space (UCS)
        :rtype:  `float`

        """
        lab1 = self.im1.icc_import(self.srgb_profile, self.intent)
        lab2 = self.im2.icc_import(self.srgb_profile, self.intent)
        return lab1.dECMC_fromLab(lab2).avg()

    def cmc_2(self):
        """Compute :math:`\ell_2` error in Uniform Colour Space (UCS).

        This method imports the images into Lab colour space, then calculates
        delta-E CMC(1:1) and returns the :math:`\ell_2` norm.

        See :eq:`l_2` for details on how the standard :math:`\ell_2` norm is
        computed.

        :return: :math:`\ell_2` error in Uniform Colour Space (UCS)
        :rtype:  `float`

        """
        lab1 = self.im1.icc_import(self.srgb_profile, self.intent)
        lab2 = self.im2.icc_import(self.srgb_profile, self.intent)
        return lab1.dECMC_fromLab(lab2).pow(2).avg() ** 0.5

    def cmc_4(self):
        """Compute :math:`\ell_4` error in Uniform Colour Space (UCS).

        This method imports the images into Lab colour space, then calculates
        delta-E CMC(1:1) and returns the :math:`\ell_4` norm.

        See :eq:`l_4` for details on how the standard :math:`\ell_4` norm is
        computed.

        :return: :math:`\ell_4` error in Uniform Colour Space (UCS)
        :rtype:  `float`

        """
        lab1 = self.im1.icc_import(self.srgb_profile, self.intent)
        lab2 = self.im2.icc_import(self.srgb_profile, self.intent)
        return lab1.dECMC_fromLab(lab2).pow(4).avg() ** 0.25

    def cmc_inf(self):
        """Compute :math:`\ell_\infty` error in Uniform Colour Space (UCS).

        This method imports the images into Lab colour space, then calculates
        delta-E CMC(1:1) and returns the :math:`\ell_\infty` norm.

        See :eq:`l_inf` for details on how the standard :math:`\ell_\infty`
        norm is computed.

        :return: :math:`\ell_\infty` error in Uniform Colour Space (UCS)
        :rtype:  `float`

        """
        lab1 = self.im1.icc_import(self.srgb_profile, self.intent)
        lab2 = self.im2.icc_import(self.srgb_profile, self.intent)
        return lab1.dECMC_fromLab(lab2).max()

    def xyz_1(self):
        """Compute :math:`\ell_1` error in XYZ Colour Space.

        This method imports the images into XYZ colour space, then calculates
        the :math:`\ell_1` error.

        See :eq:`l_1` for details on how the standard :math:`\ell_1` norm is
        computed.

        :return: :math:`\ell_1` error in XYZ Colour Space
        :rtype:  `float`

        """
        xyz1 = self.im1.icc_import(self.srgb_profile, self.intent).Lab2XYZ()
        xyz2 = self.im2.icc_import(self.srgb_profile, self.intent).Lab2XYZ()
        return xyz1.subtract(xyz2).abs().avg()

    def xyz_2(self):
        """Compute :math:`\ell_2` error in XYZ Colour Space.

        This method imports the images into XYZ colour space, then calculates
        the :math:`\ell_2` error.

        See :eq:`l_2` for details on how the standard :math:`\ell_2` norm is
        computed.

        :return: :math:`\ell_2` error in XYZ Colour Space
        :rtype:  `float`

        """
        xyz1 = self.im1.icc_import(self.srgb_profile, self.intent).Lab2XYZ()
        xyz2 = self.im2.icc_import(self.srgb_profile, self.intent).Lab2XYZ()
        return xyz1.subtract(xyz2).pow(2).avg() ** 0.5

    def xyz_4(self):
        """Compute :math:`\ell_4` error in XYZ Colour Space.

        This method imports the images into XYZ colour space, then calculates
        the :math:`\ell_4` error.

        See :eq:`l_4` for details on how the standard :math:`\ell_4` norm is
        computed.

        :return: :math:`\ell_4` error in XYZ Colour Space
        :rtype:  `float`

        """
        xyz1 = self.im1.icc_import(self.srgb_profile, self.intent).Lab2XYZ()
        xyz2 = self.im2.icc_import(self.srgb_profile, self.intent).Lab2XYZ()
        return xyz1.subtract(xyz2).pow(4).avg() ** 0.25

    def xyz_inf(self):
        """Compute :math:`\ell_\infty` error in XYZ Colour Space.

        This method imports the images into XYZ colour space, then calculates
        the :math:`\ell_\infty` error.

        See :eq:`l_inf` for details on how the standard :math:`\ell_\infty`
        norm is computed.

        :return: :math:`\ell_\infty` error in XYZ Colour Space
        :rtype:  `float`

        """
        xyz1 = self.im1.icc_import(self.srgb_profile, self.intent).Lab2XYZ()
        xyz2 = self.im2.icc_import(self.srgb_profile, self.intent).Lab2XYZ()
        return xyz1.subtract(xyz2).abs().max()


def _get_blurlist():
    """Private method to return a Gaussian blur mask.

    .. note::

        This is a private function called by :meth:`~Metrics.blur_1`,
        :meth:`~Metrics.blur_2`, :meth:`~Metrics.blur_4`,
        :meth:`~Metrics.blur_inf`, and :meth:`~Metrics.mssim`.

    """

    # Compute the raw Gaussian blur coefficients.
    blur_sigma = 1.5
    blur_divisor = 2 * blur_sigma * blur_sigma
    rawblur1 = exp(-1 / blur_divisor)
    rawblur2 = exp(-4 / blur_divisor)
    rawblur3 = exp(-9 / blur_divisor)
    rawblur4 = exp(-16 / blur_divisor)
    rawblur5 = exp(-25 / blur_divisor)

    # Normalize the raw Gaussian blur coefficients.
    rawblursum = rawblur1 + rawblur2 + rawblur3 + rawblur4 + rawblur5
    blur_normalizer = 2 * rawblursum + 1
    blur0 = 1 / blur_normalizer
    blur1 = rawblur1 / blur_normalizer
    blur2 = rawblur2 / blur_normalizer
    blur3 = rawblur3 / blur_normalizer
    blur4 = rawblur4 / blur_normalizer
    blur5 = rawblur5 / blur_normalizer

    # Return the Gaussian blur mask as a list.
    return [blur5, blur4, blur3, blur2, blur1,
            blur0, blur1, blur2, blur3, blur4, blur5]


def main():
    """Run :ref:`exquires-compare`."""

    # Obtain a list of error metrics that can be called.
    metrics = []
    methods = inspect.getmembers(Metrics, predicate=inspect.ismethod)
    for method in methods[1:]:
        metrics.append(method[0])

    # Define the command-line argument parser.
    parser = parsing.ExquiresParser(description=__doc__)
    parser.add_argument('metric', type=str, metavar='METRIC', choices=metrics,
                        help='the difference metric to use')
    parser.add_argument('image1', type=str, metavar='IMAGE_1',
                        help='the first image to compare')
    parser.add_argument('image2', type=str, metavar='IMAGE_2',
                        help='the second image to compare')
    parser.add_argument('-m', '--maxval', type=int, metavar='MAX_LEVEL',
                        default=65535,
                        help='the maximum pixel value (default: 65535)')

    # Attempt to parse the command-line arguments.
    args = parser.parse_args()

    # Attempt to call the chosen metric on the specified images.
    vipscc = __import__('vipsCC', globals(), locals(), ['VError'], -1)
    try:
        # Print the result with 15 digits after the decimal.
        metric = Metrics(args.image1, args.image2, args.maxval)
        print '%.15f' % getattr(metric, args.metric)()
    except vipscc.VError.VError, error:
        parser.error(str(error))

if __name__ == '__main__':
    main()
