# Spectral indices

[← Field guide](README.md) · Explained in [notebook 6 §7](../notebooks/06_fitting_models.ipynb)

From Rustamkulov et al. 2026, Table 5 and Eqs. 3–4. Definitions live in `data/indices.yaml`
(instructor-editable). **Use only these indices; don't invent new ones.**

  **I = −2.5 log<sub>10</sub>(F<sub>band</sub> / F<sub>norm</sub>)**, mean fluxes; bigger = deeper band.
  σ<sub>I</sub> = (2.5 / ln 10) √[(σ<sub>F</sub>/F<sub>band</sub>)² + (σ<sub>norm</sub>/F<sub>norm</sub>)²]

| Index | Feature (µm) | Normalization (µm) | Measures | Watch out for |
|---|---|---|---|---|
| CH<sub>4</sub> | 3.20–3.65 | 3.70–4.14 | 3.3 µm CH<sub>4</sub> band | other absorbers overlap; **not meaningful for Y dwarfs** (CH<sub>4</sub> undetected at SPHEREx sensitivity) |
| CO<sub>2</sub> | 4.18–4.35 | 3.70–4.14 | 4.3 µm CO<sub>2</sub> band | neighbouring band wings; drops sharply T6→T7 |
| CO | 4.55–4.80 | 3.70–4.14 | 4.6 µm CO band | small 4.67 µm peak from L4; drops sharply T6→T7 |

**Remember**
- The 3.70–4.14 µm window is only the *nearest thing* to a continuum; its flux depends on its neighbours.
- One molecule can move another molecule's index if its band overlaps a feature or normalization region.
  Check the windows on the actual spectra (`bd.plot_index_windows`).
- Indices are ratios within one spectrum, so they **don't depend on how a template was scaled** — unlike ratio plots.
- Compare two indices only with their uncertainties (`bd.index_difference` gives the difference in σ).
- Notebook 6 also plots **index planes** — one index against another (`bd.plot_index_plane(seq, x="CH4", y="CO")`).
  The CH<sub>4</sub> axis only becomes informative in the T dwarfs.
