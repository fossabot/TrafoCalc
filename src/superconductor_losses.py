import numpy as np
from numpy import pi, tanh
from scipy.constants import mu_0
from src.base_functions import C_RHO

# BSCCO cable from Magnussons' paper
# ----------------------------------
# f = 50.0
# c = 0.75
# bp = 0.033
# Ac = 0.31 * 4.29 * 1e-6
# Magnetic field's  typical value in a small transformer'S winding (630 kVA)
# bpar = 68. * 1e-3  # mT


def parallel_loss(bpar, f, C=0.77, ac=0.31 * 4.1 * 1e-6, bp=34.4 * 1e-3):
    """
    Calculates the parallel component of the AC losses.
    BSCCO cable from Magnussons' paper

    :param f: frequency of the AC current [Hz]
    :param C: empirical factor, 0.75
    :param ac: ac is an effective area of the tape which depends on the geometrical configuration of the tape.
    :param bpar: parallel magnetic field in [T]
    :param bp: is the full penetration field, it is fitted on experimental data
    :return:
    """
    if bpar <= bp:
        P_par = 2 * f * C * ac * bpar ** 3. / (3. * mu_0 * bp)
    else:
        P_par = 2 * f * C * ac * bp / (3. * mu_0) * (3.0 * bpar - 2.0 * bp)
    return P_par


def logcosh(x):
    # s always has real part >= 0
    s = np.sign(x) * x
    p = np.exp(-2 * s)
    return s + np.log1p(p) - np.log(2)


def perp_loss(f, bperp, K=1.35, w=4.1 * 1e-3, bc=15. * 1e-3):
    """
    Default parameters set acc to 10.1109/TASC.2003.813123.
    Ac losses, which generated by the perpendicular component of the magnetic field.
    :param K: geometrical parameters
    :param f: frequency
    :param w: width of the tape
    :param bc: critical magnetic field
    :param bperp:
    :return:
    """
    beta = bperp / bc
    P_perp = K * f * (w ** 2.0) * pi / mu_0 * bc ** 2.0 * beta * (2.0 / beta * logcosh(beta) - tanh(beta))

    return P_perp


def norris_equation(f, I, Ic):
    """
    Norris equation describes the self-field losses of the conductor for elliptical cross section:
    :param f: frequency
    :param I:
    :param Ic: critical current of the conductor.
    :return:
    """
    return f * Ic ** 2 * mu_0 / pi * ((1.0 - I / Ic) * np.log(1.0 - I / Ic) + (I / Ic - I ** 2 / (2 * Ic ** 2)))


def magnusson_ac_loss(b_ax, b_rad, f, I, Ic=170):
    """
    :param b_ax: parallel component of the magnetic field
    :param b_rad: radial component of the magnetic field
    :param f: network frequency
    :param I: current
    :param Ic: critical current
    :return: The result is in W/m, which can estimate the losses.
    """

    return parallel_loss(b_ax, f) + perp_loss(f, b_rad) + norris_equation(f, I, Ic)


def supra_winding_ac_loss(b_list: list, f, I, Ic=170, kappa=1.2):
    """
    This calculation is based on the ac loss calculation of the superconducting winding by the Magnusson formula.

    :param b: (bax, brad) list of b pairs
    :param f: frequency
    :param I: current
    :param Ic:critical current of the conductor.
    :param kappa: considers the winding layout, which can reduce the radial losses in the conductors
    :return:
    """
    pax = 0
    prad = 0
    for elem in b_list:
        pax += parallel_loss(elem[0], f)
        prad += perp_loss(f, elem[1]) / kappa

    return round((pax + prad) / len(b_list) + norris_equation(f, I, Ic), 3)


def cryostat_losses(Acr, dT=228.0):
    """
    Calculating the cryostat losses according to doi: 10.1088/1742-6596/97/1/012318
    :param Acr: the surface of the cryostat # m2
    :param dT: temperature difference between the maximum outside temperature (40C) and the working temp
    :return: losses of the cryostat
    """

    k_th = 2.0 * 1e-3  # W/(mK)
    d_th = 50.0 * 1e-3  # mm - thermal insulation thickness
    # the windings considered to work at 65 K -> dT = 293 - 65 = 228
    return round(k_th / d_th * Acr * 1e-6 * dT, 2)


def cryo_surface(r_in, r_ou, h):
    """
    It is assumed that the cryostat contains the low voltage and the high voltage windings.
    :param r_in:radius of the inner surface
    :param r_ou: height of the cryostat winding + end insulation
    :return:
    """

    a_in = 2. * r_in * pi * h
    a_ou = 2. * r_ou * pi * h

    return a_in + a_ou + (r_ou ** 2. - r_in ** 2.) * pi


def thermal_incomes(I1p, I2p):
    """
    Total current incomes through the current leads for 3 phase

    :param I1p: current in the primary windings
    :param I2p: current in the secondary windings
    :return:
    """
    q_cl = 45.0 * 1e-3  # W/A

    return round(6. * q_cl * (I1p + I2p), 2)


def sc_load_loss(p_ac, pcr, pcl, C=18.0):
    """
    The cooling cost in sc transformers is relatively high, therefore the cooling cost is penalized by a cooling factor.
    doi: 10.1088/1742-6596/97/1/012318

    :param C: penalty factor for considering the losses, it is about 18 due to the applied reference.
              18, factor to consider the thermal losses thorough the current leads
              the wors coolers efficiency is around 5% while the best coolers efficiency is around 15%
              doi:10.1088/1757-899X/101/1/012001, so the C should be between 20 and 12.
    :param p_ac: ac losses
    :param pcr: cryostat losses
    :param pcl: losses generated in the current lead
    :return:
    """

    return C * (p_ac + pcr + pcl)


def cooler_cost(cooling_power):
    """Gives back the approximative price of a cooler with a given loss,
       doi:10.1088/1757-899X/101/1/012001 """
    return 1.81 * cooling_power ** 0.57 * 1e3

def eddy_loss(i, t=0.31*1e-6, w=4.29*1e-6, f=50, I_c=115):
    """
    :param t: thickness of the conductor
    :param w: width of the conductor
    :param f: Hz
    :param Ic: A
    :return:
    """
    return 4*mu_0**2./pi*t*w*f**2/C_RHO*I_c**2
