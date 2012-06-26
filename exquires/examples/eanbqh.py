#!/usr/bin/env python
# coding: utf-8
#
#  Copyright (c) 2012, Adam Turcotte (adam.turcotte@gmail.com)
#                      Nicolas Robidoux (nicolas.robidoux@gmail.com)
#  License: BSD 2-Clause License

"""Wrapper script to use EANBQH with EXQUIRES.

Converts a 16-bit TIFF to PPM, upsamples it to the specified size with EANBQH,
and converts the 16-bit PPM output image back to TIFF.

By default, the image upsampling is performed using the sRGB colorspace.
The -l/--linear option can be used to perform the upsampling in linear RGB.

"""

import argparse
import os
from subprocess import call

from exquires import parsing


def main():
    # Define the command-line argument parser.
    parser = parsing.ExquiresParser(description=__doc__)
    parser.add_argument('-l', '--linear', action='store_true',
                        help='upsample within linear light instead of sRGB')
    parser.add_argument('image_in', type=str, metavar='INPUT',
                        help='the image to upsample')
    parser.add_argument('image_out', type=str, metavar='OUTPUT',
                        help='the upsampled image')
    parser.add_argument('size', type=int, metavar='SIZE',
                        help='the size of the output')

    # Attempt to parse the command-line arguments.
    args = parser.parse_args()

    # Make sure the input image exists.
    if not os.path.isfile(args.image_in):
        parser.error('input image does not exist')

    # Setup the temporary PPM images.
    output_dir = os.path.dirname(args.image_out)
    image_name = os.path.splitext(os.path.basename(args.image_out))[0]
    temp_in = os.path.join(output_dir, '_'.join([image_name, 'in.ppm']))
    temp_out = os.path.join(output_dir, '_'.join([image_name, 'out.ppm']))

    # Convert the TIF input to PPM.
    if args.linear:
        call(['magick', args.image_in, '-set', 'colorspace', 'sRGB',
              '-colorspace', 'RGB', temp_in])
    else:
        call(['magick', args.image_in, temp_in])

    # Perform upsampling with EANBQH.
    call(['eanbqh16', temp_in, temp_out, str(args.size)])

    # Convert the PPM result back to TIF.
    if args.linear:
        call(['magick', temp_out, '-set', 'colorspace', 'sRGB',
              '-colorspace', 'RGB', args.image_out])
    else:
        call(['magick', temp_out, args.image_out])

    # Delete the temporary PPM files.
    os.remove(temp_in)
    os.remove(temp_out)

if __name__ == '__main__':
    main()
