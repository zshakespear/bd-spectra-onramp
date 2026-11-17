"""Reading and writing spectra, and finding them in the library.

File format (one format for every spectrum in ``data/``)
--------------------------------------------------------
A CSV file whose first lines are ``# key: value`` comments, then a header row::

    # bdtools spectrum v1
    # name: L5 standard
    # kind: reference            (reference | model)
    # flux_unit: W/m2/um         (W/m2/um | Jy | mJy)
    # wave_unit: um
    # ...any other provenance: source, citation, grid, teff, ...
    wave_um,flux,flux_err,chan_lo_um,chan_hi_um

``flux_err``, ``chan_lo_um`` and ``chan_hi_um`` are optional. Missing values
are written as ``nan``. The toy-model outputs for notebook 2 are ``.npz``
files instead (see ``data/toy/README.md``), because they hold 2-D arrays.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .errors import BDToolsError, MissingDataError, UnitError
from .paths import MODEL_DIR, REFERENCE_DIR, TOY_DIR
from .spectrum import Spectrum

FORMAT_TAG = "bdtools spectrum v1"


# ----------------------------------------------------------------- generic
def read_spectrum(path):
    """Read one spectrum file written in the bdtools format."""
    path = Path(path)
    if not path.exists():
        raise MissingDataError(f"Spectrum file not found: {path}")
    meta = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.startswith("#"):
                break
            body = line[1:].strip()
            if ":" in body:
                key, val = body.split(":", 1)
                try:
                    meta[key.strip()] = yaml.safe_load(val.strip())
                except yaml.YAMLError:
                    meta[key.strip()] = val.strip()
    table = pd.read_csv(path, comment="#")
    if "wave_um" not in table or "flux" not in table:
        raise BDToolsError(f"{path.name} needs columns 'wave_um' and 'flux' (found: {', '.join(table.columns)}).")
    if meta.get("wave_unit", "um") not in ("um", "micron", "microns"):
        raise UnitError(f"{path.name}: wavelengths must be in microns (file says '{meta.get('wave_unit')}').")
    if "flux_unit" not in meta:
        raise UnitError(f"{path.name} does not say what unit its flux is in (no '# flux_unit:' line).")
    err = table["flux_err"].to_numpy(float) if "flux_err" in table else None
    lo = table["chan_lo_um"].to_numpy(float) if "chan_lo_um" in table else None
    hi = table["chan_hi_um"].to_numpy(float) if "chan_hi_um" in table else None
    meta["file"] = str(path)
    return Spectrum(table["wave_um"].to_numpy(float), table["flux"].to_numpy(float), err,
                    meta["flux_unit"], str(meta.get("name", path.stem)), meta, lo, hi)


def write_spectrum(spectrum, path, **extra_meta):
    """Write a Spectrum in the bdtools format (used by the build scripts)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {k: v for k, v in spectrum.meta.items() if k != "file"}
    meta.update(extra_meta)
    meta["name"] = spectrum.name
    meta["flux_unit"] = spectrum.flux_unit
    meta["wave_unit"] = "um"
    cols = {"wave_um": spectrum.wave_um, "flux": spectrum.flux}
    if spectrum.err is not None:
        cols["flux_err"] = spectrum.err
    if spectrum.chan_lo_um is not None:
        cols["chan_lo_um"] = spectrum.chan_lo_um
        cols["chan_hi_um"] = spectrum.chan_hi_um
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"# {FORMAT_TAG}\n")
        for k, v in meta.items():
            fh.write(f"# {k}: {json.dumps(v) if not isinstance(v, str) else _quote(v)}\n")
        pd.DataFrame(cols).to_csv(fh, index=False, float_format="%.7g", na_rep="nan")
    return path


def _quote(s):
    s = s.replace("\n", " ")
    return json.dumps(s) if (":" in s or s.strip() != s or s[:1] in "[{\"'&*!|>%@`#") else s


# -------------------------------------------------------------- references
def _catalog(directory, what, how_to_build):
    path = Path(directory) / "catalog.csv"
    if not path.exists():
        raise MissingDataError(
            f"The {what} library has not been built yet ({path} is missing). "
            f"Ask your instructor -- they need to run {how_to_build}."
        )
    return pd.read_csv(path, comment="#", dtype={"spectral_type": str})


def list_references():
    """Table of the reference spectra available in ``data/references``."""
    return _catalog(REFERENCE_DIR, "reference spectrum", "scripts/build_reference_library.py")


def references_available():
    """True if at least one reference spectrum is installed."""
    try:
        return len(list_references()) > 0
    except MissingDataError:
        return False


def load_reference(which, sequence="field"):
    """Load a reference spectrum by spectral type (e.g. ``"T4"``) or by its id.

    ``sequence`` is "field" (the L0-Y4 spectral sequence), "low_gravity", or
    "low_metallicity".
    """
    cat = list_references()
    key = str(which).strip()
    rows = cat[cat["id"].astype(str) == key]
    if rows.empty:
        rows = cat[(cat["spectral_type"].astype(str).str.upper() == key.upper()) & (cat["sequence"] == sequence)]
    if rows.empty:
        have = ", ".join(cat.loc[cat["sequence"] == sequence, "spectral_type"].astype(str))
        raise MissingDataError(f"No {sequence} reference spectrum for '{which}'. Available: {have or 'none'}.")
    row = rows.iloc[0]
    s = read_spectrum(REFERENCE_DIR / row["file"])
    for col in ("spectral_type", "sequence", "status"):
        if col in row and pd.notna(row[col]):
            s.meta[col] = row[col]
    return s


def load_sequence(types=None, sequence="field"):
    """Load several reference spectra, in spectral-type order. Missing types are skipped."""
    cat = list_references()
    cat = cat[cat["sequence"] == sequence]
    if types is None:
        types = list(cat.sort_values("order")["spectral_type"]) if "order" in cat else list(cat["spectral_type"])
    out = []
    for t in types:
        try:
            out.append(load_reference(t, sequence))
        except MissingDataError:
            pass
    return out


# ------------------------------------------------------------------ models
def list_models(**filters):
    """Table of the model spectra in ``data/models``.

    Keyword filters select rows, e.g. ``list_models(grid="diamondback", fiducial="L")``.
    """
    cat = _catalog(MODEL_DIR, "model", "scripts/build_model_library.py")
    for k, v in filters.items():
        if k not in cat:
            raise BDToolsError(f"Model catalog has no column '{k}'. Columns: {', '.join(cat.columns)}.")
        cat = cat[cat[k] == v]
    return cat.reset_index(drop=True)


def models_available():
    try:
        return len(list_models()) > 0
    except MissingDataError:
        return False


def load_model(model_id):
    """Load one model spectrum by its id (first column of ``list_models()``)."""
    cat = list_models()
    rows = cat[cat["id"] == model_id]
    if rows.empty:
        raise MissingDataError(f"No model with id '{model_id}'.")
    return read_spectrum(MODEL_DIR / rows.iloc[0]["file"])


def load_sweep(fiducial, parameter):
    """Models in which only ``parameter`` changes around a fiducial model.

    Returns ``(fiducial_spectrum, [spectra sorted by the parameter])``.
    ``parameter`` is one of: "teff", "logg", "mh", "clouds", "kzz".
    """
    cat = list_models(fiducial=fiducial)
    if cat.empty:
        raise MissingDataError(f"No models for fiducial '{fiducial}'.")
    fid_rows = cat[cat["sweep"] == "fiducial"]
    if fid_rows.empty:
        raise MissingDataError(f"The fiducial model for '{fiducial}' is missing from the library.")
    sweep = cat[cat["sweep"] == parameter]
    if sweep.empty:
        raise MissingDataError(f"No '{parameter}' sweep was built for fiducial '{fiducial}'.")
    fid = read_spectrum(MODEL_DIR / fid_rows.iloc[0]["file"])
    members = [read_spectrum(MODEL_DIR / f) for f in sweep["file"]] + [fid]

    def sort_key(s):
        v = s.meta.get(parameter)
        try:
            return (0, float(v))
        except (TypeError, ValueError):
            return (1, 0.0)          # e.g. clouds = "nc" (cloud-free) goes last

    return fid, sorted(members, key=sort_key)


# -------------------------------------------------------------------- toy
class ToyResult(dict):
    """Precomputed toy-model output. Keys are also attributes: ``toy.wave_um``."""

    __getattr__ = dict.__getitem__

    def __repr__(self):
        return f"ToyResult('{self.get('name')}', keys: {', '.join(k for k in self if k != 'meta')})"


def list_toys():
    if not TOY_DIR.exists():
        return []
    return sorted(p.stem for p in TOY_DIR.glob("*.npz"))


def load_toy(name):
    """Load a precomputed toy-model run (notebook 2/3). See ``list_toys()``."""
    path = TOY_DIR / f"{name}.npz"
    if not path.exists():
        raise MissingDataError(
            f"Toy-model output '{name}' not found. Available: {', '.join(list_toys()) or 'none'}. "
            "The instructor builds these with scripts/build_toy_library.py."
        )
    with np.load(path, allow_pickle=False) as z:
        out = ToyResult({k: z[k] for k in z.files if k != "meta_json"})
        out["meta"] = json.loads(str(z["meta_json"])) if "meta_json" in z.files else {}
    out["name"] = name
    return out
