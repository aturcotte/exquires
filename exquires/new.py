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

"""Generate a new project file to use with :ref:`exquires-run`.

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
(:file:`wave.tif`) is included in the project file.

Manually edit this file to customize your project.

"""

from os import path

from configobj import ConfigObj

from exquires import parsing


def _magick(method, **kwargs):
    """Return an ImageMagick resize command as a string.

    Blur and Kaiser beta values are passed as strings to avoid truncation.

    .. note::

        This is a private function called by :func:`_add_default_downsamplers`,
        :func:`_std_int_lin_tensor_mtds_1`, :func:`_std_int_lin_tensor_mtds_2`,
        :func:`_novel_int_lin_flt_mtds`, :func:`_std_nonint_lin_tensor_mtds`,
        :func:`_std_int_ewa_lin_flt_mtds`,
        :func:`_std_nonint_ewa_lin_flt_mtds`, and
        :func:`_novel_nonint_ewa_lin_flt_mtds`.

    :param method: method to use with `-resize` or `-distort Resize`
    :param lin:    `True` if using a linear method
    :param dist:   `True` if using a `-distort Resize` method
    :param lobes:  number of lobes
    :param blur:   blur value
    :param beta:   beta value for Kaiser method
    :type method:  `string`
    :type lin:     `boolean`
    :type dist:    `boolean`
    :type lobes:   `integer`
    :type blur:    `string`
    :type beta:    `string`

    :return:       the ImageMagick command
    :rtype:        `string`

    """

    # Setup keyword arguments.
    lin = kwargs.get('lin', False)
    dist = kwargs.get('dist', False)
    interp = kwargs.get('interp', False)
    lobes = kwargs.get('lobes', 0)
    blur = kwargs.get('blur', None)
    beta = kwargs.get('beta', None)

    # Create and return command string.
    cmd = 'convert {0}'
    if lin:
        cmd = ' '.join([cmd, '-colorspace RGB'])
    if method:
        cmd = ' '.join([cmd, '-filter', method])
    if lobes:
        cmd = ''.join([cmd, ' -define filter:lobes=', str(lobes)])
    if blur:
        cmd = ''.join([cmd, ' -define filter:blur=', blur])
    if beta:
        cmd = ''.join([cmd, ' -define filter:kaiser-beta=', beta])
    if interp:
        cmd = ' '.join([cmd, '-interpolative-resize {3}x{3}'])
    elif dist:
        cmd = ' '.join([cmd, '-distort Resize {3}x{3}'])
    else:
        cmd = ' '.join([cmd, '-resize {3}x{3}'])
    if lin:
        cmd = ' '.join([cmd, '-colorspace sRGB'])
    return ' '.join([cmd, '-strip {1}'])


def _metric(method, aggregator, sort):
    """Return 3-element list defining a metric, an aggregator and a sort order.

    .. note::

        This is a private function called by :func:`_add_default_metrics`.

    :param method:     image comparison metric (see :ref:`exquires-compare`)
    :param aggregator: data aggregator (see :ref:`exquires-aggregate`)
    :param sort:       best-to-worst order (`0`: ascending, `1`: descending)
    :type method:      `string`
    :type aggregator:  `string`
    :type sort:        `integer`

    :return:           metric, aggregator, and sort order
    :rtype:            `list`

    """

    return [' '.join(['exquires-compare', method, '{0} {1}']),
            ' '.join(['exquires-aggregate', aggregator, '{0}']), sort]


def _add_default_images(ini, image):
    """Add the default images to the specified :file:`.ini` file.

    .. note::

        This is a private function called by :func:`main`.

    :param ini: the :file:`.ini` file to modify
    :type ini:  :class:`configobj.ConfigObj`

    """
    # Define the list of images to be resampled.
    key = 'Images'
    ini[key] = {}
    ini.comments[key] = [
        'TEST IMAGES',
        'Images are 16-bit sRGB TIFFs with a width and height of 840 pixels.',
        'Any images that are added must conform to this standard.'
    ]
    for img in image:
        ini[key][path.splitext(path.basename(img))[0]] = path.abspath(img)


def _add_default_ratios(ini):
    """Add the default ratios to the specified :file:`.ini` file.

    .. note::

        This is a private function called by :func:`main`.

    :param ini: the :file:`.ini` file to modify
    :type ini:  :class:`configobj.ConfigObj`

    """
    # Define the list of resampling ratios to use.
    ratios = 'Ratios'
    ini[ratios] = {}
    ini.comments[ratios] = [
        '', 'RESAMPLING RATIOS',
        'The test images are downsampled to the specified sizes.',
        'Each size is obtained by dividing 840 by the ratio.'
    ]
    ini[ratios]['2'] = '420'
    ini[ratios]['3'] = '280'
    ini[ratios]['4'] = '210'
    ini[ratios]['5'] = '168'
    ini[ratios]['6'] = '140'
    ini[ratios]['7'] = '120'
    ini[ratios]['8'] = '105'


def _add_default_downsamplers(ini):
    """Add the default downsamplers to the specified :file:`.ini` file.

    .. note::

        This is a private function called by :func:`main`.

    :param ini: the :file:`.ini` file to modify
    :type ini:  :class:`configobj.ConfigObj`

    """
    # Define the list of downsamplers to use.
    downs = 'Downsamplers'
    ini[downs] = {}
    ini.comments[downs] = [
        '', 'DOWNSAMPLING COMMANDS',
        'To add a downsampler, provide the command to execute it.',
        'The command can make use of the following replacement fields:',
        '{0} = input image',
        '{1} = output image',
        '{2} = downsampling ratio',
        '{3} = downsampled size (width or height)',
        '',
        'WARNING: Be sure to use a unique name for each downsampler.'
    ]
    ini[downs]['box_srgb'] = _magick('Box')
    ini[downs]['box_linear'] = _magick('Box', lin=True)
    ini[downs]['gaussian_srgb'] = _magick('Gaussian')
    ini[downs]['gaussian_linear'] = _magick('Gaussian', lin=True)
    ini[downs]['ewa_lanczos3_srgb'] = _magick('Lanczos', dist=True)
    ini[downs]['ewa_lanczos3_linear'] = _magick('Lanczos', dist=True, lin=True)
    ini[downs]['lanczos3_srgb'] = _magick('Lanczos')
    ini[downs]['lanczos3_linear'] = _magick('Lanczos', lin=True)
    ini[downs]['nearest_srgb'] = _magick('Triangle', interp=True)
    ini[downs]['nearest_linear'] = _magick('Triangle', interp=True, lin=True)


def _std_int_lin_tensor_mtds_1(ini_ups):
    """Add the 1st part of the standard interpolatory linear tensor methods.

    .. note::

        This is a private function called by :func:`_add_default_upsamplers`.

    :param ini_ups: upsamplers for the specified :file:`.ini` file
    :type ini_ups:  `dict`

    """
    ini_ups['nearest_srgb'] = _magick('Point')
    ini_ups['nearest_linear'] = _magick('Point', lin=True)
    ini_ups['bilinear_srgb'] = _magick('Triangle')
    ini_ups['bilinear_linear'] = _magick('Triangle', lin=True)
    ini_ups['cubic_hermite_srgb'] = _magick('Hermite')
    ini_ups['cubic_hermite_linear'] = _magick('Hermite', lin=True)
    ini_ups['catmull_rom_srgb'] = _magick('Catrom')
    ini_ups['catmull_rom_linear'] = _magick('Catrom', lin=True)
    ini_ups['lanczos2_srgb'] = _magick('Lanczos2')
    ini_ups['lanczos2_linear'] = _magick('Lanczos2', lin=True)
    ini_ups['lanczos3_srgb'] = _magick('Lanczos')
    ini_ups['lanczos3_linear'] = _magick('Lanczos', lin=True)
    ini_ups['lanczos4_srgb'] = _magick('Lanczos', lobes=4)
    ini_ups['lanczos4_linear'] = _magick('Lanczos', lobes=4, lin=True)
    ini_ups['bartlett2_srgb'] = _magick('Bartlett', lobes=2)
    ini_ups['bartlett2_linear'] = _magick('Bartlett', lobes=2, lin=True)
    ini_ups['bartlett3_srgb'] = _magick('Bartlett', lobes=3)
    ini_ups['bartlett3_linear'] = _magick('Bartlett', lobes=3, lin=True)
    ini_ups['bartlett4_srgb'] = _magick('Bartlett')
    ini_ups['bartlett4_linear'] = _magick('Bartlett', lin=True)
    ini_ups['blackman2_srgb'] = _magick('Blackman', lobes=2)
    ini_ups['blackman2_linear'] = _magick('Blackman', lobes=2, lin=True)
    ini_ups['blackman3_srgb'] = _magick('Blackman', lobes=3)
    ini_ups['blackman3_linear'] = _magick('Blackman', lobes=3, lin=True)
    ini_ups['blackman4_srgb'] = _magick('Blackman')
    ini_ups['blackman4_linear'] = _magick('Blackman', lin=True)
    ini_ups['bohman2_srgb'] = _magick('Bohman', lobes=2)
    ini_ups['bohman2_linear'] = _magick('Bohman', lobes=2, lin=True)
    ini_ups['bohman3_srgb'] = _magick('Bohman', lobes=3)
    ini_ups['bohman3_linear'] = _magick('Bohman', lobes=3, lin=True)
    ini_ups['bohman4_srgb'] = _magick('Bohman')
    ini_ups['bohman4_linear'] = _magick('Bohman', lin=True)


def _std_int_lin_tensor_mtds_2(ini_ups):
    """Add the 2nd part of the standard interpolatory linear tensor methods.

    .. note::

        This is a private function called by :func:`_add_default_upsamplers`.

    :param ini_ups: upsamplers for the specified :file:`.ini` file
    :type ini_ups:  `dict`

    """
    ini_ups['cosine2_srgb'] = _magick('Cosine', lobes=2)
    ini_ups['cosine2_linear'] = _magick('Cosine', lobes=2, lin=True)
    ini_ups['cosine3_srgb'] = _magick('Cosine')
    ini_ups['cosine3_linear'] = _magick('Cosine', lin=True)
    ini_ups['cosine4_srgb'] = _magick('Cosine', lobes=4)
    ini_ups['cosine4_linear'] = _magick('Cosine', lobes=4, lin=True)
    ini_ups['hamming2_srgb'] = _magick('Hamming', lobes=2)
    ini_ups['hamming2_linear'] = _magick('Hamming', lobes=2, lin=True)
    ini_ups['hamming3_srgb'] = _magick('Hamming', lobes=3)
    ini_ups['hamming3_linear'] = _magick('Hamming', lobes=3, lin=True)
    ini_ups['hamming4_srgb'] = _magick('Hamming')
    ini_ups['hamming4_linear'] = _magick('Hamming', lin=True)
    ini_ups['parzen2_srgb'] = _magick('Parzen', lobes=2)
    ini_ups['parzen2_linear'] = _magick('Parzen', lobes=2, lin=True)
    ini_ups['parzen3_srgb'] = _magick('Parzen', lobes=3)
    ini_ups['parzen3_linear'] = _magick('Parzen', lobes=3, lin=True)
    ini_ups['parzen4_srgb'] = _magick('Parzen')
    ini_ups['parzen4_linear'] = _magick('Parzen', lin=True)
    ini_ups['welch2_srgb'] = _magick('Welsh', lobes=2)
    ini_ups['welch2_linear'] = _magick('Welsh', lobes=2, lin=True)
    ini_ups['welch3_srgb'] = _magick('Welsh')
    ini_ups['welch3_linear'] = _magick('Welsh', lin=True)
    ini_ups['welch4_srgb'] = _magick('Welsh', lobes=4)
    ini_ups['welch4_linear'] = _magick('Welsh', lobes=4, lin=True)
    ini_ups['hann2_srgb'] = _magick('Hanning', lobes=2)
    ini_ups['hann2_linear'] = _magick('Hanning', lobes=2, lin=True)
    ini_ups['hann3_srgb'] = _magick('Hanning', lobes=3)
    ini_ups['hann3_linear'] = _magick('Hanning', lobes=3, lin=True)
    ini_ups['hann4_srgb'] = _magick('Hanning')
    ini_ups['hann4_linear'] = _magick('Hanning', lin=True)


def _novel_int_lin_flt_mtds(ini_ups):
    """Add the novel interpolatory linear filtering methods.

    .. note::

        This is a private function called by :func:`_add_default_upsamplers`.

    :param ini_ups: upsamplers for the specified :file:`.ini` file
    :type ini_ups:  `dict`

    """
    ini_ups['kaiser2_srgb'] = _magick('Kaiser', lobes=2, beta='5.36')
    ini_ups['kaiser2_linear'] = _magick('Kaiser', lobes=2, beta='5.36',
                                         lin=True)
    ini_ups['kaiser3_srgb'] = _magick('Kaiser', lobes=3, beta='8.93')
    ini_ups['kaiser3_linear'] = _magick('Kaiser', lobes=3, beta='8.93',
                                         lin=True)
    ini_ups['kaiser4_srgb'] = _magick('Kaiser', beta='12.15')
    ini_ups['kaiser4_linear'] = _magick('Kaiser', beta='12.15', lin=True)
    ini_ups['kaisersharp2_srgb'] = _magick('Kaiser', lobes=2,
                                          beta='4.7123889803846899')
    ini_ups['kaisersharp2_linear'] = _magick('Kaiser', lobes=2, lin=True,
                                            beta='4.7123889803846899')
    ini_ups['kaisersharp3_srgb'] = _magick('Kaiser', lobes=3,
                                          beta='7.853981633974483')
    ini_ups['kaisersharp3_linear'] = _magick('Kaiser', lobes=3, lin=True,
                                            beta='7.853981633974483')
    ini_ups['kaisersharp4_srgb'] = _magick('Kaiser', beta='10.995574287564276')
    ini_ups['kaisersharp4_linear'] = _magick('Kaiser', lin=True,
                                            beta='10.995574287564276')
    ini_ups['kaisersoft2_srgb'] = _magick('Kaiser', lobes=2,
                                           beta='6.2831853071795865')
    ini_ups['kaisersoft2_linear'] = _magick('Kaiser', lobes=2, lin=True,
                                             beta='6.2831853071795865')
    ini_ups['kaisersoft3_srgb'] = _magick('Kaiser', lobes=3,
                                           beta='9.4247779607693797')
    ini_ups['kaisersoft3_linear'] = _magick('Kaiser', lobes=3, lin=True,
                                             beta='9.4247779607693797')
    ini_ups['kaisersoft4_srgb'] = _magick('Kaiser', beta='12.566370614359173')
    ini_ups['kaisersoft4_linear'] = _magick('Kaiser', lin=True,
                                             beta='12.566370614359173')


def _std_nonint_lin_tensor_mtds(ini_ups):
    """Add the standard non-interpolatory linear tensor methods.

    .. note::

        This is a private function called by :func:`_add_default_upsamplers`.

    :param ini_ups: upsamplers for the specified :file:`.ini` file
    :type ini_ups:  `dict`

    """
    ini_ups['quadratic_b_spline_srgb'] = _magick('Quadratic')
    ini_ups['quadratic_b_spline_linear'] = _magick('Quadratic', lin=True)
    ini_ups['cubic_b_spline_srgb'] = _magick('Cubic')
    ini_ups['cubic_b_spline_linear'] = _magick('Cubic', lin=True)
    ini_ups['mitchell_netravali_srgb'] = _magick(None)
    ini_ups['mitchell_netravali_linear'] = _magick(None, lin=True)


def _std_int_ewa_lin_flt_mtds(ini_ups):
    """Add the standard interpolatory EWA linear filtering methods.

    .. note::

        This is a private function called by :func:`_add_default_upsamplers`.

    :param ini_ups: upsamplers for the specified :file:`.ini` file
    :type ini_ups:  `dict`

    """
    ini_ups['ewa_teepee_srgb'] = _magick('Triangle', dist=True)
    ini_ups['ewa_teepee_linear'] = _magick('Triangle', dist=True, lin=True)
    ini_ups['ewa_hermite_srgb'] = _magick('Hermite', dist=True)
    ini_ups['ewa_hermite_linear'] = _magick('Hermite', dist=True, lin=True)


def _std_nonint_ewa_lin_flt_mtds(ini_ups):
    """Add the standard non-interpolatory EWA linear filtering methods.

    .. note::

        This is a private function called by :func:`_add_default_upsamplers`.

    :param ini_ups: upsamplers for the specified :file:`.ini` file
    :type ini_ups:  `dict`

    """
    ini_ups['ewa_quadratic_b_spline_srgb'] = _magick('Quadratic', dist=True)
    ini_ups['ewa_quadratic_b_spline_linear'] = _magick('Quadratic', dist=True,
                                                       lin=True)
    ini_ups['ewa_cubic_b_spline_srgb'] = _magick('Spline', dist=True)
    ini_ups['ewa_cubic_b_spline_linear'] = _magick('Spline', dist=True,
                                                   lin=True)
    ini_ups['ewa_lanczos2_srgb'] = _magick('Lanczos2', dist=True)
    ini_ups['ewa_lanczos2_linear'] = _magick('Lanczos2', dist=True, lin=True)
    ini_ups['ewa_lanczos3_srgb'] = _magick('Lanczos', dist=True)
    ini_ups['ewa_lanczos3_linear'] = _magick('Lanczos', dist=True, lin=True)
    ini_ups['ewa_lanczos4_srgb'] = _magick('Lanczos', lobes=4, dist=True)
    ini_ups['ewa_lanczos4_linear'] = _magick('Lanczos', lobes=4, dist=True,
                                             lin=True)


def _novel_nonint_ewa_lin_flt_mtds(ini_ups):
    """Add the novel non-interpolatory EWA linear filtering methods.

    .. note::

        This is a private function called by :func:`_add_default_upsamplers`.

    :param ini_ups: upsamplers for the specified :file:`.ini` file
    :type ini_ups:  `dict`

    """
    ini_ups['ewa_robidoux_srgb'] = _magick(None, dist=True)
    ini_ups['ewa_robidoux_linear'] = _magick(None, dist=True, lin=True)
    ini_ups['ewa_mitchell_netravali_srgb'] = _magick('Mitchell', dist=True)
    ini_ups['ewa_mitchell_netravali_linear'] = _magick('Mitchell', dist=True,
                                                       lin=True)
    ini_ups['ewa_robidouxsharp_srgb'] = _magick('RobidouxSharp', dist=True)
    ini_ups['ewa_robidouxsharp_linear'] = _magick('RobidouxSharp', dist=True,
                                                   lin=True)
    ini_ups['ewa_catmull_rom_srgb'] = _magick('Catrom', dist=True)
    ini_ups['ewa_catmull_rom_linear'] = _magick('Catrom', dist=True, lin=True)
    ini_ups['ewa_lanczosradius2_srgb'] = _magick('LanczosRadius', dist=True,
                                                  lobes=2)
    ini_ups['ewa_lanczosradius2_linear'] = _magick('LanczosRadius', dist=True,
                                                    lobes=2,
                                                    lin=True)
    ini_ups['ewa_lanczosradius3_srgb'] = _magick('LanczosRadius', dist=True)
    ini_ups['ewa_lanczosradius3_linear'] = _magick('LanczosRadius', dist=True,
                                                    lin=True)
    ini_ups['ewa_lanczosradius4_srgb'] = _magick('LanczosRadius', lobes=4,
                                                  dist=True)
    ini_ups['ewa_lanczosradius4_linear'] = _magick('LanczosRadius', lobes=4,
                                                    dist=True, lin=True)
    ini_ups['ewa_lanczos2sharp_srgb'] = _magick('Lanczos2', dist=True,
                                                blur='.9580278036312191')
    ini_ups['ewa_lanczos2sharp_linear'] = _magick('Lanczos2', dist=True,
                                                  blur='.9580278036312191',
                                                  lin=True)
    ini_ups['ewa_lanczos3sharp_srgb'] = _magick('Lanczos', dist=True,
                                                blur='.9891028367558475')
    ini_ups['ewa_lanczos3sharp_linear'] = _magick('Lanczos', dist=True,
                                                  blur='.9891028367558475',
                                                  lin=True)
    ini_ups['ewa_lanczos4sharp_srgb'] = _magick('Lanczos', lobes=4, dist=True,
                                                blur='.9870395083298263')
    ini_ups['ewa_lanczos4sharp_linear'] = _magick('Lanczos', lobes=4,
                                                  dist=True, lin=True,
                                                  blur='.9870395083298263')
    ini_ups['ewa_lanczos2sharpest_srgb'] = _magick('Lanczos2', dist=True,
                                                   blur='.88826421508540347')
    ini_ups['ewa_lanczos2sharpest_linear'] = _magick('Lanczos2', dist=True,
                                                     blur='.88826421508540347',
                                                     lin=True)
    ini_ups['ewa_lanczos3sharpest_srgb'] = _magick('Lanczos', dist=True,
                                                   blur='.88549061701764')
    ini_ups['ewa_lanczos3sharpest_linear'] = _magick('Lanczos', dist=True,
                                                     blur='.88549061701764',
                                                     lin=True)
    ini_ups['ewa_lanczos4sharpest_srgb'] = _magick('Lanczos', lobes=4,
                                                   dist=True,
                                                   blur='.88451002338585141')
    ini_ups['ewa_lanczos4sharpest_linear'] = _magick('Lanczos', lobes=4,
                                                     dist=True, lin=True,
                                                     blur='.88451002338585141')


def _add_default_upsamplers(ini):
    """Add the default upsamplers to the specified :file:`.ini` file.

    .. note::

        This is a private function called by :func:`main`.

    :param ini: the :file:`.ini` file to modify
    :type ini:  :class:`configobj.ConfigObj`

    """
    # Define the list of upsamplers to use.
    ups = 'Upsamplers'
    ini[ups] = {}
    ini.comments[ups] = [
        '', 'UPSAMPLING COMMANDS',
        'To add an upsampler, provide the command to execute it.',
        'The command can make use of the following replacement fields:',
        '{0} = input image',
        '{1} = output image',
        '{2} = upsampling ratio',
        '{3} = upsampled size (always 840)'
    ]

    _std_int_lin_tensor_mtds_1(ini[ups])
    _std_int_lin_tensor_mtds_2(ini[ups])
    _novel_int_lin_flt_mtds(ini[ups])
    _std_nonint_lin_tensor_mtds(ini[ups])
    _std_int_ewa_lin_flt_mtds(ini[ups])
    _std_nonint_ewa_lin_flt_mtds(ini[ups])
    _novel_nonint_ewa_lin_flt_mtds(ini[ups])


def _add_default_metrics(ini):
    """Add the default metrics to the specified :file:`.ini` file.

    .. note::

        This is a private function called by :func:`main`.

    :param ini: the :file:`.ini` file to modify
    :type ini:  :class:`configobj.ConfigObj`

    """
    # Define the list of error metrics to use.
    metrics = 'Metrics'
    ini[metrics] = {}
    ini.comments[metrics] = [
        '', 'IMAGE DIFFERENCE METRICS AND AGGREGATORS',
        'Each metric must be associated with a data aggregation method.',
        'To add a metric, you must provide the following three items:',
        '',
        '1. Error metric command, using the following replacement fields:',
        '{0} = reference image',
        '{1} = test image',
        '',
        '2. Aggregator command, using the following replacement field:',
        '{0} = list of error data to aggregate',
        '',
        '3. Best-to-worst ordering, given as a 0 or 1:',
        '0 = ascending',
        '1 = descending'
    ]
    ini[metrics]['srgb_1'] = _metric('srgb_1', 'l_1', 0)
    ini[metrics]['srgb_2'] = _metric('srgb_2', 'l_2', 0)
    ini[metrics]['srgb_4'] = _metric('srgb_4', 'l_4', 0)
    ini[metrics]['srgb_inf'] = _metric('srgb_inf', 'l_inf', 0)
    ini[metrics]['cmc_1'] = _metric('cmc_1', 'l_1', 0)
    ini[metrics]['cmc_2'] = _metric('cmc_2', 'l_2', 0)
    ini[metrics]['cmc_4'] = _metric('cmc_4', 'l_4', 0)
    ini[metrics]['cmc_inf'] = _metric('cmc_inf', 'l_inf', 0)
    ini[metrics]['xyz_1'] = _metric('xyz_1', 'l_1', 0)
    ini[metrics]['xyz_2'] = _metric('xyz_2', 'l_2', 0)
    ini[metrics]['xyz_4'] = _metric('xyz_4', 'l_4', 0)
    ini[metrics]['xyz_inf'] = _metric('xyz_inf', 'l_inf', 0)
    ini[metrics]['blur_1'] = _metric('blur_1', 'l_1', 0)
    ini[metrics]['blur_2'] = _metric('blur_2', 'l_2', 0)
    ini[metrics]['blur_4'] = _metric('blur_4', 'l_4', 0)
    ini[metrics]['blur_inf'] = _metric('blur_inf', 'l_inf', 0)
    ini[metrics]['mssim'] = _metric('mssim', 'l_1', 1)


def main():
    """Run :ref:`exquires-new`.

    Create a project file to use with :ref:`exquires-run` and
    :ref:`exquires-update`.

    """

    # Construct the path to the default test image.
    this_dir = path.abspath(path.dirname(__file__))
    wave = path.join(this_dir, 'wave.tif')

    # Define the command-line argument parser.
    parser = parsing.ExquiresParser(description=__doc__)
    parser.add_argument('-p', '--proj', metavar='PROJECT', type=str,
                        help='name of the project (default: project1)',
                        default='project1')
    parser.add_argument('-I', '--image', metavar='IMAGE', type=str, nargs='+',
                        help='the test images to use (default: wave.tif)',
                        default=[wave])

    # Attempt to parse the command-line arguments.
    args = parser.parse_args()

    # Create a new project file.
    ini = ConfigObj()
    ini.filename = '.'.join([args.proj, 'ini'])

    _add_default_images(ini, args.image)
    _add_default_ratios(ini)
    _add_default_downsamplers(ini)
    _add_default_upsamplers(ini)
    _add_default_metrics(ini)

    # Write the project file.
    ini.write()

if __name__ == '__main__':
    main()
