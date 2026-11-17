# Reference spectra

The objects of the SPHEREx reference sequences of Rustamkulov et al. 2026 ([arXiv:2607.00543](https://arxiv.org/abs/2607.00543)):
field sequence L0–~Y4 (Table 1), low-gravity L0 and L5 (Table 2), low-metallicity L0 and L7 (Table 3).

* `sequence_table1.csv`, `sequence_table2.csv`, `sequence_table3.csv` — Tables 1–3 (object, type, distance), transcribed
  from the instructor's copies in `../data/rustamkulov_*.txt`. Tables 2 and 3 add `base_type` (the subtype each group
  is built around) and the gravity or metallicity class.
* `substitutes.csv` — stand-ins for Table 1 objects that are not in the public SPIFF release, with the rule used to
  choose them and each one's distance and reason.
* `catalog.csv` — one row per installed spectrum; bdtools reads this. Columns:
  `id, order, sequence (field | low_gravity | low_metallicity), spectral_type, name, file, distance_pc,
  base_type, status (ok | substitute), table_name, source`. Ids: `field_<type>`, `lowg_<type>`, `lowz_<type>`.
* `field_<type>.csv` — one spectrum per file, bdtools format (units and provenance in the header).

## Where the spectra come from

Each spectrum is the SPIFF QR2-2026-04-24 binned spectrum (Gagné et al. 2026; Zenodo
[10.5281/zenodo.19051216](https://doi.org/10.5281/zenodo.19051216); units W m⁻² µm⁻¹), copied unchanged
and matched to a Table 1 object by position. Channel edges (`chan_lo_um`, `chan_hi_um`) come from SPIFF's
channel table (`pcat_spherex_bins_bandpasses_fulltable.csv`: centre ± width/2). Build with

    python scripts/build_reference_library.py [--spiff-bundle ../data/SPIFF_library_files]

which reads the SPIFF Zenodo zips directly (nothing is extracted). Installed: L0–Y2, 23 objects. Of these,
L9 (for DENIS J0255−4700) and Y1 (for WISE J1541−2250) are stand-ins, because those objects are not in the public release.
Missing: ~Y4 (WISE J0855−0714; nothing later than Y2 is in SPIFF). Tables 2 and 3 give 12 more spectra; the L0
standard 2MASS J0345+2540 (in both) and the esdL0 are stand-ins, and the usdL0 is missing (SPIFF has no ultra-subdwarfs).
After rebuilding, re-run `scripts/build_field_guide_figures.py`.

Please cite Rustamkulov et al. 2026, Gagné et al. 2026, and the SPIFF Zenodo record.
