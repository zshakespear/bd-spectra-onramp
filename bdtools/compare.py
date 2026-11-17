"""Comparing a spectrum with a template (another spectrum or a model).

Conventions follow Rustamkulov et al. (2026, Sec. 4):

* a model is first binned onto the data's own channels (``binning``);
* the template is multiplied by one free scale factor (for a model this
  plays the role of (radius / distance)^2);
* a 3% systematic error is added in quadrature to the data's uncertainties;
* both the reduced chi-squared and the G_k statistic of Cushing et al. (2008)
  are reported. G_k weights each channel by its width, so the many narrow
  channels at 4-5 um do not dominate the fit.
"""

from dataclasses import dataclass, field

import numpy as np

from .binning import bin_to_spectrum
from .errors import BDToolsError
from .spectrum import Spectrum

DEFAULT_SYSTEMATIC = 0.03  # fractional, added in quadrature (Rustamkulov et al. 2026)


def total_error(data, systematic=DEFAULT_SYSTEMATIC):
    """Data uncertainty with a fractional systematic added in quadrature."""
    data.require_errors()
    return np.sqrt(data.err**2 + (systematic * data.flux) ** 2)


def channel_weights(data):
    """Cushing et al. (2008) weights: each channel's width, divided by the mean width."""
    lo, hi = data.channel_edges()
    w = hi - lo
    return w / np.nanmean(w)


def _in_windows(wave, windows):
    if windows is None:
        return np.ones(wave.shape, bool)
    windows = np.atleast_2d(np.asarray(windows, float))
    mask = np.zeros(wave.shape, bool)
    for lo, hi in windows:
        mask |= (wave >= lo) & (wave <= hi)
    return mask


def on_data_channels(template, data):
    """Put ``template`` on ``data``'s wavelengths and flux unit.

    * A model (no uncertainties, finer sampling) is averaged over each channel.
    * Another observed spectrum is interpolated, uncertainties included. Its
      sampling is already SPHEREx-like, so this only shifts it slightly.
    """
    if template.has_errors:
        t = template.to_unit(data.flux_unit).clean()
        flux = np.interp(data.wave_um, t.wave_um, t.flux, left=np.nan, right=np.nan)
        err = np.interp(data.wave_um, t.wave_um, t.err, left=np.nan, right=np.nan)
        lo, hi = data.channel_edges()
        meta = dict(template.meta, interpolated_to=data.name)
        return Spectrum(data.wave_um.copy(), flux, err, data.flux_unit, template.name, meta, lo, hi)
    return bin_to_spectrum(template, data)


def fit_scale(data_flux, data_err, template_flux, weights=None):
    """Scale factor a that minimises sum w (d - a t)^2 / sigma^2."""
    w = np.ones_like(data_flux) if weights is None else weights
    ok = np.isfinite(data_flux) & np.isfinite(data_err) & np.isfinite(template_flux) & (data_err > 0)
    if ok.sum() == 0:
        raise BDToolsError("No wavelengths where both spectra have good data -- cannot scale.")
    num = np.sum(w[ok] * data_flux[ok] * template_flux[ok] / data_err[ok] ** 2)
    den = np.sum(w[ok] * template_flux[ok] ** 2 / data_err[ok] ** 2)
    if den <= 0:
        raise BDToolsError("The template is zero everywhere in the chosen windows -- cannot scale.")
    return num / den


@dataclass
class Comparison:
    """Everything ``compare`` works out. Plot it with ``bdtools.plot_comparison``."""

    data: Spectrum
    template: Spectrum           # on the data's channels, already scaled
    scale: float
    windows: object
    systematic: float
    ratio: np.ndarray            # data / scaled template
    residual: np.ndarray         # data - scaled template
    significance: np.ndarray     # residual / combined uncertainty
    chi2_red: float
    gk: float
    n_used: int
    notes: list = field(default_factory=list)

    def summary(self):
        lines = [
            f"data:      {self.data.name}",
            f"template:  {self.template.name}",
            f"scale factor applied to template: {self.scale:.4g}"
            + ("" if self.windows is None else f"  (fit only in windows {self.windows})"),
            f"channels used: {self.n_used}",
            f"reduced chi^2 = {self.chi2_red:.2f}    G_k = {self.gk:.3g}"
            f"   (with {self.systematic:.0%} systematic)",
        ]
        lines += [f"note: {n}" for n in self.notes]
        return "\n".join(lines)

    def __repr__(self):
        return self.summary()


def compare(data, template, windows=None, systematic=DEFAULT_SYSTEMATIC, scale="chi2", fixed_scale=None):
    """Compare ``data`` with ``template`` the way Rustamkulov et al. (2026) do.

    Parameters
    ----------
    data : a Spectrum with uncertainties (a reference or candidate spectrum)
    template : a model Spectrum, or another reference Spectrum
    windows : list of (short, long) wavelength ranges in microns used to fit
        the scale factor, e.g. ``[(1.0, 1.3)]`` to match the J-band peak.
        ``None`` uses every channel.
    systematic : fractional error added in quadrature to the data (0.03 = 3%)
    scale : "chi2" (inverse-variance weighted) or "gk" (also weighted by
        channel width, as for G_k)
    fixed_scale : skip fitting and use this number instead
    """
    data.require_errors()
    d = data.clean()
    t = on_data_channels(template, d)
    sigma_d = total_error(d, systematic)
    weights = channel_weights(d)
    use = _in_windows(d.wave_um, windows) & np.isfinite(t.flux)
    notes = []
    if fixed_scale is not None:
        a = float(fixed_scale)
    else:
        w = weights if scale == "gk" else None
        a = fit_scale(np.where(use, d.flux, np.nan), sigma_d, t.flux, None if w is None else w)
    ts = t.scaled(a)
    sigma = sigma_d if not ts.has_errors else np.sqrt(sigma_d**2 + ts.err**2)
    resid = d.flux - ts.flux
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = d.flux / ts.flux
        signif = resid / sigma
    good = np.isfinite(signif)
    n = int(good.sum())
    n_free = 0 if fixed_scale is not None else 1
    chi2 = np.sum(signif[good] ** 2)
    chi2_red = chi2 / max(n - n_free, 1)
    gk = np.sum(weights[good] * signif[good] ** 2)
    if not np.all(good):
        notes.append(f"{(~good).sum()} channel(s) of the data are outside the template's range and were skipped.")
    return Comparison(d, ts, a, windows, systematic, ratio, resid, signif, chi2_red, gk, n, notes)


def rank_templates(data, templates, **kwargs):
    """Compare ``data`` with several templates; return a table sorted by G_k."""
    import pandas as pd

    rows = []
    for t in templates:
        c = compare(data, t, **kwargs)
        rows.append({"template": t.name, "scale": c.scale, "chi2_red": c.chi2_red, "G_k": c.gk,
                     "channels": c.n_used})
    return pd.DataFrame(rows).sort_values("G_k").reset_index(drop=True)


def ratio_to(spectrum, reference):
    """Ratio of two spectra on ``reference``'s wavelengths (no scaling, no errors).

    Used for parameter sweeps in notebook 5 (model / fiducial model), where both
    spectra are already on the same wavelengths. If they are not, ``spectrum``
    is interpolated onto ``reference``'s wavelengths.
    """
    s = spectrum.to_unit(reference.flux_unit)
    if s.wave_um.shape == reference.wave_um.shape and np.allclose(s.wave_um, reference.wave_um):
        f = s.flux
    else:
        f = np.interp(reference.wave_um, s.wave_um, s.flux, left=np.nan, right=np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        return f / reference.flux
