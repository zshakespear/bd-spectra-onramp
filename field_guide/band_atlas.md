# Band atlas (0.75–5 µm, SPHEREx resolution)

[← Field guide](README.md) · Explained in [notebook 3](../notebooks/03_band_atlas.ipynb)

Same ranges and colours as the plots (both come from `data/bands.yaml`). Ranges are approximate at R ~ 40.
**Status:** *spec* = stated in Rustamkulov et al. 2026 Sec. 3; *checked* = range from Cushing et al. 2005's band
table; *uncertain* = listed by Cushing et al. 2005, but SPHEREx may not separate it (hidden from plots by default).

| Absorber | Bands (µm) | Prominent in | Overlaps | Status |
|---|---|---|---|---|
| 🟦 **H<sub>2</sub>O** | 0.89–0.99, 1.09–1.20, 1.30–1.51, 1.75–2.05, 2.3–3.2 | L, T, Y — everywhere | CH<sub>4</sub> at 1.15 and on the long side of 2.7 µm; CO 2.3 µm; H<sub>2</sub> CIA | checked |
| 🟧 **CH<sub>4</sub>** | 3.0–3.6 | after L4 (first as a curve at 3–3.6 µm) | H<sub>2</sub>O 2.7 µm wing | spec (Cushing: 3.0–3.8) |
| | 1.10–1.24 (narrow feature at 1.15 µm) | T4 and later | H<sub>2</sub>O | checked |
| | 1.60–1.80, 2.15–2.50 | T, Y | H<sub>2</sub> CIA, CO 2.3 µm | checked |
| 🟥 **CO** | 4.4–4.9 | beyond L3; drops sharply T6→T7 | CO<sub>2</sub> wing; small 4.67 µm peak from L4 | spec |
| | 2.29–2.45 (band heads from 2.29 µm) | L, early T | CH<sub>4</sub>, H<sub>2</sub>O, H<sub>2</sub> CIA | checked |
| 🟩 **CO<sub>2</sub>** | 4.15–4.3 | beyond L3; drops sharply T6→T7 | CO on its long side | spec |
| ▦ **H<sub>2</sub> CIA** (grey cross-hatching on plots) | 1.7–3.0, broad; changes the spectrum mostly at the K (and H) peak | all; strongest at high gravity and low metallicity | H<sub>2</sub>O, CH<sub>4</sub>, CO | spec (Cushing: 1.8–2.8) |
| FeH | 0.98–1.01, 1.19–1.24, 1.58–1.63 (band heads) | L, early T | H<sub>2</sub>O; CH<sub>4</sub> | uncertain |
| VO | 1.05–1.08 | early L | Y peak | uncertain |
| NH<sub>3</sub> | ~3.0 | late T, Y | H<sub>2</sub>O, CH<sub>4</sub> | **don't look for it**: unlikely to be detectable with SPHEREx |

**Three traps**
1. **Overlap** — a deeper trough doesn't say *which* absorber changed. Check every row that covers the region.
2. **Wings reach the windows** — a window peak's height depends on its neighbouring bands.
   Overlapping bands share the light: where one absorber already blocks it, another can't take it out again
   (why broad H<sub>2</sub> CIA shows up mainly in the windows).
3. **Saturation** — strong bands (e.g. CH<sub>4</sub> 3.3 µm in cold dwarfs) barely respond to more absorber; depth grows ~ log(amount).
