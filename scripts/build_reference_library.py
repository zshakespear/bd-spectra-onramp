"""Build data/references/ : the reference spectra students compare against.

The reference set is the SPHEREx spectral sequence of Rustamkulov et al. 2026
(Table 1: field L0-~Y4; Table 2: low gravity at L0, L5; Table 3: low metallicity at L0, L7),
transcribed in data/references/sequence_table{1,2,3}.csv.

The spectra themselves are the SPIFF binned spectra (Gagne et al. 2026, Zenodo
10.5281/zenodo.19051216, release QR2-2026-04-24), one value per SPHEREx channel,
read straight from the Zenodo bundle's zip files (nothing is extracted):

* spiff_tables.zip
    spherex_autotype_datasets_fulltable.csv  designation, position, sample of every object
    pcat_spherex_bins_bandpasses_fulltable.csv  centre and width of the 102 binned channels
* spiff_<sample>_binned_csv.zip  one CSV per object (wavelength_um, flux_flambda_w_m2_um, flux_error)

Table objects are matched to SPIFF objects by position. Objects that are not in
the bundle are replaced by the stand-in listed in data/references/substitutes.csv
(which records how each was chosen); objects with no stand-in are listed at the end.

Usage
-----
  python scripts/build_reference_library.py [--spiff-bundle ../data/SPIFF_library_files]
"""

import argparse
import datetime as dt
import getpass
import io
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))

from bdtools.io import write_spectrum  # noqa: E402
from bdtools.spectrum import Spectrum  # noqa: E402

REF_DIR = REPO / "data" / "references"
DEFAULT_BUNDLE = REPO.parent / "data" / "SPIFF_library_files"
MATCH_RADIUS_ARCSEC = 30.0   # generous: catalogue epochs differ and these objects move fast
SPIFF_RELEASE = "SPIFF QR2-2026-04-24 (Gagne et al. 2026, Zenodo 10.5281/zenodo.19051216)"
TABLES_ZIP = "spiff_tables.zip"
OBJECTS_TABLE = "spiff_tables/spherex_autotype_datasets_fulltable.csv"
BANDPASS_TABLE = "spiff_tables/pcat_spherex_bins_bandpasses_fulltable.csv"
SAMPLE_ZIPS = {  # dataset name in the objects table -> binned-spectra zip
    "Known": "spiff_known_bds_binned_csv.zip",
    "Known Candidates": "spiff_photo_known_bds_binned_csv.zip",
    "New Discoveries": "spiff_new_bds_binned_csv.zip",
    "New Candidates": "spiff_new_candidate_bds_binned_csv.zip",
}


# ----------------------------------------------------------------- coordinates
def designation_to_deg(name):
    """RA, Dec in degrees from a designation such as 'J15074769-1627386' or 'PSO J319.3102-29.6682'."""
    m = re.search(r"J(\d{3}\.\d+)([+-]\d+\.\d+)", name)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = re.search(r"J(\d{4,6}\.?\d*)([+-])(\d{4,6}\.?\d*)", name)
    if not m:
        raise ValueError(f"cannot parse coordinates from '{name}'")
    r, sign, d = m.group(1).replace(".", ""), m.group(2), m.group(3).replace(".", "")

    def sexa(s):  # 'hhmmss[s...]' -> (h, m, s.sss)
        sec = s[4:6] + ("." + s[6:] if len(s) > 6 else "") if len(s) > 4 else "0"
        return int(s[:2]), int(s[2:4]), float(sec)

    hh, mm, ss = sexa(r)
    dd, dm, ds = sexa(d)
    ra = 15 * (hh + mm / 60 + ss / 3600)
    dec = dd + dm / 60 + ds / 3600
    return ra, dec if sign == "+" else -dec


def sexagesimal_to_deg(ra, dec):
    h, m, s = (float(x) for x in ra.split(":"))
    sign = -1 if dec.strip().startswith("-") else 1
    d, dm, ds = (abs(float(x)) for x in dec.split(":"))
    return 15 * (h + m / 60 + s / 3600), sign * (d + dm / 60 + ds / 3600)


def separation_arcsec(ra1, dec1, ra2, dec2):
    r1, d1, r2, d2 = (np.radians(np.asarray(x, float)) for x in (ra1, dec1, ra2, dec2))
    c = np.sin(d1) * np.sin(d2) + np.cos(d1) * np.cos(d2) * np.cos(r1 - r2)
    return np.degrees(np.arccos(np.clip(c, -1, 1))) * 3600


# ---------------------------------------------------------------- SPIFF bundle
def _stem_key(s):
    """Designations lose spaces and '+' in SPIFF file names ('SDSS J0802+33' -> 'SDSS_J080233')."""
    return re.sub(r"[\s_+]", "", str(s))


class SpiffBundle:
    """Read-only access to the SPIFF Zenodo bundle (zips are opened, never extracted)."""

    def __init__(self, folder):
        self.folder = Path(folder)
        with zipfile.ZipFile(self.folder / TABLES_ZIP) as zt:
            self.objects = pd.read_csv(io.BytesIO(zt.read(OBJECTS_TABLE)))
            bp = pd.read_csv(io.BytesIO(zt.read(BANDPASS_TABLE)))
        self.centre = bp["wavelength_center_um"].to_numpy(float)
        self.width = bp["wavelength_width_um"].to_numpy(float)
        coords = np.array([sexagesimal_to_deg(r, d) for r, d in
                           zip(self.objects["ra_j2000"], self.objects["dec_j2000"])])
        self.objects["ra_deg"], self.objects["dec_deg"] = coords[:, 0], coords[:, 1]
        self.files = {}   # stem key -> (zip name, member)
        for zname in SAMPLE_ZIPS.values():
            with zipfile.ZipFile(self.folder / zname) as zf:
                for member in zf.namelist():
                    if member.endswith(".csv"):
                        stem = member.rsplit("/", 1)[-1].split("_moca_oid_")[0]
                        self.files[_stem_key(stem)] = (zname, member)

    def nearest(self, ra, dec):
        sep = separation_arcsec(ra, dec, self.objects["ra_deg"], self.objects["dec_deg"])
        i = int(np.argmin(sep))
        return self.objects.iloc[i], float(sep[i])

    def by_designation(self, designation):
        rows = self.objects[self.objects["designation"] == designation]
        if rows.empty:
            raise KeyError(f"'{designation}' is not in the SPIFF objects table")
        return rows.iloc[0]

    def read_binned(self, designation):
        """The binned spectrum, with channel edges from the SPIFF bandpass table."""
        zname, member = self.files[_stem_key(designation)]
        with zipfile.ZipFile(self.folder / zname) as zf:
            data = pd.read_csv(io.BytesIO(zf.read(member)))
        wave = data["wavelength_um"].to_numpy(float)
        k = np.abs(wave[:, None] - self.centre[None, :]).argmin(axis=1)
        off = np.abs(wave - self.centre[k])
        if off.max() > 1.5e-3:
            raise ValueError(f"{member}: wavelengths do not match the SPIFF channel table (max offset {off.max():.4f} um)")
        lo, hi = self.centre[k] - self.width[k] / 2, self.centre[k] + self.width[k] / 2
        return data, lo, hi, f"{zname}:{member}"


# ---------------------------------------------------------------------- build
SEQUENCES = [  # (sequence, table file, table label in the paper, id prefix)
    ("field", "sequence_table1.csv", "Table 1", "field"),
    ("low_gravity", "sequence_table2.csv", "Table 2", "lowg"),
    ("low_metallicity", "sequence_table3.csv", "Table 3", "lowz"),
]


def _label(spectral_type):
    """Display label: 'L0gamma' -> 'L0γ'."""
    return spectral_type.replace("gamma", "γ").replace("beta", "β")


def _num(x):
    return None if pd.isna(x) else float(x)


def build(bundle_dir):
    spiff = SpiffBundle(bundle_dir)
    subs = pd.read_csv(REF_DIR / "substitutes.csv", comment="#").set_index(["sequence", "slot"])
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    for _, _, _, prefix in SEQUENCES:
        for old in REF_DIR.glob(f"{prefix}_*.csv"):
            old.unlink()
    rows, missing = [], []
    for seqname, table_file, table_label, prefix in SEQUENCES:
        table = pd.read_csv(REF_DIR / table_file, comment="#")
        print(f"{seqname} ({table_label}):")
        for _, obj in table.iterrows():
            slot = obj["spectral_type"]
            base = obj.get("base_type", slot)
            match, sep = spiff.nearest(*designation_to_deg(obj["name"]))
            if sep <= MATCH_RADIUS_ARCSEC:
                used, status, sub = obj["name"], "ok", None
                dist, dist_err = _num(obj["distance_pc"]), _num(obj["distance_err_pc"])
            elif (seqname, slot) in subs.index:
                sub = subs.loc[(seqname, slot)]
                match, sep = spiff.by_designation(sub["spiff_designation"]), float("nan")
                used, status = sub["spiff_designation"], "substitute"
                dist, dist_err = _num(sub["distance_pc"]), _num(sub["distance_err_pc"])
            else:
                missing.append(f"{seqname} {slot} {obj['name']}")
                continue
            data, lo, hi, source_file = spiff.read_binned(match["designation"])
            meta = {
                "kind": "reference", "status": status, "sequence": seqname,
                "spectral_type": slot, "base_type": base, "object": used,
                "distance_pc": dist, "distance_err_pc": dist_err,
                "sequence_source": f"Rustamkulov et al. 2026, {table_label} (object choice, type, distance)",
                "spectrum_source": f"SPIFF binned spectrum, {SPIFF_RELEASE}",
                "spiff_designation": match["designation"], "spiff_sample": match["dataset"],
                "spiff_autotype": str(match["spiff_autotype"]),
                "literature_spectral_type": str(match["literature_spectral_type"]),
                "spiff_file": source_file,
                "channel_edges": "SPIFF pcat_spherex_bins_bandpasses table (centre +- width/2)",
                "author": getpass.getuser(), "date_created": now,
                "processing_history": "Copied SPIFF binned spectrum unchanged (no cleaning, no rescaling); "
                                      "units W/m2/um; channel edges added from the SPIFF bandpass table.",
            }
            if sub is None:
                meta["match_sep_arcsec"] = round(sep, 2)
            else:
                meta.update({"substitute_for": obj["name"], "substitute_reason": sub["reason"],
                             "distance_ref": None if pd.isna(sub["distance_ref"]) else sub["distance_ref"],
                             "processing_history": meta["processing_history"]
                             + f" Stand-in for the {table_label} object (see data/references/substitutes.csv)."})
            spec = Spectrum(data["wavelength_um"].to_numpy(float), data["flux_flambda_w_m2_um"].to_numpy(float),
                            data["flux_error"].to_numpy(float), "W/m2/um", f"{_label(slot)} {used}", meta, lo, hi)
            sid = f"{prefix}_{slot}"
            write_spectrum(spec, REF_DIR / f"{sid}.csv")
            rows.append({"id": sid, "order": obj["order"], "sequence": seqname, "spectral_type": slot,
                         "base_type": base, "name": used, "file": f"{sid}.csv", "distance_pc": dist,
                         "status": status, "table_name": obj["name"], "source": "SPIFF QR2 (Gagne et al. 2026)"})
            how = f'({sep:.1f}")' if sub is None else f"(stand-in for {obj['name']})"
            print(f"  {slot:>8}  {used:<28} <- {match['designation']}  {how}")
    with open(REF_DIR / "catalog.csv", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# Reference spectrum catalog, written by scripts/build_reference_library.py on "
                 f"{now}.\n# Objects: Rustamkulov et al. 2026 Tables 1-3 (status 'substitute': stand-in, see "
                 "substitutes.csv). Spectra: SPIFF QR2 binned (Gagne et al. 2026).\n")
        pd.DataFrame(rows).to_csv(fh, index=False)
    print(f"\nWrote {len(rows)} reference spectra to {REF_DIR}")
    if missing:
        print("Not in SPIFF and no stand-in in substitutes.csv:")
        for x in missing:
            print("   ", x)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spiff-bundle", type=Path, default=DEFAULT_BUNDLE,
                    help="Folder holding the SPIFF Zenodo zips (default: %(default)s)")
    build(ap.parse_args().spiff_bundle)


if __name__ == "__main__":
    main()
