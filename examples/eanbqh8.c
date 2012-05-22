/*
 * This work is licensed under the Creative Commons Attribution 2.5
 * Canada License. To view a copy of this license, visit
 * http://creativecommons.org/licenses/by/2.5/ca/ or send a letter to
 * Creative Commons, 171 Second Street, Suite 300, San Francisco,
 * California, 94105, USA.
 *
 * ***************************************************************************
 * * EANBQH: Exact Area image upsizing with Natural BiQuadratic Histosplines *
 * ***************************************************************************
 *
 * For more details regarding this method, see Fast Exact Area Image
 * Upsampling with Natural Biquadratic Histosplines by Nicolas
 * Robidoux, Adam Turcotte, Minglun Gong and Annie Tousignant,
 * pp.85-96 of Image Analysis and Recognition, 5th International
 * Conference, ICIAR 2008, Póvoa de Varzim, Portugal, June 25-27,
 * 2008. Proceedings, Aurelio C. Campilho, Mohamed S. Kamel (Eds.).
 * Lecture Notes in Computer Science 5112, Springer 2008, ISBN
 * 978-3-540-69811-1.
 */

/*
 * eanbqh8.c -- EANBQH upsampler which supports PPM files with 8-bit samples
 * Copyright (C) 2012 Nicolas Robidoux and Adam Turcotte
 *
 * LAST UPDATED:
 * May 2, 2012
 *  - Split the 8-bit and 16-bit versions.
 *
 * COMPILATION INSTRUCTIONS:
 *   gcc -o eanbqh8 eanbqh8.c -fomit-frame-pointer -O2 -Wall -march=native -lm
 *
 * LIMITATIONS:
 *  - Currently, only binary-mode PPM (P6) files are supported.
 */

#include <libgen.h>
#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "eanbqh.h"

static int
scale_up (FILE *inputfile,
          FILE *outputfile,
          int   m,
          int   n,
          int   mm,
          int   nn,
          int   maxval)
{
  float *a, *a1, *a2, *a3, *a4;
  uchar *input_row, *input_row_p;
  uchar *output_row, *output_row_p;

  int channels = 3;
  int n_times_channels  = channels * n;
  int nn_times_channels = channels * nn;
  int n_times_channels_times_2 = n_times_channels + n_times_channels;
  int n_minus_7_times_channels = (n-7) * channels;
  float mm_nn_over_m_n = ( (float)mm * nn ) / ( (float)m * n );

  int i;
  int j;
  int c;
  int ii;
  int last_ii;
  int jj;
  int last_jj;

  int last_overlapping_jj[n-1];
  int last_overlapping_ii[m-1];

  float left[nn];
  float center[nn];
  float right[nn];
  float farright[n-1];

  float top[mm];
  float middle[mm];
  float bottom[mm];
  float farbottom[m-1];

  float top_ii;
  float middle_ii;
  float bottom_ii;
  float farbottom_i;

  float left_jj;
  float center_jj;
  float right_jj;
  float farright_j;

  float a_top_left[channels];
  float a_top_center[channels];
  float a_top_right[channels];
  float a_top_farright[channels];

  float a_middle_left[channels];
  float a_middle_center[channels];
  float a_middle_right[channels];
  float a_middle_farright[channels];

  float a_bottom_left[channels];
  float a_bottom_center[channels];
  float a_bottom_right[channels];
  float a_bottom_farright[channels];

  float a_farbottom_left[channels];
  float a_farbottom_center[channels];
  float a_farbottom_right[channels];
  float a_farbottom_farright[channels];

  float coef_left[channels];
  float coef_center[channels];
  float coef_right[channels];

  int i_minus_one_times_n_times_channels;
  int i_times_n_times_channels;
  int i_plus_one_times_n_times_channels;
  int i_plus_two_times_n_times_channels;

  int m_minus_one   = m - 1;
  int m_minus_two   = m - 2;
  int m_minus_three = m - 3;
  int n_minus_two   = n - 2;
  int m_minus_one_times_n_times_channels   = m_minus_one   * n_times_channels;
  int m_minus_two_times_n_times_channels   = m_minus_two   * n_times_channels;
  int m_minus_three_times_n_times_channels = m_minus_three * n_times_channels;

#define C0            .2000000f
#define MINUS_C0     -.2000000f
#define C1            .2631579f
#define MINUS_C1     -.2631579f
#define C2            .2676056f
#define MINUS_C2     -.2676056f
#define C3            .2679245f
#define MINUS_C3     -.2679245f
#define C4            .2679474f
#define MINUS_C4     -.2679474f
#define C5            .2679491f
#define MINUS_C5     -.2679491f
#define CLAST         .2113249f
#define CINFTY        .2679492f
#define MINUS_CINFTY -.2679492f

  a          = (float *)malloc(sizeof(float[m * n_times_channels]));
  input_row  = (uchar *)malloc(sizeof(uchar[n_times_channels]));
  output_row = (uchar *)malloc(sizeof(uchar[nn_times_channels]));

  /*
   * Computation of the B-Spline coefficients.
   *
   * We rescale the input pixel values by ( mm * nn ) / ( m * n ) (in
   * double arithmetic) so as to avoid doing it when we compute
   * averages. This scaling quantity is the reciprocal of the area of
   * the fine pixels given our convention that the input pixels have
   * unit sides; since an average is the ratio of an integral and an
   * area, this rescaling must be done sooner or later. Sooner is
   * better because there are less input pixels than output pixels.
   */
  {
    i = 0;
    do {
      a1 = (a+i*n_times_channels);
      a2 = (a+i*n_times_channels);

      /*
       * Read one row of 16-bit (2 byte) intensity values into input_row.
       */
      if (!fread (input_row, sizeof(uchar), n_times_channels, inputfile))
        return 1;

      /*
       * Column forward substitution.
       */

      /*
       * Non-asymptotic LU factorization entries:
       */
      input_row_p = input_row;

      c = channels;
      do {
        *a1++ = *input_row_p++ * mm_nn_over_m_n;
      } while (--c);

      c = channels;
      do {
        *a1++ = *input_row_p++ * mm_nn_over_m_n - *a2++ * C0;
      } while (--c);

      c = channels;
      do {
        *a1++ = *input_row_p++ * mm_nn_over_m_n - *a2++ * C1;
      } while (--c);

      c = channels;
      do {
        *a1++ = *input_row_p++ * mm_nn_over_m_n - *a2++ * C2;
      } while (--c);

      c = channels;
      do {
        *a1++ = *input_row_p++ * mm_nn_over_m_n - *a2++ * C3;
      } while (--c);

      c = channels;
      do {
        *a1++ = *input_row_p++ * mm_nn_over_m_n - *a2++ * C4;
      } while (--c);

      c = channels;
      do {
        *a1++ = *input_row_p++ * mm_nn_over_m_n - *a2++ * C5;
      } while (--c);

      /*
       * Asymptotic (within roundoff) LU factorization entries:
       */
      c = n_minus_7_times_channels;
      while (c--) {
        *a1++ = *input_row_p++ * mm_nn_over_m_n - *a2++ * CINFTY;
      }

      /*
       * Column-based back substitution.
       */
      a1--;
      c = channels;
      do {
        *a1-- *= CLAST;
      } while (--c);

      a2 += channels-1;
      c = n_minus_7_times_channels;
      while (c--) {
        *a1 = ( *a1 - *a2-- ) * CINFTY;
        --a1;
      }

      c = channels;
      do {
        *a1 = ( *a1 - *a2-- ) * C5;
        --a1;
      } while (--c);

      c = channels;
      do {
        *a1 = ( *a1 - *a2-- ) * C4;
        --a1;
      } while (--c);

      c = channels;
      do {
        *a1 = ( *a1 - *a2-- ) * C3;
        --a1;
      } while (--c);

      c = channels;
      do {
        *a1 = ( *a1 - *a2-- ) * C2;
        --a1;
      } while (--c);

      c = channels;
      do {
        *a1 = ( *a1 - *a2-- ) * C1;
        --a1;
      } while (--c);

      c = channels;
      do {
        *a1 = ( *a1 - *a2-- ) * C0;
        --a1;
      } while (--c);
    } while (++i<m);

    /*
     * Row based forward substitution.
     */
    a1 = (a+n_times_channels);
    a2 = a;
    c = n_times_channels;
    do {
      *a1++ -= *a2++ * C0;
    } while (--c);

    c = n_times_channels;
    do {
      *a1++ -= *a2++ * C1;
    } while (--c);

    c = n_times_channels;
    do {
      *a1++ -= *a2++ * C2;
    } while (--c);

    c = n_times_channels;
    do {
      *a1++ -= *a2++ * C3;
    } while (--c);

    c = n_times_channels;
    do {
      *a1++ -= *a2++ * C4;
    } while (--c);

    c = n_times_channels;
    do {
      *a1++ -= *a2++ * C5;
    } while (--c);

    i = 7;
    while (i < m) {
      c = n_times_channels;
      do {
        *a1++ -= *a2++ * CINFTY;
      } while (--c);

      i++;
    }

    /*
     * Row-based back substitution.
     */
    a1 -= n_times_channels;
    i--;
    c = n_times_channels;
    do {
      *a1++ *= CLAST;
    } while (--c);

    a1 -= n_times_channels_times_2;
    i--;
    while (i > 5) {
      c = n_times_channels;
      do {
        *a1 = ( *a1 - *a2++ ) * CINFTY;
        ++a1;
      } while (--c);
      a1 -= n_times_channels_times_2;
      a2 -= n_times_channels_times_2;

      i--;
    }

    c = n_times_channels;
    do {
      *a1 = ( *a1 - *a2++ ) * C5;
      ++a1;
    } while (--c);

    a1 -= n_times_channels_times_2;
    a2 -= n_times_channels_times_2;
    c = n_times_channels;
    do {
      *a1 = ( *a1 - *a2++ ) * C4;
      ++a1;
    } while (--c);

    a1 -= n_times_channels_times_2;
    a2 -= n_times_channels_times_2;
    c = n_times_channels;
    do {
      *a1 = ( *a1 - *a2++ ) * C3;
      ++a1;
    } while (--c);

    a1 -= n_times_channels_times_2;
    a2 -= n_times_channels_times_2;
    c = n_times_channels;
    do {
      *a1 = ( *a1 - *a2++ ) * C2;
      ++a1;
    } while (--c);

    a1 -= n_times_channels_times_2;
    a2 -= n_times_channels_times_2;
    c = n_times_channels;
    do {
      *a1 = ( *a1 - *a2++ ) * C1;
      ++a1;
    } while (--c);

    a1 -= n_times_channels_times_2;
    a2 -= n_times_channels_times_2;
    c = n_times_channels;
    do {
      *a1 = ( *a1 - *a2++ ) * C0;
      ++a1;
    } while (--c);
  }

  /*
   * The scaled B-Spline coefficients have now been computed and
   * stored in the array a[][].
   */

  /*
   * Now, we compute the tensor components of the linear
   * transformation from B-Spline coefficents to fine cell averages
   * (actually fine cell integrals, since we have alread rescaled by
   * the reciprocal of the fine cell areas).
   */

  last_overlapping_index (n,nn,last_overlapping_jj);
  last_overlapping_index (m,mm,last_overlapping_ii);

  coarse_to_fine_coefficients (n, nn, last_overlapping_jj,
                               left, center, right, farright);
  coarse_to_fine_coefficients (m, mm, last_overlapping_ii,
                               top, middle, bottom, farbottom);

  last_ii = last_overlapping_ii[0];

  for (ii=0; ii<last_ii; ii++)
  {
    /* move output_row_p to start of output_row */
    output_row_p = output_row;

    middle_ii = middle[ii];
    bottom_ii = bottom[ii];

    a1 = a;
    a2 = (a+n_times_channels);

    c = 0;
    do {
      a_middle_center[c]   = *a1++;
      a_bottom_center[c]   = *a2++;
    } while (++c<channels);

    c = 0;
    do {
      a_middle_right[c]    = *a1++;
      a_bottom_right[c]    = *a2++;
    } while (++c<channels);

    c = 0;
    do {
      a_middle_farright[c] = *a1++;
      a_bottom_farright[c] = *a2++;
    } while (++c<channels);

    c = 0;
    do {
      coef_center[c] =   middle_ii * a_middle_center[c]
                       + bottom_ii * a_bottom_center[c];
      coef_right[c]  =   middle_ii * a_middle_right[c]
                       + bottom_ii * a_bottom_right[c];
    } while (++c<channels);

    last_jj = last_overlapping_jj[0];

    /*
     * TODO ADAM: I think all we have to do is round and clamp to
     * 2^16-1=65535 instead of 2^8-1=255. Pretty trivial mod.
     */
#define ROUND_AND_CLAMP_TO_065535(x) ({ int out = .5 + (x); (out > 255) ? (int)255 : ((out < 0) ? (int)0 : (int)out); })

    for (jj=0; jj<last_jj; jj++)
    {
      center_jj = center[jj];
      right_jj  =  right[jj];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535( coef_center[c] * center_jj
                                   +  coef_right[c] * right_jj  );
      } while (++c<channels);
    }

    center_jj  =   center[jj];
    right_jj   =    right[jj];
    farright_j = farright[0];

    c = 0;
    do {
      *output_row_p++ =
        ROUND_AND_CLAMP_TO_065535( coef_center[c] * center_jj
                                 +  coef_right[c] * right_jj
                                 + (    middle_ii * a_middle_farright[c]
                                     +  bottom_ii * a_bottom_farright[c]  )
                                                  * farright_j  );
    } while (++c<channels);

    jj++;

    j = 1;
    do {
      c = 0;
      do {
        a_middle_left[c]     =   a_middle_center[c];
        a_middle_center[c]   =   a_middle_right[c];
        a_middle_right[c]    =   a_middle_farright[c];
        a_middle_farright[c] =   *a1++;

        a_bottom_left[c]     =   a_bottom_center[c];
        a_bottom_center[c]   =   a_bottom_right[c];
        a_bottom_right[c]    =   a_bottom_farright[c];
        a_bottom_farright[c] =   *a2++;

        coef_left[c]         =   middle_ii * a_middle_left[c]
                               + bottom_ii * a_bottom_left[c];
        coef_center[c]       =   middle_ii * a_middle_center[c]
                               + bottom_ii * a_bottom_center[c];
        coef_right[c]        =   middle_ii * a_middle_right[c]
                               + bottom_ii * a_bottom_right[c];
      } while (++c<channels);

      last_jj = last_overlapping_jj[j];

      while (jj<last_jj)
      {
        left_jj   =   left[jj];
        center_jj = center[jj];
        right_jj  =  right[jj];

        c = 0;
        do {
          *output_row_p++ =
            ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                     + coef_center[c] * center_jj
                                     +  coef_right[c] * right_jj  );
        } while (++c<channels);

        jj++;
      }

      left_jj    =    left[jj];
      center_jj  =  center[jj];
      right_jj   =   right[jj];
      farright_j = farright[j];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                   + coef_center[c] * center_jj
                                   +  coef_right[c] * right_jj
                                   + (    middle_ii * a_middle_farright[c]
                                       +  bottom_ii * a_bottom_farright[c]  )
                                                    * farright_j  );
      } while (++c<channels);

      jj++;

    } while (++j<n_minus_two);

    /*
     * Now, we deal with j = n-2.
     */
    c = 0;
    do {
      a_middle_left[c]   =   a_middle_center[c];
      a_middle_center[c] =   a_middle_right[c];
      a_middle_right[c]  =   a_middle_farright[c];

      a_bottom_left[c]   =   a_bottom_center[c];
      a_bottom_center[c] =   a_bottom_right[c];
      a_bottom_right[c]  =   a_bottom_farright[c];

      coef_left[c]       =   middle_ii * a_middle_left[c]
                           + bottom_ii * a_bottom_left[c];
      coef_center[c]     =   middle_ii * a_middle_center[c]
                           + bottom_ii * a_bottom_center[c];
      coef_right[c]      =   middle_ii * a_middle_right[c]
                           + bottom_ii * a_bottom_right[c];
    } while (++c<channels);

    last_jj = last_overlapping_jj[n_minus_two] + 1; /* The "+ 1" is because
                                                       there is no farright to
                                                       deal with in any case.
                                                       Consequently, no
                                                       exception needs to be
                                                       made for the last
                                                       overlapping fine cell. */

    while (jj<last_jj)
    {
      left_jj   =   left[jj];
      center_jj = center[jj];
      right_jj  =  right[jj];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                   + coef_center[c] * center_jj
                                   +  coef_right[c] * right_jj  );
      } while (++c<channels);

      jj++;
    }

    /*
     * Now, we deal with j = n-1.
     */
    c = 0;
    do {
      a_middle_left[c]   =   a_middle_center[c];
      a_middle_center[c] =   a_middle_right[c];

      a_bottom_left[c]   =   a_bottom_center[c];
      a_bottom_center[c] =   a_bottom_right[c];

      coef_left[c]       =   middle_ii * a_middle_left[c]
                           + bottom_ii * a_bottom_left[c];
      coef_center[c]     =   middle_ii * a_middle_center[c]
                           + bottom_ii * a_bottom_center[c];
    } while (++c<channels);

    while (jj<nn)
    {
      left_jj   =   left[jj];
      center_jj = center[jj];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                   + coef_center[c] * center_jj  );
      } while (++c<channels);

      jj++;
    }

    /* write output_row */
    fwrite(output_row, sizeof(uchar), nn_times_channels, outputfile);
  }

  /*
   * Now, we take care of the last fine row which overlaps the first
   * coarse row. Right now, ii = last_ii.
   */
  output_row_p = output_row;

  middle_ii   = middle[ii];
  bottom_ii   = bottom[ii];
  farbottom_i = farbottom[0];

  a1 = a;
  a2 = (a+n_times_channels);
  a3 = (a+n_times_channels_times_2);

  c = 0;
  do {
    a_middle_center[c]     = *a1++;
    a_bottom_center[c]     = *a2++;
    a_farbottom_center[c]  = *a3++;
  } while (++c<channels);

  c = 0;
  do {
    a_middle_right[c]       = *a1++;
    a_bottom_right[c]       = *a2++;
    a_farbottom_right[c]    = *a3++;
  } while (++c<channels);

  c = 0;
  do {
    a_middle_farright[c]    = *a1++;
    a_bottom_farright[c]    = *a2++;
    a_farbottom_farright[c] = *a3++;
  } while (++c<channels);

  c = 0;
  do {
    coef_center[c] =     middle_ii * a_middle_center[c]
                     +   bottom_ii * a_bottom_center[c]
                     + farbottom_i * a_farbottom_center[c];
    coef_right[c]  =     middle_ii * a_middle_right[c]
                     +   bottom_ii * a_bottom_right[c]
                     + farbottom_i * a_farbottom_right[c];
  } while (++c<channels);

  last_jj = last_overlapping_jj[0];

  for (jj=0; jj<last_jj; jj++)
  {
    center_jj = center[jj];
    right_jj  =  right[jj];

    c = 0;
    do {
      *output_row_p++ =
        ROUND_AND_CLAMP_TO_065535( coef_center[c] * center_jj
                                 +  coef_right[c] * right_jj  );
    } while (++c<channels);
  }

  center_jj  =  center[jj];
  right_jj   =   right[jj];
  farright_j = farright[0];

  c = 0;
  do {
    *output_row_p++ =
      ROUND_AND_CLAMP_TO_065535(  coef_center[c] * center_jj
                               +   coef_right[c] * right_jj
                               + (     middle_ii * a_middle_farright[c]
                                   +   bottom_ii * a_bottom_farright[c]
                                   + farbottom_i * a_farbottom_farright[c]  )
                                                 * farright_j  );
  } while (++c<channels);

  jj++;

  j = 1;
  do {
    c = 0;
    do {
      a_middle_left[c]        = a_middle_center[c];
      a_middle_center[c]      = a_middle_right[c];
      a_middle_right[c]       = a_middle_farright[c];
      a_middle_farright[c]    = *a1++;

      a_bottom_left[c]        = a_bottom_center[c];
      a_bottom_center[c]      = a_bottom_right[c];
      a_bottom_right[c]       = a_bottom_farright[c];
      a_bottom_farright[c]    = *a2++;

      a_farbottom_left[c]     = a_farbottom_center[c];
      a_farbottom_center[c]   = a_farbottom_right[c];
      a_farbottom_right[c]    = a_farbottom_farright[c];
      a_farbottom_farright[c] = *a3++;

      coef_left[c]   =     middle_ii * a_middle_left[c]
                       +   bottom_ii * a_bottom_left[c]
                       + farbottom_i * a_farbottom_left[c];
      coef_center[c] =     middle_ii * a_middle_center[c]
                       +   bottom_ii * a_bottom_center[c]
                       + farbottom_i * a_farbottom_center[c];
      coef_right[c]  =     middle_ii * a_middle_right[c]
                       +   bottom_ii * a_bottom_right[c]
                       + farbottom_i * a_farbottom_right[c];
    } while (++c<channels);

    last_jj = last_overlapping_jj[j];

    while (jj<last_jj)
    {
      left_jj   =   left[jj];
      center_jj = center[jj];
      right_jj  =  right[jj];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                   + coef_center[c] * center_jj
                                   +  coef_right[c] * right_jj  );
      } while (++c<channels);

      jj++;
    }

    left_jj    =    left[jj];
    center_jj  =  center[jj];
    right_jj   =   right[jj];
    farright_j = farright[j];

    c = 0;
    do {
      *output_row_p++ =
        ROUND_AND_CLAMP_TO_065535(    coef_left[c] * left_jj
                                 +  coef_center[c] * center_jj
                                 +   coef_right[c] * right_jj
                                 + (     middle_ii * a_middle_farright[c]
                                     +   bottom_ii * a_bottom_farright[c]
                                     + farbottom_i * a_farbottom_farright[c]  )
                                                   * farright_j  );
    } while (++c<channels);

    jj++;

  } while (++j<n_minus_two);

  /*
   * Now, we deal with j = n-2.
   */
  c = 0;
  do {
    a_middle_left[c]      = a_middle_center[c];
    a_middle_center[c]    = a_middle_right[c];
    a_middle_right[c]     = a_middle_farright[c];

    a_bottom_left[c]      = a_bottom_center[c];
    a_bottom_center[c]    = a_bottom_right[c];
    a_bottom_right[c]     = a_bottom_farright[c];

    a_farbottom_left[c]   = a_farbottom_center[c];
    a_farbottom_center[c] = a_farbottom_right[c];
    a_farbottom_right[c]  = a_farbottom_farright[c];

    coef_left[c]   =     middle_ii * a_middle_left[c]
                     +   bottom_ii * a_bottom_left[c]
                     + farbottom_i * a_farbottom_left[c];
    coef_center[c] =     middle_ii * a_middle_center[c]
                     +   bottom_ii * a_bottom_center[c]
                     + farbottom_i * a_farbottom_center[c];
    coef_right[c]  =     middle_ii * a_middle_right[c]
                     +   bottom_ii * a_bottom_right[c]
                     + farbottom_i * a_farbottom_right[c];

  } while (++c<channels);

  last_jj = last_overlapping_jj[n_minus_two] + 1;

  while (jj<last_jj)
  {
    left_jj   =   left[jj];
    center_jj = center[jj];
    right_jj  =  right[jj];

    c = 0;
    do {
      *output_row_p++ =
        ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                 + coef_center[c] * center_jj
                                 +  coef_right[c] * right_jj  );
    } while (++c<channels);

    jj++;
  }

  /*
   * Now, we deal with j = n-1.
   */
  c = 0;
  do {
    a_middle_left[c]      = a_middle_center[c];
    a_middle_center[c]    = a_middle_right[c];

    a_bottom_left[c]      = a_bottom_center[c];
    a_bottom_center[c]    = a_bottom_right[c];

    a_farbottom_left[c]   = a_farbottom_center[c];
    a_farbottom_center[c] = a_farbottom_right[c];

    coef_left[c]   =     middle_ii * a_middle_left[c]
                     +   bottom_ii * a_bottom_left[c]
                     + farbottom_i * a_farbottom_left[c];
    coef_center[c] =     middle_ii * a_middle_center[c]
                     +   bottom_ii * a_bottom_center[c]
                     + farbottom_i * a_farbottom_center[c];

  } while (++c<channels);

  while (jj<nn)
  {
    left_jj   =   left[jj];
    center_jj = center[jj];

    c = 0;
    do {
      *output_row_p++ =
        ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                 + coef_center[c] * center_jj  );
    } while (++c<channels);

    jj++;
  }

  /* write output_row */
  fwrite(output_row, sizeof(uchar), nn_times_channels, outputfile);

  ii++;

  /*
   * Now, we deal with the second, and later, coarse rows.
   */
  i = 1;
  do {
    i_minus_one_times_n_times_channels = (i - 1) * n_times_channels;
    i_times_n_times_channels           =    i    * n_times_channels;
    i_plus_one_times_n_times_channels  = (i + 1) * n_times_channels;
    i_plus_two_times_n_times_channels  = (i + 2) * n_times_channels;

    last_ii = last_overlapping_ii[i];

    while (ii<last_ii)
    {
      output_row_p = output_row;

      top_ii    =    top[ii];
      middle_ii = middle[ii];
      bottom_ii = bottom[ii];

      a1 = (a+i_minus_one_times_n_times_channels);
      a2 = (a+i_times_n_times_channels);
      a3 = (a+i_plus_one_times_n_times_channels);

      c = 0;
      do {
        a_top_center[c]     = *a1++;
        a_middle_center[c]  = *a2++;
        a_bottom_center[c]  = *a3++;
      } while (++c<channels);

      c = 0;
      do {
        a_top_right[c]       = *a1++;
        a_middle_right[c]    = *a2++;
        a_bottom_right[c]    = *a3++;
      } while (++c<channels);

      c = 0;
      do {
        a_top_farright[c]    = *a1++;
        a_middle_farright[c] = *a2++;
        a_bottom_farright[c] = *a3++;
      } while (++c<channels);

      c = 0;
      do {
        coef_center[c] =      top_ii * a_top_center[c]
                         + middle_ii * a_middle_center[c]
                         + bottom_ii * a_bottom_center[c];
        coef_right[c]  =      top_ii * a_top_right[c]
                         + middle_ii * a_middle_right[c]
                         + bottom_ii * a_bottom_right[c];
      } while (++c<channels);

      last_jj = last_overlapping_jj[0];

      for (jj=0; jj<last_jj; jj++)
      {
        center_jj = center[jj];
        right_jj  =  right[jj];

        c = 0;
        do {
          *output_row_p++ =
            ROUND_AND_CLAMP_TO_065535( coef_center[c] * center_jj
                                     +  coef_right[c] * right_jj  );
        } while (++c<channels);
      }

      center_jj  =  center[jj];
      right_jj   =   right[jj];
      farright_j = farright[0];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535( coef_center[c] * center_jj
                                   +  coef_right[c] * right_jj
                                   + (       top_ii * a_top_farright[c]
                                       +  middle_ii * a_middle_farright[c]
                                       +  bottom_ii * a_bottom_farright[c]  )
                                                    * farright_j  );
      } while (++c<channels);

      jj++;

      j = 1;
      do {
        c = 0;
        do {
          a_top_left[c]        = a_top_center[c];
          a_top_center[c]      = a_top_right[c];
          a_top_right[c]       = a_top_farright[c];
          a_top_farright[c]    = *a1++;

          a_middle_left[c]     = a_middle_center[c];
          a_middle_center[c]   = a_middle_right[c];
          a_middle_right[c]    = a_middle_farright[c];
          a_middle_farright[c] = *a2++;

          a_bottom_left[c]     = a_bottom_center[c];
          a_bottom_center[c]   = a_bottom_right[c];
          a_bottom_right[c]    = a_bottom_farright[c];
          a_bottom_farright[c] = *a3++;

          coef_left[c]   =      top_ii * a_top_left[c]
                           + middle_ii * a_middle_left[c]
                           + bottom_ii * a_bottom_left[c];
          coef_center[c] =      top_ii * a_top_center[c]
                           + middle_ii * a_middle_center[c]
                           + bottom_ii * a_bottom_center[c];
          coef_right[c]  =      top_ii * a_top_right[c]
                           + middle_ii * a_middle_right[c]
                           + bottom_ii * a_bottom_right[c];
        } while (++c<channels);

        last_jj = last_overlapping_jj[j];

        while (jj<last_jj)
        {
          left_jj   =   left[jj];
          center_jj = center[jj];
          right_jj  =  right[jj];

          c = 0;
          do {
            *output_row_p++ =
              ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                       + coef_center[c] * center_jj
                                       +  coef_right[c] * right_jj  );
          } while (++c<channels);

          jj++;
        }

        left_jj    =    left[jj];
        center_jj  =  center[jj];
        right_jj   =   right[jj];
        farright_j = farright[j];

        c = 0;
        do {
          *output_row_p++ =
            ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                     + coef_center[c] * center_jj
                                     +  coef_right[c] * right_jj
                                     + (       top_ii * a_top_farright[c]
                                         +  middle_ii * a_middle_farright[c]
                                         +  bottom_ii * a_bottom_farright[c]  )
                                                      * farright_j  );
        } while (++c<channels);

        jj++;

      } while (++j<n_minus_two);

      /*
       * Now, we deal with j = n-2.
       */
      c = 0;
      do {
        a_top_left[c]      = a_top_center[c];
        a_top_center[c]    = a_top_right[c];
        a_top_right[c]     = a_top_farright[c];

        a_middle_left[c]   = a_middle_center[c];
        a_middle_center[c] = a_middle_right[c];
        a_middle_right[c]  = a_middle_farright[c];

        a_bottom_left[c]   = a_bottom_center[c];
        a_bottom_center[c] = a_bottom_right[c];
        a_bottom_right[c]  = a_bottom_farright[c];

        coef_left[c]   =      top_ii * a_top_left[c]
                         + middle_ii * a_middle_left[c]
                         + bottom_ii * a_bottom_left[c];
        coef_center[c] =      top_ii * a_top_center[c]
                         + middle_ii * a_middle_center[c]
                         + bottom_ii * a_bottom_center[c];
        coef_right[c]  =      top_ii * a_top_right[c]
                         + middle_ii * a_middle_right[c]
                         + bottom_ii * a_bottom_right[c];
      } while (++c<channels);

      last_jj = last_overlapping_jj[n_minus_two] + 1;

      while (jj<last_jj)
      {
        left_jj   =   left[jj];
        center_jj = center[jj];
        right_jj  =  right[jj];

        c = 0;
        do {
          *output_row_p++ =
            ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                     + coef_center[c] * center_jj
                                     +  coef_right[c] * right_jj  );
        } while (++c<channels);

        jj++;
      }

      /*
       * Now, we deal with j = n-1.
       */
      c = 0;
      do {
        a_top_left[c]      = a_top_center[c];
        a_top_center[c]    = a_top_right[c];

        a_middle_left[c]   = a_middle_center[c];
        a_middle_center[c] = a_middle_right[c];

        a_bottom_left[c]   = a_bottom_center[c];
        a_bottom_center[c] = a_bottom_right[c];

        coef_left[c]   =      top_ii * a_top_left[c]
                         + middle_ii * a_middle_left[c]
                         + bottom_ii * a_bottom_left[c];
        coef_center[c] =      top_ii * a_top_center[c]
                         + middle_ii * a_middle_center[c]
                         + bottom_ii * a_bottom_center[c];
      } while (++c<channels);

      while (jj<nn)
      {
        left_jj   =   left[jj];
        center_jj = center[jj];

        c = 0;
        do {
          *output_row_p++ =
            ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                     + coef_center[c] * center_jj  );
        } while (++c<channels);

        jj++;
      }

      /* write output_row */
      fwrite(output_row, sizeof(uchar), nn_times_channels, outputfile);

      ii++;
    }

    /*
     * Now, we take care of the last fine row which overlaps the
     * current coarse row. Right now, ii = last_ii.
     */

    /* move output_row_p back to start of output_row */
    output_row_p = output_row;

    top_ii      =      top[ii];
    middle_ii   =   middle[ii];
    bottom_ii   =   bottom[ii];
    farbottom_i = farbottom[i];

    a1 = (a+i_minus_one_times_n_times_channels);
    a2 = (a+i_times_n_times_channels);
    a3 = (a+i_plus_one_times_n_times_channels);
    a4 = (a+i_plus_two_times_n_times_channels);

    c = 0;
    do {
      a_top_center[c]        = *a1++;
      a_middle_center[c]     = *a2++;
      a_bottom_center[c]     = *a3++;
      a_farbottom_center[c]  = *a4++;
    } while (++c<channels);

    c = 0;
    do {
      a_top_right[c]          = *a1++;
      a_middle_right[c]       = *a2++;
      a_bottom_right[c]       = *a3++;
      a_farbottom_right[c]    = *a4++;
    } while (++c<channels);

    c = 0;
    do {
      a_top_farright[c]       = *a1++;
      a_middle_farright[c]    = *a2++;
      a_bottom_farright[c]    = *a3++;
      a_farbottom_farright[c] = *a4++;
    } while (++c<channels);

    c = 0;
    do {
      coef_center[c] =        top_ii * a_top_center[c]
                       +   middle_ii * a_middle_center[c]
                       +   bottom_ii * a_bottom_center[c]
                       + farbottom_i * a_farbottom_center[c];
      coef_right[c]  =        top_ii * a_top_right[c]
                       +   middle_ii * a_middle_right[c]
                       +   bottom_ii * a_bottom_right[c]
                       + farbottom_i * a_farbottom_right[c];
    } while (++c<channels);

    last_jj = last_overlapping_jj[0];

    for (jj=0; jj<last_jj; jj++)
    {
      center_jj = center[jj];
      right_jj  =  right[jj];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535( coef_center[c] * center_jj
                                   +  coef_right[c] * right_jj  );
      } while (++c<channels);
    }

    center_jj = center[jj];
    right_jj  =  right[jj];
    farright_j = farright[0];

    c = 0;
    do {
      *output_row_p++ =
        ROUND_AND_CLAMP_TO_065535(  coef_center[c] * center_jj
                                 +   coef_right[c] * right_jj
                                 + (        top_ii * a_top_farright[c]
                                     +   middle_ii * a_middle_farright[c]
                                     +   bottom_ii * a_bottom_farright[c]
                                     + farbottom_i * a_farbottom_farright[c]  )
                                                   * farright_j  );
    } while (++c<channels);

    jj++;

    j = 1;
    do {
      c = 0;
      do {
        a_top_left[c]           = a_top_center[c];
        a_top_center[c]         = a_top_right[c];
        a_top_right[c]          = a_top_farright[c];
        a_top_farright[c]       = *a1++;

        a_middle_left[c]        = a_middle_center[c];
        a_middle_center[c]      = a_middle_right[c];
        a_middle_right[c]       = a_middle_farright[c];
        a_middle_farright[c]    = *a2++;

        a_bottom_left[c]        = a_bottom_center[c];
        a_bottom_center[c]      = a_bottom_right[c];
        a_bottom_right[c]       = a_bottom_farright[c];
        a_bottom_farright[c]    = *a3++;

        a_farbottom_left[c]     = a_bottom_center[c];
        a_farbottom_center[c]   = a_bottom_right[c];
        a_farbottom_right[c]    = a_bottom_farright[c];
        a_farbottom_farright[c] = *a4++;

        coef_left[c]   =        top_ii * a_top_left[c]
                         +   middle_ii * a_middle_left[c]
                         +   bottom_ii * a_bottom_left[c]
                         + farbottom_i * a_farbottom_left[c];
        coef_center[c] =        top_ii * a_top_center[c]
                         +   middle_ii * a_middle_center[c]
                         +   bottom_ii * a_bottom_center[c]
                         + farbottom_i * a_farbottom_center[c];
        coef_right[c]  =        top_ii * a_top_right[c]
                         +   middle_ii * a_middle_right[c]
                         +   bottom_ii * a_bottom_right[c]
                         + farbottom_i * a_farbottom_right[c];
      } while (++c<channels);

      last_jj = last_overlapping_jj[j];

      while (jj<last_jj)
      {
        left_jj   =   left[jj];
        center_jj = center[jj];
        right_jj  =  right[jj];

        c = 0;
        do {
          *output_row_p++ =
            ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                     + coef_center[c] * center_jj
                                     +  coef_right[c] * right_jj  );
        } while (++c<channels);

        jj++;
      }

      left_jj    =    left[jj];
      center_jj  =  center[jj];
      right_jj   =   right[jj];
      farright_j = farright[j];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535(    coef_left[c] * left_jj
                                   +  coef_center[c] * center_jj
                                   +   coef_right[c] * right_jj
                                   + (        top_ii * a_top_farright[c]
                                       +   middle_ii * a_middle_farright[c]
                                       +   bottom_ii * a_bottom_farright[c]
                                       + farbottom_i * a_farbottom_farright[c] )
                                                     * farright_j  );
      } while (++c<channels);

      jj++;

    } while (++j<n_minus_two);

    c = 0;
    do {
      a_top_left[c]         = a_top_center[c];
      a_top_center[c]       = a_top_right[c];
      a_top_right[c]        = a_top_farright[c];

      a_middle_left[c]      = a_middle_center[c];
      a_middle_center[c]    = a_middle_right[c];
      a_middle_right[c]     = a_middle_farright[c];

      a_bottom_left[c]      = a_bottom_center[c];
      a_bottom_center[c]    = a_bottom_right[c];
      a_bottom_right[c]     = a_bottom_farright[c];

      a_farbottom_left[c]   = a_farbottom_center[c];
      a_farbottom_center[c] = a_farbottom_right[c];
      a_farbottom_right[c]  = a_farbottom_farright[c];

      coef_left[c]   =        top_ii * a_top_left[c]
                       +   middle_ii * a_middle_left[c]
                       +   bottom_ii * a_bottom_left[c]
                       + farbottom_i * a_farbottom_left[c];
      coef_center[c] =        top_ii * a_top_center[c]
                       +   middle_ii * a_middle_center[c]
                       +   bottom_ii * a_bottom_center[c]
                       + farbottom_i * a_farbottom_center[c];
      coef_right[c]  =        top_ii * a_top_right[c]
                       +   middle_ii * a_middle_right[c]
                       +   bottom_ii * a_bottom_right[c]
                       + farbottom_i * a_farbottom_right[c];
    } while (++c<channels);

    last_jj = last_overlapping_jj[j] + 1;

    while (jj<last_jj)
    {
      left_jj   =   left[jj];
      center_jj = center[jj];
      right_jj  =  right[jj];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                   + coef_center[c] * center_jj
                                   +  coef_right[c] * right_jj  );
      } while (++c<channels);

      jj++;
    }

    /*
     * Now, we deal with j = n-1.
     */
    c = 0;
    do {
      a_top_left[c]         = a_top_center[c];
      a_top_center[c]       = a_top_right[c];

      a_middle_left[c]      = a_middle_center[c];
      a_middle_center[c]    = a_middle_right[c];

      a_bottom_left[c]      = a_bottom_center[c];
      a_bottom_center[c]    = a_bottom_right[c];

      a_farbottom_left[c]   = a_farbottom_center[c];
      a_farbottom_center[c] = a_farbottom_right[c];

      coef_left[c]   =        top_ii * a_top_left[c]
                       +   middle_ii * a_middle_left[c]
                       +   bottom_ii * a_bottom_left[c]
                       + farbottom_i * a_farbottom_left[c];
      coef_center[c] =        top_ii * a_top_center[c]
                       +   middle_ii * a_middle_center[c]
                       +   bottom_ii * a_bottom_center[c]
                       + farbottom_i * a_farbottom_center[c];
    } while (++c<channels);

    while (jj<nn)
    {
      left_jj   =   left[jj];
      center_jj = center[jj];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                   + coef_center[c] * center_jj  );
      } while (++c<channels);

      jj++;
    }

    /* write output_row */
    fwrite(output_row, sizeof(uchar), nn_times_channels, outputfile);

    ii++;
  } while (++i<m_minus_two);

  /*
   * Now, we deal with the second to last coarse row.
   */

  last_ii = last_overlapping_ii[m_minus_two] + 1; /* The "+1" comes from the
                                                     fact that no exception
                                                     needs to be made for
                                                     farbottom, because there
                                                     is none. */

  while (ii<last_ii)
  {
    /* move output_row_p back to start of output_row */
    output_row_p = output_row;

    top_ii    =    top[ii];
    middle_ii = middle[ii];
    bottom_ii = bottom[ii];

    a1 = (a+m_minus_three_times_n_times_channels);
    a2 = (a+m_minus_two_times_n_times_channels);
    a3 = (a+m_minus_one_times_n_times_channels);

    c = 0;
    do {
      a_top_center[c]     = *a1++;
      a_middle_center[c]  = *a2++;
      a_bottom_center[c]  = *a3++;
    } while (++c<channels);

    c = 0;
    do {
      a_top_right[c]       = *a1++;
      a_middle_right[c]    = *a2++;
      a_bottom_right[c]    = *a3++;
    } while (++c<channels);

    c = 0;
    do {
      a_top_farright[c]    = *a1++;
      a_middle_farright[c] = *a2++;
      a_bottom_farright[c] = *a3++;
    } while (++c<channels);

    c = 0;
    do {
      coef_center[c] =      top_ii * a_top_center[c]
                       + middle_ii * a_middle_center[c]
                       + bottom_ii * a_bottom_center[c];
      coef_right[c]  =      top_ii * a_top_right[c]
                       + middle_ii * a_middle_right[c]
                       + bottom_ii * a_bottom_right[c];
    } while (++c<channels);

    last_jj = last_overlapping_jj[0];

    for (jj=0; jj<last_jj; jj++)
    {
      center_jj = center[jj];
      right_jj  =  right[jj];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535( coef_center[c] * center_jj
                                   +  coef_right[c] * right_jj  );
      } while (++c<channels);
    }

    center_jj = center[jj];
    right_jj  =  right[jj];
    farright_j = farright[0];

    c = 0;
    do {
      *output_row_p++ =
        ROUND_AND_CLAMP_TO_065535( coef_center[c] * center_jj
                                 +  coef_right[c] * right_jj
                                 + (       top_ii * a_top_farright[c]
                                     +  middle_ii * a_middle_farright[c]
                                     +  bottom_ii * a_bottom_farright[c]  )
                                                  * farright_j  );
    } while (++c<channels);

    jj++;

    j = 1;
    do {
      c = 0;
      do {
        a_top_left[c]        = a_top_center[c];
        a_top_center[c]      = a_top_right[c];
        a_top_right[c]       = a_top_farright[c];
        a_top_farright[c]    = *a1++;

        a_middle_left[c]     = a_middle_center[c];
        a_middle_center[c]   = a_middle_right[c];
        a_middle_right[c]    = a_middle_farright[c];
        a_middle_farright[c] = *a2++;

        a_bottom_left[c]     = a_bottom_center[c];
        a_bottom_center[c]   = a_bottom_right[c];
        a_bottom_right[c]    = a_bottom_farright[c];
        a_bottom_farright[c] = *a3++;

        coef_left[c]   =      top_ii * a_top_left[c]
                         + middle_ii * a_middle_left[c]
                         + bottom_ii * a_bottom_left[c];
        coef_center[c] =      top_ii * a_top_center[c]
                         + middle_ii * a_middle_center[c]
                         + bottom_ii * a_bottom_center[c];
        coef_right[c]  =      top_ii * a_top_right[c]
                         + middle_ii * a_middle_right[c]
                         + bottom_ii * a_bottom_right[c];
      } while (++c<channels);

      last_jj = last_overlapping_jj[j];

      while (jj<last_jj)
      {
        left_jj   =   left[jj];
        center_jj = center[jj];
        right_jj  =  right[jj];

        c = 0;
        do {
          *output_row_p++ =
            ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                     + coef_center[c] * center_jj
                                     +  coef_right[c] * right_jj  );
        } while (++c<channels);

        jj++;
      }

      left_jj    =    left[jj];
      center_jj  =  center[jj];
      right_jj   =   right[jj];
      farright_j = farright[j];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                   + coef_center[c] * center_jj
                                   +  coef_right[c] * right_jj
                                   + (       top_ii * a_top_farright[c]
                                       +  middle_ii * a_middle_farright[c]
                                       +  bottom_ii * a_bottom_farright[c]  )
                                                    * farright_j  );
      } while (++c<channels);

      jj++;

    } while (++j<n_minus_two);

    /*
     * Now, we deal with j = n-2.
     */
    c = 0;
    do {
      a_top_left[c]      = a_top_center[c];
      a_top_center[c]    = a_top_right[c];
      a_top_right[c]     = a_top_farright[c];

      a_middle_left[c]   = a_middle_center[c];
      a_middle_center[c] = a_middle_right[c];
      a_middle_right[c]  = a_middle_farright[c];

      a_bottom_left[c]   = a_bottom_center[c];
      a_bottom_center[c] = a_bottom_right[c];
      a_bottom_right[c]  = a_bottom_farright[c];

      coef_left[c]   =      top_ii * a_top_left[c]
                       + middle_ii * a_middle_left[c]
                       + bottom_ii * a_bottom_left[c];
      coef_center[c] =      top_ii * a_top_center[c]
                       + middle_ii * a_middle_center[c]
                       + bottom_ii * a_bottom_center[c];
      coef_right[c]  =      top_ii * a_top_right[c]
                       + middle_ii * a_middle_right[c]
                       + bottom_ii * a_bottom_right[c];
    } while (++c<channels);

    last_jj = last_overlapping_jj[j] + 1;

    while (jj<last_jj)
    {
      left_jj   =   left[jj];
      center_jj = center[jj];
      right_jj  =  right[jj];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                   + coef_center[c] * center_jj
                                   +  coef_right[c] * right_jj  );
      } while (++c<channels);

      jj++;
    }

    /*
     * Now, we deal with j = n-1.
     */
    c = 0;
    do {
      a_top_left[c]      = a_top_center[c];
      a_top_center[c]    = a_top_right[c];

      a_middle_left[c]   = a_middle_center[c];
      a_middle_center[c] = a_middle_right[c];

      a_bottom_left[c]   = a_bottom_center[c];
      a_bottom_center[c] = a_bottom_right[c];

      coef_left[c]   =      top_ii * a_top_left[c]
                       + middle_ii * a_middle_left[c]
                       + bottom_ii * a_bottom_left[c];
      coef_center[c] =      top_ii * a_top_center[c]
                       + middle_ii * a_middle_center[c]
                       + bottom_ii * a_bottom_center[c];
    } while (++c<channels);

    while (jj<nn)
    {
      left_jj   =   left[jj];
      center_jj = center[jj];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                   + coef_center[c] * center_jj  );
      } while (++c<channels);

      jj++;
    }

    /* write output_row */
    fwrite(output_row, sizeof(uchar), nn_times_channels, outputfile);

    ii++;
  }

  /*
   * Compute the last coarse row.
   */

  while (ii<mm)
  {
    /* move output_row_p back to start of output_row */
    output_row_p = output_row;

    top_ii = top[ii];
    middle_ii = middle[ii];

    a1 = (a+m_minus_two_times_n_times_channels);
    a2 = (a+m_minus_one_times_n_times_channels);

    c = 0;
    do {
      a_top_center[c]     = *a1++;
      a_middle_center[c]  = *a2++;
    } while (++c<channels);

    c = 0;
    do {
      a_top_right[c]       = *a1++;
      a_middle_right[c]    = *a2++;
    } while (++c<channels);

    c = 0;
    do {
      a_top_farright[c]    = *a1++;
      a_middle_farright[c] = *a2++;
    } while (++c<channels);

    c = 0;
    do {
      coef_center[c]       =      top_ii * a_top_center[c]
                             + middle_ii * a_middle_center[c];
      coef_right[c]        =      top_ii * a_top_right[c]
                             + middle_ii * a_middle_right[c];
    } while (++c<channels);

    last_jj = last_overlapping_jj[0];

    for (jj=0; jj<last_jj; jj++)
    {
      center_jj = center[jj];
      right_jj  =  right[jj];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535( coef_center[c] * center_jj
                                   +  coef_right[c] * right_jj  );
      } while (++c<channels);
    }

    center_jj = center[jj];
    right_jj  =  right[jj];
    farright_j = farright[0];

    c = 0;
    do {
      *output_row_p++ =
        ROUND_AND_CLAMP_TO_065535( coef_center[c] * center_jj
                                 +  coef_right[c] * right_jj
                                 + (       top_ii * a_top_farright[c]
                                     +  middle_ii * a_middle_farright[c]  )
                                                  * farright_j  );
    } while (++c<channels);

    jj++;

    j = 1;
    do {
      c = 0;
      do {
        a_top_left[c]        = a_top_center[c];
        a_top_center[c]      = a_top_right[c];
        a_top_right[c]       = a_top_farright[c];
        a_top_farright[c]    = *a1++;

        a_middle_left[c]     = a_middle_center[c];
        a_middle_center[c]   = a_middle_right[c];
        a_middle_right[c]    = a_middle_farright[c];
        a_middle_farright[c] = *a2++;

        coef_left[c]   =      top_ii * a_top_left[c]
                         + middle_ii * a_middle_left[c];
        coef_center[c] =      top_ii * a_top_center[c]
                         + middle_ii * a_middle_center[c];
        coef_right[c]  =      top_ii * a_top_right[c]
                         + middle_ii * a_middle_right[c];
      } while (++c<channels);

      last_jj = last_overlapping_jj[j];

      while (jj<last_jj)
      {
        left_jj   =   left[jj];
        center_jj = center[jj];
        right_jj  =  right[jj];

        c = 0;
        do {
          *output_row_p++ =
            ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                     + coef_center[c] * center_jj
                                     +  coef_right[c] * right_jj  );
        } while (++c<channels);

        jj++;
      }

      left_jj    =    left[jj];
      center_jj  =  center[jj];
      right_jj   =   right[jj];
      farright_j = farright[j];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                   + coef_center[c] * center_jj
                                   +  coef_right[c] * right_jj
                                   + (       top_ii * a_top_farright[c]
                                       +  middle_ii * a_middle_farright[c]  )
                                                    * farright_j  );
      } while (++c<channels);

      jj++;

    } while (++j<n_minus_two);

    /*
     * Now, we deal with j = n-2.
     */
    c = 0;
    do {
      a_top_left[c]      = a_top_center[c];
      a_top_center[c]    = a_top_right[c];
      a_top_right[c]     = a_top_farright[c];

      a_middle_left[c]   = a_middle_center[c];
      a_middle_center[c] = a_middle_right[c];
      a_middle_right[c]  = a_middle_farright[c];

      coef_left[c]   =      top_ii * a_top_left[c]
                       + middle_ii * a_middle_left[c];
      coef_center[c] =      top_ii * a_top_center[c]
                       + middle_ii * a_middle_center[c];
      coef_right[c]  =      top_ii * a_top_right[c]
                       + middle_ii * a_middle_right[c];
    } while (++c<channels);

    last_jj = last_overlapping_jj[j] + 1;

    while (jj<last_jj)
    {
      left_jj   =   left[jj];
      center_jj = center[jj];
      right_jj  =  right[jj];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                   + coef_center[c] * center_jj
                                   +  coef_right[c] * right_jj  );
      } while (++c<channels);

      jj++;
    }

    /*
     * Now, we deal with j = n-1.
     */
    c = 0;
    do {
      a_top_left[c]      = a_top_center[c];
      a_top_center[c]    = a_top_right[c];

      a_middle_left[c]   = a_middle_center[c];
      a_middle_center[c] = a_middle_right[c];

      coef_left[c]   =      top_ii * a_top_left[c]
                       + middle_ii * a_middle_left[c];
      coef_center[c] =      top_ii * a_top_center[c]
                       + middle_ii * a_middle_center[c];
    } while (++c<channels);

    while (jj<nn)
    {
      left_jj   =   left[jj];
      center_jj = center[jj];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535(   coef_left[c] * left_jj
                                   + coef_center[c] * center_jj  );
      } while (++c<channels);

      jj++;
    }

    /* write output_row */
    fwrite(output_row, sizeof(uchar), nn_times_channels, outputfile);

    ii++;
  }

  free(a);
  free(input_row);
  free(output_row);

  return 0;
}

int
main (int argc, char **argv)
{
  int n, m, nn, mm, maxval, header_char;
  double scale;
  FILE *inputfile, *outputfile;

  const char *progname = basename(argv[0]);

  if (argc < 4)
    usage (progname, "too few arguments");

  if (argc > 6)
    usage (progname, "too many arguments");

  if ((inputfile = fopen (argv[1], "rb")) == NULL)
    usage (progname, "cannot open input file");

  /* Try to read the PPM binary-mode "magic number" (P6) */
  header_char = fgetc (inputfile);
  if (header_char != 80 || fgetc (inputfile) != 54) {
    fclose (inputfile);
    usage (progname, "input must be a binary-mode PPM (P6) file...");
  }

  /* Skip the comment lines */
  do {
    header_char = fgetc (inputfile);
    if (header_char == 35) { /* 35 == '#' */
      do {
        header_char = fgetc (inputfile);
      } while (header_char != 10 && header_char != EOF); /* 10 == '\n'. */
    }
    if (header_char == EOF) {
      fclose (inputfile);
      usage (progname, "error reading PPM header");
    }
  } while (header_char < 48 || header_char > 57); /* 48 == '0', 57 == '9'. */
  fseek (inputfile, -1, SEEK_CUR); /* Rewind to the beginning of real data. */

  /* Read the PPM header */
  if (!fscanf (inputfile, "%d %d %d\n", &n, &m, &maxval)) {
    fclose (inputfile);
    usage (progname, "error reading PPM header");
  }

  /* Check for minimum dimensions */
  if (n < 15 || m < 15) {
    fclose (inputfile);
    usage (progname, "input image must be at least 15x15");
  }

  /* Check for 8-bit samples */
  if (maxval != 255) {
    fclose (inputfile);
    usage (progname, "input image must contain 8-bit samples");
  }

  /* Parse the command-line arguments */
  switch (argc) {
    case 4:
      /* width specified */
      nn = atoi (argv[3]);
      mm = (m * nn) / (double) n + 0.5;
      break;
    case 5:
      if (strcmp (argv[3], "-s") == 0)
        /* scale specified */
        scale = atof (argv[4]);
      else if (strcmp (argv[3], "-p") == 0)
        /* percentage specified */
        scale = .01 * atof (argv[4]);
      else if (strcmp (argv[3], "-h") == 0) {
        /* height specified */
        mm = atoi (argv[4]);
        nn = (n * mm) / (double) m + 0.5;
        break;
      }
      else {
        fclose (inputfile);
        usage (progname, "invalid arguments");
      }

      nn = rint (scale * n);
      mm = rint (scale * m);
      break;
    case 6:
      if (strcmp (argv[3], "-d") == 0) {
        /* dimensions specified */
        nn = atoi (argv[4]);
        mm = atoi (argv[5]);
        break;
      }
    default:
      fclose (inputfile);
      usage (progname, "invalid arguments");
  }

  /* Open the output file */
  if ((outputfile = fopen (argv[2], "wb")) == NULL) {
    fclose (inputfile);
    usage (progname, "cannot open output file");
  }

  /* Write the output file header */
  fprintf (outputfile, "%c%c\n# created by eanbqh\n%d %d\n%d\n",
           'P', '6', nn, mm, maxval);

  /* Call the upsampler */
  if (scale_up (inputfile, outputfile, m, n, mm, nn, maxval)) {
    fclose (inputfile);
    fclose (outputfile);
    usage (progname, "unable to read input file");
  }

  /* Close the image files */
  fclose(inputfile);
  fclose(outputfile);

  return 0;
}
