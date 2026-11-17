"""Blackbodies and brightness temperature."""

import numpy as np

from .units import C_M_S, H_J_S, K_J_K

# Second radiation constant hc/k in um K
_HC_OVER_K_UM_K = H_J_S * C_M_S / K_J_K * 1e6
WIEN_B_UM_K = 2897.771955  # Wien displacement constant for the peak of B_lambda [um K]


def planck_lambda(wave_um, temperature_k):
    """Planck function B_lambda in W / m^2 / um / sr.

    ``wave_um`` and ``temperature_k`` can be numbers or arrays; normal numpy
    broadcasting applies (e.g. a column of temperatures times a row of
    wavelengths gives a 2-D table).
    """
    lam_m = np.asarray(wave_um, float) * 1e-6
    t = np.asarray(temperature_k, float)
    x = _HC_OVER_K_UM_K / (np.asarray(wave_um, float) * t)
    with np.errstate(over="ignore"):
        b_per_m = 2 * H_J_S * C_M_S**2 / lam_m**5 / np.expm1(x)
    return b_per_m * 1e-6


def blackbody_surface_flux(wave_um, temperature_k):
    """Flux leaving the surface of a blackbody, pi * B_lambda, in W / m^2 / um."""
    return np.pi * planck_lambda(wave_um, temperature_k)


def wien_peak_um(temperature_k):
    """Wavelength (um) where B_lambda peaks: lambda_max = 2898 um K / T."""
    return WIEN_B_UM_K / np.asarray(temperature_k, float)


def brightness_temperature(wave_um, surface_flux_flambda):
    """Temperature of the blackbody that would give this surface flux at this wavelength.

    Parameters
    ----------
    wave_um : wavelength(s) in microns
    surface_flux_flambda : surface flux F_lambda in W / m^2 / um
        (use ``units.observed_to_surface`` first for an observed spectrum).

    Returns NaN where the flux is zero, negative, or missing.
    """
    lam_um = np.asarray(wave_um, float)
    f = np.asarray(surface_flux_flambda, float)
    lam_m = lam_um * 1e-6
    # pi * B = F  ->  B = F/pi, in per-metre units
    b_per_m = f / np.pi * 1e6
    with np.errstate(divide="ignore", invalid="ignore"):
        arg = 2 * H_J_S * C_M_S**2 / (lam_m**5 * b_per_m)
        tb = _HC_OVER_K_UM_K / (lam_um * np.log1p(arg))
    tb = np.where(np.isfinite(tb) & (f > 0), tb, np.nan)
    return tb
