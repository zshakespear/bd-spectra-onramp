# Global atmospheric parameters

[← Field guide](../README.md) · Explained in [notebook 5](../../notebooks/05_global_parameters.ipynb)

| Parameter | Page | One-line effect |
|---|---|---|
| T<sub>eff</sub> | [teff.md](teff.md) | global: slope + many bands at once |
| log g | [gravity.md](gravity.md) | H<sub>2</sub> CIA (1.7–3 µm), K vs H, water depth |
| [M/H] | [metallicity.md](metallicity.md) | all molecular bands vs H<sub>2</sub> CIA; J/K ratio |
| clouds (f<sub>sed</sub>) | [clouds.md](clouds.md) | dim, redden, and smooth the windows |
| mixing (K<sub>zz</sub>) | [mixing.md](mixing.md) | CO/CO<sub>2</sub> vs CH<sub>4</sub> in cold atmospheres |

**Before you trust any best-fit parameter:** even the best-matching model rarely reproduces a real spectrum within
its uncertainties (notebook 6), and different grids with the same parameters differ by up to ~2× at some wavelengths
(Rustamkulov et al. 2026). Treat parameters as rough.

**Degeneracies:** when two parameter changes alter the spectrum in nearly the same way, the data cannot tell them
apart (e.g. cooler vs higher gravity in some bands). Look for the bands where they differ. Unresolved **binarity** can mimic a parameter change too.
