"""Precompute every toy-model output the notebooks load (notebooks 2 and 3).

Usage:   python scripts/build_toy_library.py [--out data/toy]

Each output is an .npz file; the keys are documented in data/toy/README.md.
Nothing here is slow (a few seconds), but notebooks must only *load* these.
"""

import argparse
import datetime as dt
import getpass
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from bdtools.binning import bin_mean, log_wavelength_grid, spherex_like_channels  # noqa: E402
from bdtools.planck import brightness_temperature  # noqa: E402
import toy_atmosphere as toy  # noqa: E402

P_GRID = np.logspace(-7, 3, 500)            # bar; used for the calculation
P_STORE = np.logspace(-5, 2, 120)           # bar; stored for plotting contribution functions
TOY_R = 300


def provenance(description, **params):
    return {
        "label": "TOY MODEL - schematic, not a real brown dwarf",
        "description": description,
        "teff_toy_k": toy.TOY_TEFF,
        "parameters": params,
        "bands": [list(b) for b in toy.TOY_BANDS] + [list(toy.CIA)],
        "script_name": "scripts/build_toy_library.py (physics in scripts/toy_atmosphere.py)",
        "author": getpass.getuser(),
        "date_created": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "processing_history": "Grey-Eddington toy atmosphere, pure absorption, Gaussian bands; "
                              "flux = 2 pi int B E2 dtau; binned to approximate SPHEREx channels "
                              "(R~40 below 3.82 um, R~115 above) by mean F_lambda per channel.",
    }


def run(wave, t_kind="eddington", multipliers=None, store_cf=True):
    t = toy.temperature_profile(P_GRID, t_kind)
    r = toy.emergent_spectrum(wave, P_GRID, t, multipliers)
    out = {"flux": r["flux"], "photosphere_bar": r["photosphere_bar"]}
    if store_cf:
        lnp = np.log(P_GRID)
        cf = np.array([np.interp(np.log(P_STORE), lnp, row) for row in r["contribution"]])
        out["contribution"] = cf.astype(np.float32)
    return out, t


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(HERE.parent / "data" / "toy"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    edges = log_wavelength_grid(0.70, 5.20, TOY_R)
    wave = np.sqrt(edges[:-1] * edges[1:])
    sx_w, sx_lo, sx_hi = spherex_like_channels()

    def bin_sx(f):
        return bin_mean(wave, f, sx_lo, sx_hi)

    def save(name, arrays, meta):
        arrays = dict(arrays)
        arrays["meta_json"] = np.array(json.dumps(meta))
        np.savez_compressed(out / f"{name}.npz", **arrays)
        print(f"wrote {out / name}.npz")

    # --- single atmospheres: standard, isothermal, inversion, continuum only -------------
    cases = {
        "standard": ("eddington", None, "Temperature falls with height (Eddington-like profile); all toy absorbers."),
        "isothermal": ("isothermal", None, "Same absorbers, but every layer has the same temperature."),
        "inversion": ("inversion", None, "Temperature rises again above ~30 mbar (a thermal inversion)."),
        "continuum_only": ("eddington", {a: 0.0 for a in toy.ABSORBERS}, "Standard profile with every band removed."),
    }
    for name, (kind, mult, desc) in cases.items():
        r, t = run(wave, kind, mult)
        sx = bin_sx(r["flux"])
        save(name, {
            "wave_um": wave, "flux": r["flux"], "brightness_temp_k": brightness_temperature(wave, r["flux"]),
            "photosphere_bar": r["photosphere_bar"], "contribution": r["contribution"],
            "pressure_bar": P_STORE, "temperature_k": np.interp(np.log(P_STORE), np.log(P_GRID), t),
            "spherex_wave_um": sx_w, "spherex_lo_um": sx_lo, "spherex_hi_um": sx_hi, "spherex_flux": sx,
        }, provenance(desc, temperature_profile=kind, multipliers=mult or {}))

    # --- CH4 abundance sweep (saturation) -----------------------------------------------
    mults = np.array([0.0, 0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000.0])
    fluxes, photos = [], []
    for m in mults:
        r, _ = run(wave, "eddington", {"CH4": m}, store_cf=False)
        fluxes.append(r["flux"])
        photos.append(r["photosphere_bar"])
    fluxes = np.array(fluxes)
    save("ch4_sweep", {
        "wave_um": wave, "multipliers": mults, "flux": fluxes, "photosphere_bar": np.array(photos),
        "brightness_temp_k": brightness_temperature(wave, fluxes),
        "spherex_wave_um": sx_w, "spherex_flux": np.array([bin_sx(f) for f in fluxes]),
    }, provenance("Standard profile with the toy CH4 bands multiplied by each value in 'multipliers'.",
                  swept="CH4 multiplier"))

    # --- remove one absorber at a time --------------------------------------------------
    labels = ["all"] + [f"no {a}" for a in toy.ABSORBERS]
    fl = []
    for lab in labels:
        mult = None if lab == "all" else {lab[3:]: 0.0}
        r, _ = run(wave, "eddington", mult, store_cf=False)
        fl.append(r["flux"])
    fl = np.array(fl)
    # ... and each absorber on its own (continuum + that absorber), with "none" = continuum only
    alone_labels = ["none"] + [f"only {a}" for a in toy.ABSORBERS]
    al = []
    for lab in alone_labels:
        keep = None if lab == "none" else lab[5:]
        r, _ = run(wave, "eddington", {a: 0.0 for a in toy.ABSORBERS if a != keep}, store_cf=False)
        al.append(r["flux"])
    al = np.array(al)
    save("remove_one", {
        "wave_um": wave, "labels": np.array(labels), "flux": fl,
        "spherex_wave_um": sx_w, "spherex_flux": np.array([bin_sx(f) for f in fl]),
        "alone_labels": np.array(alone_labels), "alone_flux": al,
        "alone_spherex_flux": np.array([bin_sx(f) for f in al]),
    }, provenance("Standard profile with all toy absorbers, then with each one removed in turn "
                  "('labels', 'flux'); and the continuum alone plus each absorber on its own "
                  "('alone_labels', 'alone_flux').", absorbers=toy.ABSORBERS))

    # --- temperature change vs absorber change ------------------------------------------
    rows, labs = [], []
    for lab, teff, mult in [("toy, T_eff = 1000 K", 1000.0, None),
                            ("toy, T_eff = 900 K", 900.0, None),
                            ("toy, T_eff = 1000 K, CH4 x 3", 1000.0, {"CH4": 3.0})]:
        t = toy.temperature_profile(P_GRID, "eddington", teff=teff)
        rows.append(toy.emergent_spectrum(wave, P_GRID, t, mult)["flux"])
        labs.append(lab)
    rows = np.array(rows)
    save("temp_vs_absorber", {
        "wave_um": wave, "labels": np.array(labs), "flux": rows,
        "spherex_wave_um": sx_w, "spherex_flux": np.array([bin_sx(f) for f in rows]),
    }, provenance("A cooler atmosphere versus more CH4 absorption, to contrast global and local changes."))


if __name__ == "__main__":
    main()
