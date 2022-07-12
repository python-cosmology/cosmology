# author: Nicolas Tessore <n.tessore@ucl.ac.uk>
# license: MIT
'''module for large scale structure'''

import numpy as np
from scipy.special import loggamma

PI = np.pi
SRPI = PI**0.5


def sigma2_r(k, pk, q=0.0, kr=1.0, window='tophat', krgood=True, deriv=False):
    r'''mass variance from matter power spectrum

    Computes the mass variance :math:`\sigma^2(r)` inside a spherical window of
    scale :math:`r` from an input matter power spectrum.  Commonly a tophat
    window is used to produce the variance in spheres of a given radius, but
    other choices are supported.

    The input matter power must be given on a logarithmic grid, and the mass
    variance will returned on a logarithmic grid.  By default, the output grid
    is scaled such that :math:`k_i \, r_{n-i+1} = 1 \forall i = 1, \ldots, n`,
    but can be shifted to other constants using the ``kr`` parameter.

    The function optionally computes the derivative of :math:`\sigma^2(r)` with
    respect to :math:`\ln r` at the same time, if ``deriv`` is true.

    Parameters
    ----------
    k : array_like (N,)
        Wavenumbers at which the power spectrum is given.  Must have
        logarithmic spacing.
    pk : array_like (..., N)
        Power spectrum for given wavenumbers ``k``.  Can be multidimensional.
        Last axis must agree with the wavenumber axis.
    q : float, optional
        Bias parameter for integral transform.
    kr : float, optional
        Shift parameter for logarithmic output grid.
    window : str, optional
        Type of window function for computing the mass variance.  Supported
        values are ``'tophat'``, ``'gaussian'``.
    krgood : bool, optional
        Change given ``kr`` to the nearest value fulfilling the low-ringing
        condition.
    deriv : bool, optional
        Also return the first derivative of the mass variance.

    Returns
    -------
    r : array_like (N,)
        Scales at which the mass variance is evaluated.
    sigma2_r : array_like (..., N)
        Mass variance in spheres of scale ``r``.  Leading axes correspond to
        the input power spectrum.
    dsigma2_dlnr : array_like (..., N), optional
        If ``deriv`` is true, the derivative of ``sigma2_r`` with respect to
        the logarithm of ``r``.

    Notes
    -----
    The mass variance is an integral transform of the matter power spectrum
    :math:`P(k)`,

    .. math::

        \sigma^2_r = \frac{1}{2\pi^2}
                        \int_{0}^{\infty} \! P(k) \, k^2 \, w^2(kr) \, dk \;.

    If :math:`P(k)` is given on a logarithmic grid of :math:`k` values, the
    integral can be computed for a logarithmic grid of :math:`r` values with a
    modification of Hamilton's FFTLog algorithm [1]_,

    .. math::

        U(x) = \int_{0}^{\infty} \! t^x \, w^2(t) \, dt \;.

    The implementation supports the usual tophat window function,

    .. math::

        w(x) = \frac{3}{x^3} \, \bigl\{\sin(x) - x \cos(x)\bigr\} \;,

    and the Gaussian window function,

    .. math::

        w(x) = \exp(-x^2/2) \;.

    References
    ----------
    .. [1] Hamilton A. J. S., 2000, MNRAS, 312, 257.
           doi:10.1046/j.1365-8711.2000.03071.x

    Examples
    --------
    Create a mock power spectrum with a realistic shape.

    >>> k = np.logspace(-4, 2, 40)
    >>> pk = 4e6*k/(1 + k*25)**3.5
    >>>
    >>> import matplotlib.pyplot as plt
    >>> plt.loglog(k, pk)
    >>> plt.xlabel('$k$')
    >>> plt.ylabel('$P(k)$')
    >>> plt.show()

    Compute the mass variance from the power spectrum without setting any
    optional parameters.

    >>> from cosmology import sigma2_r
    >>>
    >>> r, s2 = sigma2_r(k, pk)
    >>>
    >>> plt.loglog(r, s2)
    >>> plt.xlabel('$r$')
    >>> plt.ylabel('$\\sigma^2_r$')
    >>> plt.show()

    The computed mass variance shows a numerical issue on the right, which is
    due to the circular nature of the integral transform it employs.  By
    computing the mass variance with a biased transform (``q = 0.8``), the
    problem disappears.  The exact value of the bias parameter ``q`` depends on
    the shape of the input power spectrum.

    >>> r, s2 = sigma2_r(k, pk, q=0.8)
    >>>
    >>> plt.loglog(r, s2)
    >>> plt.xlabel('$r$')
    >>> plt.ylabel('$\\sigma^2_r$')
    >>> plt.show()

    The integral transform method makes it possible to compute the derivative
    of the mass variance with very little extra computational cost.

    >>> r, s2, ds2_dlnr = sigma2_r(k, pk, q=0.8, deriv=True)
    >>>
    >>> plt.loglog(r, s2)
    >>> plt.loglog(r, -ds2_dlnr)
    >>> plt.xlabel('$r$')
    >>> plt.ylabel('$\\sigma^2_r$ and $-d\\sigma^2_r/d\ln r$')
    >>> plt.show()

    '''

    if np.ndim(k) != 1:
        raise TypeError('k must be 1d array')
    if np.shape(pk)[-1] != len(k):
        raise TypeError('last axis of pk must agree with size of k')

    # set up log space k
    lnkr = np.log(kr)
    n = len(k)
    lnk1 = np.log(k[0])
    lnkn = np.log(k[-1])
    lnkc = (lnk1 + lnkn)/2
    dlnk = (lnkn - lnk1)/(n-1)
    jc = (n-1)/2
    j = np.arange(n)

    # make sure given k is linear in log space
    if not np.allclose(k, np.exp(lnkc + (j-jc)*dlnk)):
        raise ValueError('k array not a logarithmic grid')

    # window function
    if window == 'tophat':
        if not -1 < q < 3:
            raise ValueError('bias error: tophat window requires -1 < q < 3')

        def U(x):
            dlg = loggamma((1 + x)/2) - loggamma((4 - x)/2)
            return 9*SRPI*np.exp(dlg)/((4 - x)**2 - 1)

    elif window == 'gaussian':
        if not q > -1:
            raise ValueError('bias error: gaussian window requires q > -1')

        def U(x):
            return np.exp(loggamma((x + 1)/2))/2

    else:
        raise ValueError(f'unknown window function: {window}')

    # low-ringing condition
    if krgood:
        y = PI/dlnk
        u = np.exp(-1j*y*lnkr)*U(q + 1j*y)
        a = np.angle(u)/PI
        lnkr = lnkr + dlnk*(a - np.round(a))

    # transform factor
    y = np.linspace(0, 2*PI*(n//2)/(n*dlnk), n//2+1)
    u = np.exp(-1j*y*lnkr)*U(q + 1j*y)

    # low-ringing kr should make last coefficient real
    if krgood and not np.isclose(u[-1].imag, 0):
        raise ValueError('unable to construct low-ringing transform, '
                         'try odd number of points or different q')

    # fix last coefficient to real when n is even
    if not n & 1:
        u.imag[-1] = 0

    # transform via real FFT
    cm = np.fft.rfft(pk*k**(2-q), axis=-1)
    cm *= u
    s2 = np.fft.irfft(cm, n, axis=-1)
    s2[..., :] = s2[..., ::-1]

    # set up r in log space
    r = np.exp(lnkr)/k[::-1]

    # prefactor for output
    s2 /= 2*PI**2
    s2 /= r**(1+q)

    # result for scales and sigma2
    result = (r, s2)

    # derivative
    if deriv:
        cm *= -(1 + q + 1j*y)
        ds2 = np.fft.irfft(cm, n, axis=-1)
        ds2[..., :] = ds2[..., ::-1]
        ds2 /= 2*PI**2
        ds2 /= r**(1+q)
        result = result + (ds2,)

    # return all results
    return result
