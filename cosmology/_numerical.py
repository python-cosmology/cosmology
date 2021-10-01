# author: Nicolas Tessore <n.tessore@ucl.ac.uk>
# license: MIT
'''numerical methods'''

import numpy as np
from functools import partial


def rk23(f, x0, x1, y0, h, atol=1e-8, rtol=1e-8):
    '''adaptive Runge-Kutta integrator of order 3(2)

    Uses the Bogacki–Shampine method. The adaptive Runge-Kutta integration is
    described by Press & Teukolsky (1992).

    Returns evaluation points and derivatives for cubic interpolation.

    The function f must be vectorised.

    '''
    # constants
    a = np.array([0, 1/2, 3/4, 1])
    c = np.array([2/9, 1/3, 4/9, 0])
    cs = np.array([7/24, 1/4, 1/3, 1/8])
    S = 0.95

    x, y, yp = [], [], []
    xn, yn = x0, y0
    while xn < x1:
        if xn + h > x1:
            h = x1 - xn
        k = f(xn + a*h)
        xnp1 = xn + h
        ynp1 = yn + h*(c@k)
        ysnp1 = yn + h*(cs@k)
        D0 = (atol + rtol*np.fabs(yn))/2
        D1 = np.fabs(ynp1 - ysnp1)
        if D0 >= D1:
            h = S*h*(D0/D1)**0.20 if D1 > 0 else 2*h
            x.append(xn)
            y.append(yn)
            yp.append(k[0])
            xn = xnp1
            yn = ysnp1
        else:
            h = S*h*(D0/D1)**0.25
    x.append(xn)
    y.append(yn)
    yp.append(f(xn))
    return np.array(x), np.array(y), np.array(yp)


def cubic(xi, x, y, yp):
    '''cubic interpolation given derivatives'''
    i1 = np.digitize(xi, x)
    i0 = i1-1

    x0, x1 = x[i0], x[i1]
    dx = x1 - x0
    t = (xi - x0)/dx

    f0, f1 = y[i0], y[i1]
    fp0, fp1 = dx*yp[i0], dx*yp[i1]

    a = 2*f0 - 2*f1 + fp0 + fp1
    b = -3*f0 + 3*f1 - 2*fp0 - fp1
    c = fp0
    d = f0

    return ((a*t + b)*t + c)*t + d


def antideriv(f, x0, x1, h, *, c=0., atol=1e-8, rtol=1e-8, inverse=False):
    '''antiderivative of a function

    Returns a function that is the antiderivative of the input function.
    Uses automatic integration and interpolation.

    The function f must be vectorised.

    '''
    x, y, yp = rk23(f, x0, x1, c, h, atol=atol, rtol=rtol)

    ad = partial(cubic, x=x, y=y, yp=yp)

    if inverse:
        dy = np.diff(y)
        if np.all(dy > 0):
            ad_inv = partial(cubic, x=y, y=x, yp=1/yp)
        elif np.all(dy < 0):
            ad_inv = partial(cubic, x=y[::-1], y=x[::-1], yp=1/yp[::-1])
        else:
            raise ValueError('antiderivative not invertible')

    return ad if not inverse else (ad, ad_inv)