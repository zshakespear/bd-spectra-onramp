# Reading a model fit

[← Field guide](README.md) · Explained in [notebook 6](../notebooks/06_fitting_models.ipynb)

**How the fit is made** (Rustamkulov et al. 2026, Sec. 4)
1. Every model in the grid is averaged onto the data's own SPHEREx channels.
2. Each model gets one free scale factor.
3. A 3% systematic is added in quadrature to the data uncertainties.
4. Models are ranked by reduced χ² (G<sub>k</sub>, which weights channels by width, is listed too).

**Reading it**

| Look at | Ask |
|---|---|
| χ²<sub>red</sub> of the best fit | Usually ≫ 1 (≥ 10 for high-S/N spectra). The models are imperfect; best-fit parameters are rough. |
| the top ~10 models | Do very different parameter sets give almost the same χ²<sub>red</sub>? Then those parameters are not pinned down. |
| χ² map (`bd.plot_chi2_map`) | Bright yellow = low χ² (good). Small bright spot = constrained. Long bright valley = two parameters trade off (degeneracy). |
| ratio panel | Where is the data brighter / fainter than the model? Inside which absorber band? The look depends on the scaling. |
| significance panel | Points beyond ±3σ. Clusters inside a band = a feature; isolated single points = check for a [data problem](data_problems.md). |

**Is it the object or the models?** Fit the **template** (the reference spectrum of the object's type) with the same grid
and compare residuals (`bd.plot_fit_residuals`).
- Residual shared with the template → a **model problem**.
- Residual only your object shows → worth explaining: temperature, gravity, metallicity, clouds, mixing, binarity,
  or a data problem ([global parameters](parameters/README.md)).

**Code**
```python
fit = bd.fit_models(data)                  # whole Diamondback grid; fixed parameters: fit_models(data, mh=0.0)
print(fit.summary()); fit.table.head(10)
bd.plot_comparison(fit.comparison(), panel="both")
bd.plot_chi2_map(fit, "teff", "logg")
```
