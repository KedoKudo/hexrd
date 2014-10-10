import numpy as np
from scipy import optimize as opt

def dummy(xy_in, params, invert=False):
    """
    """
    return xy_in

def newton(x0, f, fp, extra, prec=3e-16, maxiter=100):
    for i in range(maxiter):
        x = x0 - f(x0, *extra) / fp(x0, *extra)
        relerr = np.max(np.abs(x - x0)) / np.max(np.abs(x))
        if relerr < prec:
            # print 'stopping at %d iters' % i
            return x
        x0 = x
    print 'Newtons method got to maximum of %d iters, relerr was %g' % (maxiter, relerr)
    return x0


def GE_41RT(xy_in, params, invert=False):
    """
    Apply radial distortion to polar coordinates on GE detector

    xin, yin are 1D arrays or scalars, assumed to be relative to self.xc, self.yc
    Units are [mm, radians].  This is the power-law based function of Bernier.

    Available Keyword Arguments :

    invert = True or >False< :: apply inverse warping
    """
    if params[0] == 0 and params[1] == 0 and params[2] == 0:
        return xy_in
    else:
        # canonical max radius based on perfectly centered beam
        rhoMax = 204.8

        x0 = xy_in[:, 0].flatten()
        y0 = xy_in[:, 1].flatten()

        npts = len(x0)

        # detector relative polar coordinates
        #   - this is the radius that gets rescaled
        rho0 = np.sqrt( x0*x0 + y0*y0 )
        eta0 = np.arctan2( y0, x0 )

        if invert:
            # in here must do nonlinear solve for distortion
            # must loop to call fsolve individually for each point
            
            rhoSclFuncInv = lambda ri, ni, ro, rx, p: \
                (p[0]*(ri/rx)**p[3] * np.cos(2.0 * ni) + \
                 p[1]*(ri/rx)**p[4] * np.cos(4.0 * ni) + \
                 p[2]*(ri/rx)**p[5] + 1)*ri - ro

            rhoSclFIprime = lambda ri, ni, ro, rx, p: \
                p[0]*(ri/rx)**p[3] * np.cos(2.0 * ni) * (p[3] + 1) + \
                p[1]*(ri/rx)**p[4] * np.cos(4.0 * ni) * (p[4] + 1) + \
                p[2]*(ri/rx)**p[5] * (p[5] + 1) + 1

            useNewton = False
            if useNewton:
                rhoOut = newton(rho0, rhoSclFuncInv, rhoSclFIprime,
                                (eta0, rho0, rhoMax, params))
            else:
                rhoOut = np.zeros(npts, dtype=float)
                for iRho in range(len(rho0)):
                    rhoOut[iRho] = opt.fsolve(rhoSclFuncInv, rho0[iRho],
                                              fprime=rhoSclFIprime,
                                              args=(eta0[iRho], rho0[iRho], rhoMax, params) )
                    pass
            if False: # len(rho0) > 1:
                # Save versions of this data!
                np.save('rho0.npy', rho0)
                np.save('rhoOut.npy', rhoOut)
                np.save('eta0.npy', eta0)
                np.save('rhoMax.npy', rhoMax)
                np.save('params.npy', params)
                import sys
                sys.exit(1)
        else:
            # usual case: calculate scaling to take you from image to detector plane
            # 1 + p[0]*(ri/rx)**p[2] * np.cos(p[4] * ni) + p[1]*(ri/rx)**p[3]
            rhoSclFunc = lambda ri, rx=rhoMax, p=params, ni=eta0: \
                         p[0]*(ri/rx)**p[3] * np.cos(2.0 * ni) + \
                         p[1]*(ri/rx)**p[4] * np.cos(4.0 * ni) + \
                         p[2]*(ri/rx)**p[5] + 1

            rhoOut = np.squeeze( rho0 * rhoSclFunc(rho0) )
            pass

        xout = rhoOut * np.cos(eta0) 
        yout = rhoOut * np.sin(eta0) 
    return np.vstack([xout, yout]).T
