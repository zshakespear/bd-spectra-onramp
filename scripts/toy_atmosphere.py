"""A deliberately simple TOY atmosphere for notebooks 2 and 3.

THIS IS A TOY. Its band positions roughly follow the real absorbers so the
pictures look familiar, but the band shapes and strengths are made up. It is
used to show *ideas* (photosphere, tau = 2/3, saturation, isothermal and
inverted atmospheres, band footprints). It must never be used to make a
quantitative claim about a real brown dwarf.

Physics
-------
* Plane-parallel, pure absorption (no scattering), local thermodynamic equilibrium.
* Optical depth at wavelength lambda down to pressure P:
      tau(lambda, P) = [k_cont + sum_i A_i * m_i * phi_i(lambda)] * (P / 1 bar)
                       + A_cia * phi_cia(lambda) * (P / 1 bar)^2 / 2
  phi_i are band shapes: a Gaussian core plus weak Lorentzian wings (so band
  wings reach into the windows, as real ones do); m_i are abundance
  multipliers (1 = default).
  The collision-induced (CIA) term grows as P^2, as for real H2-H2 collisions.
* Temperature from an Eddington-like relation on the continuum optical depth:
      T^4 = (3/4) T_eff^4 (tau_cont + Q)
  The grey Eddington solution has Q = 2/3; the toy uses Q = 0.15 so the upper
  atmosphere is cooler (as non-grey opacity makes it in real atmospheres) and
  the bands are easier to see. Isothermal and inverted variants are included.
* Emergent surface flux:  F_lambda = 2 pi * integral B_lambda(T(tau)) E_2(tau) dtau
* Contribution function: the integrand per unit ln P.
"""

import numpy as np
from scipy.special import expn

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bdtools.planck import planck_lambda  # noqa: E402

TOY_TEFF = 1000.0
K_CONT = 1.0
Q_TOP = 0.15

# (absorber, centre um, Gaussian sigma um, strength A relative to the continuum)
TOY_BANDS = [
    ("H2O", 0.93, 0.025, 4.0),
    ("H2O", 1.14, 0.025, 8.0),
    ("H2O", 1.40, 0.040, 40.0),
    ("H2O", 1.88, 0.060, 40.0),
    ("H2O", 2.75, 0.150, 60.0),
    ("CH4", 1.16, 0.020, 3.0),
    ("CH4", 1.68, 0.040, 8.0),
    ("CH4", 2.30, 0.080, 10.0),
    ("CH4", 3.32, 0.120, 80.0),
    ("CO", 2.35, 0.040, 3.0),
    ("CO", 4.65, 0.120, 25.0),
    ("CO2", 4.25, 0.040, 15.0),
]
# Centre and width put the toy CIA at ~1.6-3 um, the range the band atlas gives (1.7-3 um).
CIA = ("H2_CIA", 2.35, 0.30, 1.5)
ABSORBERS = ["H2O", "CH4", "CO", "CO2", "H2_CIA"]


WING = 0.01   # strength of the Lorentzian wing relative to the Gaussian core


def band_shape(w, centre, sigma):
    x = (w - centre) / sigma
    return np.exp(-0.5 * x**2) + WING / (1 + x**2)


def opacity_profile(wave_um, multipliers=None):
    """Return (k_lin, k_cia): coefficients of P and P^2/2 in the optical depth."""
    m = {a: 1.0 for a in ABSORBERS}
    m.update(multipliers or {})
    w = np.asarray(wave_um, float)
    k_lin = np.full_like(w, K_CONT)
    for name, c, s, a in TOY_BANDS:
        k_lin += m[name] * a * band_shape(w, c, s)
    _, c, s, a = CIA
    k_cia = m["H2_CIA"] * a * np.exp(-0.5 * ((w - c) / s) ** 2)
    return k_lin, k_cia


def temperature_profile(p_bar, kind="eddington", teff=TOY_TEFF, inversion_dt=900.0, inversion_p_bar=3e-2):
    """Temperature at each pressure for the three toy cases."""
    p = np.asarray(p_bar, float)
    if kind == "isothermal":
        return np.full_like(p, teff)
    t = (0.75 * teff**4 * (K_CONT * p + Q_TOP)) ** 0.25
    if kind == "eddington":
        return t
    if kind == "inversion":
        # warm the layers above inversion_p_bar, smoothly, by up to inversion_dt
        x = np.clip(np.log10(inversion_p_bar / p), 0, 1)
        return t + inversion_dt * (3 * x**2 - 2 * x**3)
    raise ValueError(kind)


def emergent_spectrum(wave_um, p_bar, t_k, multipliers=None):
    """Flux, photosphere pressure, and contribution function for one toy atmosphere.

    Returns dict with surface flux F_lambda [W/m^2/um] (n_wave), photosphere
    pressure where tau = 2/3 (n_wave), and contribution per ln P (n_wave, n_p).
    """
    w = np.asarray(wave_um, float)
    p = np.asarray(p_bar, float)
    k_lin, k_cia = opacity_profile(w, multipliers)
    tau = k_lin[:, None] * p[None, :] + 0.5 * k_cia[:, None] * p[None, :] ** 2
    b = planck_lambda(w[:, None], t_k[None, :])
    e2 = expn(2, np.maximum(tau, 1e-12))
    dtau_dlnp = (k_lin[:, None] * p[None, :] + k_cia[:, None] * p[None, :] ** 2)
    contrib = 2 * np.pi * b * e2 * dtau_dlnp        # dF / d ln P
    lnp = np.log(p)
    flux = np.trapezoid(contrib, lnp, axis=1) if hasattr(np, "trapezoid") else np.trapz(contrib, lnp, axis=1)
    # Light from above the top of the grid is negligible if tau(top) << 1; add the
    # optically thick bottom boundary 2 pi B(T_bottom) E_3(tau_bottom) for completeness.
    flux += 2 * np.pi * b[:, -1] * expn(3, tau[:, -1])
    photo = np.array([np.exp(np.interp(np.log(2 / 3), np.log(np.maximum(tau_i, 1e-300)), lnp)) for tau_i in tau])
    return {"flux": flux, "photosphere_bar": photo, "contribution": contrib, "tau": tau}
