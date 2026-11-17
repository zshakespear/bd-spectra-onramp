"""Unit conversions.

Conventions used everywhere in bdtools
--------------------------------------
* Wavelength is always in microns (um).
* F_lambda ("flux per unit wavelength") is in W / m^2 / um.
* F_nu ("flux per unit frequency") is in Jy (1 Jy = 1e-26 W / m^2 / Hz),
  or mJy where a function name says so.
* "Surface flux" is the flux leaving the top of the atmosphere. "Observed
  flux" is what reaches the telescope: surface flux * (R / d)^2.
"""

import numpy as np

C_M_S = 2.99792458e8          # speed of light [m/s]
H_J_S = 6.62607015e-34        # Planck constant [J s]
K_J_K = 1.380649e-23          # Boltzmann constant [J/K]
JY_SI = 1e-26                 # 1 Jy in W / m^2 / Hz
PARSEC_M = 3.085677581e16     # 1 parsec [m]
R_JUP_M = 7.1492e7            # Jupiter equatorial radius [m] (IAU nominal)

#: Flux units bdtools understands, mapped to a canonical name.
#: Keys are lower-case with spaces removed.
FLUX_UNIT_ALIASES = {
    "w/m2/um": "W/m2/um", "wm-2um-1": "W/m2/um", "w/m^2/um": "W/m2/um",
    "w/m2/micron": "W/m2/um", "w_m2_um": "W/m2/um",
    "jy": "Jy",
    "mjy": "mJy",
}


def canonical_flux_unit(unit):
    """Return bdtools' name for a flux unit string, or None if unknown."""
    if unit is None:
        return None
    return FLUX_UNIT_ALIASES.get(str(unit).strip().lower().replace(" ", ""))


def flambda_to_fnu_jy(wave_um, flambda):
    """Convert F_lambda [W/m^2/um] to F_nu [Jy].

    F_nu = F_lambda * lambda^2 / c  (with lambda in metres and F_lambda per metre).
    """
    wave_m = np.asarray(wave_um, float) * 1e-6
    flam_per_m = np.asarray(flambda, float) * 1e6
    return flam_per_m * wave_m**2 / C_M_S / JY_SI


def fnu_jy_to_flambda(wave_um, fnu_jy):
    """Convert F_nu [Jy] to F_lambda [W/m^2/um]. Inverse of ``flambda_to_fnu_jy``."""
    wave_m = np.asarray(wave_um, float) * 1e-6
    fnu_si = np.asarray(fnu_jy, float) * JY_SI
    return fnu_si * C_M_S / wave_m**2 * 1e-6


def fnu_mjy_to_flambda(wave_um, fnu_mjy):
    """Convert F_nu [mJy] to F_lambda [W/m^2/um]."""
    return fnu_jy_to_flambda(wave_um, np.asarray(fnu_mjy, float) * 1e-3)


def dilution_factor(distance_pc, radius_rjup):
    """(R / d)^2: the fraction by which surface flux is diluted on its way to us."""
    if distance_pc <= 0 or radius_rjup <= 0:
        from .errors import BDToolsError
        raise BDToolsError("Distance and radius must both be positive numbers.")
    return (radius_rjup * R_JUP_M / (distance_pc * PARSEC_M)) ** 2


def observed_to_surface(flux_observed, distance_pc, radius_rjup=1.0):
    """Turn flux measured at Earth into flux leaving the object's surface.

    Surface flux = observed flux * (d / R)^2. Works for any flux unit.
    The radius is an *assumption* (brown dwarfs are all roughly 0.8-1.3 R_Jup).
    """
    return np.asarray(flux_observed, float) / dilution_factor(distance_pc, radius_rjup)


def surface_to_observed(flux_surface, distance_pc, radius_rjup=1.0):
    """Turn surface flux into the flux an observer at ``distance_pc`` would measure."""
    return np.asarray(flux_surface, float) * dilution_factor(distance_pc, radius_rjup)
