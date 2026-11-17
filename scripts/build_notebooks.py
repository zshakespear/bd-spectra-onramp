"""Generate notebooks/00-06 from the text in this file.

Keeping the notebooks in one script means the setup cell, the Colab badge,
and the house style are identical everywhere. Edit here, then run:

    python scripts/build_notebooks.py            # write notebooks/*.ipynb (no outputs)
    python scripts/build_notebooks.py --execute  # also run them top to bottom (checks they work)

Set GITHUB_OWNER / REPO_NAME below (or pass --owner) before publishing.
"""

import argparse
import sys
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

GITHUB_OWNER = "zshakespear"
REPO_NAME = "bd-spectra-onramp"
BRANCH = "main"

REPO = Path(__file__).resolve().parent.parent
NB_DIR = REPO / "notebooks"


def md(text):
    return new_markdown_cell(text.strip("\n"))


def code(text):
    return new_code_cell(text.strip("\n"))


def answer(text, label="Answer"):
    return f"\n<details><summary><b>{label}</b> (try first, then click)</summary>\n\n{text.strip()}\n\n</details>\n"


def header(owner, fname, title, goals, minutes):
    badge = (f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]"
             f"(https://colab.research.google.com/github/{owner}/{REPO_NAME}/blob/{BRANCH}/notebooks/{fname})")
    g = "\n".join(f"- {x}" for x in goals)
    return md(f"""
{badge}

# {title}

*Brown Dwarf Spectra On-Ramp · about {minutes} minutes*

**By the end of this notebook you will be able to:**
{g}

> **First time here?** Do *File → Save a copy in Drive* before you change anything (notebook 0 explains why).
> Then run the **Setup** cell below. Run cells in order, top to bottom, with **Shift + Enter**.
""")


def setup_cell(owner):
    return code(f'''
# ▶ SETUP - run this cell first. It is safe to run more than once.
REPO_URL = "https://github.com/{owner}/{REPO_NAME}.git"
import os, subprocess, sys
from pathlib import Path

if "google.colab" in sys.modules:                       # running in Google Colab
    ROOT = Path("/content/{REPO_NAME}")
    if not (ROOT / "bdtools").exists():
        subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(ROOT)], check=True)
    else:
        subprocess.run(["git", "-C", str(ROOT), "pull", "--ff-only", "--quiet"], check=False)
else:                                                   # running in Jupyter on your own computer
    ROOT = Path.cwd()
    while not (ROOT / "bdtools").exists() and ROOT != ROOT.parent:
        ROOT = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import matplotlib.pyplot as plt
import bdtools as bd
bd.setup_notebook()
''')


def footer(summary, questions, next_nb):
    s = "\n".join(f"- {x}" for x in summary)
    q = "\n".join(f"{i + 1}. {x[0]}" + answer(x[1]) for i, x in enumerate(questions))
    return [md(f"""
## Summary

{s}

**Field guide:** the pages linked above are the short versions to keep open while you work.
"""), md(f"""
## Self-check

Answer these without scrolling up. If one is hard, revisit that section.

{q}
"""), md(f"**Next:** {next_nb}")]


# =============================================================== notebook 0
def nb00(owner):
    f = "00_getting_started.ipynb"
    cells = [
        header(owner, f, "0 · Getting started", [
            "run cells in Google Colab and save your own copy in Google Drive",
            "restart a notebook and get back to where you were",
            "say what a spectrum file holds, and what F<sub>λ</sub>, F<sub>ν</sub>, and µm mean",
            "read a spectrum plot on linear and logarithmic axes",
        ], 20),
        md("""
## 1. Working in Colab

Colab runs Python on a Google computer. That computer is **temporary**: when you close the tab
or stay idle for a while, it is wiped. Two consequences:

1. **Save your own copy before editing.** *File → Save a copy in Drive.* A tab opens titled
   "Copy of …" — work in *that* tab. Your edits and answers are saved in your Google Drive
   (folder *Colab Notebooks*). If you skip this, your changes disappear.
2. **Every time you come back, run the Setup cell again.** The notebook text is saved, but
   the variables and downloaded files are not.

| To… | Do this |
|---|---|
| run one cell | click it, press **Shift + Enter** |
| run everything from the top | *Runtime → Run all* |
| start fresh after things get confusing | *Runtime → Restart session*, then Run all |
| see help on a function | run `help(bd.plot_spectrum)` or `bd.plot_spectrum?` |

> If a cell shows ⚠️ and a short message, read the message — it says what to fix.
> ⏳ means some data has not been supplied by your instructor yet; just keep going.
"""),
        setup_cell(owner),
        md("""
If the last line says `bdtools … ready`, you are set up. `bd` is the small helper library
for this course; `np` is numpy (numbers) and `plt` is matplotlib (plots).

## 2. What a spectrum file holds

A **spectrum** is a list of brightness measurements at different wavelengths. Our
reference spectra come from **SPHEREx**, a NASA space telescope that measures every
part of the sky at 102 wavelengths ("channels") between 0.75 and 5 µm
(1 µm = 1 micron = 10<sup>−6</sup> m; visible light is 0.4–0.7 µm, so all of this is infrared).
"""),
        code("""
# ✏️ SETTINGS YOU CAN CHANGE
SPECTRAL_TYPE = "L5"     # which reference spectrum to look at
"""),
        code("""
spec = bd.load_reference(SPECTRAL_TYPE)
print(spec)
spec.meta     # everything else we know about it
"""),
        md("""
Each spectrum has three columns: wavelength, flux, and the flux **uncertainty** (the 1σ error bar).
Let's look at the first few rows as a table:
"""),
        code("""
import pandas as pd
pd.DataFrame({"wavelength (um)": spec.wave_um, "flux": spec.flux, "uncertainty": spec.err}).head(8)
"""),
        md("""
### Units

* **F<sub>λ</sub>** ("F-lambda"): energy per second, per square metre of telescope, *per micron
  of wavelength*. Unit: W m<sup>−2</sup> µm<sup>−1</sup>. Our files use this.
* **F<sub>ν</sub>** ("F-nu"): the same, but *per hertz of frequency*. Astronomers often quote it
  in **janskys** (1 Jy = 10<sup>−26</sup> W m<sup>−2</sup> Hz<sup>−1</sup>). The SPHEREx papers use Jy.

They describe the same light, but the shapes of the curves differ, because a micron of
wavelength covers more hertz at short wavelengths than at long ones. bdtools converts for you:
"""),
        code("""
spec_jy = spec.to_fnu_jy()
print(spec_jy)
print("flux at the first channel:", spec.flux[0], "W/m2/um  =", spec_jy.flux[0], "Jy")
"""),
        md("""
## 3. Reading a spectrum plot

The coloured bars above the plot show where different molecules absorb light (more on these
in notebook 3). The shaded band around the line is the ±1σ uncertainty.
"""),
        code("""
fig, ax = bd.plot_spectrum(spec, title=f"{spec.name}  (linear flux axis)")
"""),
        md("""
**Predict, then run.** On a *logarithmic* flux axis, equal steps up the axis mean equal
*factors* of brightness (×10, ×100), not equal amounts. Before running the next cell:
will the faint parts of the spectrum (beyond 3 µm) look more or less important?
"""),
        code("""
fig, ax = bd.plot_spectrum(spec, log=True, title=f"{spec.name}  (log flux axis)")
"""),
        md("""
On the linear plot the long-wavelength part looks almost flat and empty. On the log plot you
can see its shape: dips and bumps that are invisible on a linear axis. **We will use both
axes all the time.** Linear shows where most of the light is; log shows the structure in faint regions.

Same spectrum in F<sub>ν</sub>:
"""),
        code("""
fig, ax = bd.plot_spectrum(spec, unit="Jy", log=True, title=f"{spec.name} in F_nu (Jy)")
"""),
        md("""
### Exercise 0.1
Using the linear-axis plot, at roughly what wavelength is this object brightest in F<sub>λ</sub>?
Now look at the F<sub>ν</sub> plot. Is the brightest wavelength the same?
""" + answer("""
In F<sub>λ</sub> the L5 spectrum peaks near 1.2–1.3 µm (the "J peak"). In F<sub>ν</sub> the peak
moves to longer wavelength, because F<sub>ν</sub> = F<sub>λ</sub> λ²/c weights long wavelengths up.
"Where is it brightest?" therefore depends on the unit — always say which one you mean.
""")),
        md("""
### Exercise 0.2
Change `SPECTRAL_TYPE` in the settings cell to `"L0"`, then re-run the cells below it.
How does the L0 spectrum differ from the L5 on the log plot?
""" + answer("""
The L0 is bluer: relatively more light at short wavelengths and a steeper drop toward 5 µm,
because it is hotter. You will see the whole sequence in notebook 4.
""")),
    ]
    cells += footer(
        ["Colab is temporary: save a copy to Drive, and re-run Setup each time you return.",
         "A spectrum = wavelengths, fluxes, and uncertainties, with units attached.",
         "F<sub>λ</sub> (W m⁻² µm⁻¹) and F<sub>ν</sub> (Jy) describe the same light but peak in different places.",
         "Linear axes show where the light is; log axes show structure in faint regions."],
        [("Why must you save a copy to Drive before editing?",
          "Colab's computer is wiped when the session ends; only a copy saved in your Drive keeps your work."),
         ("What do you need to do every time you reopen a notebook?", "Run the Setup cell (and then the cells you need) again."),
         ("What is the difference between F<sub>λ</sub> and F<sub>ν</sub>?",
          "Flux per unit wavelength versus per unit frequency. Same light, different shape; F<sub>ν</sub> = F<sub>λ</sub> λ²/c."),
         ("When is a log flux axis more useful than a linear one?",
          "When the flux covers a big range, so faint regions (like 3–5 µm here) would look flat on a linear axis.")],
        "[Notebook 1 · Blackbodies and brightness temperature](01_blackbodies.ipynb)")
    return f, cells


# =============================================================== notebook 1
def nb01(owner):
    f = "01_blackbodies.ipynb"
    cells = [
        header(owner, f, "1 · Blackbodies and brightness temperature", [
            "plot Planck curves for 250–2500 K and use Wien's law to find their peaks",
            "explain why flux on the short-wavelength side of the peak is so sensitive to temperature",
            "convert an observed spectrum to surface flux using a distance and an assumed radius",
            "turn a spectrum into a brightness-temperature spectrum and say what it means",
        ], 35),
        setup_cell(owner),
        md("""
## 1. Planck curves

A **blackbody** absorbs all light that hits it and glows with a spectrum set *only* by its
temperature — the Planck function B<sub>λ</sub>(T). Brown dwarfs are not blackbodies (that is the
whole point of the later notebooks), but blackbodies are the yardstick we measure them against.
Brown dwarfs span roughly 2500 K (early L) down to 250 K (the coldest Y dwarfs)
(Rustamkulov et al. 2026, Table 1).
"""),
        code("""
# ✏️ SETTINGS YOU CAN CHANGE
TEMPERATURES = [2500, 1800, 1300, 900, 600, 400, 250]    # kelvin
"""),
        code("""
wave = np.linspace(0.5, 15, 2000)          # microns
fig, ax = plt.subplots()
colors = plt.cm.inferno(np.linspace(0.1, 0.85, len(TEMPERATURES)))
for T, c in zip(TEMPERATURES, colors):
    ax.plot(wave, bd.blackbody_surface_flux(wave, T), color=c, label=f"{T} K")
    ax.axvline(bd.wien_peak_um(T), color=c, ls=":", lw=1)
ax.axvspan(0.75, 5.0, color="0.85", zorder=0, label="SPHEREx range")
ax.set_yscale("log"); ax.set_ylim(1e-2, 1e7)
ax.set_xlabel("Wavelength [µm]"); ax.set_ylabel(r"Surface flux $\\pi B_\\lambda$ [W m$^{-2}$ µm$^{-1}$]")
ax.legend(); ax.set_title("Blackbodies (dotted lines: Wien peaks)");
"""),
        md("""
**Wien's law**: the peak of B<sub>λ</sub> is at λ<sub>max</sub> = 2898 µm·K / T.
"""),
        code("""
for T in TEMPERATURES:
    peak = bd.wien_peak_um(T)
    where = "inside" if 0.75 <= peak <= 5.0 else ("longward of" if peak > 5 else "shortward of")
    print(f"T = {T:5d} K   peak at {peak:5.2f} um   ({where} the SPHEREx range)")
"""),
        md("""
Notice: for L dwarfs (≈1300–2500 K) the peak sits *inside* the SPHEREx range. For Y dwarfs and the
very coldest T dwarfs (below about 580 K) the peak is beyond 5 µm, so **everything SPHEREx sees is on
the short-wavelength side of the peak** — the steep side. That matters a lot, as the next section shows.

## 2. Why a small temperature change makes a huge flux change

**Predict, then run.** Take two blackbodies, 1000 K and 1100 K (10% hotter). At 1.25 µm, how
many times brighter is the hotter one? At 4.5 µm? Write your guesses down first.
"""),
        code("""
for lam in [1.25, 2.2, 4.5]:
    ratio = bd.planck_lambda(lam, 1100) / bd.planck_lambda(lam, 1000)
    print(f"at {lam:4.2f} um: 1100 K is {ratio:4.2f} times brighter than 1000 K")
"""),
        md("""
On the short-wavelength side of the peak, B<sub>λ</sub> falls off *exponentially*
(∝ e<sup>−hc/λkT</sup>), so a modest temperature contrast becomes an **enormous flux contrast**.
At long wavelengths the dependence is gentler. This is why:

* we plot spectra on **log** axes, and
* we often convert flux into **brightness temperature**, which turns those huge flux ratios back
  into modest, comparable temperature differences.

## 3. From observed flux to surface flux

The flux we measure is diluted by distance. Light leaving a sphere of radius R spreads over a
sphere of radius d by the time it reaches us, so

  F<sub>observed</sub> = F<sub>surface</sub> × (R / d)².

Distances come from parallaxes (stored with each reference spectrum). Radii are **not measured**;
brown dwarfs are all about the size of Jupiter (≈0.8–1.3 R<sub>Jup</sub>), so we *assume* one.
"""),
        code("""
# ✏️ SETTINGS YOU CAN CHANGE
SPECTRAL_TYPE = "L5"
RADIUS_RJUP = 1.0          # assumed radius, in Jupiter radii
"""),
        code("""
spec = bd.load_reference(SPECTRAL_TYPE)
d = spec.meta["distance_pc"]
surface = bd.observed_to_surface(spec.flux, distance_pc=d, radius_rjup=RADIUS_RJUP)
print(f"{spec.name}: distance {d} pc; surface flux is {surface[0] / spec.flux[0]:.3g} times the observed flux")
"""),
        md("""
## 4. Brightness temperature

The **brightness temperature** T<sub>b</sub>(λ) is the temperature a blackbody would need to emit the
same surface flux *at that wavelength*. For a real blackbody T<sub>b</sub> is the same at every λ.
For a brown dwarf it is not — and the way it varies tells us about the atmosphere.
"""),
        code("""
tb = bd.brightness_temperature(spec.wave_um, surface)
fig, axes = plt.subplots(2, 1, sharex=True, figsize=(9, 7))
axes[0].plot(spec.wave_um, spec.flux, "o-", ms=3, color="k"); axes[0].set_yscale("log")
axes[0].set_ylabel(r"observed $F_\\lambda$ [W m$^{-2}$ µm$^{-1}$]")
axes[1].plot(spec.wave_um, tb, "o-", ms=3, color=bd.LINE_COLORS[1])
axes[1].set_ylabel("brightness temperature [K]"); axes[1].set_xlabel("Wavelength [µm]")
axes[0].set_title(f"{spec.name}, assuming R = {RADIUS_RJUP} R_Jup");
"""),
        md("""
Read the bottom panel like a map of *depth*. Where T<sub>b</sub> is **high**, we see light from deep, hot
layers (these are the "windows"). Where T<sub>b</sub> is **low**, something absorbs the deep light and we
only see cooler, higher layers. Notebook 2 explains why.

**A caution that worked well in past versions of this course:** comparing fluxes at different
wavelengths and saying "brighter here, so hotter here" can mislead, because the Planck function
itself depends on wavelength. The flux peak of a blackbody is not where it is "hottest". Brightness
temperature fixes this: it is the one quantity you can compare fairly across wavelengths.
"""),
        md("""
### Exercise 1.1
At about what wavelength is T<sub>b</sub> highest for this spectrum, and roughly what is it? Where is it lowest?
""" + answer("""
For the L5 the highest T<sub>b</sub> is in the near-infrared windows (around the J peak, 1.2–1.3 µm)
and the lowest in the absorption troughs (e.g. near 1.4 µm, 1.9 µm, 2.7 µm) and at long
wavelengths. Exact numbers depend on the assumed radius — see the next exercise.
""")),
        md("""
### Exercise 1.2
Set `RADIUS_RJUP = 0.8`, then 1.2, and re-run. Does the *shape* of the T<sub>b</sub> curve change, or only its level?
Which wavelengths change most in kelvin?
""" + answer("""
Only the level shifts — the pattern of high and low T<sub>b</sub> stays the same. Because surface flux
∝ 1/R², a smaller radius means more surface flux and a higher T<sub>b</sub>. The shift in kelvin is larger at
long wavelengths, where B<sub>λ</sub> depends less steeply on T, so a given flux change needs a bigger
temperature change. This is why we treat absolute T<sub>b</sub> values as rough but trust the pattern.
""")),
        md("""
### Exercise 1.3
Use `bd.brightness_temperature` to find the T<sub>b</sub> a blackbody at 1500 K has at 1 µm and at 4 µm.
(Hint: first compute its surface flux with `bd.blackbody_surface_flux`.)
""" + answer("""
```python
for lam in [1.0, 4.0]:
    print(lam, bd.brightness_temperature(lam, bd.blackbody_surface_flux(lam, 1500)))
```
Both are 1500 K — for a true blackbody T<sub>b</sub> is the same at every wavelength. Any variation of
T<sub>b</sub> with wavelength in a real spectrum is information about the atmosphere.
""")),
    ]
    cells += footer(
        ["Wien's law: λ<sub>max</sub> = 2898 µm K / T. L dwarfs peak inside 0.75–5 µm; Y dwarfs peak beyond it.",
         "Short of the peak, flux depends exponentially on temperature: small ΔT, huge flux ratio.",
         "Surface flux = observed flux × (d/R)²; R is assumed (~1 R<sub>Jup</sub>).",
         "Brightness temperature lets you compare wavelengths fairly; high T<sub>b</sub> = seeing deep, low T<sub>b</sub> = seeing high."],
        [("Why is SPHEREx's whole range on the steep side of the Planck curve for a Y dwarf?",
          "Its temperature is below ~580 K, so the Wien peak is beyond 5 µm."),
         ("A 10% hotter blackbody is about how many times brighter at 1.25 µm? At 4.5 µm?",
          "About 2.8× at 1.25 µm and about 1.3× at 4.5 µm."),
         ("What two numbers do you need to turn observed flux into surface flux, and which is assumed?",
          "Distance (measured from parallax) and radius (assumed, ~1 R<sub>Jup</sub>)."),
         ("What does a low brightness temperature at some wavelength tell you?",
          "Light at that wavelength comes from higher, cooler layers — deep light is being absorbed.")],
        "[Notebook 2 · Opacity and the photosphere](02_opacity_photosphere.ipynb)")
    return f, cells


# =============================================================== notebook 2
def nb02(owner):
    f = "02_opacity_photosphere.ipynb"
    toy = "> 🧸 **TOY MODEL.** The atmosphere in this notebook is a deliberately simple toy. Its bands sit at roughly the right wavelengths so the plots look familiar, but their shapes and strengths are made up. Use it for *ideas*, never for numbers about real objects."
    cells = [
        header(owner, f, "2 · Opacity and the photosphere", [
            "describe a brown dwarf atmosphere as a temperature–pressure profile with no surface",
            "explain optical depth, the τ ≈ 2/3 photosphere, and the Eddington–Barbier idea",
            "read a contribution function",
            "predict the spectrum of an isothermal atmosphere and of one with a thermal inversion",
            "explain why an absorption band stops deepening (saturates)",
        ], 45),
        setup_cell(owner),
        md(f"""
## 1. No surface, just layers

A brown dwarf is a ball of gas — mostly hydrogen and helium — with **no solid surface**. Going down,
the pressure and temperature rise smoothly. We describe the atmosphere by its **temperature–pressure
(T–P) profile**. Pressure is the natural "height" coordinate: low pressure = high up.

{toy}
"""),
        code("""
std, iso, inv = bd.load_toy("standard"), bd.load_toy("isothermal"), bd.load_toy("inversion")
print(std.meta["label"]); print(std.meta["description"])
fig, ax = plt.subplots(figsize=(5, 6))
for t, c in [(std, bd.LINE_COLORS[0]), (iso, bd.LINE_COLORS[1]), (inv, bd.LINE_COLORS[2])]:
    ax.plot(t.temperature_k, t.pressure_bar, color=c, label=t.name)
ax.set_yscale("log"); ax.invert_yaxis()
ax.set_xlabel("Temperature [K]"); ax.set_ylabel("Pressure [bar]  (up = higher)")
ax.legend(); ax.set_title("TOY temperature-pressure profiles", fontsize=10);
"""),
        md("""
## 2. Optical depth and the photosphere

Light trying to escape from deep down gets absorbed on the way out. The **optical depth** τ counts how
many "absorption lengths" lie between a layer and space: light from a layer at depth τ escapes with
probability about e<sup>−τ</sup>. So:

* layers with τ ≫ 1 are hidden;
* layers with τ ≪ 1 emit too little to matter (too little gas);
* most escaping light comes from around **τ ≈ 2/3** — call that the **photosphere**.

Crucially, τ depends on wavelength. At a wavelength where a molecule absorbs strongly, τ = 2/3 is
reached *high up*; in a "window" with little absorption, we see *deep*.

**Eddington–Barbier idea:** the emerging flux at each wavelength is roughly the blackbody flux of the
temperature at that wavelength's τ = 2/3 level:
  F<sub>λ</sub> ≈ π B<sub>λ</sub>( T(τ<sub>λ</sub> = 2/3) ).
"""),
        code("""
fig, ax = plt.subplots()
ax.plot(std.wave_um, std.photosphere_bar, color="k")
ax.set_yscale("log"); ax.invert_yaxis()
ax.set_xlabel("Wavelength [µm]"); ax.set_ylabel("pressure where τ = 2/3 [bar]")
ax.set_title("TOY: where each wavelength's light comes from", fontsize=10);
"""),
        md("""
### Contribution functions
The τ = 2/3 level is a shorthand. The **contribution function** shows *how much* light at each
wavelength comes from each layer (dark = most). The cyan line is the τ = 2/3 level.
"""),
        code("""
fig, ax = bd.plot_contribution_function(std)
"""),
        md("""
### Test the Eddington–Barbier idea
Look up the temperature at each wavelength's photosphere and compare it with the toy spectrum's
brightness temperature.
"""),
        code("""
t_at_photosphere = np.interp(np.log(std.photosphere_bar), np.log(std.pressure_bar), std.temperature_k)
fig, ax = plt.subplots()
ax.plot(std.wave_um, std.brightness_temp_k, label="brightness temperature of the toy spectrum")
ax.plot(std.wave_um, t_at_photosphere, "--", label="temperature at the τ = 2/3 level")
ax.set_xlabel("Wavelength [µm]"); ax.set_ylabel("K"); ax.legend()
ax.set_title("TOY: Eddington-Barbier check", fontsize=10);
"""),
        md("""
Over most of the spectrum the two curves track each other closely: **brightness temperature ≈ temperature of
the layer you see.** That is the bridge between notebook 1 and the rest of the course.

Where they disagree — the short-wavelength windows, below about 2 µm — the spectrum is *hotter* than the τ = 2/3
layer. Notebook 1 explains why: on the steep side of the Planck curve, slightly deeper (hotter) layers are so much
brighter that they contribute more than their share, so the light comes from a bit below τ = 2/3. You can see this
in the contribution function above: in those windows the dark band sits below the cyan line. Eddington–Barbier is
a rule of thumb, not an exact law.

## 3. Thought experiment: an isothermal atmosphere

**Predict before running:** the "isothermal" toy has the *same absorbers* as the standard one, but
every layer has the same temperature (1000 K). What will its spectrum look like? Will the bands show?
"""),
        code("""
fig, axes = plt.subplots(2, 1, sharex=True, figsize=(9, 7))
for t in (std, iso):
    axes[0].plot(t.wave_um, t.flux, label=t.name)
    axes[1].plot(t.wave_um, t.brightness_temp_k, label=t.name)
axes[0].plot(std.wave_um, bd.blackbody_surface_flux(std.wave_um, 1000), "k:", label="1000 K blackbody")
axes[0].set_yscale("log"); axes[0].set_ylabel(r"$F_\\lambda$ (toy)"); axes[0].legend()
axes[1].set_ylabel("brightness temperature [K]"); axes[1].set_xlabel("Wavelength [µm]")
axes[0].set_title("TOY: standard vs isothermal", fontsize=10);
"""),
        md("""
No features at all — the isothermal toy is exactly a 1000 K blackbody, even though its absorbers are
just as strong. Absorption only makes a **band** when the layer you see in the band has a *different
temperature* from the layer you see in the window. **Spectral features need a temperature gradient.**

## 4. Thought experiment: a thermal inversion

**Predict:** in the "inversion" toy, the temperature *rises* again high in the atmosphere (above ~30 mbar).
What happens to the strongest bands, whose τ = 2/3 level sits in that warm upper layer?
"""),
        code("""
fig, axes = plt.subplots(2, 1, sharex=True, figsize=(9, 7))
for t in (std, inv):
    axes[0].plot(t.wave_um, t.flux, label=t.name)
    axes[1].plot(t.wave_um, t.brightness_temp_k, label=t.name)
axes[0].set_yscale("log"); axes[0].set_ylabel(r"$F_\\lambda$ (toy)"); axes[0].legend()
axes[1].set_ylabel("brightness temperature [K]"); axes[1].set_xlabel("Wavelength [µm]")
axes[0].set_title("TOY: standard vs inversion", fontsize=10);
"""),
        md("""
The strongest bands flip from **absorption** (dips) to **emission** (bumps), because the layer we see
in them is now *hotter* than the layer we see in the windows. Weaker bands, which form deeper (below the
inversion), stay in absorption.

**A real example.** Rustamkulov et al. (2026) report a weak **3.3 µm CH<sub>4</sub> emission feature** in their
T7 spectrum, possibly from a thermal inversion. The next cell shows it once the T7 reference is installed.
"""),
        code("""
t7 = bd.optional(bd.load_reference, "T7")
if t7 is not None:
    bd.plot_spectrum(t7.between(2.8, 4.2), log=True, title="T7 reference near 3.3 um (look for a small bump)")
"""),
        md(f"""
## 5. Adding absorber: deeper, then saturated

{toy}

Below, the toy's CH<sub>4</sub> bands are multiplied by factors from 0 (none) to 1000.
**Predict:** if you multiply the CH<sub>4</sub> absorption by 10, does the 3.3 µm band get 10 times deeper?
"""),
        code("""
sw = bd.load_toy("ch4_sweep")
fig, ax = plt.subplots()
colors = plt.cm.viridis(np.linspace(0, 0.9, len(sw.multipliers)))
for m, f, c in zip(sw.multipliers, sw.spherex_flux, colors):
    ax.plot(sw.spherex_wave_um, f, "o-", ms=2, color=c, label=f"CH4 x {m:g}")
ax.set_xlim(2.6, 4.4); ax.set_yscale("log"); ax.legend(ncol=2, fontsize=8)
ax.set_xlabel("Wavelength [µm]"); ax.set_ylabel(r"$F_\\lambda$ (toy, SPHEREx-like channels)")
ax.set_title("TOY: CH4 multiplied by each factor", fontsize=10);
"""),
        code("""
i33 = np.argmin(abs(sw.wave_um - 3.32))
fig, ax = plt.subplots(figsize=(7, 4))
ax.semilogx(sw.multipliers[1:], sw.brightness_temp_k[1:, i33], "o-")
ax.axhline(sw.brightness_temp_k[0, i33], color="0.5", ls=":", label="no CH4")
ax.set_xlabel("CH4 multiplier (log scale)"); ax.set_ylabel("brightness temperature at 3.32 µm [K]")
ax.legend(); ax.set_title("TOY: band depth vs amount of absorber", fontsize=10);
"""),
        md("""
Two lessons, both true of real atmospheres too:

1. **Roughly logarithmic growth.** Each *factor* of 10 more absorber raises the τ = 2/3 level by about
   the same step in log P, so the band deepens by similar steps per factor of 10 — not in proportion.
2. **Saturation.** Once the τ = 2/3 level reaches the cool, nearly isothermal upper atmosphere, adding
   more absorber barely changes anything: the band is **saturated**. Strong real bands — CH<sub>4</sub> at 3.3 µm in
   cold dwarfs, for example — barely respond to changes in absorber amount.

That is why in this course we say a band shows **more absorption**, not "more abundance": a deeper band
can come from more molecules, a different temperature profile, or both, and a saturated band can hide a
big change in the amount of a molecule.
"""),
        md("""
### Exercise 2.1
In the contribution-function plot, find a wavelength whose light comes from the deepest layers. What
kind of region of the spectrum is it — a band or a window?
""" + answer("""
The deepest light comes out in the windows between bands (e.g. near 1.1, 1.27, 1.6, 2.1 and 4.0 µm in
the toy), where there is the least absorption. In real brown dwarfs, these are the Y, J, H, K and 4 µm peaks.
""")),
        md("""
### Exercise 2.2
In the isothermal toy, the light at 3.3 µm still comes from much higher up than at 4.0 µm. So why is
there no band?
""" + answer("""
Because every layer has the same temperature, so B<sub>λ</sub>(T) is the same wherever the light comes
from. A band only appears when the layer you see in the band has a different temperature from the one you
see in the window.
""")),
        md("""
### Exercise 2.3
From the band-depth plot, roughly how much does T<sub>b</sub> at 3.32 µm drop going from ×0.01 to ×0.1?
From ×10 to ×100?
""" + answer("""
Tens of kelvin for the first step and almost nothing for the second (read the exact numbers off your
plot). The band is saturated at large multipliers.
""")),
    ]
    cells += footer(
        ["There is no surface: we see light from the layer where τ ≈ 2/3, and that depth depends on wavelength.",
         "Brightness temperature ≈ temperature at the τ = 2/3 level (Eddington–Barbier).",
         "No temperature gradient → no features. A thermal inversion turns strong bands into emission.",
         "Band depth grows roughly with the log of the absorber amount, then saturates.",
         "Field guide: [Glossary](../field_guide/glossary.md)"],
        [("What does τ = 2/3 mean physically?",
          "The depth from which a typical escaping photon comes; deeper light is mostly absorbed on the way out."),
         ("Why does an isothermal atmosphere show no absorption bands?",
          "Every layer emits the same B<sub>λ</sub>(T), so it doesn't matter which layer you see."),
         ("What turns an absorption band into an emission feature?",
          "A thermal inversion: the layer seen in the band is hotter than the layer seen in the windows."),
         ("Why might a band barely change when a molecule's amount changes by 10×?", "It is saturated.")],
        "[Notebook 3 · The band atlas](03_band_atlas.ipynb)")
    return f, cells


# =============================================================== notebook 3
def nb03(owner):
    f = "03_band_atlas.ipynb"
    cells = [
        header(owner, f, "3 · The band atlas", [
            "name the absorbers that shape a brown dwarf spectrum between 0.75 and 5 µm, and where they act",
            "read 'molecule bar' plots",
            "explain two traps: overlapping bands, and band wings reaching into windows",
            "explain why band depth tracks absorption, not abundance",
        ], 35),
        setup_cell(owner),
        md("""
## 1. The atlas

The band positions live in one instructor-editable file, `data/bands.yaml`, so every plot and the
field guide use the same ranges and colours. Each row says where its numbers come from.
`status` tells you where the row comes from: **spec** = stated in Rustamkulov et al. (2026, Sec. 3);
**checked** = range from the band table of Cushing et al. (2005); **uncertain** = listed by Cushing et al. (2005),
but whether SPHEREx can separate it at all is unclear.
"""),
        code("""
import pandas as pd
rows = []
for name, ab in bd.load_bands()["absorbers"].items():
    for b in ab["bands"]:
        rows.append({"absorber": name, "range (um)": f"{b['range_um'][0]:.2f}-{b['range_um'][1]:.2f}",
                     "types": b["types"], "status": b["status"], "overlaps": b.get("overlaps", ""),
                     "source": b["source"]})
pd.set_option("display.max_colwidth", 70)
pd.DataFrame(rows)
"""),
        md("""
**NH<sub>3</sub>** is in the list for completeness: it is unlikely to be detectable with SPHEREx
(Rustamkulov et al. 2026), so don't go looking for it. Uncertain rows are hidden from plots unless you ask.
"""),
        code("""
# ✏️ SETTINGS YOU CAN CHANGE
SPECTRAL_TYPE = "L8"
SHOW_UNCERTAIN = False
"""),
        code("""
spec = bd.load_reference(SPECTRAL_TYPE)
fig, ax = bd.plot_spectrum(spec, log=True, include_uncertain=SHOW_UNCERTAIN,
                           title=f"{spec.name} with molecule bars")
"""),
        md("""
## 2. Footprints: remove one absorber at a time

The cleanest way to see what an absorber does is to compute the spectrum with and without it.
The curated model grids don't provide spectra with single absorbers removed, so we use the toy —
at SPHEREx-like resolution, so the footprints look the way SPHEREx would see them.

> 🧸 **TOY MODEL** — real band shapes and strengths differ; use this for *where* and *how*, not *how much*.
"""),
        code("""
r1 = bd.load_toy("remove_one")
labels = list(r1.labels)
full = r1.spherex_flux[labels.index("all")]
fig, axes = plt.subplots(2, 1, sharex=True, figsize=(9, 7.5), gridspec_kw={"height_ratios": [2, 1.4]})
axes[0].plot(r1.spherex_wave_um, full, "k-o", ms=2, label="all toy absorbers")
for lab, f in zip(labels, r1.spherex_flux):
    if lab == "all":
        continue
    name = lab[3:]
    c = bd.molecule_color(name)
    axes[0].plot(r1.spherex_wave_um, f, color=c, lw=1.2, label=lab)
    axes[1].plot(r1.spherex_wave_um, f / full, color=c, lw=1.5, label=lab)
axes[0].set_yscale("log"); axes[0].legend(ncol=3, fontsize=8); axes[0].set_ylabel(r"$F_\\lambda$ (toy)")
axes[1].axhline(1, color="0.4"); axes[1].set_yscale("log")
axes[1].set_ylabel("without X / with all"); axes[1].set_xlabel("Wavelength [µm]")
axes[0].set_title("TOY: footprint of each absorber", fontsize=10);
"""),
        md("""
Each curve in the bottom panel is one absorber's **footprint**: where the spectrum would get brighter
if that absorber disappeared.

## 3. Trap 1 — overlapping bands

Look at 1.1–1.2 µm and 2.2–2.5 µm in the footprint plot: more than one absorber's footprint is above 1 there.
When bands overlap, a deeper trough doesn't tell you *which* absorber changed. In real spectra:

* 1.1–1.2 µm: H<sub>2</sub>O and (in T dwarfs) CH<sub>4</sub>;
* 2.2–2.5 µm: CH<sub>4</sub>, CO, and H<sub>2</sub> collision-induced absorption (CIA);
* 3–3.6 µm: CH<sub>4</sub> on the wing of the broad 2.7 µm H<sub>2</sub>O band.

Always check the atlas for *every* absorber in a region before naming one.

## 4. Trap 2 — band wings reach into the windows

The footprints are not zero in the windows. Removing H<sub>2</sub>O changes the flux at the J and H peaks too, because
the wings of its bands reach into the windows. **The height of a window peak depends on its neighbours.**
"""),
        code("""
for target in [1.27, 1.60, 4.00]:
    i = np.argmin(abs(r1.spherex_wave_um - target))
    changes = {lab: f"{(f[i] / full[i] - 1) * 100:+.0f}%" for lab, f in zip(labels, r1.spherex_flux) if lab != "all"}
    print(f"window at {target} um, flux change when removing:", changes)
"""),
        md("""
## 5. Trap 3 — depth tracks absorption, not abundance

From notebook 2: band depth grows roughly with the *log* of the absorber amount and saturates. So when two
spectra differ in a band, say "**more absorption** at 3.3 µm", not "more methane". A temperature difference
also changes many bands at once (next cell): a **global** change, while removing one absorber changes only
its own bands — a **local** change.
"""),
        code("""
tv = bd.load_toy("temp_vs_absorber")
base = tv.spherex_flux[0]
fig, ax = plt.subplots()
bd.shade_bands(ax)
for lab, f, c in zip(tv.labels[1:], tv.spherex_flux[1:], bd.LINE_COLORS[1:]):
    ax.plot(tv.spherex_wave_um, f / base, "o-", ms=2, color=c, label=f"{lab}  /  {tv.labels[0]}")
ax.axhline(1, color="0.4"); ax.set_yscale("log"); ax.legend(fontsize=8)
ax.set_xlabel("Wavelength [µm]"); ax.set_ylabel("ratio"); ax.set_title("TOY: global vs local change", fontsize=10);
"""),
        md("""
## 6. Where the real band data come from (pointers only)

Real models use **line lists** — laboratory and theoretical catalogues of millions to billions of individual
molecular transitions (e.g. the ExoMol and HITRAN/HITEMP databases) — and **radiative-transfer codes** that
compute spectra from them (e.g. PICASO, petitRADTRANS). You will not need them in this course; the model
grids in notebook 5 were built with tools like these.

### Exercise 3.1
In the footprint plot, which toy absorber affects the most wavelengths? Is that also true in the real atlas table?
""" + answer("""
H<sub>2</sub>O: it has bands throughout the near-infrared (0.93, 1.15, 1.4, 1.9, 2.7 µm). In real L, T and Y dwarfs,
water is the dominant absorber, carving the troughs between the Y, J, H, K and 4 µm peaks.
""")),
        md("""
### Exercise 3.2
Two spectra differ only at 2.2–2.5 µm. List every absorber that could be responsible.
""" + answer("""
CH<sub>4</sub>, CO (2.3 µm overtone), and H<sub>2</sub> CIA — and possibly the wing of the 1.9 µm H<sub>2</sub>O band at the
short end. Gravity and metallicity change CIA, so they belong on the list of explanations too (notebook 5).
""")),
    ]
    cells += footer(
        ["H<sub>2</sub>O shapes the whole near-infrared; CH<sub>4</sub> appears at 3–3.6 µm after L4 and defines T dwarfs; CO and CO<sub>2</sub> make notches beyond 4.15 µm; H<sub>2</sub> CIA is broad, ~1.7–3 µm.",
         "Footprints (spectrum without X / with X) show where an absorber acts.",
         "Bands overlap, and band wings set the height of window peaks.",
         "Temperature changes many bands at once; one absorber changes only its own bands.",
         "Field guide: [Band atlas](../field_guide/band_atlas.md)"],
        [("Name the absorbers that could deepen the trough near 1.15 µm in a T dwarf.", "H<sub>2</sub>O and CH<sub>4</sub>."),
         ("Why can removing H<sub>2</sub>O change the J-peak flux?", "The wings of neighbouring H<sub>2</sub>O bands reach into the J window."),
         ("How does a global (temperature) change look different from a local (one absorber) change in a ratio plot?",
          "A temperature change moves many bands and the overall slope at once; an absorber change is confined to that absorber's bands."),
         ("Why is NH<sub>3</sub> in the atlas but not on the plots?", "It is unlikely to be detectable with SPHEREx (Rustamkulov et al. 2026).")],
        "[Notebook 4 · The spectral sequence](04_spectral_sequence.ipynb)")
    return f, cells


# =============================================================== notebook 4
def nb04(owner):
    f = "04_spectral_sequence.ipynb"
    cells = [
        header(owner, f, "4 · The spectral sequence", [
            "describe how brown dwarf spectra change from L0 to ~Y4",
            "say when CH<sub>4</sub> appears, what happens at the L/T transition, and how late-T and Y dwarfs differ",
            "estimate a rough spectral type by eye",
            "appreciate how small the differences between adjacent subtypes are",
        ], 40),
        setup_cell(owner),
        md("""
## 1. The reference sequence

Rustamkulov et al. (2026) assembled SPHEREx spectra of one object per subtype from L0 to ~Y4
(their Table 1; ~2500 K down to ~250 K). These are our **references**.
"""),
        code("""
cat = bd.list_references()
cat
"""),
        md("""
> The spectra are SPHEREx spectra from the SPIFF library (Gagné et al. 2026), one object per subtype in Table 1.
> Three Table 1 objects are not in the public SPIFF release. For L9 and Y1 we use a **stand-in**: another object
> of the same type (`status` = `substitute`; `table_name` gives the object it replaces). There is no stand-in
> for ~Y4 (WISE 0855−0714, the coldest known brown dwarf), so our sequence stops at Y2.
"""),
        code("""
# ✏️ SETTINGS YOU CAN CHANGE
NORMALIZE_AT = (1.20, 1.30)   # divide each spectrum by its mean flux here (J peak) to compare shapes
OFFSET = 0.6                  # vertical spacing between stacked spectra
"""),
        code("""
seq = bd.load_sequence()
print("loaded:", [s.meta["spectral_type"] for s in seq])
fig, ax = bd.plot_spectrum(seq, normalize_at=NORMALIZE_AT, offset=OFFSET, errors=False,
                           colors=list(plt.cm.viridis(np.linspace(0, 0.9, len(seq)))),
                           labels=[s.meta["spectral_type"] for s in seq], title="The sequence (normalized, stacked)")
"""),
        code("""
fig, ax = bd.plot_spectrum(seq, log=True, normalize_at=NORMALIZE_AT, errors=False,
                           colors=list(plt.cm.viridis(np.linspace(0, 0.9, len(seq)))),
                           labels=[s.meta["spectral_type"] for s in seq], title="The sequence on a log axis")
"""),
        md("""
## 2. What changes along the sequence

These milestones are from Rustamkulov et al. (2026, Sec. 3). Check each one against the plots.

| Where | What to look for |
|---|---|
| **After L4** | CH<sub>4</sub> becomes visible, first as a downward curve at 3–3.6 µm, later dominating the short side of the 4 µm peak. |
| **Beyond L3** | CO<sub>2</sub> (4.15–4.3 µm) and CO (4.4–4.9 µm) notches grow; from L4 a small peak appears at 4.67 µm. |
| **T0** | The K peak (≈2.1 µm) drops below the H peak (≈1.6 µm). |
| **T4** | The H peak drops below the J peak (≈1.27 µm). A narrow CH<sub>4</sub> feature appears at 1.15 µm. |
| **L/T transition** | The 4 µm peak is sharpest here. Clouds clear and the J band brightens. |
| **T6 → T7** (~1000 → 700 K) | The CO and CO<sub>2</sub> indices drop sharply. |
| **Late T and Y** | The 4 µm peak shifts redward. For Y dwarfs, only flux beyond ~3.9 µm is reliably detected. |

### Brightness temperature along the sequence
Converting each spectrum to T<sub>b</sub> (notebook 1) puts all of them on one comparable scale.
"""),
        code("""
fig, ax = plt.subplots()
colors = plt.cm.viridis(np.linspace(0, 0.9, len(seq)))
for s, c in zip(seq, colors):
    surf = bd.observed_to_surface(s.flux, s.meta["distance_pc"], radius_rjup=1.0)
    ax.plot(s.wave_um, bd.brightness_temperature(s.wave_um, surf), color=c, label=s.meta["spectral_type"])
ax.set_xlabel("Wavelength [µm]"); ax.set_ylabel("brightness temperature [K] (R = 1 R_Jup assumed)")
ax.legend(ncol=4, fontsize=8); ax.set_title("Brightness temperature along the sequence");
"""),
        md("""
## 3. Indices along the sequence

The three indices of Rustamkulov et al. (2026, Table 5) measure band depths in the 3–5 µm range
(details in notebook 6 and the [field guide](../field_guide/indices.md)). Larger = deeper band.
"""),
        code("""
tab = bd.index_table(seq)
tab
"""),
        code("""
fig, ax = plt.subplots()
x = np.arange(len(tab))
for name, c in [("CH4", bd.molecule_color("CH4")), ("CO2", bd.molecule_color("CO2")), ("CO", bd.molecule_color("CO"))]:
    ax.errorbar(x, tab[name], yerr=tab[name + "_err"], fmt="o-", color=c, label=name, capsize=2)
ax.set_xticks(x, tab["type"]); ax.set_ylabel("index [mag]  (bigger = deeper band)"); ax.legend()
ax.set_title("Indices along the sequence");
"""),
        md("""
## 4. Estimate a spectral type by eye

Run the next cell to draw a random reference and hide its label. Use the milestones above, then reveal.
"""),
        code("""
rng = np.random.default_rng()           # put a number inside () to get the same 'mystery' every time
mystery = seq[rng.integers(len(seq))]
fig, ax = bd.plot_spectrum(mystery.copy(name="mystery object"), log=True, title="What type is this?")
"""),
        code("""
print("It was:", mystery.meta["spectral_type"])
"""),
        md("""
## 5. Adjacent subtypes are subtle

Your real task will often be judging between neighbouring subtypes (an L8 versus an L9 fit, say). Overlay two
neighbours, normalized at the J peak, and look at their ratio.
"""),
        code("""
# ✏️ SETTINGS YOU CAN CHANGE
PAIR = ("L8", "L9")      # try ("L4", "L5") or ("T6", "T7") too
"""),
        code("""
a = bd.optional(bd.load_reference, PAIR[0]); b = bd.optional(bd.load_reference, PAIR[1])
if a is not None and b is not None:
    fig, ax = bd.plot_spectrum([a, b], log=True, normalize_at=NORMALIZE_AT, title=f"{PAIR[0]} vs {PAIR[1]}")
    c = bd.compare(a, b, windows=[NORMALIZE_AT])
    fig, axes = bd.plot_comparison(c, panel="both", title=f"{PAIR[0]} / {PAIR[1]} (scaled at the J peak)")
"""),
        md("""
Most of the ratio is within a few percent of 1, and the largest differences sit in specific bands. That is
normal — and it is why the comparison notebook (6) is about uncertainties and significance, not just shapes.

### Exercise 4.1
On the stacked plot, at which subtype does a downward curve at 3–3.6 µm first become obvious?
""" + answer("""
Rustamkulov et al. (2026) find CH<sub>4</sub> becomes visible after L4. With noisy data you may not see it
clearly until L5–L6; that is fine — say what *you* see and how confident you are.
""")),
        md("""
### Exercise 4.2
Using the index plot, which index changes most steadily across the L sequence?
""" + answer("""
Read it off your plot. Expect the CO and CO<sub>2</sub> indices to grow beyond L3 and the CH<sub>4</sub> index to rise
after L4 (Rustamkulov et al. 2026). Check the error bars before calling a trend real.
""")),
    ]
    cells += footer(
        ["Going later: the flux peak moves to longer wavelengths and CH<sub>4</sub>, CO and CO<sub>2</sub> features develop in a known order.",
         "Key markers: CH<sub>4</sub> after L4; K < H at T0; H < J at T4; CO/CO<sub>2</sub> collapse between T6 and T7; Y dwarfs are detected only beyond ~3.9 µm.",
         "Adjacent subtypes differ by a few percent — judge with uncertainties.",
         "Field guide: [Spectral sequence cheat sheet](../field_guide/spectral_sequence.md)"],
        [("At which subtype does the K peak drop below the H peak?", "T0 (Rustamkulov et al. 2026)."),
         ("What happens to the CO and CO<sub>2</sub> indices between T6 and T7?", "They drop sharply (~1000 → 700 K)."),
         ("Where is the 4 µm peak sharpest?", "At the L/T transition."),
         ("Why do Y-dwarf spectra look empty below ~3.9 µm?", "Too little flux there to be reliably detected by SPHEREx.")],
        "[Notebook 5 · Global atmospheric parameters](05_global_parameters.ipynb)")
    return f, cells


# =============================================================== notebook 5
def nb05(owner):
    f = "05_global_parameters.ipynb"
    sweep_cell = lambda fid, par, lab: code(f"""
r = bd.optional(bd.load_sweep, "{fid}", "{par}")
if r is not None:
    fid_spec, members = r
    bd.plot_parameter_stack(fid_spec, members, "{par}", value_label="{lab}", log=True,
                            title="{fid} fiducial: only {lab} changes")
""")
    cells = [
        header(owner, f, "5 · Global atmospheric parameters", [
            "say what effective temperature, gravity, metallicity, clouds, and vertical mixing each do to a spectrum",
            "read a parameter stack and a ratio-to-fiducial plot",
            "compare real low-gravity and low-metallicity objects with field objects of the same type",
            "recognize degeneracies: different parameter changes that look alike",
        ], 50),
        setup_cell(owner),
        md("""
## 1. Model grids

A **model grid** is a large set of computed spectra, each for one combination of a few **global parameters**:

| Parameter | Symbol | What it is |
|---|---|---|
| Effective temperature | T<sub>eff</sub> | the temperature of a blackbody with the same total emitted power |
| Surface gravity | log g | log<sub>10</sub> of g in cm s<sup>−2</sup>; young, low-mass objects have low gravity |
| Metallicity | [M/H] | log<sub>10</sub> of the heavy-element fraction relative to the Sun (0 = solar, −0.5 ≈ ⅓ solar) |
| Clouds | f<sub>sed</sub> | sedimentation efficiency: small f<sub>sed</sub> = thick, extended clouds; "nc" = cloud-free |
| Vertical mixing | K<sub>zz</sub> | how fast gas is stirred up from below; strong mixing carries deep-layer chemistry (e.g. CO) upward (disequilibrium chemistry) |

We use a curated subset of model grids: **Sonora Diamondback** (cloudy, equilibrium chemistry; L and T),
**Sonora Flame Skimmer** (cloud-free, disequilibrium chemistry with a K<sub>zz</sub> axis; late T and Y) and **Exo-REM**
(clouds and disequilibrium chemistry). Only Flame Skimmer's 500–550 K models have been downloaded so far, so its
temperature sweep is narrow.
The models were averaged to modest resolution (R ~ 500) once, by your instructor. **Never compare a high-resolution
model directly with SPHEREx data** — bdtools always bins it onto the data's own channels first (notebook 6).

The library is organised around a few **fiducial** models; in each sweep only *one* parameter changes.
"""),
        code("""
lib = bd.optional(bd.list_models)
lib if lib is None else lib[lib["sweep"] == "fiducial"]
"""),
        md("""
Each plot below has two panels: the spectra (thick line = fiducial) and each model **divided by the fiducial**,
with absorber bands shaded. The ratio panel is where you read the effect of a parameter.

## 2. Effective temperature

**Predict:** a cooler model at the same gravity — will it be fainter everywhere by the same factor?
"""),
        sweep_cell("L", "teff", "Teff [K]"),
        sweep_cell("T_early", "teff", "Teff [K]"),
        md("""
Temperature is a **global** parameter: it changes the overall slope (Planck, notebook 1) *and* the depths of
many bands at once, because the chemistry and the temperature profile both change.

## 3. Surface gravity
"""),
        sweep_cell("L", "logg", "log g"),
        sweep_cell("T_early", "logg", "log g"),
        md("""
Higher gravity means higher pressure at the photosphere, which strengthens pressure-dependent absorption such as
H<sub>2</sub> CIA (≈1.7–3 µm). Watch the K-band region. The observed signs of **low gravity** (Rustamkulov et al.
2026): a shallower 0.75–1.2 µm slope, weaker water features, and a taller K peak relative to H.

## 4. Metallicity
"""),
        sweep_cell("L", "mh", "[M/H]"),
        sweep_cell("T_early", "mh", "[M/H]"),
        md("""
Fewer heavy elements → less H<sub>2</sub>O, CH<sub>4</sub>, CO, … but H<sub>2</sub> (and its CIA) is untouched. In observed
**low-metallicity** objects the J (1.3 µm) to K (2.2 µm) peak ratio reverses, because H<sub>2</sub> CIA dominates from
~1.7 to 3 µm (Rustamkulov et al. 2026).

## 5. Clouds
"""),
        sweep_cell("L", "clouds", "f_sed"),
        sweep_cell("T_early", "clouds", "f_sed"),
        md("""
Thick clouds (small f<sub>sed</sub>) block the deep windows, so the window peaks drop and the spectrum looks redder and
smoother; cloud-free models have the deepest, brightest windows. Clearing clouds is part of why the J band
brightens across the L/T transition.

## 6. Vertical mixing (K<sub>zz</sub>)
"""),
        sweep_cell("T_late_Y", "kzz", "log Kzz"),
        md("""
Stronger mixing dredges up CO (and CO<sub>2</sub>) from hot deep layers faster than chemistry can convert it to CH<sub>4</sub>,
so the 4.3–4.9 µm notches deepen and the 3.3 µm CH<sub>4</sub> band changes. This is **disequilibrium chemistry**; the
Diamondback grid assumes equilibrium and has no K<sub>zz</sub> axis.

The late-T/Y fiducial's other sweeps:
"""),
        sweep_cell("T_late_Y", "teff", "Teff [K]"),
        sweep_cell("T_late_Y", "logg", "log g"),
        md("""
## 7. Grids disagree

Even with the **same** parameters, different grids differ by up to about a factor of 2 at some wavelengths
(Rustamkulov et al. 2026). And the best fits to high-S/N data typically still have reduced χ² ≥ 10. **Treat
best-fit parameters as rough.**

"Same parameters" means the same *numbers*, not the same physics: each grid has its own cloud recipe (so
f<sub>sed</sub> = 4 in one grid is not the same cloud as f<sub>sed</sub> = 4 in another), its own chemistry
(Diamondback assumes equilibrium; Exo-REM includes disequilibrium chemistry), and its own opacities. The Exo-REM
spectra in this library also start near 0.93 µm, so the shortest wavelengths show only one grid.
"""),
        code("""
lib = bd.optional(bd.list_models)
if lib is not None:
    for fid in lib["fiducial"].unique():
        cg = lib[(lib["fiducial"] == fid) & (lib["sweep"] == "cross_grid")]
        f0 = lib[(lib["fiducial"] == fid) & (lib["sweep"] == "fiducial")]
        if cg.empty or f0.empty:
            continue
        a = bd.at_spherex_resolution(bd.load_model(f0.iloc[0]["id"]))
        b = bd.at_spherex_resolution(bd.load_model(cg.iloc[0]["id"]))
        fig, ax = bd.plot_spectrum([a, b], log=True, title=f"{fid}: two grids, same nominal parameters (SPHEREx resolution)")
        print(fid, "largest ratio between the grids:", round(float(np.nanmax(a.flux / b.flux)), 2),
              " smallest:", round(float(np.nanmin(a.flux / b.flux)), 2))
"""),
        md("""
## 8. Real low-gravity and low-metallicity objects

Rustamkulov et al. (2026) include a **low-gravity** sequence at L0 and L5 (their Table 2: field, β = intermediate
gravity, γ = low gravity, i.e. young) and a **low-metallicity** sequence at L0 and L7 (Table 3: field, sd = subdwarf,
esd = extreme subdwarf). Each group below has the same spectral type, so the differences come from gravity or
metallicity rather than temperature. All are normalized at the J peak.

**Predict** before you run it, using sections 3 and 4:
* low gravity: what happens to the 0.75–1.2 µm slope, the water bands, and the K peak relative to H?
* low metallicity: what happens to the K peak (≈2.2 µm) relative to J (≈1.3 µm)?

> Three objects in Tables 2 and 3 are not in the public SPIFF release. The field L0 in both groups is a **stand-in**
> (the Table 1 L0, which the paper itself preferred over the L0 standard for its S/N), and so is the esdL0 (an
> esdL0.5, with low S/N). There is no usdL0 (no ultra-subdwarfs at all in SPIFF). `bd.list_references()` marks
> stand-ins with `status` = `substitute`.
"""),
        code("""
refs = bd.optional(bd.list_references)
if refs is not None:
    for seqname in ["low_gravity", "low_metallicity"]:
        rows = refs[refs["sequence"] == seqname]
        for base in rows["base_type"].unique():
            group = rows[rows["base_type"] == base].sort_values("order")
            specs = [bd.load_reference(i) for i in group["id"]]
            bd.plot_spectrum(specs, log=True, normalize_at=(1.2, 1.3), errors=False,
                             labels=[s.name.split(" ")[0] for s in specs],
                             title=f"{base}: {seqname.replace('_', ' ')} sequence (normalized at 1.2-1.3 um)")
"""),
        md("""
## 9. Degeneracies: different causes, similar effects

Different parameter changes can look alike in some bands. Here we put a *cooler* model and a *higher-gravity*
model on the same ratio plot.
"""),
        code("""
# ✏️ SETTINGS YOU CAN CHANGE
FIDUCIAL = "T_early"
"""),
        code("""
lib = bd.optional(bd.list_models, fiducial=FIDUCIAL)
if lib is not None and not lib.empty:
    fid = bd.load_model(lib[lib["sweep"] == "fiducial"].iloc[0]["id"])
    cool = lib[(lib["sweep"] == "teff") & (lib["teff"] < fid.meta["teff"])].sort_values("teff").tail(1)
    heavy = lib[(lib["sweep"] == "logg") & (lib["logg"] > fid.meta["logg"])].sort_values("logg").head(1)
    if not cool.empty and not heavy.empty:
        fig, ax = plt.subplots()
        bd.shade_bands(ax)
        for row, c in [(cool.iloc[0], bd.LINE_COLORS[1]), (heavy.iloc[0], bd.LINE_COLORS[2])]:
            m = bd.at_spherex_resolution(bd.load_model(row["id"]))
            r = bd.ratio_to(m, bd.at_spherex_resolution(fid))
            ax.plot(m.wave_um, r / np.nanmedian(r), color=c, label=m.name + "  / fiducial (shape only)")
        ax.axhline(1, color="0.4"); ax.legend(fontsize=8); ax.set_xlim(0.7, 5.1)
        ax.set_xlabel("Wavelength [µm]"); ax.set_ylabel("ratio, divided by its median")
        ax.set_title("Cooler vs higher gravity: where do they look alike? where not?")
"""),
        md("""
Dividing by the median removes the overall brightness difference, leaving the shape change. Look for bands where the
two curves move the same way (degenerate) and bands where they differ (these let you tell them apart).

Unresolved **binarity** (two objects blended into one spectrum) can also mimic a parameter change — see notebook 6.

### Exercise 5.1
In the T<sub>eff</sub> sweep, which wavelength range changes most in ratio? Why does that make sense from notebook 1?
""" + answer("""
The short wavelengths (and the deep windows) change most, because they are on the steep, short-wavelength side of
the Planck function, where flux is most sensitive to temperature.
""")),
        md("""
### Exercise 5.2
Name two things that can make the K peak taller relative to H.
""" + answer("""
Lower gravity (less H<sub>2</sub> CIA; Rustamkulov et al. 2026 list a taller K peak relative to H as a low-gravity sign) and
thicker clouds / redder colours. Metallicity matters too. That's a degeneracy — use other bands to break it.
""")),
    ]
    cells += footer(
        ["T<sub>eff</sub>: global — slope and many bands. log g and [M/H]: act strongly through H<sub>2</sub> CIA (~1.7–3 µm) and band depths.",
         "Clouds (f<sub>sed</sub>) dim the windows and redden; K<sub>zz</sub> sets how much CO/CO<sub>2</sub> survives in cold atmospheres.",
         "Grids with the same parameters can differ by ~2×; best fits still have χ²<sub>red</sub> ≥ 10. Parameters are rough.",
         "Degeneracies are common: look for bands that respond differently.",
         "Field guide: [Global parameters](../field_guide/parameters/README.md)"],
        [("Which parameter changes the spectrum most globally?", "Effective temperature."),
         ("Name one observed sign of low gravity.", "A shallower 0.75–1.2 µm slope, weaker water features, or a taller K peak relative to H."),
         ("What does vertical mixing do to CO in a cold atmosphere?", "Brings it up from hot deep layers faster than it converts to CH<sub>4</sub>, so more CO absorption."),
         ("Two grids give different spectra for the same parameters. What should you conclude?", "Model physics differs; treat best-fit parameters as rough.")],
        "[Notebook 6 · Fitting models to spectra](06_fitting_models.ipynb)")
    return f, cells


# =============================================================== notebook 6
def nb06(owner):
    f = "06_fitting_models.ipynb"
    cells = [
        header(owner, f, "6 · Fitting models to spectra", [
            "fit a grid of models to a spectrum with one free scale factor, and read the best fit and its residuals",
            "use a χ² map to see which parameters the data pin down and which trade off against each other",
            "check fitted parameters against what we know about the reference sequence",
            "tell a model problem from something peculiar about one object, by comparing with the named template",
            "compare indices between a spectrum and its best-fit model, and list what can mimic a chemistry difference",
            "recognize data problems before interpreting a feature",
        ], 75),
        setup_cell(owner),
        md("""
## 1. The setup

The objects you will review later already have spectral types, so the question is not *what type is it?* but
*how well do models describe it, and where do they fail?* Here we practise on the references, whose types and
distances we know.

We fit a **grid** of models: every model in Sonora Diamondback (Morley et al. 2024), 1440 spectra covering
T<sub>eff</sub>, log g, [M/H] and clouds (f<sub>sed</sub>, or "nc" = cloud-free). The conventions follow Rustamkulov et al. (2026):

* each model is **averaged onto the data's own SPHEREx channels** first;
* each model is multiplied by **one free scale factor** (physically (R/d)², but here we just let it float);
* a **3% systematic** is added in quadrature to the data uncertainties;
* models are ranked by **reduced χ²**; **G<sub>k</sub>** (Cushing et al. 2008), which weights each channel by its width,
  is listed too.
"""),
        code("""
grid = bd.optional(bd.load_grid, "diamondback")
grid
"""),
        code("""
# ✏️ SETTINGS YOU CAN CHANGE
DATA_TYPE = "L5"
FIT_WINDOW = None      # None = fit the scale over all channels; e.g. [(1.2, 1.3)] = J peak only
FIXED = {}             # hold parameters fixed, e.g. {"mh": 0.0} or {"clouds": "nc"}
"""),
        md("""
## 2. Fit one reference

**Predict:** this object is an L5. Roughly what T<sub>eff</sub> do you expect the best model to have? (Notebook 4 and
the [spectral sequence page](../field_guide/spectral_sequence.md) give the scale.)
"""),
        code("""
data = bd.load_reference(DATA_TYPE)
fit = bd.fit_models(data, windows=FIT_WINDOW, **FIXED) if grid is not None else None
if fit is not None:
    print(fit.summary())
    display(fit.table.head(10))
"""),
        md("""
Look at the top ten. Are they all similar models, or do quite different parameter combinations give almost the same
χ²<sub>red</sub>? And notice the size of χ²<sub>red</sub>: even the best model is usually **far** above 1. With a 3% systematic
already included, that means the models do not reproduce the spectrum within its uncertainties. Rustamkulov et al.
(2026) find χ²<sub>red</sub> ≥ 10 for best fits to high-S/N spectra. **Treat best-fit parameters as rough.**

## 3. The best fit and its residuals
"""),
        code("""
if fit is not None:
    comp = fit.comparison()
    fig, axes = bd.plot_comparison(comp, panel="both", title=f"{data.meta['spectral_type']}: best-fit model")
"""),
        md("""
Read the two lower panels with the band atlas in mind:

* **ratio** (data / model): where is the data brighter (> 1) or fainter (< 1) than the model, and does each departure sit
  inside a shaded absorber band?
* **significance** ((data − model)/σ): points beyond ±3 are hard to explain by noise alone. Clusters of same-sign points
  inside a band are a *feature*; isolated single points are suspicious (section 9).

### Scaling changes how residuals look
**Predict:** if the same model is scaled to match only at the J peak, will the ratio plot look the same?
"""),
        code("""
if fit is not None:
    c_j = bd.compare(data, fit.model(), windows=[(1.2, 1.3)])
    fig, axes = bd.plot_comparison(c_j, panel="ratio", title="Same best-fit model, scaled at the J peak only")
"""),
        md("""
Same two spectra, different-looking ratio plot. With J-peak scaling the ratio is 1 at J by construction and every
other difference looks like a slope. **A ratio plot always depends on the scaling**, so say how you scaled whenever
you describe one. Indices (section 7) are ratios within one spectrum and do not depend on it.

## 4. Which parameters do the data pin down? The χ² map

Each cell shows the best χ²<sub>red</sub> among models with that pair of values (the other parameters are free). The star is
the overall best fit. A small dark spot means a well-constrained pair; a long dark valley means the two parameters
**trade off** — a degeneracy (notebook 5).
"""),
        code("""
# ✏️ SETTINGS YOU CAN CHANGE
MAP_X, MAP_Y = "teff", "logg"     # any two of: "teff", "logg", "mh", "clouds"
"""),
        code("""
if fit is not None:
    fig, ax = bd.plot_chi2_map(fit, x=MAP_X, y=MAP_Y)
    fig, ax = bd.plot_chi2_map(fit, x="teff", y="clouds")
"""),
        md("""
## 5. Fit the whole sequence

**Predict:** from L0 to Y2, how should the best-fit T<sub>eff</sub> change? What about clouds? Diamondback's coolest model is
900 K. What do you expect for the late-T and Y dwarfs, which are cooler than that?
"""),
        code("""
seq = bd.load_sequence()
fits = [bd.fit_models(s, windows=FIT_WINDOW, **FIXED) for s in seq] if grid is not None else []
if fits:
    table = bd.fits_table(fits)
    display(table)
    fig, axes = bd.plot_fit_parameters(table)
"""),
        md("""
T<sub>eff</sub> should fall along the sequence — roughly 2300 K at L0 to roughly 1300–1400 K at the end of the L types,
from bolometric luminosities (e.g. Filippazzo et al. 2015). Where does the fit follow that trend, and where does it jump
around? Parameters that jump between neighbouring types (often log g, [M/H], or clouds) are poorly constrained by the
fit, even when the formal best fit names one value. Look also at χ²<sub>red</sub> along the sequence: which types do the models
describe worst?

Three things to look for in the table:

* **The grid edge.** From about T8 onward every fit lands on 900 K, the coolest Diamondback model. A best fit on the
  edge of a grid is **not a measurement**: it only says the object is at least as extreme as the grid allows. (A grid
  built for cooler objects, such as Sonora Flame Skimmer in notebook 5, is the right tool there.)
* **A small χ²<sub>red</sub> is not always a good fit.** The Y dwarfs are faint, with S/N of only a few per channel, so their
  large error bars keep χ²<sub>red</sub> small even when the model is poor. Always look at the residuals too.
* **One huge χ²<sub>red</sub>.** Look at L0. Set `DATA_TYPE = "L0"` in section 1 and look at the significance panel and the quality
  check in section 9: a couple of bad channels with small error bars (near 0.92 and 3.85 µm) dominate χ² and drag
  the scale, so the whole spectrum ends up off. **Check the data before trusting any fit.**

## 6. Is it the object or the models? Compare with the named template

In the review task every candidate has a spectral type, and that type names a **template**: the reference of the same
type. Fit both with the same grid and compare their residuals:

* a residual pattern the template **shares** is a **model problem** — the models get every object of that type wrong
  in the same way;
* a residual pattern only the candidate shows is something about **the candidate** worth explaining.

Here we practise with the data spectrum and its neighbours in the sequence, which all play the role of "named template".
"""),
        code("""
# ✏️ SETTINGS YOU CAN CHANGE
COMPARE_TYPES = ["L4", "L5", "L6"]
"""),
        code("""
if fits:
    chosen = [ft for ft in fits if ft.data.meta.get("spectral_type") in COMPARE_TYPES]
    fig, ax = bd.plot_fit_residuals(chosen, title="data / best-fit model for neighbouring types")
"""),
        md("""
Which departures appear in all of them (shared model problems)? Is there anything only one object shows? Remember
that each object has its own best-fit model, so part of the difference between curves is the fit itself — a shared
pattern is the strong clue, not a perfect match.

## 7. Indices: data versus best-fit model

The indices from Rustamkulov et al. (2026, Table 5) are magnitudes,

  I = −2.5 log<sub>10</sub>(F<sub>band</sub> / F<sub>norm</sub>),

with mean F<sub>ν</sub> in a feature region and in the 3.70–4.14 µm normalization window (the nearest thing to a continuum).
Bigger = deeper band. The uncertainty is (2.5/ln 10) √[(σ<sub>F</sub>/F)² + (σ<sub>norm</sub>/F<sub>norm</sub>)²]. A model has no
uncertainty, so a data–model difference is measured against the data's error alone.
"""),
        code("""
fig, ax = bd.plot_index_windows([data, comp.template] if fit is not None else data)
if fit is not None:
    import pandas as pd
    display(pd.DataFrame([bd.index_difference(data, comp.template, n) for n in ["CH4", "CO2", "CO"]]))
"""),
        md("""
**Before reading an index as chemistry, check its windows on the actual spectra.** The feature regions overlap other
absorbers (see the [band atlas](../field_guide/band_atlas.md)), so one molecule can move another molecule's index. And
the CH<sub>4</sub> index is **not meaningful for Y dwarfs** — CH<sub>4</sub> is undetected there at SPHEREx sensitivity.

### Index planes
An index plane plots **one index against another** for many spectra. The sequence traces a path through the plane.
Where does the "data" spectrum fall relative to the references? Try each pair of indices.
"""),
        code("""
# ✏️ SETTINGS YOU CAN CHANGE
PLANE_X = "CH4"     # one of: "CH4", "CO2", "CO"
PLANE_Y = "CO"
"""),
        code("""
fig, ax = bd.plot_index_plane(seq, x=PLANE_X, y=PLANE_Y, highlight=data)
"""),
        md("""
## 8. What can mimic a chemistry difference?

A residual in one band does not have to mean different chemistry. Before you write "more CO<sub>2</sub>", consider:

* **temperature** — changes many bands at once (notebooks 3 and 5);
* **gravity** and **metallicity** — act strongly through H<sub>2</sub> CIA and band depths (notebook 5);
* **clouds** — dim and redden the windows;
* **vertical mixing** — changes CO, CO<sub>2</sub> and CH<sub>4</sub> together (notebook 5);
* **the models themselves** — every grid has its own shortcomings (section 6);
* **unresolved binarity** — two objects of different type blended into one spectrum.

Here is a *simulated* unresolved binary made by adding two references. It is labeled as simulated and is only for practice.
"""),
        code("""
# ✏️ SETTINGS YOU CAN CHANGE
BINARY_PAIR = ("L2", "L8")      # brighter + fainter component
"""),
        code("""
p = bd.optional(bd.load_reference, BINARY_PAIR[0]); q = bd.optional(bd.load_reference, BINARY_PAIR[1])
if p is not None and q is not None and grid is not None:
    # put both at 10 pc so their relative brightness is physical, then add them on p's channels
    p10 = p.scaled((p.meta["distance_pc"] / 10) ** 2)
    q10 = q.scaled((q.meta["distance_pc"] / 10) ** 2)
    qf = np.interp(p10.wave_um, q10.wave_um, q10.flux); qe = np.interp(p10.wave_um, q10.wave_um, q10.err)
    blend = p10.copy(flux=p10.flux + qf, err=np.hypot(p10.err, qe),
                     name=f"SIMULATED blend {BINARY_PAIR[0]}+{BINARY_PAIR[1]}")
    bfit = bd.fit_models(blend)
    print(bfit.summary())
    fig, axes = bd.plot_comparison(bfit.comparison(), panel="both",
                                   title="SIMULATED unresolved binary vs its best single model")
"""),
        md("""
A single model can match the blend reasonably well overall but leave structured residuals in specific bands —
exactly the kind of thing that could be misread as a chemistry difference. Compare the best-fit T<sub>eff</sub> with those of the
two components in section 5.

## 9. Data problems: check these *first*

Real spectra contain spurious points even after cleaning (Rustamkulov et al. 2026), and candidate spectra are cleaned
unevenly. Before interpreting any feature, run a quality check. `bd.quality_report` flags points far from a running
median, gaps, and missing values — it never deletes anything; you decide.
"""),
        code("""
print(bd.quality_report(data))
flags = bd.running_median_outliers(data)
fig, ax = bd.plot_spectrum(data, log=True, title="Flagged points (red rings) - are they real?")
ax.plot(data.wave_um[flags], data.flux[flags], "o", mfc="none", mec="red", ms=10, mew=2);
"""),
        md("""
Now some **simulated** problems, so you know what each looks like against the best-fit model. Each is applied to a
copy of the data and labeled as simulated.
"""),
        code("""
rng = np.random.default_rng(1)
problems = {}
# 1. isolated outlier points
f = data.flux.copy(); idx = rng.choice(len(f), 3, replace=False); f[idx] *= rng.choice([0.6, 1.5], 3)
problems["isolated outliers"] = data.copy(flux=f)
# 2. a gap (channels missing)
keep = ~((data.wave_um > 2.0) & (data.wave_um < 2.6))
problems["gap at 2.0-2.6 um"] = data.select(keep)
# 3. uneven sampling (random channels missing)
problems["uneven sampling"] = data.select(rng.random(len(data)) > 0.3)
# 4. contamination by a bluer neighbour (an L0 adding ~20% of the data's J-band flux)
nb = bd.optional(bd.load_reference, "L0")
if nb is not None:
    nbf = np.interp(data.wave_um, nb.wave_um, nb.flux)
    j = (data.wave_um > 1.2) & (data.wave_um < 1.3)
    problems["contaminated by a neighbour"] = data.copy(flux=data.flux + 0.2 * nbf * data.flux[j].mean() / nbf[j].mean())
for label, bad in problems.items():
    if fit is not None:
        c = bd.compare(bad.copy(name=f"SIMULATED: {label}"), fit.model())
        bd.plot_comparison(c, panel="significance", title=f"SIMULATED problem: {label}")
"""),
        md("""
What to remember:

| Problem | What it looks like |
|---|---|
| isolated outlier | one point far off, neighbours fine; big single spike in significance |
| gap | missing stretch; an index or fit can silently use fewer channels |
| uneven sampling | irregular spacing; fine for fitting, but check every region still has points |
| contamination | a smooth, broad excess (often at short wavelengths for a bluer neighbour); not confined to one band |

See the [field guide page on data problems](../field_guide/data_problems.md).

## 10. Where this leads

You now have every skill the review task uses: reading a spectrum, the band atlas, the sequence, the effect of
each parameter, model fits with uncertainties, comparing with the named template, indices, and data-quality checks.
The **review notebook** (a separate part of the project, given to you by your instructor) applies them to real SPHEREx
candidates and asks you to explain, in words, where and why a candidate departs from its best-fit model.

### Exercise 6.1
Set `FIXED = {"clouds": "nc"}` (cloud-free models only) and re-run sections 2–5. How do the best-fit T<sub>eff</sub> and
χ²<sub>red</sub> change, and for which types most?
""" + answer("""
Without clouds the models cannot dim and redden the windows, so the fit usually compensates with a different
T<sub>eff</sub> (often cooler for mid/late L dwarfs) and χ²<sub>red</sub> gets worse, most for the dusty mid/late L types.
A parameter you hold fixed pushes the error into the others — another reason to treat best-fit values as rough.
""")),
        md("""
### Exercise 6.2
A candidate's CO<sub>2</sub> index is 0.15 ± 0.04 mag larger than its best-fit model's, and its named template shows no such
difference. List three explanations other than "more CO<sub>2</sub>".
""" + answer("""
Any three of: a different temperature, gravity, or metallicity than the fit found (the fit balances all channels, not
this band); vertical mixing changing CO/CO<sub>2</sub>; clouds; an overlapping absorber in the index window; an unresolved
companion; a bad point or gap in the 4.18–4.35 µm region or the normalization window. (And the difference is ~4σ —
check that it is not one bad channel.) Because the template does *not* share it, a pure model problem is less likely.
""")),
    ]
    cells += footer(
        ["Fit a grid: bin each model onto the data's channels, one free scale, 3% systematic, rank by χ²<sub>red</sub>.",
         "Best fits typically still have χ²<sub>red</sub> ≫ 1; best-fit parameters are rough, and χ² maps show degeneracies.",
         "Ratio plots depend on the scaling; indices do not.",
         "Residuals shared with the named template are model problems; residuals only the candidate shows are worth explaining.",
         "Temperature, gravity, metallicity, clouds, mixing, the models, and binarity can all mimic a chemistry difference.",
         "Check for outliers, gaps, uneven sampling, and contamination before interpreting any feature.",
         "Field guide: [Indices](../field_guide/indices.md), [Data problems](../field_guide/data_problems.md)"],
        [("Why is each model averaged onto the data's channels before fitting?",
          "SPHEREx blurs narrow model features together; comparing an unbinned model with SPHEREx data is not fair."),
         ("What does a long dark valley in a χ² map mean?", "The two parameters trade off (a degeneracy); the data do not pin down either alone."),
         ("A residual appears in the candidate and in its named template. What is the likely cause?",
          "The models — they get every object of that type wrong in the same way."),
         ("When is the CH<sub>4</sub> index not meaningful?", "For Y dwarfs (CH<sub>4</sub> undetected at SPHEREx sensitivity)."),
         ("What does an isolated outlier look like in a significance plot?", "A single large spike with normal neighbours, often outside any band.")],
        "the review notebook (analysis job) — ask your instructor for the link.")
    return f, cells


NOTEBOOKS = [nb00, nb01, nb02, nb03, nb04, nb05, nb06]


def build(owner, execute=False, timeout=600):
    NB_DIR.mkdir(exist_ok=True)
    written = []
    for make in NOTEBOOKS:
        fname, cells = make(owner)
        nb = new_notebook(cells=cells, metadata={
            "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
            "language_info": {"name": "python"},
            "colab": {"provenance": [], "toc_visible": True},
        })
        path = NB_DIR / fname
        nbformat.write(nb, path)
        written.append(path)
        print(f"wrote {path.relative_to(REPO)}")
    if execute:
        from nbclient import NotebookClient

        failures = 0
        for path in written:
            nb = nbformat.read(path, as_version=4)
            try:
                NotebookClient(nb, timeout=timeout, kernel_name="python3",
                               resources={"metadata": {"path": str(NB_DIR)}}).execute()
                print(f"  ran OK: {path.name}")
            except Exception as e:  # noqa: BLE001
                failures += 1
                print(f"  FAILED: {path.name}: {str(e)[:2000]}")
        if failures:
            sys.exit(1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--owner", default=GITHUB_OWNER)
    ap.add_argument("--execute", action="store_true", help="run every notebook to check it works (outputs are not saved)")
    args = ap.parse_args()
    build(args.owner, args.execute)
