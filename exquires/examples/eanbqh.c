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
 * For more information, see Fast Exact Area Image Upsampling with
 * Natural Biquadratic Histosplines by Nicolas Robidoux, Adam
 * Turcotte, Minglun Gong and Annie Tousignant, pp.85-96 of Image
 * Analysis and Recognition, 5th International Conference, ICIAR 2008,
 * Póvoa de Varzim, Portugal, June 25-27, 2008. Proceedings, Aurelio
 * C. Campilho, Mohamed S. Kamel (Eds.).  Lecture Notes in Computer
 * Science 5112, Springer 2008, ISBN 978-3-540-69811-1.
 */

/*
 * eanbqh.c -- EANBQH upsampler which supports PPM files with 16-bit samples
 * Copyright (C) 2012 Nicolas Robidoux and Adam Turcotte
 *
 * LAST UPDATED:
 *   October 28, 2012
 *
 * COMPILATION INSTRUCTIONS:
 *   gcc -o eanbqh eanbqh.c -fomit-frame-pointer -O2 -Wall -march=native -lm
 *
 * LIMITATIONS:
 *  - Currently, only binary-mode PPM (P6) files are supported.
 */

#include <libgen.h>
#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

typedef unsigned short int pixval;
typedef unsigned char uchar;

static void
last_overlapping_index (int o,
                        int oo,
                        int last_overlapping_kk[])
{
  /*
   * The comments use the variables which are relevant to the use of
   * this function in the horizontal direction. That is, n is o, nn is
   * oo, j is k, and jj is kk.
   *
   * This code uses a general convention that the input pixels have
   * unit sides, and that (describing things in 1D) the global
   * coordinate of the left endpoint of an input cell is exactly its
   * index. That, is the first input cell goes from 0 to 1, the last
   * one from n-1 to n. Given that,
   *
   * jj * n / nn (in rational arithmetic)
   *
   * is the absolute coordinate of the left endpoint of the index jj
   * fine cell (recall that jj starts at zero).  Given that the left
   * endpoints j of the coarse cells are 0, sizeof(pixval), 2...
   * this implies that
   *
   * (j * nn ) / n (in integer arithmetic)
   *
   * is the index of the first fine cell which is contained in the
   * index j coarse cell, so that
   *
   * ((j+1) * nn ) / n - 1 (in integer arithmetic)
   *
   * is the index of the last fine cell which overlaps the index j
   * coarse cell.
   *
   * There is another way of caracterizing this index: It is the
   * largest jj such that jj * n < j + 1. Using this caracterization
   * allows one to avoid integer divisions, and because by sweeping
   * through the jjs we know approximately what this index is, few
   * iterations are necessary. The key idea is as follows: whenever
   * the product of the next candidate jj by n initially fails the
   * above condition, the current jj is last_jj for this value of j.
   *
   * If n=nn, the last overlapping index is equal to the index.
   */
  int o_minus_1 = o-1; /* Useful iteration bound. */

  int k = 0;

  if (oo>o)
  {
    int k_plus_one_times_oo = oo;

    int kk = 0;
    int kk_plus_one_times_o = o;

    do
    {
      kk++; /* Because n < nn, we know that the first overlapping jj
               can't be the last overlapping jj, so we can increment
               without checking the condition. */
      kk_plus_one_times_o += o;

      while (kk_plus_one_times_o < k_plus_one_times_oo)
      {
        kk++; /* If the next jj satisfies the key condition, make it jj. */
        kk_plus_one_times_o += o;
      }

      last_overlapping_kk[k] = kk; /* We have found the last overlapping jj
                                      for the current value of j. */
      k++;
      k_plus_one_times_oo += oo;
    }
    while (k<o_minus_1);
  }
  else
  {
    do
    {
      last_overlapping_kk[k] = k;
      k++;
    }
    while (k<o_minus_1);
  }
}

/*
 * coarse_to_fine_coefficients ()
 *
 * This function is called twice: once in the "vertical" direction,
 * and once in the "horizontal" direction.
 *
 * The comments use the variables which are relevant to the use of
 * this function in the horizontal direction. That is, n is o, nn is
 * oo, j is k, and jj is kk.
 *
 * "INPUTS:" number of coarse cells n
 *           number of fine cells nn
 *           one int array with at last n-1 entries: last_overlapping_jj[]
 *
 * "OUTPUTS:" two double arrays with at least nn entries: left, center.
 *            one double array with at least nn-(nn/n) entries: right
 *            one double array with at least n entries: farright.
 *
 * Note that the very last entry of farright gets some storage, but
 * should not be used (incorrect value). The program could be
 * rewritten so that it only uses the first n-1 entries of farright.
 *
 * Also, the first nn/n + 1 entries of left should not be used (they do
 * not receive a value).
 *
 */
static void
coarse_to_fine_coefficients (int   o,
                             int   oo,
                             int   last_overlapping_kk[],
                             float left[],
                             float center[],
                             float right[],
                             float farright[])
{
  /*
   * Possible improvements: use long or unsigned integers to prevent
   * integer overflow: integers as large as n times nn are computed.
   * This does not appear to have been a problem, but it could be.
   */

  /*
   * Possible improvement: Use left/right symmetry to eliminate the
   * computation of half the coefficients. This is a Theta(m+n)
   * improvement (probably not worth the trouble). Because of the way
   * indices "stay left" for fine cells which overlap two coarse
   * cells, this is not as simple as it looks, unless there are no
   * overlapping fine cells, that is, unless the magnification factor
   * is an integer.
   */

  /*
   * Formulas for the antiderivatives of the cardinal basis functions,
   * with constants of integration set so that they are equal to zero
   * at the left boundary of the cell of interest: They are structured
   * a la Horner to minimize flops. Because x is Theta(1), some mild
   * cancellation will occur.
   */

  /*
   * The following describe the centered B-Spline (applicable in the
   * interior):
   */
#define LEFT_BSPLINE(x)            ( (x) *         (x) *       (x))
#define CENTER_BSPLINE(x)          ( (x) * (  3. - (x) * (-3.+(x)+(x))))
#define RIGHT_BSPLINE(x)           ( (x) * (  3. + (x) * (-3.+(x))))

  /*
   * For not a knot, the antiderivative which comes from the second
   * cell's B-Spline on the first (boundary) cell is not the same as
   * in the interior, as it is for natural boundary
   * conditions. LEFT_BOUNDARY_LEFT_SPLINE is consequently redundant
   * as far as natural boundary conditions are concerned.
   */
#ifdef NOT_A_KNOT

#define LEFT_BDRY_SPLINE(x)        ( (x) * ( 12. + (x) * (-6.+ (x))))
#define LEFT_BDRY_LEFT_SPLINE(x)   ( (x) * ( -9. + (x) * ( 9.-((x)+(x)))))
#define RIGHT_BDRY_SPLINE(x)       ( (x) * (  3. + (x) * ( 3.+ (x))))
#define RIGHT_BDRY_RIGHT_SPLINE(x) ( (x) * (  3. + (x) * (-3.-((x)+(x)))))
#define BDRY_INTEGRAL_LEFT_BDRY_SPLINE       (7.)
#define BDRY_INTEGRAL_LEFT_BDRY_LEFT_SPLINE (-2.)

#else

#define LEFT_BDRY_SPLINE(x)        ( (x) * (  6. -         (x)*(x)))
#define LEFT_BDRY_LEFT_SPLINE(x)   ( (x) *                 (x)*(x))
#define RIGHT_BDRY_SPLINE(x)       ( (x) * (  3. + (x) * ( 3.- (x))))
#define RIGHT_BDRY_RIGHT_SPLINE(x) ( (x) * (  3. + (x) * (-3.+ (x))))
#define BDRY_INTEGRAL_LEFT_BDRY_SPLINE       (5.)
#define BDRY_INTEGRAL_LEFT_BDRY_LEFT_SPLINE  (1.)

#endif

  double one_over_oo = 1./oo;
  double h = o * one_over_oo;

  /*
   * jj * n / nn (in rational arithmetic)
   *
   * is the absolute coordinate of the left endpoint of the index jj
   * fine cell (recall that jj starts at zero).  Given that the left
   * endpoints j of the coarse cells are 0, sizeof(pixval), 2... this implies that
   *
   * (j * nn ) / n (in integer arithmetic)
   *
   * is the index of the first fine cell which is contained in the
   * index j coarse cell, so that
   *
   * ((j+1) * nn ) / n - 1 (in integer arithmetic)
   *
   * is the index of the last fine cell which overlaps the index j
   * coarse cell.
   *
   * There is another way of caracterizing this index: It is the
   * largest jj such that jj * n < j + 1. Using this caracterization
   * allows one to avoid integer divisions, and because we usually know
   * approximately what this index is, few iterations allow one to find
   * it.
   */

  int k;
  int kk;

  int o_minus_1 = o-1;

  double x = 0.;

  double previous_integral_l;
  double previous_integral_c = 0.;
  double previous_integral_r = 0.;

  double integral_l;
  double integral_c;
  double integral_r;

  int last_kk = last_overlapping_kk[0];

  for (kk=0; kk<last_kk; kk++)
  {
    x += h;

    integral_c = LEFT_BDRY_SPLINE(x);
    center[kk] = integral_c - previous_integral_c;
    previous_integral_c = integral_c;

    /*
     * The integral which is contributed from the right coarse cell
     * (integral_r) is computed using the left piece of the
     * appropriate B-spline. This left/right duality is taken into
     * account throughout the code.
     */
    integral_r = LEFT_BDRY_LEFT_SPLINE(x);
    right[kk] = integral_r - previous_integral_r;
    previous_integral_r = integral_r;
  }

  /*
   * At this point, jj = last_jj, and the contributions to the last
   * fine cell which overlaps the first coarse cell are to be
   * computed.  Two cases may occur this last overlapping fine cell
   * may overlap the second coarse cell, or it may end right at the
   * first coarse cell's right boundary (located at the absolute
   * coordinate equal to 1.). It turns out that using the next piece
   * of antiderivative (after correcting for the different constants
   * of integration and local coordinate) works in both cases because,
   * in the no overlap case, the left and center pieces agree at their
   * common boundary once corrected for the different choices of
   * global antiderivatives.
   */

  /*
   * Alternate formula for x:
   *
   * x = ( kk+1 ) * h - 1.;
   */
  x = ( (kk+1) * o - oo ) * one_over_oo;

  /*
   * Because we are crossing to the next coarse cell, we use the right
   * piece of the B-splines to compute the "center" contribution. If it
   * happens that this fine cell ends right at the boundary of the first
   * coarse cell, RIGHT_BSPLINE(x) turns out to be 0, and consequently
   * the second coarse cell does not contribute to center[jj], as should
   * be.
   */
  previous_integral_l = RIGHT_BSPLINE(x);
  center[kk] = previous_integral_l +
               ( BDRY_INTEGRAL_LEFT_BDRY_SPLINE - previous_integral_c );

  previous_integral_c = CENTER_BSPLINE(x);
  right[kk]  = previous_integral_c +
               ( BDRY_INTEGRAL_LEFT_BDRY_LEFT_SPLINE - previous_integral_r );

  previous_integral_r = LEFT_BSPLINE(x); /* There is an hidden "- 0.". */
  farright[0] = previous_integral_r;

  /*
   * The very last coarse cell (the nth one, which has index n-1) is
   * an exception, just like the very first one, hence the
   * j<n_minus_1.
   */
  k = 1;
  do {
    last_kk = last_overlapping_kk[k];

    for (kk++; kk<last_kk; kk++)
    {
      x += h;

      integral_l = RIGHT_BSPLINE(x);
      left[kk] = integral_l - previous_integral_l;
      previous_integral_l = integral_l;

      integral_c = CENTER_BSPLINE(x);
      center[kk] = integral_c - previous_integral_c;
      previous_integral_c = integral_c;

      integral_r = LEFT_BSPLINE(x);
      right[kk] = integral_r - previous_integral_r;
      previous_integral_r = integral_r;
    }

    /*
     * x = ( kk+1 ) * h - (k + 1);
     *
     * is the distance from the left endpoint of the current coarse
     * cell to the right endpoint of the current fine cell.
     *
     * When we use large images, this quantity, which uses theta(nn)
     * quantities to compute a theta(1) value, may suffer from round
     * off error. Although we have not seen evidence of this---and
     * consequently the above formula, most likely, could most likely
     * used safely, especially if the output images are not too
     * large---we use integer arithmetic to compute this quantity.
     *
     * One disadvantage is that we may suffer from integer overflow if
     * the images are large. This could be fixed using long integers.
     *
     * NICOLAS: ADD A COMMENT SOMEWHERE ABOUT INTEGER OVERFLOW IF n *
     * nn or m * mm is larger than maxint.
     */

    x = ( (kk+1)*o - (k+1)*oo ) * one_over_oo;

    left[kk] = 1. - previous_integral_l;

    previous_integral_l = RIGHT_BSPLINE(x);
    center[kk] = previous_integral_l + ( 4. - previous_integral_c );

    previous_integral_c = CENTER_BSPLINE(x);
    right[kk] = previous_integral_c + ( 1. - previous_integral_r );

    previous_integral_r = LEFT_BSPLINE(x);
    farright[k] = previous_integral_r;
  } while (++k<o_minus_1);

  /*
   * Now, we deal with the very last coarse cell
   */

  /*
   * First, we need to correct the computed value which is wrong by
   * the fact that we used the centered B-spline instead of the right
   * boundary one. This correction is to be done only if the last_jj
   * cell overlaps the very last one, since otherwise the last cell
   * did not comtribute anything anyway, and consequently no
   * correction is needed. This is what the "if n divide nn" condition
   * checks.
   *
   * Note that farright[j] = farright[last_j] = farright[n-1] may also
   * be incorrect, but it is not used, so there is no need to correct
   * it.
   */

  /*
   * If not a knot, we also need to undo and correct the fact that we
   * used, over the overlap with the last cell, CENTER_BSPLINE instead
   * of RIGHT_BDRY_SPLINE and RIGHT_BSPLINE instead of
   * RIGHT_BDRY_RIGHT_SPLINE (for natural boundary conditions, these
   * last two are the same, so there is no need to do anything in this
   * case).
   */
  if ( oo%o )
  {
#ifdef NOT_A_KNOT
    center[kk] -= previous_integral_l;
    previous_integral_l = RIGHT_BDRY_RIGHT_SPLINE(x);
    center[kk] += previous_integral_l;
#endif
    right[kk] -= previous_integral_c;
    previous_integral_c = RIGHT_BDRY_SPLINE(x);
    right[kk] += previous_integral_c;
  }

  kk++;

  /*
   * Now we can proceed with the fine cells which have not received
   * values (those which are fully contained in the last coarse cell).
   */
  while (kk<oo)
  {
    x += h;

    integral_l = RIGHT_BDRY_RIGHT_SPLINE(x);
    left[kk] = integral_l - previous_integral_l;
    previous_integral_l = integral_l;

    integral_c = RIGHT_BDRY_SPLINE(x);
    center[kk] = integral_c - previous_integral_c;
    previous_integral_c = integral_c;

    kk++;
  }
}

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
  pixval *input_row, *input_row_p;
  pixval *output_row, *output_row_p;

  pixval val;
  uchar *p;
  int index;
  uchar temp;

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
  input_row  = (pixval *)malloc(sizeof(pixval[n_times_channels]));
  output_row = (pixval *)malloc(sizeof(pixval[nn_times_channels]));

  /*
   * Computation of the B-Spline coefficients:
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
       * Read one row of 16-bit (2 byte) intensity values into input_row
       */
      if (!fread (input_row, sizeof(pixval), n_times_channels, inputfile))
        return 1;

      /*
       * Column forward substitution
       */

      /*
       * Non-asymptotic LU factorization entries:
       */
      input_row_p = input_row;

      /*
       * Note that the bytes are swapped since standard PPM is big endian
       * while Intel is little endian
       */
      c = channels;
      do {
        val = *input_row_p++;
        val = ((val & 0x00ff)<<8)|((val & 0xff00)>>8);
        *a1++ = val * mm_nn_over_m_n;
      } while (--c);

      c = channels;
      do {
        val = *input_row_p++;
        val = ((val & 0x00ff)<<8)|((val & 0xff00)>>8);
        *a1++ = val * mm_nn_over_m_n - *a2++ * C0;
      } while (--c);

      c = channels;
      do {
        val = *input_row_p++;
        val = ((val & 0x00ff)<<8)|((val & 0xff00)>>8);
        *a1++ = val * mm_nn_over_m_n - *a2++ * C1;
      } while (--c);
    
      c = channels;
      do {
        val = *input_row_p++;
        val = ((val & 0x00ff)<<8)|((val & 0xff00)>>8);
        *a1++ = val * mm_nn_over_m_n - *a2++ * C2;
      } while (--c);

      c = channels;
      do {
        val = *input_row_p++;
        val = ((val & 0x00ff)<<8)|((val & 0xff00)>>8);
        *a1++ = val * mm_nn_over_m_n - *a2++ * C3;
      } while (--c);

      c = channels;
      do {
        val = *input_row_p++;
        val = ((val & 0x00ff)<<8)|((val & 0xff00)>>8);
        *a1++ = val * mm_nn_over_m_n - *a2++ * C4;
      } while (--c);

      c = channels;
      do {
        val = *input_row_p++;
        val = ((val & 0x00ff)<<8)|((val & 0xff00)>>8);
        *a1++ = val * mm_nn_over_m_n - *a2++ * C5;
      } while (--c);
    
      /*
       * Asymptotic (within roundoff) LU factorization entries:
       */
      c = n_minus_7_times_channels;
      while (c--) {
        val = *input_row_p++;
        val = ((val & 0x00ff)<<8)|((val & 0xff00)>>8);
        *a1++ = val * mm_nn_over_m_n - *a2++ * CINFTY;
      }

      /*
       * Column-based back substitution
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
     * Row based forward substitution
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
     * Row-based back substitution
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
   * stored in the array a[][]
   */

  /*
   * Now, we compute the tensor components of the linear
   * transformation from B-Spline coefficents to fine cell averages
   * (actually fine cell integrals, since we have alread rescaled by
   * the reciprocal of the fine cell areas)
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

#define ROUND_AND_CLAMP_TO_065535(x)                                     \
({                                                                       \
  int out = .5 + (x);                                                    \
  (out > 65535) ? (pixval)65535 : ((out < 0) ? (pixval)0 : (pixval)out); \
})

    for (jj=0; jj<last_jj; jj++)
    {
      center_jj = center[jj];
      right_jj  =  right[jj];

      c = 0;
      do {
        *output_row_p++ =
          ROUND_AND_CLAMP_TO_065535( coef_center[c] * center_jj
                                   +  coef_right[c] * right_jj );
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
                                     +  bottom_ii * a_bottom_farright[c] )
                                                  * farright_j );
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
                                     +  coef_right[c] * right_jj );
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
                                       +  bottom_ii * a_bottom_farright[c] )
                                                    * farright_j );
      } while (++c<channels);

      jj++;

    } while (++j<n_minus_two);

    /*
     * Now, we deal with j = n-2
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
                                   +  coef_right[c] * right_jj );
      } while (++c<channels);

      jj++;
    }

    /*
     * Now, we deal with j = n-1
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
                                   + coef_center[c] * center_jj );
      } while (++c<channels);

      jj++;
    }

    /* write output_row */
    p = (uchar *) output_row;

    /* Swap bytes again, since standard PPM is big endian
     * while Intel is little endian
     */
    for (index = 0; index < nn; index++) {
      temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
      temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
      temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
    }
    fwrite(output_row, sizeof(pixval), nn_times_channels, outputfile);
  }

  /*
   * Now, take care of the last fine row which overlaps the first
   * coarse row. (Right now, ii = last_ii.)
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
                                 +  coef_right[c] * right_jj );
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
                                   + farbottom_i * a_farbottom_farright[c] )
                                                 * farright_j );
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
                                   +  coef_right[c] * right_jj );
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
                                     + farbottom_i * a_farbottom_farright[c] )
                                                   * farright_j );
    } while (++c<channels);

    jj++;

  } while (++j<n_minus_two);

  /*
   * Now, we deal with j = n-2
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
                                 +  coef_right[c] * right_jj );
    } while (++c<channels);

    jj++;
  }

  /*
   * Now, we deal with j = n-1
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
                                 + coef_center[c] * center_jj );
    } while (++c<channels);

    jj++;
  }

  /* write output_row */
  p = (uchar *) output_row;
  for (index = 0; index < nn; index++) {
    temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
    temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
    temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
  }
  fwrite(output_row, sizeof(pixval), nn_times_channels, outputfile);

  ii++;

  /*
   * Now, we deal with the second, and later, coarse rows
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
                                     +  coef_right[c] * right_jj );
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
                                       +  bottom_ii * a_bottom_farright[c] )
                                                    * farright_j );
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
                                       +  coef_right[c] * right_jj );
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
                                         +  bottom_ii * a_bottom_farright[c] )
                                                      * farright_j );
        } while (++c<channels);

        jj++;

      } while (++j<n_minus_two);

      /*
       * Now, we deal with j = n-2
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
                                     +  coef_right[c] * right_jj );
        } while (++c<channels);

        jj++;
      }

      /*
       * Now, we deal with j = n-1
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
                                     + coef_center[c] * center_jj );
        } while (++c<channels);

        jj++;
      }

      /* write output_row */
      p = (uchar *) output_row;
      for (index = 0; index < nn; index++) {
        temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
        temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
        temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
      }
      fwrite(output_row, sizeof(pixval), nn_times_channels, outputfile);

      ii++;
    }

    /*
     * Now, take care of the last fine row which overlaps the current
     * coarse row. (Right now, ii = last_ii.)
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
                                   +  coef_right[c] * right_jj );
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
                                     + farbottom_i * a_farbottom_farright[c] )
                                                   * farright_j );
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
                                     +  coef_right[c] * right_jj );
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
                                                     * farright_j );
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
                                   +  coef_right[c] * right_jj );
      } while (++c<channels);

      jj++;
    }

    /*
     * Now, we deal with j = n-1
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
                                   + coef_center[c] * center_jj );
      } while (++c<channels);

      jj++;
    }

    /* write output_row */
    p = (uchar *) output_row;
    for (index = 0; index < nn; index++) {
      temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
      temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
      temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
    }
    fwrite(output_row, sizeof(pixval), nn_times_channels, outputfile);

    ii++;
  } while (++i<m_minus_two);

  /*
   * Now, we deal with the second to last coarse row
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
                                   +  coef_right[c] * right_jj );
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
                                     +  bottom_ii * a_bottom_farright[c] )
                                                  * farright_j );
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
                                     +  coef_right[c] * right_jj );
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
                                       +  bottom_ii * a_bottom_farright[c] )
                                                    * farright_j );
      } while (++c<channels);

      jj++;

    } while (++j<n_minus_two);

    /*
     * Now, we deal with j = n-2
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
                                   +  coef_right[c] * right_jj );
      } while (++c<channels);

      jj++;
    }

    /*
     * Now, we deal with j = n-1
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
                                   + coef_center[c] * center_jj );
      } while (++c<channels);

      jj++;
    }

    /* write output_row */
    p = (uchar *) output_row;
    for (index = 0; index < nn; index++) {
      temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
      temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
      temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
    }
    fwrite(output_row, sizeof(pixval), nn_times_channels, outputfile);

    ii++;
  }

  /*
   * Compute the last coarse row
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
                                   +  coef_right[c] * right_jj );
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
                                     +  middle_ii * a_middle_farright[c] )
                                                  * farright_j );
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
                                     +  coef_right[c] * right_jj );
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
                                       +  middle_ii * a_middle_farright[c] )
                                                    * farright_j );
      } while (++c<channels);

      jj++;

    } while (++j<n_minus_two);

    /*
     * Now, we deal with j = n-2
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
                                   +  coef_right[c] * right_jj );
      } while (++c<channels);

      jj++;
    }

    /*
     * Now, we deal with j = n-1
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
                                   + coef_center[c] * center_jj );
      } while (++c<channels);

      jj++;
    }

    /* write output_row */
    p = (uchar *) output_row;
    for (index = 0; index < nn; index++) {
      temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
      temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
      temp = *p; *p = *(p+1); *(p+1) = temp; p += 2;
    }
    fwrite(output_row, sizeof(pixval), nn_times_channels, outputfile);

    ii++;
  }

  free(a);
  free(input_row);
  free(output_row);

  return 0;
}

static void
usage (const char *progname, const char *errmsg)
{
  printf ("%s: error: %s\n\n", progname, errmsg);
  printf ("USAGE:\n");
  printf ("  1. Specify output width:\n         ");
  printf ("\033[1m%s\033[0m input.ppm output.ppm ", progname);
  printf ("\033[4mwidth\033[0m\n");
  printf ("  2. Specify output height:\n         ");
  printf ("\033[1m%s\033[0m input.ppm output.ppm ", progname);
  printf ("\033[1m-h\033[0m \033[4mheight\033[0m\n");
  printf ("  3. Specify output dimensions:\n         ");
  printf ("\033[1m%s\033[0m input.ppm output.ppm ", progname);
  printf ("\033[1m-d\033[0m \033[4mwidth\033[0m \033[4mheight\033[0m\n");
  printf ("  4. Specify the scaling factor:\n         ");
  printf ("\033[1m%s\033[0m input.ppm output.ppm ", progname);
  printf ("\033[1m-s\033[0m \033[4mscale\033[0m\n");
  printf ("  5. Specify the scaling factor as a percentage:\n         ");
  printf ("\033[1m%s\033[0m input.ppm output.ppm ", progname);
  printf ("\033[1m-p\033[0m \033[4mpercentage\033[0m\n");

  exit(1);
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

  /* Check for 16-bit samples */
  if (maxval != 65535) {
    fclose (inputfile);
    usage (progname, "input image must contain 16-bit samples");
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
