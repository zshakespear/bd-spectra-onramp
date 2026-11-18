# Model library

Curated, resampled subset of model grids, built by `scripts/build_model_library.py` from
`library_plan.yaml` (approved 2026-11-16). Built: the L and early-T baselines with their sweeps (Diamondback) and
the Exo-REM cross-grid models. The late-T/Y baseline (Flame Skimmer, added 2026-11-17) has T<sub>eff</sub> 500–550 K only,
because only that range has been downloaded. To widen it, edit the `teff` sweep and run
`build_model_library.py --only flameskimmer`; `--only` replaces that grid's rows and keeps the others.

* Each model: one bdtools CSV (F<sub>λ</sub> surface flux, W m⁻² µm⁻¹, averaged into constant R = 500
  channels over 0.65–5.3 µm), header records grid, parameters, original file, citation, and processing.
* `catalog.csv`: `id, file, grid, baseline, sweep (baseline | teff | logg | mh | clouds | kzz | cross_grid),
  sweep_value, teff, logg, mh, clouds, kzz, co`.
* Notebooks average these to SPHEREx resolution (or to a spectrum's own channels) before plotting or comparing.

`_exorem_extracted/` (if present) caches HDF5 files pulled from the Exo-REM archives; it is git-ignored.

Grid facts used by the readers were read from the local files and must be confirmed against each grid's
paper / Zenodo record — see the main README, "Questions for the instructor".
