"""Fitting a spectrum with a whole grid of models (notebook 6).

``fit_models(data)`` compares the data with every model in a grid, using the
same conventions as ``bdtools.compare`` (Rustamkulov et al. 2026, Sec. 4):

* each model is averaged onto the data's own channels;
* each model gets one free scale factor (for a model this is (radius / distance)^2);
* a 3% systematic is added in quadrature to the data uncertainties;
* models are ranked by reduced chi-squared; G_k (Cushing et al. 2008) is also listed.

The grid is a single file built by ``scripts/build_fit_grid.py``.
"""

import json
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .binning import bin_mean
from .compare import DEFAULT_SYSTEMATIC, _in_windows, channel_weights, compare, total_error
from .errors import BDToolsError, MissingDataError
from .paths import MODEL_DIR
from .spectrum import Spectrum

GRID_FILES = {"diamondback": "fit_grid_diamondback.npz"}
PARAMETERS = ["teff", "logg", "mh", "clouds"]
PARAM_LABELS = {"teff": "T$_{eff}$ [K]", "logg": "log g [cgs]", "mh": "[M/H]", "clouds": "clouds (f$_{sed}$)"}
_GRID_CACHE = {}


@dataclass
class ModelGrid:
    """A grid of model spectra on one wavelength grid (surface F_lambda, W m^-2 um^-1)."""

    name: str
    wave_um: np.ndarray
    lo_um: np.ndarray
    hi_um: np.ndarray
    flux: np.ndarray              # (n_model, n_wave)
    params: pd.DataFrame          # one row per model: teff, logg, mh, clouds
    meta: dict

    def __len__(self):
        return len(self.params)

    def __repr__(self):
        p = self.params
        parts = [f"{len(self)} {self.name} models"]
        for k in PARAMETERS:
            vals = sorted(p[k].unique(), key=_sort_key)
            parts.append(f"{k}: {', '.join(str(v) for v in vals)}")
        return "\n".join(parts)

    def spectrum(self, i):
        """Model number ``i`` as a Spectrum (surface flux, W m^-2 um^-1)."""
        row = self.params.iloc[i]
        label = f"{self.name} " + ", ".join(f"{k}={row[k]}" for k in PARAMETERS)
        meta = dict(kind="model", grid=self.name, **{k: row[k] for k in PARAMETERS},
                    grid_citation=self.meta.get("grid_citation", ""), surface_flux=True)
        return Spectrum(self.wave_um.copy(), self.flux[i].astype(float), None, "W/m2/um", label, meta,
                        self.lo_um.copy(), self.hi_um.copy())

    def find(self, **params):
        """Index of the model with exactly these parameters, e.g. ``find(teff=1600, logg=5.0, mh=0.0, clouds="2")``."""
        mask = np.ones(len(self), bool)
        for k, v in params.items():
            mask &= _matches(self.params[k], v)
        idx = np.flatnonzero(mask)
        if idx.size != 1:
            raise BDToolsError(f"{idx.size} models match {params}; give all of {', '.join(PARAMETERS)}.")
        return int(idx[0])

    def binned_to(self, data):
        """Every model averaged onto ``data``'s channels, in ``data``'s flux unit. Shape (n_model, n_channel)."""
        lo, hi = data.channel_edges()
        # bin_mean is linear in the flux, so build the (channel x wavelength) averaging matrix once
        eye = np.eye(self.wave_um.size)
        mat = np.stack([bin_mean(self.wave_um, eye[j], lo, hi) for j in range(self.wave_um.size)], axis=1)
        binned = self.flux.astype(float) @ mat.T
        to_unit = Spectrum(data.wave_um.copy(), np.ones(data.wave_um.size), None, "W/m2/um").to_unit(data.flux_unit)
        return binned * to_unit.flux[None, :]


def _sort_key(v):
    try:
        return (0, float(v))
    except (TypeError, ValueError):
        return (1, str(v))


def _norm_label(v):
    """'2', 2, 2.0 -> '2';  'nc' -> 'nc'."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return str(int(f)) if f.is_integer() else str(f)


def _matches(column, value):
    if column.dtype == object:
        return column.map(_norm_label) == _norm_label(value)
    return pd.Series(np.isclose(column.astype(float), float(value)), index=column.index)


def load_grid(name="diamondback"):
    """Load a model grid for fitting (built by scripts/build_fit_grid.py)."""
    if name not in GRID_FILES:
        raise BDToolsError(f"Unknown grid '{name}'. Available: {', '.join(GRID_FILES)}.")
    if name in _GRID_CACHE:
        return _GRID_CACHE[name]
    path = MODEL_DIR / GRID_FILES[name]
    if not path.exists():
        raise MissingDataError(
            f"The {name} fitting grid is not installed yet ({path.name}). "
            "Your instructor builds it with scripts/build_fit_grid.py."
        )
    with np.load(path, allow_pickle=False) as z:
        params = pd.DataFrame({"teff": z["teff"], "logg": z["logg"], "mh": z["mh"],
                               "clouds": z["clouds"].astype(str).astype(object)})
        grid = ModelGrid(name, z["wave_um"], z["lo_um"], z["hi_um"], z["flux"], params,
                         json.loads(str(z["meta_json"])))
    _GRID_CACHE[name] = grid
    return grid


@dataclass
class FitResult:
    """Everything ``fit_models`` works out.

    ``table``: one row per model tried, best first (columns: the parameters,
    ``scale``, ``chi2_red``, ``G_k``, ``model`` = row number in the grid).
    """

    data: Spectrum
    grid: ModelGrid
    table: pd.DataFrame
    windows: object
    systematic: float
    notes: list = field(default_factory=list)

    @property
    def best(self):
        """The best model's parameters, scale, and statistics (a pandas row)."""
        return self.table.iloc[0]

    def model(self, rank=0):
        """The model at ``rank`` (0 = best) as a Spectrum, unscaled and not yet binned."""
        return self.grid.spectrum(int(self.table.iloc[rank]["model"]))

    def comparison(self, rank=0):
        """A ``Comparison`` of the data with the model at ``rank`` (plot it with ``plot_comparison``)."""
        return compare(self.data, self.model(rank), windows=self.windows, systematic=self.systematic)

    def summary(self, n=5):
        b = self.best
        lines = [f"data: {self.data.name}",
                 f"grid: {self.grid.name} ({len(self.table)} models tried, {self.systematic:.0%} systematic"
                 + ("" if self.windows is None else f", scale fit in {self.windows}") + ")",
                 "best fit: " + ", ".join(f"{k} = {b[k]}" for k in PARAMETERS)
                 + f"   reduced chi^2 = {b['chi2_red']:.1f}"]
        lines += [f"note: {x}" for x in self.notes]
        return "\n".join(lines)

    def __repr__(self):
        return self.summary()


def fit_models(data, grid="diamondback", windows=None, systematic=DEFAULT_SYSTEMATIC, **fixed):
    """Fit ``data`` with every model in a grid; return a ``FitResult`` (best first).

    Parameters
    ----------
    data : a Spectrum with uncertainties
    grid : grid name or a ``ModelGrid``
    windows : wavelength ranges (microns) used to fit each scale factor; None = all channels
    systematic : fractional error added in quadrature (0.03 = 3%)
    **fixed : hold parameters fixed, e.g. ``mh=0.0`` or ``clouds="nc"``

    The statistics for each model are exactly those of ``bd.compare(data, model)``.
    """
    data.require_errors()
    g = load_grid(grid) if isinstance(grid, str) else grid
    keep = np.ones(len(g), bool)
    for k, v in fixed.items():
        if k not in PARAMETERS:
            raise BDToolsError(f"Unknown parameter '{k}'. Choose from: {', '.join(PARAMETERS)}.")
        keep &= _matches(g.params[k], v).to_numpy()
    if not keep.any():
        raise BDToolsError(f"No models with {fixed}. The grid has:\n{g}")
    d = data.clean()
    models = g.binned_to(d)[keep]                          # (n, n_chan)
    sigma = total_error(d, systematic)
    weights = channel_weights(d)
    covered = np.all(np.isfinite(models), axis=0)
    use = _in_windows(d.wave_um, windows) & covered
    if use.sum() == 0:
        raise BDToolsError("No channels to fit: check `windows` and the grid's wavelength range.")
    iv = 1.0 / sigma**2
    scale = (models[:, use] * d.flux[use] * iv[use]).sum(1) / (models[:, use] ** 2 * iv[use]).sum(1)
    signif = (d.flux[covered][None, :] - scale[:, None] * models[:, covered]) / sigma[covered][None, :]
    n = int(covered.sum())
    chi2_red = (signif**2).sum(1) / max(n - 1, 1)
    gk = (weights[covered][None, :] * signif**2).sum(1)
    table = g.params[keep].copy()
    table["scale"] = scale
    table["chi2_red"] = chi2_red
    table["G_k"] = gk
    table["model"] = np.flatnonzero(keep)
    table = table.sort_values("chi2_red").reset_index(drop=True)
    notes = []
    if (~covered).any():
        notes.append(f"{(~covered).sum()} channel(s) outside the grid's wavelength range were skipped.")
    return FitResult(data, g, table, windows, systematic, notes)


def fits_table(fits):
    """One row per fit: the data's spectral type and name, then the best-fit parameters and statistics."""
    rows = []
    for f in fits:
        b = f.best
        rows.append({"spectral_type": f.data.meta.get("spectral_type", ""), "data": f.data.name,
                     **{k: b[k] for k in PARAMETERS}, "scale": b["scale"], "chi2_red": b["chi2_red"],
                     "G_k": b["G_k"]})
    return pd.DataFrame(rows)
