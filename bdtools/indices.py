"""Spectral indices (Rustamkulov et al. 2026, Table 5 and Eqs. 3-4).

An index is a magnitude:  I = -2.5 log10(F_band / F_norm), where F_band and
F_norm are the mean fluxes in the feature and normalization regions. A larger
index means a deeper absorption band. The regions live in
``data/indices.yaml`` so the instructor can edit them without touching code.
"""

from dataclasses import dataclass, field

import numpy as np
import yaml

from .errors import BDToolsError, MissingDataError
from .paths import INDICES_FILE

_LN10 = np.log(10.0)


def load_index_definitions(path=None):
    """Read the index definitions from ``data/indices.yaml``."""
    path = INDICES_FILE if path is None else path
    try:
        with open(path, encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh)
    except FileNotFoundError:
        raise MissingDataError(f"Index definition file not found: {path}") from None
    if not cfg or "indices" not in cfg:
        raise BDToolsError(f"{path} has no 'indices:' section.")
    return cfg


@dataclass
class IndexResult:
    name: str
    value: float
    err: float
    n_feature: int
    n_norm: int
    feature_um: tuple
    norm_um: tuple
    warnings: list = field(default_factory=list)

    def __repr__(self):
        s = f"{self.name} index = {self.value:.3f} +/- {self.err:.3f}"
        s += f"  ({self.n_feature} feature channels, {self.n_norm} normalization channels)"
        for w in self.warnings:
            s += f"\n  ! {w}"
        return s


def _region_mean(wave, flux, err, region):
    lo, hi = region
    m = (wave >= lo) & (wave <= hi) & np.isfinite(flux)
    if err is not None:
        m &= np.isfinite(err)
    n = int(m.sum())
    if n == 0:
        return np.nan, np.nan, 0
    mean = flux[m].mean()
    sig = np.sqrt(np.sum(err[m] ** 2)) / n if err is not None else np.nan
    return mean, sig, n


def compute_index(spectrum, name, definitions=None, spectral_type=None):
    """Compute one index for one spectrum.

    Parameters
    ----------
    spectrum : a Spectrum (any flux unit; it is converted to the unit set in
        indices.yaml before the means are taken)
    name : "CH4", "CO2", or "CO" (or any other name in indices.yaml)
    spectral_type : optional, e.g. "Y1"; used only to warn when the index is
        not meaningful for that type. Taken from ``spectrum.meta`` if not given.
    """
    cfg = load_index_definitions() if definitions is None else definitions
    defs = cfg["indices"]
    if name not in defs:
        raise BDToolsError(f"No index called '{name}'. Available: {', '.join(defs)}.")
    d = defs[name]
    s = spectrum.to_unit(cfg.get("flux_unit", "Jy"))
    err = s.err if s.has_errors else None
    fb, sb, nb = _region_mean(s.wave_um, s.flux, err, d["feature_um"])
    fn, sn, nn = _region_mean(s.wave_um, s.flux, err, d["norm_um"])
    warnings = []
    if nb == 0 or nn == 0:
        warnings.append("No data in the feature or normalization region; the index cannot be computed.")
        value = np.nan
    elif fb <= 0 or fn <= 0:
        warnings.append("Mean flux is zero or negative in a region (too faint?); the index is undefined.")
        value = np.nan
    else:
        value = -2.5 * np.log10(fb / fn)
    if err is None:
        e = np.nan
        warnings.append("No uncertainties in this spectrum, so the index has no error bar.")
    else:
        e = 2.5 / _LN10 * np.sqrt((sb / fb) ** 2 + (sn / fn) ** 2)
    if 0 < nb < 3 or 0 < nn < 3:
        warnings.append("Fewer than 3 channels in a region -- treat this value with care.")
    spt = spectral_type or spectrum.meta.get("spectral_type")
    if spt:
        letter = str(spt).lstrip("~").strip()[:1].upper()
        if letter in [x.upper() for x in d.get("not_meaningful_for", [])]:
            warnings.append(f"Not meaningful for {spt}: {d.get('not_meaningful_reason', '')}".strip())
    return IndexResult(name, value, e, nb, nn, tuple(d["feature_um"]), tuple(d["norm_um"]), warnings)


def index_table(spectra, names=None, definitions=None):
    """All indices for several spectra, as a pandas table (one row per spectrum)."""
    import pandas as pd

    cfg = load_index_definitions() if definitions is None else definitions
    names = list(cfg["indices"]) if names is None else names
    rows = []
    for s in spectra:
        row = {"spectrum": s.name, "type": s.meta.get("spectral_type", "")}
        for n in names:
            r = compute_index(s, n, cfg)
            row[n] = r.value
            row[f"{n}_err"] = r.err
        rows.append(row)
    return pd.DataFrame(rows)


def index_difference(spec_a, spec_b, name, definitions=None):
    """Difference of one index between two spectra, and how many sigma it is.

    A spectrum without uncertainties (a model) contributes no error, so the
    difference is then measured against the other spectrum's error alone.
    """
    a = compute_index(spec_a, name, definitions)
    b = compute_index(spec_b, name, definitions)
    diff = a.value - b.value
    ea = a.err if spec_a.has_errors else 0.0
    eb = b.err if spec_b.has_errors else 0.0
    err = np.hypot(ea, eb)
    return {"index": name, spec_a.name: a.value, spec_b.name: b.value,
            "difference": diff, "err": err, "n_sigma": abs(diff) / err if err > 0 else np.nan}
