import numpy as np
from bokeh.plotting import figure, output_file, show
from numpy import cosh, log, pi, tanh
from scipy.constants import mu_0

flux_dens = np.linspace(0.01, 1.0, 200)


def parallel_loss(f, C, ac, bpar, bp):
    """
    Calculates the parallel component of the AC losses.

    :param f: frequency of the AC current [Hz]
    :param C: empirical factor, 0.75
    :param ac: ac is an effective area of the tape which depends on the geometrical configuration of the tape.
    :param bpar: parallel magnetic field in [T]
    :param bp: is the full penetration field, it is fitted on experimental data
    :return:
    """
    if bpar < bp:
        P_par = 2 * f * C * ac * bpar**3 / (3 * mu_0 * bp)
    else:
        P_par = 2 * f * C * ac * bp / (3 * mu_0) * (3.0 * bpar - 2.0 * bp)
    return P_par


def logcosh(x):
    # s always has real part >= 0
    s = np.sign(x) * x
    p = np.exp(-2 * s)
    return s + np.log1p(p) - np.log(2)


def perp_loss(K, f, w, bc, bperp):
    """
    Ac losses, which generated by the perpendicular component of the magnetic field.
    :param K: geometrical parameters
    :param f: frequency
    :param w: width of the tape
    :param bc: critical magnetic field
    :param bperp:
    :return:
    """
    beta = bperp / bc
    # P_perp = K * f * (w ** 2.) * pi / mu_0 * bc ** 2. * beta * (2. / beta * log(cosh(beta)) - tanh(beta))
    P_perp = K * f * (w**2.0) * pi / mu_0 * bc**2.0 * beta * (2.0 / beta * logcosh(beta) - tanh(beta))

    return P_perp


def norris_equation(f, I, Ic):
    """
    Norris equation describes the self-field losses of the conductor for elliptical cross section:
    :param f: frequency
    :param I:
    :param Ic: critical current of the conductor.
    :return:
    """
    return f * Ic**2 * mu_0 / pi * ((1.0 - I / Ic) * np.log(1.0 - I / Ic) + (I / Ic - I**2 / (2 * Ic**2)))


def plot_pp_losses():
    """Plots the parallel and the perpendicular losses, the parameters are based on:
    N. Magnussona,*, A. Wolfbrandt. AC losses in high-temperature superconducting tapes exposed
    to longitudinal magnetic fields
    """
    p = figure(title="Losses", y_axis_type="log", x_range=(0.01, 1), y_range=(0.01, 30))
    # background_fill_color="#fafafa")

    p.line(
        flux_dens,
        perp_loss(1.35, 50, 4.29 * 1e-3, 0.011, flux_dens),
        legend_label="perpendicular loss",
        line_color="tomato",
        line_dash="dashed",
        line_width=2.5,
    )

    f = 50.0
    c = (0.75,)
    bp = 0.033
    Ac = 0.21 * 4.29 * 1e-6

    bpv = np.vectorize(parallel_loss)
    p.line(
        flux_dens,
        bpv(f, c, Ac, flux_dens, bp),
        legend_label="parallel losses",
        line_dash="dotted",
        line_color="indigo",
        line_width=2.5,
    )

    p.legend.location = "top_left"

    output_file("logplot.html", title="log plot example")

    show(p)


def plot_self_field_losses():
    """Plots the parallel and the perpendicular losses, the parameters are based on:
    N. Magnussona,*, A. Wolfbrandt. AC losses in high-temperature superconducting tapes exposed
    to longitudinal magnetic fields
    """

    Ic = 115.0  # A
    current = np.linspace(2.0, 114.9, 100)

    p = figure(x_range=(0.01, 1), y_range=(0.01, 0.12), x_axis_label="Ic [A]", y_axis_label="P [W/m]")

    p.line(
        current / Ic,
        norris_equation(50, current, Ic),
        legend_label="self-field losses",
        line_color="teal",
        line_dash="dashed",
        line_width=2.5,
    )

    p.legend.location = "top_left"

    output_file("logplot.html", title="log plot example")

    show(p)


if __name__ == "__main__":
    plot_pp_losses()
    plot_self_field_losses()
