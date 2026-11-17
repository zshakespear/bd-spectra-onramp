"""Build data/models/fit_grid_diamondback.npz : the full model grid students fit with (notebook 6).

Every local Sonora Diamondback spectrum (Morley et al. 2024) is read, converted to
surface F_lambda [W m^-2 um^-1], and averaged into constant-R channels (default
R = 300, which still has several points per SPHEREx channel; SPHEREx has R ~ 40-130).
bdtools.fitting then averages the grid onto each spectrum's own channels before fitting.

Output arrays
-------------
wave_um   (n_wave,)            channel centres
lo_um, hi_um (n_wave,)         channel edges
flux      (n_model, n_wave)    float32, surface F_lambda [W m^-2 um^-1]
teff, logg, mh (n_model,)      float
clouds    (n_model,)           str: "1", "2", "3", "4", "8" (f_sed) or "nc" (cloud-free)
source_file (n_model,)         original file name
meta_json                      provenance (author, date_created, processing_history, citation)

Usage
-----
  python scripts/build_fit_grid.py [--resolution 300] [--limit N]
"""

import argparse
import datetime as dt
import getpass
import json
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))

from bdtools.binning import log_wavelength_grid, resample_to_resolution  # noqa: E402
from build_model_library import PLAN, Diamondback  # noqa: E402

OUT = REPO / "data" / "models" / "fit_grid_diamondback.npz"
WMIN_UM, WMAX_UM = 0.65, 5.3


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--resolution", type=float, default=300.0)
    ap.add_argument("--limit", type=int, help="only the first N files (for testing)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    with open(PLAN, encoding="utf-8") as fh:
        src = yaml.safe_load(fh)["sources"]["diamondback"]
    reader = Diamondback(src["local_dir"])
    keys = sorted(reader.index)                      # (teff, g_si, clouds, mh, co)
    keys = [k for k in keys if k[4] == 1.0]          # solar C/O only (the whole local grid)
    if args.limit:
        keys = keys[: args.limit]
    if not keys:
        sys.exit(f"No Diamondback spectra found in {reader.folder}")

    edges = log_wavelength_grid(WMIN_UM, WMAX_UM, args.resolution)
    flux = np.empty((len(keys), len(edges) - 1), np.float32)
    teff, logg, mh, clouds, files = [], [], [], [], []
    for i, k in enumerate(keys):
        t, g_si, c, m, _ = k
        f = reader.index[k]
        w, flam = Diamondback.read(f)
        centres, mean = resample_to_resolution(w, flam, args.resolution, WMIN_UM, WMAX_UM)
        flux[i] = mean
        teff.append(float(t))
        logg.append(round(np.log10(g_si) + 2, 1))   # g [m/s^2] -> log g [cgs]
        mh.append(float(m))
        clouds.append("nc" if c == "nc" else c[1:])
        files.append(f.name)
        if (i + 1) % 100 == 0 or i + 1 == len(keys):
            print(f"  {i + 1}/{len(keys)}", flush=True)

    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    meta = {
        "label": "Sonora Diamondback fitting grid",
        "grid": "diamondback",
        "grid_citation": src["citation"],
        "grid_url": src["url"],
        "flux_unit": "W/m2/um",
        "surface_flux": True,
        "resolution": args.resolution,
        "n_models": len(keys),
        "author": getpass.getuser(),
        "date_created": now,
        "processing_history": (
            f"Read every Diamondback .spec file (C/O = 1.0 x solar) from {src['local_dir']}; converted "
            f"W/m2/m -> W/m2/um; averaged into constant-R={args.resolution:g} channels over "
            f"{WMIN_UM}-{WMAX_UM} um (bdtools.binning.resample_to_resolution); stored as float32. "
            "Built by scripts/build_fit_grid.py."
        ),
    }
    out = Path(args.out)
    np.savez_compressed(
        out, wave_um=centres, lo_um=edges[:-1], hi_um=edges[1:], flux=flux,
        teff=np.array(teff), logg=np.array(logg), mh=np.array(mh),
        clouds=np.array(clouds), source_file=np.array(files), meta_json=json.dumps(meta),
    )
    print(f"Wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {len(keys)} models)")


if __name__ == "__main__":
    main()
