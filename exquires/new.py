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

"""Generate a new project file to use with **exquires-run**.

For the specified project name and list of images, a default project file will
be created with the name $PROJECT.ini. Manually edit this file to customize
your project.

The project file is used to specify the following components of the suite:

 * Images (sRGB TIFF | 16 bits/sample (48/pixel) | 840x840 pixels)
 * Downsamplers
 * Resampling Ratios
 * Upsamplers
 * Difference Metrics

"""

import argparse
import os
from subprocess import check_output

from configobj import ConfigObj

from parsing import format_doc, ExquiresHelp
from __init__ import __version__ as VERSION


def _magick(method, **kwargs):
    """Return an ImageMagick resize command as a string.

    :param method: The method to use with -resize or -distort Resize.
    :param lin: True if using a linear method.
    :param dist: True if using a -distort Resize method.
    :param lobes: Number of lobes.
    :param blur: Blur value.
    :param beta: Beta value for Kaiser method.
    :return: The command string.

    """

    # Setup keyword arguments.
    lin = kwargs.get('lin', False)
    dist = kwargs.get('dist', False)
    lobes = kwargs.get('lobes', 0)
    blur = kwargs.get('blur', 0)
    beta = kwargs.get('beta', 0)

    # Create and return command string.
    cmd = 'magick {0}'
    if lin:
        cmd = ' '.join([cmd, '-colorspace RGB'])
    if method:
        cmd = ' '.join([cmd, '-filter', method])
    if lobes:
        cmd = ''.join([cmd, ' -define filter:lobes=', str(lobes)])
    if blur:
        cmd = ''.join([cmd, ' -define filter:blur=', str(blur)])
    if beta:
        cmd = ''.join([cmd, ' -define filter:kaiser-beta=', str(beta)])
    if dist:
        cmd = ' '.join([cmd, '-distort Resize {3}x{3}'])
    else:
        cmd = ' '.join([cmd, '-resize {3}x{3}'])
    if lin:
        cmd = ' '.join([cmd, '-colorspace sRGB'])
    return ' '.join([cmd, '-strip {1}'])


def _metric(method, aggregator, sort):
    """Return 3-element list defining a metric, an aggregator and a sort order.

    :param method: The exquires-compare image comparison metric.
    :param aggregator: The exquires-aggregate data aggregator.
    :param sort: Best-to-worst ordering: 0 if ascending, 1 if descending.
    :return: A 3-element list.

    """

    return [' '.join(['exquires-compare', method, '{0} {1}']),
            ' '.join(['exquires-aggregate', aggregator, '{0}']), sort]


def main():
    # Construct the path to the default test image.
    this_dir = os.path.abspath(os.path.dirname(__file__))
    wave = os.path.join(this_dir, 'wave.tif')

    # Define the command-line argument parser.
    parser = argparse.ArgumentParser(
        version=VERSION,
        description=format_doc(__doc__),
        formatter_class=lambda prog: ExquiresHelp(prog, max_help_position=34)
    )
    parser.add_argument('-p', '--proj', metavar='PROJECT', type=str,
                        help='name of the project (default: project1)',
                        default='project1')
    parser.add_argument('-I', '--image', metavar='IMAGE', type=str, nargs='+',
                        help='the test images to use (default: wave.tif)',
                        default=[wave])

    # Attempt to parse the command-line arguments.
    try:
        args = parser.parse_args()
    except Exception, e:
        parser.error(str(e))

    # Convenience strings for indexing.
    I = 'Images'
    R = 'Ratios'
    D = 'Downsamplers'
    U = 'Upsamplers'
    M = 'Metrics'

    # Create a new project file.
    ini = ConfigObj()
    ini.filename = '.'.join([args.proj, 'ini'])

    # Define the list of images to be resampled.
    ini[I] = {}
    ini.comments[I] = [
        'TEST IMAGES',
        'Images are 16-bit sRGB TIFFs with a width and height of 840 pixels.',
        'Any images that are added must conform to this standard.'
    ]
    for image in args.image:
        image_path = os.path.abspath(image)
        name = os.path.splitext(os.path.basename(image))[0]
        ini[I][name] = image_path

    # Define the list of resampling ratios to use.
    ini[R] = {}
    ini.comments[R] = [
        '', 'RESAMPLING RATIOS',
        'The test images are downsampled to the specified sizes.',
        'Each size is obtained by dividing 840 by the ratio.'
    ]
    ini[R]['2'] = '420'
    ini[R]['3'] = '280'
    ini[R]['4'] = '240'
    ini[R]['5'] = '168'
    ini[R]['6'] = '140'
    ini[R]['7'] = '120'
    ini[R]['8'] = '105'

    # Define the list of downsamplers to use.
    ini[D] = {}
    ini.comments[D] = [
        '', 'DOWNSAMPLING COMMANDS',
        'To add a downsampler, provide the command to execute it.',
        'The command can make use of the following replacement fields:',
        '    {0} = input image',
        '    {1} = output image',
        '    {2} = downsampling ratio',
        '    {3} = downsampled size (width or height)',
        'WARNING: Be sure to use a unique name for each downsampler.'
    ]
    ini[D]['box_srgb'] = _magick('Box')
    ini[D]['box_linear'] = _magick('Box', lin=True)
    ini[D]['gaussian_srgb'] = _magick('Gaussian')
    ini[D]['gaussian_linear'] = _magick('Gaussian', lin=True)
    ini[D]['ewa_lanczos3_srgb'] = _magick('Lanczos', dist=True)
    ini[D]['ewa_lanczos3_linear'] = _magick('Lanczos', dist=True, lin=True)
    ini[D]['lanczos3_srgb'] = _magick('Lanczos')
    ini[D]['lanczos3_linear'] = _magick('Lanczos', lin=True)
    ini[D]['nearest_srgb'] = _magick('Point')
    ini[D]['nearest_linear'] = _magick('Point', lin=True)

    # Define the list of upsamplers to use.
    ini[U] = {}
    ini.comments[U] = [
        '', 'UPSAMPLING COMMANDS',
        'To add an upsampler, provide the command to execute it.',
        'The command can make use of the following replacement fields:',
        '    {0} = input image',
        '    {1} = output image',
        '    {2} = upsampling ratio',
        '    {3} = upsampled size (always 840)'
    ]
    ini[U]['nearest_srgb'] = _magick('Point')
    ini[U]['nearest_linear'] = _magick('Point', lin=True)
    ini[U]['bilinear_srgb'] = _magick('Triangle')
    ini[U]['bilinear_linear'] = _magick('Triangle', lin=True)
    ini[U]['cubic_hermite_srgb'] = _magick('Hermite')
    ini[U]['cubic_hermite_linear'] = _magick('Hermite', lin=True)
    ini[U]['catmull_rom_srgb'] = _magick('Catrom')
    ini[U]['catmull_rom_linear'] = _magick('Catrom', lin=True)
    ini[U]['lanczos2_srgb'] = _magick('Lanczos2')
    ini[U]['lanczos2_linear'] = _magick('Lanczos2', lin=True)
    ini[U]['lanczos3_srgb'] = _magick('Lanczos')
    ini[U]['lanczos3_linear'] = _magick('Lanczos', lin=True)
    ini[U]['lanczos4_srgb'] = _magick('Lanczos', lobes=4)
    ini[U]['lanczos4_linear'] = _magick('Lanczos', lobes=4, lin=True)
    ini[U]['bartlett2_srgb'] = _magick('Bartlett', lobes=2)
    ini[U]['bartlett2_linear'] = _magick('Bartlett', lobes=2, lin=True)
    ini[U]['bartlett3_srgb'] = _magick('Bartlett', lobes=3)
    ini[U]['bartlett3_linear'] = _magick('Bartlett', lobes=3, lin=True)
    ini[U]['bartlett4_srgb'] = _magick('Bartlett')
    ini[U]['bartlett4_linear'] = _magick('Bartlett', lin=True)
    ini[U]['blackman2_srgb'] = _magick('Blackman', lobes=2)
    ini[U]['blackman2_linear'] = _magick('Blackman', lobes=2, lin=True)
    ini[U]['blackman3_srgb'] = _magick('Blackman', lobes=3)
    ini[U]['blackman3_linear'] = _magick('Blackman', lobes=3, lin=True)
    ini[U]['blackman4_srgb'] = _magick('Blackman')
    ini[U]['blackman4_linear'] = _magick('Blackman', lin=True)
    ini[U]['bohman2_srgb'] = _magick('Bohman', lobes=2)
    ini[U]['bohman2_linear'] = _magick('Bohman', lobes=2, lin=True)
    ini[U]['bohman3_srgb'] = _magick('Bohman', lobes=3)
    ini[U]['bohman3_linear'] = _magick('Bohman', lobes=3, lin=True)
    ini[U]['bohman4_srgb'] = _magick('Bohman')
    ini[U]['bohman4_linear'] = _magick('Bohman', lin=True)
    ini[U]['cosine2_srgb'] = _magick('Cosine', lobes=2)
    ini[U]['cosine2_linear'] = _magick('Cosine', lobes=2, lin=True)
    ini[U]['cosine3_srgb'] = _magick('Cosine', lobes=3)
    ini[U]['cosine3_linear'] = _magick('Cosine', lobes=3, lin=True)
    ini[U]['cosine4_srgb'] = _magick('Cosine')
    ini[U]['cosine4_linear'] = _magick('Cosine', lin=True)
    ini[U]['hamming2_srgb'] = _magick('Hamming', lobes=2)
    ini[U]['hamming2_linear'] = _magick('Hamming', lobes=2, lin=True)
    ini[U]['hamming3_srgb'] = _magick('Hamming', lobes=3)
    ini[U]['hamming3_linear'] = _magick('Hamming', lobes=3, lin=True)
    ini[U]['hamming4_srgb'] = _magick('Hamming')
    ini[U]['hamming4_linear'] = _magick('Hamming', lin=True)
    ini[U]['parzen2_srgb'] = _magick('Parzen', lobes=2)
    ini[U]['parzen2_linear'] = _magick('Parzen', lobes=2, lin=True)
    ini[U]['parzen3_srgb'] = _magick('Parzen', lobes=3)
    ini[U]['parzen3_linear'] = _magick('Parzen', lobes=3, lin=True)
    ini[U]['parzen4_srgb'] = _magick('Parzen')
    ini[U]['parzen4_linear'] = _magick('Parzen', lin=True)
    ini[U]['welsh2_srgb'] = _magick('Welsh', lobes=2)
    ini[U]['welsh2_linear'] = _magick('Welsh', lobes=2, lin=True)
    ini[U]['welsh3_srgb'] = _magick('Welsh', lobes=3)
    ini[U]['welsh3_linear'] = _magick('Welsh', lobes=3, lin=True)
    ini[U]['welsh4_srgb'] = _magick('Welsh')
    ini[U]['welsh4_linear'] = _magick('Welsh', lin=True)
    ini[U]['hann2_srgb'] = _magick('Hanning', lobes=2)
    ini[U]['hann2_linear'] = _magick('Hanning', lobes=2, lin=True)
    ini[U]['hann3_srgb'] = _magick('Hanning', lobes=3)
    ini[U]['hann3_linear'] = _magick('Hanning', lobes=3, lin=True)
    ini[U]['hann4_srgb'] = _magick('Hanning')
    ini[U]['hann4_linear'] = _magick('Hanning', lin=True)
    ini[U]['kaiser2_srgb'] = _magick('Kaiser', lobes=2, beta=5.36)
    ini[U]['kaiser2_linear'] = _magick('Kaiser', lobes=2, beta=5.36, lin=True)
    ini[U]['kaiser3_srgb'] = _magick('Kaiser', lobes=3, beta=8.93)
    ini[U]['kaiser3_linear'] = _magick('Kaiser', lobes=3, beta=8.93, lin=True)
    ini[U]['kaiser4_srgb'] = _magick('Kaiser', beta=12.15)
    ini[U]['kaiser4_linear'] = _magick('Kaiser', beta=12.15, lin=True)
    ini[U]['kaisersoft2_srgb'] = _magick('Kaiser', lobes=2,
                                         beta=4.7123889803846899)
    ini[U]['kaisersoft2_linear'] = _magick('Kaiser', lobes=2, lin=True,
                                           beta=4.7123889803846899)
    ini[U]['kaisersoft3_srgb'] = _magick('Kaiser', lobes=3,
                                         beta=7.853981633974483)
    ini[U]['kaisersoft3_linear'] = _magick('Kaiser', lobes=3, lin=True,
                                           beta=7.853981633974483)
    ini[U]['kaisersoft4_srgb'] = _magick('Kaiser', beta=10.995574287564276)
    ini[U]['kaisersoft4_linear'] = _magick('Kaiser', lin=True,
                                           beta=10.995574287564276)
    ini[U]['kaisersharp2_srgb'] = _magick('Kaiser', lobes=2,
                                          beta=6.2831853071795865)
    ini[U]['kaisersharp2_linear'] = _magick('Kaiser', lobes=2, lin=True,
                                            beta=6.2831853071795865)
    ini[U]['kaisersharp3_srgb'] = _magick('Kaiser', lobes=3,
                                          beta=9.4247779607693797)
    ini[U]['kaisersharp3_linear'] = _magick('Kaiser', lobes=3, lin=True,
                                            beta=9.4247779607693797)
    ini[U]['kaisersharp4_srgb'] = _magick('Kaiser', beta=12.566370614359173)
    ini[U]['kaisersharp4_linear'] = _magick('Kaiser', lin=True,
                                            beta=12.566370614359173)
    ini[U]['quadratic_b_spline_srgb'] = _magick('Quadratic')
    ini[U]['quadratic_b_spline_linear'] = _magick('Quadratic', lin=True)
    ini[U]['cubic_b_spline_srgb'] = _magick('Cubic')
    ini[U]['cubic_b_spline_linear'] = _magick('Cubic', lin=True)
    ini[U]['mitchell_netravali_srgb'] = _magick(None)
    ini[U]['mitchell_netravali_linear'] = _magick(None, lin=True)
    ini[U]['ewa_teepee_srgb'] = _magick('Triangle', dist=True)
    ini[U]['ewa_teepee_linear'] = _magick('Triangle', dist=True, lin=True)
    ini[U]['ewa_hermite_srgb'] = _magick('Hermite', dist=True)
    ini[U]['ewa_hermite_linear'] = _magick('Hermite', dist=True, lin=True)
    ini[U]['ewa_quadratic_b_spline_srgb'] = _magick('Quadratic', dist=True)
    ini[U]['ewa_quadratic_b_spline_linear'] = _magick('Quadratic', dist=True,
                                                      lin=True)
    ini[U]['ewa_cubic_b_spline_srgb'] = _magick('Cubic', dist=True)
    ini[U]['ewa_cubic_b_spline_linear'] = _magick('Cubic', dist=True, lin=True)
    ini[U]['ewa_lanczos2_srgb'] = _magick('Lanczos2', dist=True)
    ini[U]['ewa_lanczos2_linear'] = _magick('Lanczos2', dist=True, lin=True)
    ini[U]['ewa_lanczos3_srgb'] = _magick('Lanczos', dist=True)
    ini[U]['ewa_lanczos3_linear'] = _magick('Lanczos', dist=True, lin=True)
    ini[U]['ewa_lanczos4_srgb'] = _magick('Lanczos', lobes=4, dist=True)
    ini[U]['ewa_lanczos4_linear'] = _magick('Lanczos', lobes=4, dist=True,
                                            lin=True)
    ini[U]['ewa_robidoux_srgb'] = _magick(None, dist=True)
    ini[U]['ewa_robidoux_linear'] = _magick(None, dist=True, lin=True)
    ini[U]['ewa_mitchell_netravali_srgb'] = _magick('Mitchell', dist=True)
    ini[U]['ewa_mitchell_netravali_linear'] = _magick('Mitchell', dist=True,
                                                      lin=True)
    ini[U]['ewa_robidoux_sharp_srgb'] = _magick('RobidouxSharp', dist=True)
    ini[U]['ewa_robidoux_sharp_linear'] = _magick('RobidouxSharp', dist=True,
                                                  lin=True)
    ini[U]['ewa_catmull_rom_srgb'] = _magick('Catrom', dist=True)
    ini[U]['ewa_catmull_rom_linear'] = _magick('Catrom', dist=True, lin=True)
    ini[U]['ewa_lanczos_radius2_srgb'] = _magick('Lanczos2', dist=True,
                                                 blur=.8956036897402793)
    ini[U]['ewa_lanczos_radius2_linear'] = _magick('Lanczos2', dist=True,
                                                   blur=.8956036897402793,
                                                   lin=True)
    ini[U]['ewa_lanczos_radius3_srgb'] = _magick('Lanczos', dist=True,
                                                 blur=.9264075766146068)
    ini[U]['ewa_lanczos_radius3_linear'] = _magick('Lanczos', dist=True,
                                                   blur=.9264075766146068,
                                                   lin=True)
    ini[U]['ewa_lanczos_radius4_srgb'] = _magick('Lanczos', lobes=4, dist=True,
                                                 blur=.9431597994328477)
    ini[U]['ewa_lanczos_radius4_linear'] = _magick('Lanczos', lobes=4,
                                                   dist=True, lin=True,
                                                   blur=.9431597994328477)
    ini[U]['ewa_lanczos2sharp_srgb'] = _magick('Lanczos2', dist=True,
                                               blur=.9580278036312191)
    ini[U]['ewa_lanczos2sharp_linear'] = _magick('Lanczos2', dist=True,
                                                 blur=.9580278036312191,
                                                 lin=True)
    ini[U]['ewa_lanczos3sharp_srgb'] = _magick('Lanczos', dist=True,
                                               blur=.9891028367558475)
    ini[U]['ewa_lanczos3sharp_linear'] = _magick('Lanczos', dist=True,
                                                 blur=.9891028367558475,
                                                 lin=True)
    ini[U]['ewa_lanczos4sharp_srgb'] = _magick('Lanczos', lobes=4, dist=True,
                                               blur=.9870395083298263)
    ini[U]['ewa_lanczos4sharp_linear'] = _magick('Lanczos', lobes=4,
                                                 dist=True, lin=True,
                                                 blur=.9870395083298263)
    ini[U]['ewa_lanczos2sharpest_srgb'] = _magick('Lanczos2', dist=True,
                                                  blur=.88826421508540347)
    ini[U]['ewa_lanczos2sharpest_linear'] = _magick('Lanczos2', dist=True,
                                                    blur=.88826421508540347,
                                                    lin=True)
    ini[U]['ewa_lanczos3sharpest_srgb'] = _magick('Lanczos', dist=True,
                                                  blur=.88549061701764)
    ini[U]['ewa_lanczos3sharpest_linear'] = _magick('Lanczos', dist=True,
                                                    blur=.88549061701764,
                                                    lin=True)
    ini[U]['ewa_lanczos4sharpest_srgb'] = _magick('Lanczos', lobes=4,
                                                   dist=True,
                                                   blur=.88451002338585141)
    ini[U]['ewa_lanczos4sharpest_linear'] = _magick('Lanczos', lobes=4,
                                                    dist=True, lin=True,
                                                    blur=.88451002338585141)

    # Define the list of error metrics to use.
    ini[M] = {}
    ini.comments[M] = [
        '', 'IMAGE DIFFERENCE METRICS AND AGGREGATORS',
        'Each metric must be associated with a data aggregation method.',
        'To add a metric, you must provide the following three items:',
        '    1. Error metric command, using the following replacement fields:',
        '        {0} = reference image',
        '        {1} = test image',
        '    2. Aggragator command, using the following replacement field:',
        '        {0} = list of error data to aggregate',
        '    3. Best-to-worst ordering, given as a 0 or 1:',
        '        0 = ascending',
        '        1 = descending'
    ]
    ini[M]['l_1'] = _metric('l_1', 'l_1', 0)
    ini[M]['l_2'] = _metric('l_2', 'l_2', 0)
    ini[M]['l_4'] = _metric('l_4', 'l_4', 0)
    ini[M]['l_inf'] = _metric('l_inf', 'l_inf', 0)
    ini[M]['mssim'] = _metric('mssim', 'l_1', 1)
    ini[M]['blur_1'] = _metric('blur_1', 'l_1', 0)
    ini[M]['blur_2'] = _metric('blur_2', 'l_2', 0)
    ini[M]['blur_4'] = _metric('blur_4', 'l_4', 0)
    ini[M]['blur_inf'] = _metric('blur_inf', 'l_inf', 0)
    ini[M]['cmc_1'] = _metric('cmc_1', 'l_1', 0)
    ini[M]['cmc_2'] = _metric('cmc_2', 'l_2', 0)
    ini[M]['cmc_4'] = _metric('cmc_4', 'l_4', 0)
    ini[M]['cmc_inf'] = _metric('cmc_inf', 'l_inf', 0)
    ini[M]['xyz_1'] = _metric('xyz_1', 'l_1', 0)
    ini[M]['xyz_2'] = _metric('xyz_2', 'l_2', 0)
    ini[M]['xyz_4'] = _metric('xyz_4', 'l_4', 0)
    ini[M]['xyz_inf'] = _metric('xyz_inf', 'l_inf', 0)

    # Write the project file.
    ini.write()

if __name__ == '__main__':
    main()
