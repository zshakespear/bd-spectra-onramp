# Toy-model outputs (notebooks 2 and 3)

> **TOY MODEL.** Band positions roughly follow real absorbers; band shapes and strengths are made up.
> For ideas only — never for quantitative claims about real objects.

Built by `scripts/build_toy_library.py` (physics in `scripts/toy_atmosphere.py`). Load with
`bd.load_toy(name)`. Every file has `meta_json` (label, description, parameters, band list, author,
date, processing history).

| File | Contents |
|---|---|
| `standard.npz`, `isothermal.npz`, `inversion.npz`, `continuum_only.npz` | `wave_um` (R = 300), `flux` (surface F<sub>λ</sub>, W m⁻² µm⁻¹), `brightness_temp_k`, `photosphere_bar` (τ = 2/3 pressure per wavelength), `contribution` (n_wave × n_pressure, dF/d ln P), `pressure_bar`, `temperature_k`, and `spherex_*` (binned to approximate SPHEREx channels) |
| `ch4_sweep.npz` | `multipliers` (CH<sub>4</sub> × 0 … 1000), `flux`, `brightness_temp_k`, `photosphere_bar` (one row per multiplier), `spherex_wave_um`, `spherex_flux` |
| `remove_one.npz` | `labels` ("all", "no H2O", …), `flux`, `spherex_flux` |
| `temp_vs_absorber.npz` | `labels`, `flux`, `spherex_flux`: 1000 K, 900 K, and 1000 K with CH<sub>4</sub> × 3 |
