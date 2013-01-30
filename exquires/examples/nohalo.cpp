/* Wrapper for VIPS Nohalo subdivision followed by LBB
 * (locally bounded bicubic) interpolation resampler
 *
 * This program is a wrapper around the Nohalo implementation found in VIPS.
 * Unfortunately, VIPS does not conform to the pixel alignment convention used in
 * the EXQUIRES test suite. In order to alleviate this problem, the leftmost
 * column of the image is duplicated and the topmost row of the resulting image is
 * duplicated before performing the resampling step.
 *
 * Note: this program only supports aspect ratio preserving upsampling.
 *
 * Code written by Adam Turcotte with contributions by Nicolas Robidoux
 *
 * Published December 9, 2012
 */

#include <vips/vips>
#include <cstdlib>
#include <iostream>

using namespace vips;
using std::cout;
using std::endl;


int
main (int argc, char **argv)
{
    // Check for correct number of command-line arguments
    if (argc != 5) {
        cout << "usage: nohalo image_in image_out enlargement_factor "
                "(0: sRGB | 1: linear)" << endl;
        return (1);
    }

    try {
        // Define sRGB profile path and method name
        char profile[] = "/usr/local/lib/python2.7/dist-packages"
                         "/exquires/sRGB_IEC61966-2-1_black_scaled.icc";
        char method[] = "nohalo";

        // Read input image
        VImage image_in (argv[1]);

        // Get ratio, size, and determine if we're using linear light
        double ratio = atof (argv[3]);
        bool linear = atoi (argv[4]);
        double dx = -0.5 * (ratio + 1);
        int size = (int) (ratio * image_in.Xsize() + 0.5);

        // Import from sRGB to XYZ if linear option selected
        if (linear)
            image_in = image_in.icc_import (profile, 1);

        // Create the temporarily padded image
        VImage col = image_in.extract_area (0, 0, 1, image_in.Ysize ());
        VImage added_col = col.lrjoin (image_in);
        VImage row = added_col.extract_area (0, 0, added_col.Xsize (), 1);
        VImage padded = row.tbjoin (added_col);

        // Prepare the output image
        VImage image_out = padded.affinei (method, ratio, 0, 0,ratio,
                                           dx, dx, 0, 0, size, size);

        // Export from XYZ to sRGB if linear option selected
        if (linear)
            image_out = image_out.icc_export_depth (16, profile, 1);

        // Write output image
        image_out.write (argv[2]);
    }
    catch (VError &e) {
        e.perror (argv[0]);
    }

    return (0);
}
