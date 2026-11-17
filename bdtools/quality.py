"""Spotting data problems before interpreting a feature.

Rustamkulov et al. (2026) clip points more than 4 sigma from a running median,
yet some spurious points remain; candidate spectra are cleaned unevenly. These
helpers *flag* suspicious points -- they never delete anything. Deciding
whether a flagged point is bad is the student's job.
"""

import numpy as np
from scipy.ndimage import median_filter

from .errors import MissingDataError


def running_median_outliers(spectrum, window=3, nsigma=4.0, systematic=0.03):
    """Flag points more than ``nsigma`` uncertainties from a running median.

    Returns a boolean array (True = suspicious). ``window`` is the number of
    channels in the running median. The uncertainty includes a fractional
    ``systematic`` (3%, as in the model comparisons), because at high S/N
    real spectral structure would otherwise be flagged. Steep real features
    (e.g. the red optical slope below 1 um) can still be flagged: a flag is a
    reason to look, not proof of a bad point.
    """
    spectrum.require_errors()
    f = spectrum.flux.copy()
    good = spectrum.good()
    med = np.full_like(f, np.nan)
    med[good] = median_filter(f[good], size=window, mode="nearest")
    sigma = np.sqrt(spectrum.err**2 + (systematic * f) ** 2)
    with np.errstate(invalid="ignore", divide="ignore"):
        dev = np.abs(f - med) / sigma
    return good & (dev > nsigma)


def find_gaps(spectrum, factor=2.5):
    """Wavelength ranges where the spacing between channels is much bigger than usual.

    Returns a list of (short, long) pairs in microns.
    """
    w = spectrum.clean().wave_um
    if w.size < 3:
        return []
    step = np.diff(w) / w[1:]                     # fractional spacing, ~1/R
    typical = median_filter(step, size=9, mode="nearest")
    big = step > factor * typical
    return [(w[i], w[i + 1]) for i in np.where(big)[0]]


def missing_or_bad(spectrum):
    """Number of channels with missing flux or uncertainty."""
    return int((~spectrum.good()).sum())


def quality_report(spectrum, window=3, nsigma=4.0):
    """A short plain-language summary of possible data problems."""
    lines = [f"Quality check for '{spectrum.name}':"]
    nbad = missing_or_bad(spectrum)
    lines.append(f"  {len(spectrum)} channels, {nbad} with missing flux or uncertainty")
    try:
        out = running_median_outliers(spectrum, window, nsigma)
        if out.any():
            wl = ", ".join(f"{x:.2f}" for x in spectrum.wave_um[out])
            lines.append(f"  {out.sum()} point(s) more than {nsigma:g} sigma from the running median at: {wl} um")
        else:
            lines.append(f"  no isolated outliers beyond {nsigma:g} sigma")
    except MissingDataError:
        raise
    except Exception as e:  # noqa: BLE001 -- report, don't crash, in a teaching tool
        lines.append(f"  outlier check skipped ({e})")
    gaps = find_gaps(spectrum)
    if gaps:
        lines.append("  gaps in wavelength coverage: " + ", ".join(f"{a:.2f}-{b:.2f} um" for a, b in gaps))
    else:
        lines.append("  no unusual gaps in wavelength coverage")
    if spectrum.has_errors:
        snr = np.nanmedian(spectrum.snr())
        lines.append(f"  median signal-to-noise: {snr:.0f}")
    return "\n".join(lines)
