"""Build data/models/ : the curated model-spectrum subset for notebook 5.

Reads data/models/library_plan.yaml, finds each requested grid point in the
original grid files, averages it to R ~ 500 over 0.65-5.3 um, and writes one
bdtools spectrum file per model plus data/models/catalog.csv. Every file
records its grid, parameters, original file name, and source.

Students never run this. The instructor runs it once (and again whenever the
plan changes):

    python scripts/build_model_library.py               # build everything in the plan
    python scripts/build_model_library.py --check       # only report which grid points exist
    python scripts/build_model_library.py --only diamondback

The script refuses to build until library_plan.yaml says `approved: true`.

Grid readers
------------
diamondback   text .spec files: wavelength [um], F_lambda [W/m^2/m] (surface flux)
              file name t{Teff}g{g in m/s^2}{f{fsed}|nc}_m{[M/H]}_co{C/O}.spec
exorem        HDF5 inside per-temperature .tar.gz archives: flux [W/m^2/cm^-1] per
              wavenumber, wavenumber [cm^-1] in a separate wavenumber.h5
flameskimmer  netCDF4 (read with h5py): 'wavel' [micron], 'flux_emission' [erg/cm^2/s/cm]
              file name spectra_logkzz_{k}_teff_{T}_grav_{g in m/s^2}_mh_{mh}_co_{co}.nc
Unit and naming conventions were read from the local files; confirm them
against each grid's documentation before trusting the library.
"""

import argparse
import datetime as dt
import getpass
import re
import subprocess
import sys
import time
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))

from bdtools.binning import resample_to_resolution  # noqa: E402
from bdtools.io import write_spectrum  # noqa: E402
from bdtools.spectrum import Spectrum  # noqa: E402

MODEL_DIR = REPO / "data" / "models"
PLAN = MODEL_DIR / "library_plan.yaml"


# ------------------------------------------------------------------ helpers
def resolve(path_str):
    p = Path(path_str)
    return p if p.is_absolute() else (REPO / p).resolve()


def g_si_from_logg(logg):
    """log g [cgs] -> g [m/s^2]."""
    return 10 ** (logg - 2)


def model_points(plan):
    """Every (baseline, sweep, value, grid, params) the plan asks for."""
    pts = []
    pending = {fid for fid, spec in plan["baselines"].items() if spec.get("pending")}
    for fid, spec in plan["baselines"].items():
        if fid in pending:
            continue
        base = dict(spec["params"])
        pts.append((fid, "baseline", None, spec["grid"], base))
        for par, values in (spec.get("sweeps") or {}).items():
            for v in values:
                p = dict(base)
                p[par] = v
                pts.append((fid, par, v, spec["grid"], p))
    for cg in plan.get("cross_grid") or []:
        if cg["matches"] in pending:
            continue
        pts.append((cg["matches"], "cross_grid", cg["grid"], cg["grid"], dict(cg["params"])))
    return pts


def model_id(grid, p):
    keys = ["teff", "logg", "mh", "clouds", "kzz", "co"]
    return grid + "_" + "_".join(f"{k}{p[k]}" for k in keys if k in p).replace("+", "p").replace("-", "m")


def read_onedrive(path, reader, wait_seconds=2.0, retries=60):
    """Run ``reader(path)``; if the file is a OneDrive cloud-only placeholder, download it first.

    Same lifecycle as the parent project's flameskimmer_tools.onedrive: pin the file
    (attrib -U +P), wait until it is readable, read it, then return it to cloud-only
    (attrib +U -P). Files that are already local are read directly and left alone.
    """
    try:
        return reader(path)
    except OSError:
        if sys.platform != "win32":
            raise
    subprocess.run(["attrib", "-U", "+P", str(path)], check=False, shell=True)
    try:
        for _ in range(retries):
            try:
                return reader(path)
            except OSError:
                time.sleep(wait_seconds)
        raise RuntimeError(f"Could not download OneDrive file: {path}")
    finally:
        subprocess.run(["attrib", "+U", "-P", str(path)], check=False, shell=True)


# -------------------------------------------------------------- diamondback
class Diamondback:
    PATTERN = re.compile(r"t(\d+)g(\d+)(nc|f\d+)_m([+-]?\d+\.\d+)_co([\d.]+)\.spec$")

    def __init__(self, folder):
        self.folder = resolve(folder)
        self.index = {}
        for f in self.folder.glob("*.spec"):
            m = self.PATTERN.match(f.name)
            if m:
                t, g, c, mh, co = m.groups()
                self.index[(int(t), int(g), c, float(mh), float(co))] = f

    def find(self, p):
        g = int(round(g_si_from_logg(p["logg"])))
        g = min({k[1] for k in self.index} or {g}, key=lambda x: abs(x - g))   # 316 vs 316.2, 3160 vs 3162
        c = "nc" if str(p.get("clouds")) == "nc" else f"f{int(p['clouds'])}"
        return self.index.get((int(p["teff"]), g, c, float(p["mh"]), float(p.get("co", 1.0))))

    @staticmethod
    def read(path):
        d = read_onedrive(path, lambda q: np.loadtxt(q, skiprows=3))
        wave_um, flam_per_m = d[:, 0], d[:, 1]
        return wave_um, flam_per_m * 1e-6        # W/m^2/m -> W/m^2/um


# ------------------------------------------------------------------ exorem
class ExoREM:
    PATTERN = re.compile(r"spect_(\d+)K_logg([\d.]+)_met([\d.]+)_CO([\d.]+)_fsed([\d.]+)\.h5$")

    def __init__(self, folder):
        self.folder = resolve(folder)
        self.cache = MODEL_DIR / "_exorem_extracted"

    @staticmethod
    def key(p):
        met = 10 ** float(p["mh"])          # [M/H] -> x solar
        return (int(p["teff"]), float(p["logg"]), round(met, 2), round(float(p["co"]), 2), float(p["clouds"]))

    def key_from_name(self, name):
        m = self.PATTERN.search(name)
        if not m:
            return None
        t, lg, met, co, fs = m.groups()
        return (int(t), float(lg), round(float(met), 2), round(float(co), 2), float(fs))

    def extract(self, wanted_keys):
        """Stream each temperature archive once, pulling out only the wanted spectra."""
        self.cache.mkdir(parents=True, exist_ok=True)
        found = {}
        for k in wanted_keys:
            hits = [f for f in self.cache.glob("*.h5") if self.key_from_name(f.name) == k]
            if hits:
                found[k] = hits[0]
        todo = set(wanted_keys) - set(found)
        for arch in sorted(self.folder.glob("*K.tar.gz")):
            lo, hi = (int(x) for x in arch.name.split("K")[0].split("-"))
            need = {k for k in todo if lo <= k[0] < hi}
            if not need:
                continue
            print(f"  streaming {arch.name} for {len(need)} spectra (this can take a while) ...")
            with tarfile.open(arch, mode="r|gz") as tar:
                for member in tar:
                    k = self.key_from_name(member.name)
                    if k in need:
                        out = self.cache / Path(member.name).name
                        with tar.extractfile(member) as src, open(out, "wb") as dst:
                            dst.write(src.read())
                        found[k] = out
                        need.discard(k)
                        if not need:
                            break
        return found

    def read(self, path):
        import h5py

        with h5py.File(path, "r") as f:
            f_sigma = f["flux"][:]               # W/m^2/(cm^-1)
        with h5py.File(self.folder / "wavenumber.h5", "r") as k:
            sigma = k["wavenumber"][:]           # cm^-1
        wave_um = 1e4 / sigma
        flam = f_sigma * sigma**2 * 1e-4         # F_lambda = F_sigma * sigma^2 [per cm] -> per um
        o = np.argsort(wave_um)
        return wave_um[o], flam[o]


# ------------------------------------------------------------ flame skimmer
class FlameSkimmer:
    # disequilibrium-chemistry files; newer downloads end in _R<resolution> (e.g. _R30000)
    PATTERN = re.compile(r"spectra_logkzz_([\d.]+)_teff_([\d.]+)_grav_([\d.]+)_mh_([+-]?[\d.]+)_co_([\d.]+)(?:_R\d+)?\.nc$")

    def __init__(self, folder):
        self.folder = resolve(folder)
        self.index = {}
        if self.folder.exists():
            for f in self.folder.rglob("*.nc"):
                m = self.PATTERN.match(f.name)
                if m:
                    kzz, t, g, mh, co = (float(x) for x in m.groups())
                    self.index[(kzz, t, g, mh, co)] = f

    def find(self, p):
        g_want = g_si_from_logg(p["logg"])
        for (kzz, t, g, mh, co), f in self.index.items():
            if (kzz == float(p["kzz"]) and t == float(p["teff"]) and abs(np.log10(g / g_want)) < 0.02
                    and mh == float(p["mh"]) and co == float(p.get("co", 1.0))):
                return f
        return None

    @staticmethod
    def read(path):
        import h5py

        def load(q):
            with h5py.File(q, "r") as f:
                wname = "wavel" if "wavel" in f else "wavelength"   # R30000 rebinned files use 'wavelength'
                return (f[wname][:], f["flux_emission"][:], f[wname].attrs.get("units", b"micron"),
                        f["flux_emission"].attrs.get("units", b""))

        w, fl, wu, fu = read_onedrive(path, load)
        wu = wu.decode() if isinstance(wu, bytes) else str(wu)
        fu = fu.decode() if isinstance(fu, bytes) else str(fu)
        if wu != "micron" or fu != "erg/cm**2/s/cm":
            raise SystemExit(f"{path.name}: unexpected units ({wu}, {fu}); update FlameSkimmer.read")
        o = np.argsort(w)
        return w[o], fl[o] * 1e-7                # erg/cm^2/s/cm -> W/m^2/um


# --------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", default=str(PLAN))
    ap.add_argument("--check", action="store_true", help="only report which grid points exist")
    ap.add_argument("--only", choices=["diamondback", "exorem", "flameskimmer"])
    ap.add_argument("--out", default=str(MODEL_DIR))
    args = ap.parse_args()

    with open(args.plan, encoding="utf-8") as fh:
        plan = yaml.safe_load(fh)
    if not plan.get("approved") and not args.check:
        sys.exit("library_plan.yaml is not approved yet (approved: false). Review the baselines and sweeps,\n"
                 "set approved: true, then run again. Use --check to see which grid points exist.")
    out = Path(args.out)
    src = plan["sources"]
    for fid, spec in plan["baselines"].items():
        if spec.get("pending"):
            print(f"Skipping baseline {fid}: pending ({spec.get('pending_reason', 'see plan')}).")
    points = [pt for pt in model_points(plan) if not args.only or pt[3] == args.only]
    reader_classes = {"diamondback": Diamondback, "exorem": ExoREM, "flameskimmer": FlameSkimmer}
    readers = {g: reader_classes[g](src[g]["local_dir"]) for g in {pt[3] for pt in points}}

    # locate every file first, so nothing is half-built
    located, missing = [], []
    exo_keys = {ExoREM.key(p) for (_, _, _, g, p) in points if g == "exorem"}
    exo_found = {}
    if exo_keys and not args.check:
        exo_found = readers["exorem"].extract(exo_keys)
    for fid, sweep, val, grid, p in points:
        if grid == "exorem":
            f = exo_found.get(ExoREM.key(p)) if not args.check else "(inside archive; not checked)"
        else:
            f = readers[grid].find(p)
        (located if f else missing).append((fid, sweep, val, grid, p, f))
    print(f"{len(located)} of {len(points)} requested models found.")
    for m in missing:
        print(f"  MISSING  {m[3]:<12} {m[0]:<9} {m[1]:<10} {m[4]}")
    if args.check:
        return
    if missing:
        sys.exit("Stopping: fix the plan (use only grid points that exist) or supply the missing grid files.")

    lo_um, hi_um = plan["wave_range_um"]
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    rows = []
    for fid, sweep, val, grid, p, f in located:
        w, flam = readers[grid].read(f)
        c, mean = resample_to_resolution(w, flam, plan["resolution"], lo_um, hi_um)
        mid = model_id(grid, p)
        label = f"{grid} " + ", ".join(f"{k}={v}" for k, v in p.items())
        meta = {"kind": "model", "grid": grid, **{k: (str(v) if k == "clouds" else v) for k, v in p.items()},
                "baseline": fid, "sweep": sweep, "surface_flux": True,
                "grid_citation": src[grid]["citation"], "grid_url": src[grid]["url"],
                "original_file": Path(f).name, "resolution": plan["resolution"],
                "author": getpass.getuser(), "date_created": now,
                "processing_history": f"Read {Path(f).name}; converted to W/m2/um; averaged into "
                                      f"constant-R={plan['resolution']} channels over {lo_um}-{hi_um} um "
                                      "(bdtools.binning.resample_to_resolution)."}
        spec = Spectrum(c, mean, None, "W/m2/um", label, meta)
        fname = f"{mid}.csv"
        write_spectrum(spec, out / fname)
        rows.append({"id": mid, "file": fname, "grid": grid, "baseline": fid, "sweep": sweep,
                     "sweep_value": p.get(sweep, val) if sweep not in ("baseline", "cross_grid") else "",
                     **{k: p.get(k, "") for k in ["teff", "logg", "mh", "clouds", "kzz", "co"]}})
        print(f"  wrote {fname}")
    cat = pd.DataFrame(rows)
    old_catalog = out / "catalog.csv"
    if args.only and old_catalog.exists():
        # rebuilt one grid only: keep every other grid's rows (and their files) as they are
        old = pd.read_csv(old_catalog, comment="#", dtype=str)
        cat = pd.concat([old[old["grid"] != args.only], cat.astype(str)], ignore_index=True)
    cat["sweep_value"] = cat["sweep_value"].astype(str)
    with open(out / "catalog.csv", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"# Model library catalog, written by scripts/build_model_library.py on {now}.\n")
        cat.to_csv(fh, index=False)
    print(f"Done: {len(rows)} models in {out}")


if __name__ == "__main__":
    main()
