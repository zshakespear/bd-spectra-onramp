"""Putting a model onto the same channels as a SPHEREx spectrum.

Rustamkulov et al. (2026) compare models with data by averaging the model
flux over each SPHEREx channel's bandwidth, then converting to Jy. bdtools
does exactly that: ``bin_to_spectrum(model, data)``.

Never compare a high-resolution model directly with a SPHEREx spectrum. A
model at R ~ 500 has narrow features that SPHEREx (R ~ 40 below ~4 um) blurs
together; the comparison is only fair once the model is binned.
"""

import warnings

import numpy as np

from .errors import BDToolsError

#: If one neighbour of a channel is more than this many times farther away
#: than the other, we treat the far side as a gap when guessing channel edges.
GAP_RATIO = 1.8


def edges_from_centers(wave_um):
    """Guess the short and long edge of each channel from the channel centres.

    Each edge is put halfway to the neighbouring centre. Where a channel sits
    next to a gap in the data (its neighbour on one side is much farther away
    than on the other side), the channel is made symmetric using the *near*
    side, so it does not swallow the gap.

    This is an approximation. If the spectrum file lists real channel edges,
    those are used instead (see ``Spectrum.channel_edges``).
    """
    w = np.asarray(wave_um, float)
    if w.size < 2:
        raise BDToolsError("Need at least two wavelength points to work out channel widths.")
    if np.any(np.diff(w) <= 0):
        raise BDToolsError("Wavelengths must be strictly increasing to work out channel widths.")
    d = np.diff(w)
    left = np.empty_like(w)
    right = np.empty_like(w)
    left[1:] = d / 2
    right[:-1] = d / 2
    left[0] = right[0]
    right[-1] = left[-1]
    too_wide_left = left > GAP_RATIO * right
    too_wide_right = right > GAP_RATIO * left
    left[too_wide_left] = right[too_wide_left]
    right[too_wide_right] = left[too_wide_right]
    return w - left, w + right


def _cumulative_integral(x, y):
    """Running integral of the straight-line interpolant through (x, y)."""
    out = np.zeros_like(x)
    out[1:] = np.cumsum(0.5 * (y[1:] + y[:-1]) * np.diff(x))
    return out


def _integral_to(xq, x, y, cum):
    """Integral of the piecewise-linear (x, y) curve from x[0] to each xq."""
    i = np.clip(np.searchsorted(x, xq, side="right") - 1, 0, x.size - 2)
    yq = np.interp(xq, x, y)
    return cum[i] + 0.5 * (y[i] + yq) * (xq - x[i])


def bin_mean(wave_um, flux, lo_um, hi_um):
    """Mean of ``flux`` over each wavelength interval [lo, hi].

    The flux is treated as a straight-line curve between its points, and the
    mean is the exact integral over the interval divided by its width. Channels
    that fall partly outside the input wavelength range come back as NaN.
    """
    x = np.asarray(wave_um, float)
    y = np.asarray(flux, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if x.size < 2:
        raise BDToolsError("The spectrum to be binned has fewer than two usable points.")
    order = np.argsort(x)
    x, y = x[order], y[order]
    lo = np.asarray(lo_um, float)
    hi = np.asarray(hi_um, float)
    cum = _cumulative_integral(x, y)
    inside = (lo >= x[0]) & (hi <= x[-1]) & (hi > lo)
    out = np.full(lo.shape, np.nan)
    out[inside] = (_integral_to(hi[inside], x, y, cum) - _integral_to(lo[inside], x, y, cum)) \
        / (hi[inside] - lo[inside])
    return out


def bin_to_spectrum(model, data, name=None):
    """Bin a model ``Spectrum`` onto the channels of a data ``Spectrum``.

    The model flux is averaged over each of the data's channels (in the model's
    own F_lambda units, as in Rustamkulov et al. 2026) and then expressed in the
    data's flux unit. The result has the data's wavelengths and channel edges
    and no uncertainties.
    """
    lo, hi = data.channel_edges()
    m = model.to_flambda()
    binned = bin_mean(m.wave_um, m.flux, lo, hi)
    if np.all(np.isnan(binned)):
        raise BDToolsError(
            f"Model '{model.name}' does not cover the wavelengths of '{data.name}', so it cannot be binned."
        )
    meta = dict(model.meta)
    meta.update(kind="binned model", binned_to=data.name,
                binning="mean F_lambda over each channel's bandwidth")
    out = type(model)(wave_um=data.wave_um.copy(), flux=binned, err=None, flux_unit="W/m2/um",
                      name=name or model.name, meta=meta, chan_lo_um=lo, chan_hi_um=hi)
    return out.to_unit(data.flux_unit)


def at_spherex_resolution(model, like=None, name=None):
    """Return a model averaged to SPHEREx resolution, for plotting and comparing.

    ``like`` : a real spectrum whose channels to use (best). If None, an
    approximate SPHEREx channel layout is used (see ``spherex_like_channels``).
    """
    if like is not None:
        return bin_to_spectrum(model, like, name=name)
    from .spectrum import Spectrum

    centres, lo, hi = spherex_like_channels()
    m = model.to_flambda()
    flux = bin_mean(m.wave_um, m.flux, lo, hi)
    meta = dict(model.meta, kind="binned model", binned_to="approximate SPHEREx channels",
                binning="mean F_lambda over each channel's bandwidth")
    return Spectrum(centres, flux, None, "W/m2/um", name or model.name, meta, lo, hi).to_unit(model.flux_unit)


def log_wavelength_grid(wmin_um, wmax_um, resolution):
    """Wavelength grid with constant resolving power R = lambda / d_lambda."""
    if wmin_um <= 0 or wmax_um <= wmin_um or resolution <= 0:
        raise BDToolsError("Need 0 < wmin < wmax and a positive resolution.")
    n = int(np.floor(np.log(wmax_um / wmin_um) * resolution)) + 1
    return wmin_um * np.exp(np.arange(n) / resolution)


def resample_to_resolution(wave_um, flux, resolution, wmin_um, wmax_um):
    """Average a spectrum into channels of constant resolving power.

    Returns ``(centres, mean_flux)``; used by the library build scripts to
    store models at modest resolution (R ~ 500).
    """
    edges = log_wavelength_grid(wmin_um, wmax_um, resolution)
    lo, hi = edges[:-1], edges[1:]
    centres = np.sqrt(lo * hi)
    xs = np.sort(np.asarray(wave_um, float))
    native_step = np.nanmedian(np.diff(xs) / xs[1:])
    if native_step > 1.0 / resolution:
        warnings.warn(
            f"The input spectrum (R ~ {1 / native_step:.0f}) is coarser than the requested R = {resolution}; "
            "the output will not really have that resolution."
        )
    return centres, bin_mean(wave_um, flux, lo, hi)


def spherex_like_channels(r_short=40.0, r_long=115.0, split_um=3.82, wmin_um=0.75, wmax_um=5.0):
    """An *approximate* SPHEREx channel layout, for toy models only.

    R ~ 40 below ``split_um`` and R ~ 115 above, following the numbers in the
    job spec. Real spectra carry their own channels; use those whenever there
    is a real spectrum to compare with.
    Returns ``(centres, lo, hi)``.
    """
    e1 = log_wavelength_grid(wmin_um, split_um, r_short)
    e2 = log_wavelength_grid(e1[-1], wmax_um, r_long)
    edges = np.concatenate([e1, e2[1:]])
    lo, hi = edges[:-1], edges[1:]
    return np.sqrt(lo * hi), lo, hi
