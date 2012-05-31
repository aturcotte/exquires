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
 * eanbqh.h -- header file for eanbqh8.c and eanbqh16.c
 * Copyright (C) 2012 Nicolas Robidoux and Adam Turcotte
 *
 * LAST UPDATED:
 * May 2, 2012
 *  - Added implementations of methods common between eanbqh8 and eanbqh16.
 *
 * COMPILATION INSTRUCTIONS:
 * For the version that supports PPM files with 8-bit samples, type
 *   gcc -o eanbqh8 eanbqh8.c -fomit-frame-pointer -O2 -Wall -march=native -lm
 * For the version that supports PPM files with 16-bit samples, type
 *   gcc -o eanbqh16 eanbqh16.c -fomit-frame-pointer -O2 -Wall -march=native -lm
 */

typedef unsigned short int pixval;
typedef unsigned char uchar;

static int scale_up (FILE *inputfile,
                     FILE *outputfile,
                     int   m,
                     int   n,
                     int   mm,
                     int   nn,
                     int   maxval);

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
