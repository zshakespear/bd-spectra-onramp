"""Generate notebooks/00-06 from the text in this file.

Keeping the notebooks in one script means the setup cell, the Colab badge,
and the house style are identical everywhere. Edit here, then run:

    python scripts/build_notebooks.py            # write notebooks/*.ipynb (no outputs)
    python scripts/build_notebooks.py --execute  # also run them top to bottom (checks they work)

Set GITHUB_OWNER / REPO_NAME below (or pass --owner) before publishing.
"""

import argparse
import re
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
> **Moving between notebooks:** use the links inside the notebooks (such as **Next** at the bottom). They always open
> the original notebook, so they work from your copy too — then save a copy of the new notebook before you edit it.
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
3. **Use the links to move between notebooks.** The **Next** link at the bottom of each notebook opens the
   *original* version of the next notebook (from any copy). Save a copy of that one too before you edit it.

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

The pale **coloured shading** marks wavelengths where different molecules absorb light; the key above the plot
says which colour is which molecule (more on these in notebook 3). The narrow grey strip that hugs the line is the
±1σ uncertainty.
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
            "explain why flux blueward of the peak is so sensitive to temperature",
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

Two words we will use from now on: **blueward** means *toward shorter wavelengths* and **redward** means *toward
longer wavelengths*. Astronomers use them even in the infrared, where nothing is actually blue or red.
"""),
        code("""
for T in TEMPERATURES:
    peak = bd.wien_peak_um(T)
    where = "inside" if 0.75 <= peak <= 5.0 else ("redward of" if peak > 5 else "blueward of")
    print(f"T = {T:5d} K   peak at {peak:5.2f} um   ({where} the SPHEREx range)")
"""),
        md("""
Notice: for L dwarfs (≈1300–2500 K) the peak sits *inside* the SPHEREx range. For Y dwarfs and the
very coldest T dwarfs (below about 580 K) the peak is beyond 5 µm, so **everything SPHEREx sees is blueward
of the peak** — on the steep side. That matters a lot, as the next section shows.

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
Blueward of the peak, B<sub>λ</sub> falls off *exponentially*
(∝ e<sup>−hc/λkT</sup>), so a modest temperature contrast becomes an **enormous flux contrast**.
Redward of the peak the dependence is gentler. This is why:

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
axes[1].invert_yaxis()      # flipped so that down = hotter = deeper in the atmosphere
axes[1].set_ylabel("brightness temperature [K]\\n(flipped: down = hotter = deeper)"); axes[1].set_xlabel("Wavelength [µm]")
axes[0].set_title(f"{spec.name}, assuming R = {RADIUS_RJUP} R_Jup");
"""),
        md("""
Read the bottom panel like a map of *depth*. Its axis is **flipped**, so that **lower on the plot = hotter =
deeper in the atmosphere** ("hotter means deeper"). Where T<sub>b</sub> is high (the curve dips down), we see light from
deep, hot layers; these wavelengths are called **windows**. Where T<sub>b</sub> is low (the curve rises), something absorbs
the deep light and we only see cooler, higher layers. Notebook 2 explains why.

**A caution:** comparing fluxes at different
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
∝ 1/R², a smaller radius means more surface flux and a higher T<sub>b</sub>. The shift in kelvin is larger
redward, where B<sub>λ</sub> depends less steeply on T, so a given flux change needs a bigger
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
         "Blueward of the peak, flux depends exponentially on temperature: small ΔT, huge flux ratio.",
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
            "explain optical depth and the τ ≈ 2/3 photosphere, and what the flux at a wavelength tells you about temperature",
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

**What the flux tells you:** the flux at each wavelength tells you the approximate **temperature of the layer
where τ = 2/3** at that wavelength. A hot layer gives a lot of flux; a cool layer gives little.

**Pressure as depth.** Atmospheric scientists use **pressure as a stand-in for depth**: pressure rises steadily as
you go down, so **higher pressure = deeper in the atmosphere**. The plots below put high pressure at the bottom, so
down on the plot is down into the atmosphere.
"""),
        code("""
fig, ax = plt.subplots()
ax.plot(std.wave_um, std.photosphere_bar, color="k")
ax.set_yscale("log"); ax.invert_yaxis()
ax.set_xlabel("Wavelength [µm]"); ax.set_ylabel("pressure where τ = 2/3 [bar]\\n(higher pressure = deeper)")
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
### Check: does the flux really tell you the temperature at τ = 2/3?
Look up the temperature at each wavelength's τ = 2/3 level and compare it with the toy spectrum's
brightness temperature (notebook 1).
"""),
        code("""
t_at_photosphere = np.interp(np.log(std.photosphere_bar), np.log(std.pressure_bar), std.temperature_k)
fig, ax = plt.subplots()
ax.plot(std.wave_um, std.brightness_temp_k, label="brightness temperature of the toy spectrum")
ax.plot(std.wave_um, t_at_photosphere, "--", label="temperature at the τ = 2/3 level")
ax.invert_yaxis()     # flipped, as in notebook 1: down = hotter = deeper
ax.set_xlabel("Wavelength [µm]"); ax.set_ylabel("temperature [K]\\n(flipped: down = hotter = deeper)"); ax.legend()
ax.set_title("TOY: brightness temperature vs temperature at τ = 2/3", fontsize=10);
"""),
        md("""
Over most of the spectrum the two curves track each other closely: **brightness temperature ≈ temperature of
the layer you see.** That is the bridge between notebook 1 and the rest of the course.

Where they disagree — the short-wavelength windows, below about 2 µm — the spectrum is *hotter* than the τ = 2/3
layer. Notebook 1 explains why: on the steep side of the Planck curve, slightly deeper (hotter) layers are so much
brighter that they contribute more than their share, so the light comes from a bit below τ = 2/3. You can see this
in the contribution function above: in those windows the dark band sits below the cyan line. "Flux tells you the
temperature at τ = 2/3" is a rule of thumb, not an exact law.

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
axes[1].invert_yaxis()
axes[1].set_ylabel("brightness temperature [K]\\n(flipped: down = hotter)"); axes[1].set_xlabel("Wavelength [µm]")
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
axes[1].invert_yaxis()
axes[1].set_ylabel("brightness temperature [K]\\n(flipped: down = hotter)"); axes[1].set_xlabel("Wavelength [µm]")
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
ax.invert_yaxis()     # down = hotter = deeper, so the curve rises as we see higher, cooler layers
ax.set_xlabel("CH4 multiplier (log scale)"); ax.set_ylabel("brightness temperature at 3.32 µm [K]\\n(flipped: down = hotter)")
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
         "The flux at a wavelength tells you the approximate temperature at that wavelength's τ = 2/3 level.",
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
            "read plots with the absorption bands shaded",
            "define a band, a window, a band's core and wings, and collision-induced absorption",
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

### Words we will use
* A **band** is a range of wavelengths where a molecule absorbs strongly. It shows up as a **trough** in the spectrum.
* A **window** is a range *between* bands where little absorbs. There we see deep, hot layers, so the spectrum
  **peaks** — the Y, J, H, K and 4 µm peaks are all windows.
* **H<sub>2</sub> collision-induced absorption (CIA).** A single H<sub>2</sub> molecule barely absorbs infrared light. But
  while two molecules (H<sub>2</sub>–H<sub>2</sub> or H<sub>2</sub>–He) are colliding, the pair can absorb. Because it needs
  collisions, CIA is strongest where the gas is densest (deep down, and in high-gravity objects). It is broad and
  smooth, with no sharp edges, spread over roughly 1.7–3 µm.
"""),
        code("""
# ✏️ SETTINGS YOU CAN CHANGE
SPECTRAL_TYPE = "L8"
SHOW_UNCERTAIN = False
"""),
        code("""
spec = bd.load_reference(SPECTRAL_TYPE)
fig, ax = bd.plot_spectrum(spec, log=True, include_uncertain=SHOW_UNCERTAIN,
                           title=f"{spec.name} with its absorption bands shaded")
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
others = [lab for lab in labels if lab != "all"]
fig, axes = plt.subplots(1 + len(others), 1, sharex=True, figsize=(9, 9.5),
                         gridspec_kw={"height_ratios": [2.2] + [0.75] * len(others), "hspace": 0.12})
axes[0].plot(r1.spherex_wave_um, full, "k-o", ms=2, label="all toy absorbers")
for ax, lab in zip(axes[1:], others):
    f = r1.spherex_flux[labels.index(lab)]
    name = lab[3:]
    c = bd.molecule_color(name)
    axes[0].plot(r1.spherex_wave_um, f, color=c, lw=1.2, label=lab)
    kept = full / f                      # fraction of the light that gets through this absorber
    ax.fill_between(r1.spherex_wave_um, kept, 1, color=c, alpha=0.5, lw=0)
    ax.plot(r1.spherex_wave_um, kept, color=c, lw=1.2)
    ax.set_ylim(0, 1.05); ax.set_yticks([0, 1])
    ax.text(1.01, 0.5, name.replace("_", " "), transform=ax.transAxes, color=c, fontweight="bold", va="center")
axes[0].set_yscale("log"); axes[0].legend(ncol=3, fontsize=8); axes[0].set_ylabel(r"$F_\\lambda$ (toy)")
axes[len(others) // 2 + 1].set_ylabel("fraction of light that gets through\\n(filled dip = light this absorber takes out)")
axes[-1].set_xlabel("Wavelength [µm]")
axes[0].set_title("TOY: footprint of each absorber", fontsize=10);
"""),
        md("""
Each lower row is one absorber's **footprint**: the fraction of the light that still gets through when that
absorber is added to all the others. **1 = it takes out nothing; a filled dip = light it takes out**, and a dip all the
way to 0 means it blocks almost all the light there. The top panel shows the same thing as spectra: the coloured
curves are the spectrum with one absorber removed, and the black curve has all of them.

## 3. Trap 1 — overlapping bands

Look at 1.1–1.2 µm and 2.2–2.5 µm in the footprint plot: more than one absorber takes out light there.
When bands overlap, a deeper trough doesn't tell you *which* absorber changed. In real spectra:

* 1.1–1.2 µm: H<sub>2</sub>O and (in T dwarfs) CH<sub>4</sub>;
* 2.2–2.5 µm: CH<sub>4</sub>, CO, and H<sub>2</sub> collision-induced absorption (CIA);
* 3–3.6 µm: CH<sub>4</sub> on the wing of the broad 2.7 µm H<sub>2</sub>O band.

Always check the atlas for *every* absorber in a region before naming one.

## 4. Trap 2 — band wings reach into the windows

### Core, wings and broadening
A band absorbs most strongly at its **core**. Away from the core the absorption gets weaker, but it does not stop
abruptly: these weak tails on either side are the band's **wings**, and they can stretch well into a neighbouring
window. Wings come mainly from **pressure broadening**: molecules that collide often — at high pressure, deep in the
atmosphere — absorb over a wider range of wavelengths, so the band spreads out.

Here is a single made-up band at two pressures. The top panel shows how strongly it absorbs; the bottom panel shows
what fraction of the light gets through.

> 🧸 **TOY** — one invented band, to show the shapes. Real bands are many overlapping lines.
"""),
        code("""
lam = np.linspace(1.0, 2.0, 2000)          # microns
centre = 1.40

def toy_band(width, wing=0.01):
    x = (lam - centre) / width
    return np.exp(-0.5 * x**2) + wing / (1 + x**2)     # strong core + weak, wide wings

fig, axes = plt.subplots(2, 1, sharex=True, figsize=(9, 7))
for width, label, c in [(0.03, "low pressure", bd.LINE_COLORS[1]), (0.06, "high pressure (broadened)", bd.LINE_COLORS[2])]:
    tau = 300 * toy_band(width)            # optical depth of the band
    axes[0].plot(lam, tau, color=c, label=label)
    axes[1].plot(lam, np.exp(-tau), color=c, label=label)
for ax in axes:
    ax.axvspan(1.60, 1.75, color="0.85", zorder=0)
axes[0].set_yscale("log"); axes[0].set_ylim(1e-2, 1e3)
axes[0].set_ylabel("absorption strength\\n(optical depth τ)"); axes[0].legend(loc="upper left")
axes[1].set_ylabel("fraction of light\\nthat gets through"); axes[1].set_xlabel("Wavelength [µm]")
axes[1].text(1.40, 0.06, "core:\\nalmost no light\\ngets through", ha="center", va="bottom", fontsize=9)
axes[1].annotate("wings: weaker absorption\\nspreading out to the sides", (1.52, 0.6), (1.77, 0.3),
                 fontsize=9, arrowprops=dict(arrowstyle="->"))
axes[0].text(1.675, 100, "a neighbouring\\nwindow", ha="center", va="center", fontsize=9, color="0.3")
axes[0].set_title("TOY: one absorption band, its core and wings", fontsize=10);
"""),
        md("""
The core is so strong that it lets almost nothing through at either pressure (it is *saturated*, notebook 2). The
wings are what change: at high pressure they reach further and take out part of the light in the neighbouring window.

Back to the footprint plot: the dips are not zero in the windows. H<sub>2</sub>O takes out part of the light at the J and H
peaks too, because the wings of its bands reach into those windows. **The height of a window peak depends on its
neighbours.**
"""),
        code("""
for target in [1.27, 1.60, 4.00]:
    i = np.argmin(abs(r1.spherex_wave_um - target))
    taken = {lab[3:]: f"{(1 - full[i] / f[i]) * 100:.0f}%" for lab, f in zip(labels, r1.spherex_flux) if lab != "all"}
    print(f"window at {target} um - share of the light each absorber takes out:", taken)
"""),
        md("""
## 5. Trap 3 — depth tracks absorption, not abundance

From notebook 2: band depth grows roughly with the *log* of the absorber amount and saturates. So when two
spectra differ in a band, say "**more absorption** at 3.3 µm", not "more methane".

A second reason to be careful: a deeper band does not even have to come from that molecule. Below, we take the
toy atmosphere (T<sub>eff</sub> = 1000 K) and change it in two different ways:

* **top panel:** make the whole atmosphere cooler (T<sub>eff</sub> = 900 K);
* **bottom panel:** keep the temperature, but triple the CH<sub>4</sub> absorption.

Each curve is the **changed spectrum divided by the original**: 1 = no change, below 1 = fainter than before. The
shading shows the absorption bands, as in every plot. **Predict:** which change makes the spectrum fainter
everywhere, and which only in certain bands?
"""),
        code("""
tv = bd.load_toy("temp_vs_absorber")
base = tv.spherex_flux[0]
fig, axes = plt.subplots(2, 1, sharex=True, figsize=(9, 7))
for ax, k, what, c in [(axes[0], 1, "cooler atmosphere (1000 K -> 900 K): a GLOBAL change", bd.LINE_COLORS[1]),
                       (axes[1], 2, "3 x more CH4 absorption, same temperature: a LOCAL change", bd.LINE_COLORS[5])]:
    bd.shade_bands(ax)
    ax.plot(tv.spherex_wave_um, tv.spherex_flux[k] / base, "o-", ms=3, color=c)
    ax.axhline(1, color="0.4")
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("changed / original")
    ax.text(0.01, 0.04, what, transform=ax.transAxes, fontsize=10, color=c, fontweight="bold")
bd.add_band_key(axes[0])
axes[1].set_xlabel("Wavelength [µm]")
axes[0].set_title("TOY: two ways to change a spectrum", fontsize=10, pad=24);
"""),
        md("""
The cooler atmosphere (top) is fainter at **every** wavelength — most in the blue, where the Planck function is
steepest (notebook 1) — and the bands change depth too: a **global** change. The extra CH<sub>4</sub> (bottom) changes the
spectrum **only inside the CH<sub>4</sub> bands** (orange shading): a **local** change.

So: a difference confined to one absorber's bands points to that absorber; a difference everywhere points to
temperature or another global parameter (notebook 5). Real objects often have both at once.
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
         "Bands are troughs where a molecule absorbs; windows are the peaks between them, where we see deep.",
         "Footprints show where an absorber takes out light.",
         "A band has a strong core and weaker wings; pressure broadening spreads the wings into neighbouring windows.",
         "Bands overlap, and band wings set the height of window peaks.",
         "Temperature changes many bands at once; one absorber changes only its own bands.",
         "Field guide: [Band atlas](../field_guide/band_atlas.md)"],
        [("Name the absorbers that could deepen the trough near 1.15 µm in a T dwarf.", "H<sub>2</sub>O and CH<sub>4</sub>."),
         ("Why can removing H<sub>2</sub>O change the J-peak flux?", "The wings of neighbouring H<sub>2</sub>O bands reach into the J window."),
         ("What is H<sub>2</sub> CIA, and why is it stronger in high-gravity objects?",
          "Absorption by pairs of colliding H<sub>2</sub> molecules. It needs collisions, so it is strongest in dense gas — and high gravity means denser gas at the photosphere."),
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
        md("""
Twenty-three spectra on one plot are unreadable, so — like Rustamkulov et al. — we split the sequence in two:
the **L dwarfs**, then the **T and Y dwarfs**. Each spectrum is divided by its own peak flux, so every curve runs from
0 to 1, and the curves are stacked with the earliest type on top. Colours run through the whole sequence, so the
same colour means the same type in every plot.
"""),
        code("""
# ✏️ SETTINGS YOU CAN CHANGE
OFFSET = 1.0                  # vertical spacing between stacked spectra (1 = no overlap)
NORMALIZE_AT = (1.20, 1.30)   # used further down: the J peak, to compare two spectra's shapes
"""),
        code("""
seq = bd.load_sequence()
types = [s.meta["spectral_type"] for s in seq]
colour_of = dict(zip(types, plt.cm.viridis(np.linspace(0, 0.9, len(seq)))))
groups = {"L dwarfs": [s for s in seq if s.meta["spectral_type"].startswith("L")],
          "T and Y dwarfs": [s for s in seq if not s.meta["spectral_type"].startswith("L")]}
for name, grp in groups.items():
    labs = [s.meta["spectral_type"] for s in grp]
    fig, ax = bd.plot_spectrum(grp, normalize_at="peak", offset=OFFSET, errors=False, figsize=(9, 1.0 + 0.8 * len(grp)),
                               colors=[colour_of[t] for t in labs], labels=labs, inline_labels=True,
                               title=f"{name}: each scaled to its own peak, stacked")
"""),
        md("""
The same spectra on a **log** axis (not stacked), which shows the faint 3–5 µm region better:
"""),
        code("""
for name, grp in groups.items():
    labs = [s.meta["spectral_type"] for s in grp]
    fig, ax = bd.plot_spectrum(grp, log=True, normalize_at="peak", errors=False, figsize=(9, 6),
                               colors=[colour_of[t] for t in labs], labels=labs,
                               title=f"{name} on a log axis (each scaled to its own peak)")
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
fig, ax = plt.subplots(figsize=(9, 6))
for s in seq:
    surf = bd.observed_to_surface(s.flux, s.meta["distance_pc"], radius_rjup=1.0)
    ax.plot(s.wave_um, bd.brightness_temperature(s.wave_um, surf), color=colour_of[s.meta["spectral_type"]],
            label=s.meta["spectral_type"])
ax.invert_yaxis()      # as in notebook 1: down = hotter = deeper
ax.set_xlabel("Wavelength [µm]")
ax.set_ylabel("brightness temperature [K], R = 1 R_Jup assumed\\n(flipped: down = hotter = deeper)")
ax.legend(ncol=2, fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1.0))
ax.set_title("Brightness temperature along the sequence");
"""),
        md("""
**Look at the L0 curve just blueward of 4 µm (near 3.85 µm).** One point sits far up the plot: by its brightness
temperature, the L0 — the *hottest* object in the sequence — would be colder there than several T dwarfs. Could that be
real? Think about it before you open the answer.
""" + answer("""
No. An L0 has no absorber strong enough at 3.85 µm to hide its deep, hot layers — that wavelength is right next to
the 4 µm window, where we see deepest. And only **one** channel is affected; its neighbours look normal. A single point
that disagrees with its neighbours *and* with the physics is almost certainly a **bad measurement**, not the object.
Notebook 6 (section 9) shows how to check for these, and you will meet this same point again there, where it spoils a
model fit. **Before explaining a feature, ask whether it is real.**
""")),
        md("""
## 3. Spectral indices

A **spectral index** turns a feature you would otherwise judge by eye into **one number**. It compares the flux
*inside* a band with the flux in a nearby **reference region** where little absorbs:

  I = −2.5 log<sub>10</sub>(F<sub>band</sub> / F<sub>reference</sub>).

The −2.5 log<sub>10</sub> makes it a *magnitude*, astronomers' usual brightness scale: **0 = no band, bigger = deeper band**.

What indices are for:

* an index comes with an **uncertainty**, so you can say whether two objects *really* differ;
* it is easy to **track along a sequence** (as below) and to compare many objects at once;
* it can be computed in exactly the same way for **data and models**, so you can ask whether a model gets one
  particular band right (notebook 6).

Rustamkulov et al. (2026, Table 5) define three indices for SPHEREx, all measured against the 3.70–4.14 µm region (the
4 µm peak): **CH<sub>4</sub>** (the 3.3 µm band), **CO<sub>2</sub>** (4.3 µm) and **CO** (4.6 µm). Details in notebook 6 and the
[field guide](../field_guide/indices.md).
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

You will often need to judge between neighbouring subtypes (is it an L8 or an L9?). Overlay two
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
    names = {"L": "mid/late-L", "T_early": "early-T", "T_late_Y": "late-T/Y"}
    sweep_cell = lambda base, par, lab: code(f"""
r = bd.optional(bd.load_sweep, "{base}", "{par}")
if r is not None:
    baseline, members = r
    bd.plot_parameter_stack(baseline, members, "{par}", value_label="{lab}", log=True,
                            title="{names[base]} baseline model: only {lab} changes")
""")
    cells = [
        header(owner, f, "5 · Global atmospheric parameters", [
            "say what effective temperature, gravity, metallicity, clouds, and vertical mixing each do to a spectrum",
            "read a parameter stack and a ratio-to-baseline plot",
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
| Clouds | f<sub>sed</sub> | how quickly cloud particles **rain out**: large f<sub>sed</sub> = fast, so thin clouds; small f<sub>sed</sub> = slow, so thick, extended clouds; "nc" = cloud-free (section 5) |
| Vertical mixing | K<sub>zz</sub> | how fast gas is stirred up and down inside the atmosphere (section 6) |

We use a curated subset of model grids: **Sonora Diamondback** (cloudy, equilibrium chemistry; L and T),
**Sonora Flame Skimmer** (cloud-free, disequilibrium chemistry with a K<sub>zz</sub> axis; late T and Y) and **Exo-REM**
(clouds and disequilibrium chemistry). Only Flame Skimmer's 500–550 K models have been downloaded so far, so its
temperature sweep is narrow.
The models were averaged to modest resolution (R ~ 500) once, by your instructor. **Never compare a high-resolution
model directly with SPHEREx data** — bdtools always bins it onto the data's own channels first (notebook 6).

The library is organised around three **baseline** models — a typical mid/late-L dwarf, an early-T dwarf and a
late-T/Y dwarf. Each **sweep** starts from a baseline and changes only *one* parameter, keeping the rest fixed.
"""),
        code("""
lib = bd.optional(bd.list_models)
lib if lib is None else lib[lib["sweep"] == "baseline"]
"""),
        md("""
Each plot below has two panels: the spectra (thick line = baseline) and each model **divided by the baseline**,
with the absorption bands shaded. The ratio panel is where you read the effect of a parameter.

## 2. Effective temperature

**Predict:** a cooler model at the same gravity — will it be fainter everywhere by the same factor?
"""),
        sweep_cell("L", "teff", "Teff [K]"),
        sweep_cell("T_early", "teff", "Teff [K]"),
        md("""
Temperature is a **global** parameter: it changes the overall slope (Planck, notebook 1) *and* the depths of
many bands at once, because the chemistry and the temperature profile both change.

**Careful: "only T<sub>eff</sub> changes" describes the model's inputs, not its physics.** A grid lets you lower T<sub>eff</sub>
while holding the other *numbers* fixed, but the atmosphere itself still changes in ways that are not held fixed.
For example, as an L dwarf cools, its silicate clouds form deeper and eventually sink below the layers we see (they
**rain out** of view), and carbon shifts from CO toward CH<sub>4</sub>. So one step in T<sub>eff</sub> can carry a change in clouds
and chemistry along with it.

## 3. Surface gravity
"""),
        sweep_cell("L", "logg", "log g"),
        sweep_cell("T_early", "logg", "log g"),
        md("""
Higher gravity means higher pressure at the photosphere, which strengthens pressure-dependent absorption such as
H<sub>2</sub> CIA (≈1.7–3 µm; notebook 3). Watch the K-band region. The observed signs of **low gravity** (Rustamkulov et al.
2026): a shallower 0.75–1.2 µm slope, weaker water features, and a taller K peak relative to H.

**Gravity is a tricky parameter to fit.** Its effects are modest, and other parameters can produce similar ones. When
two different parameter changes produce nearly the **same** change in the spectrum, they are **degenerate**: the data
cannot tell them apart, so a fit can trade one for the other — for example, a slightly different temperature,
metallicity or cloud thickness can partly mimic a change in gravity. Section 9 shows an example. Expect a fitted
log g to be uncertain.

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

**What f<sub>sed</sub> means.** Cloud particles are always being lifted by the moving gas and are always settling back
down under gravity. f<sub>sed</sub> (the *sedimentation efficiency*) says how quickly they settle — how fast the clouds
**rain out**:

* **large f<sub>sed</sub>:** particles grow big and rain out quickly, so the cloud is thin and stays in a narrow layer near
  where it forms;
* **small f<sub>sed</sub>:** particles stay small and are carried high before they fall, so the cloud is thick and extends
  far up — where it blocks more of the light from below.

## 6. Vertical mixing (K<sub>zz</sub>)

The atmosphere is not still: convection and turbulence keep carrying gas up and down. This is **vertical mixing**,
and K<sub>zz</sub> measures how fast it happens (we quote log<sub>10</sub> K<sub>zz</sub>, with K<sub>zz</sub> in cm² s⁻¹; bigger = faster).

Why it matters: which molecules are present depends on temperature. Deep down it is hot, and carbon is mostly in
**CO**; high up it is cold, and carbon "wants" to be in **CH<sub>4</sub>**. Converting CO into CH<sub>4</sub> takes time. If mixing
lifts gas faster than that conversion can happen, CO survives up into the cold layers we see. The atmosphere then
has more CO (and less CH<sub>4</sub>) than equilibrium chemistry predicts — this is **disequilibrium chemistry**. Stronger
mixing means more of it.
"""),
        sweep_cell("T_late_Y", "kzz", "log Kzz"),
        md("""
Stronger mixing dredges up CO (and CO<sub>2</sub>) from hot deep layers faster than chemistry can convert it to CH<sub>4</sub>,
so the 4.3–4.9 µm notches deepen and the 3.3 µm CH<sub>4</sub> band changes. The Diamondback grid assumes equilibrium
chemistry and has no K<sub>zz</sub> axis.

The late-T/Y baseline's other sweeps:
"""),
        sweep_cell("T_late_Y", "teff", "Teff [K]"),
        sweep_cell("T_late_Y", "logg", "log g"),
        md("""
## 7. Grids disagree

Even with the **same** parameters, different grids differ by up to about a factor of 2 at some wavelengths
(Rustamkulov et al. 2026). And even the best-matching model rarely reproduces a real spectrum within its
uncertainties (notebook 6). **Treat parameters read off a model grid as rough.**

"Same parameters" means the same *numbers*, not the same physics: each grid has its own cloud recipe (so
f<sub>sed</sub> = 4 in one grid is not the same cloud as f<sub>sed</sub> = 4 in another), its own chemistry
(Diamondback assumes equilibrium; Exo-REM includes disequilibrium chemistry), and its own opacities. The Exo-REM
spectra in this library also start near 0.93 µm, so the shortest wavelengths show only one grid.
"""),
        code("""
lib = bd.optional(bd.list_models)
if lib is not None:
    for base in lib["baseline"].unique():
        cg = lib[(lib["baseline"] == base) & (lib["sweep"] == "cross_grid")]
        b0 = lib[(lib["baseline"] == base) & (lib["sweep"] == "baseline")]
        if cg.empty or b0.empty:
            continue
        a = bd.at_spherex_resolution(bd.load_model(b0.iloc[0]["id"]))
        b = bd.at_spherex_resolution(bd.load_model(cg.iloc[0]["id"]))
        fig, ax = bd.plot_spectrum([a, b], log=True, title=f"{base}: two grids, same nominal parameters (SPHEREx resolution)")
        print(base, "largest ratio between the grids:", round(float(np.nanmax(a.flux / b.flux)), 2),
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

Two parameters are **degenerate** when changing either one changes the spectrum in nearly the same way (section 3).
Here we take a baseline model and change it in two different ways — make it **cooler**, or give it **higher
gravity** — and ask: could you tell which one happened?

Both changed models are scaled to match the baseline at the J peak, so only their *shapes* differ. In the bottom
panel, each changed model is divided by the baseline: 1 = same shape as the baseline.
"""),
        code("""
# ✏️ SETTINGS YOU CAN CHANGE
BASELINE = "L"            # "L" (mid/late-L) or "T_early" (early-T): try both
"""),
        code("""
lib = bd.optional(bd.list_models, baseline=BASELINE)
if lib is not None and not lib.empty:
    base = bd.load_model(lib[lib["sweep"] == "baseline"].iloc[0]["id"])
    cool = lib[(lib["sweep"] == "teff") & (lib["teff"] < base.meta["teff"])].sort_values("teff").tail(1)
    heavy = lib[(lib["sweep"] == "logg") & (lib["logg"] > base.meta["logg"])].sort_values("logg").head(1)
    if not cool.empty and not heavy.empty:
        b = bd.at_spherex_resolution(base)
        c = bd.at_spherex_resolution(bd.load_model(cool.iloc[0]["id"]))
        h = bd.at_spherex_resolution(bd.load_model(heavy.iloc[0]["id"]))
        at_j = lambda s: s.flux / np.nanmean(s.flux[(s.wave_um >= 1.2) & (s.wave_um <= 1.3)])
        lab_b = f"baseline: T_eff = {b.meta['teff']:g} K, log g = {b.meta['logg']:g}"
        lab_c = f"cooler: T_eff = {c.meta['teff']:g} K"
        lab_h = f"higher gravity: log g = {h.meta['logg']:g}"
        fig, axes = plt.subplots(2, 1, sharex=True, figsize=(9, 8), gridspec_kw={"height_ratios": [2, 1.6]})
        for ax in axes:
            bd.shade_bands(ax)
        bd.add_band_key(axes[0])
        axes[0].plot(b.wave_um, at_j(b), color="k", lw=2.2, label=lab_b)
        axes[0].plot(c.wave_um, at_j(c), color=bd.LINE_COLORS[1], lw=1.4, label=lab_c)
        axes[0].plot(h.wave_um, at_j(h), color=bd.LINE_COLORS[2], lw=1.4, label=lab_h)
        axes[0].set_yscale("log"); axes[0].set_ylabel("flux / flux at the J peak"); axes[0].legend(fontsize=8)
        axes[1].plot(c.wave_um, at_j(c) / at_j(b), "o-", ms=3, color=bd.LINE_COLORS[1], label=lab_c)
        axes[1].plot(h.wave_um, at_j(h) / at_j(b), "o-", ms=3, color=bd.LINE_COLORS[2], label=lab_h)
        axes[1].axhline(1, color="0.4")
        axes[1].set_ylabel("changed / baseline\\n(both = 1 at the J peak)"); axes[1].legend(fontsize=8)
        axes[1].set_xlabel("Wavelength [µm]"); axes[1].set_xlim(0.7, 5.1)
        axes[0].set_title("Cooler, or higher gravity? Both scaled to match the baseline at the J peak", fontsize=11, pad=24)
"""),
        md("""
Read the bottom panel. **Where the two curves move together**, a cooler object and a higher-gravity object look the
same: those wavelengths cannot tell the two apart (degenerate). **Where the curves split**, the data *can* tell them
apart — those are the wavelengths that break the degeneracy. Which bands are they, and which absorbers sit there?

For the mid/late-L baseline, both changes make the spectrum redder relative to J over most of the range — a partial
degeneracy. Now set `BASELINE = "T_early"` and re-run: for the early-T model the two changes look quite different.
**Whether two parameters are degenerate depends on the kind of object**, which is one reason fitted parameters are
more trustworthy for some objects than for others.

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
         "Grids with the same parameters can differ by ~2×, and no model matches a real spectrum perfectly: treat parameters as rough.",
         "Holding the other numbers fixed does not hold the physics fixed (e.g. clouds rain out of view as T<sub>eff</sub> drops).",
         "Degeneracy: two parameter changes that look alike. Gravity is especially hard to pin down; look for bands that respond differently.",
         "Field guide: [Global parameters](../field_guide/parameters/README.md)"],
        [("Which parameter changes the spectrum most globally?", "Effective temperature."),
         ("Name one observed sign of low gravity.", "A shallower 0.75–1.2 µm slope, weaker water features, or a taller K peak relative to H."),
         ("What does vertical mixing do to CO in a cold atmosphere?", "Brings it up from hot deep layers faster than it converts to CH<sub>4</sub>, so more CO absorption."),
         ("Why does a small f<sub>sed</sub> mean thick clouds?", "Particles rain out slowly, so they stay aloft and spread high into the atmosphere."),
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
            "tell a model problem from something peculiar about one object, by comparing with the template for its spectral type",
            "compare indices between a spectrum and its best-fit model, and list what can mimic a chemistry difference",
            "recognize data problems before interpreting a feature",
        ], 75),
        setup_cell(owner),
        md("""
## 1. How a model fit works

A brown dwarf you look at usually already has a spectral type, so the question is not *what type is it?* but *how well
do models describe it, and where do they fail?* Here we practise on the references, whose types and distances we know.

**Step 1 — put the model on the data's wavelengths.** A model spectrum is computed at thousands of wavelengths;
SPHEREx measures 102 channels, each covering a small range of wavelengths. The two don't line up, so we **always
adjust the model to fit the data, never the other way round**: for each SPHEREx channel we average the model over the
wavelengths that channel covers.

**Step 2 — scale the model.** A model gives the light leaving the object's surface; we see the object from far away,
so it looks much fainter. We multiply the model by one number, the **scale factor**, chosen to make it match the data
as closely as possible.

**Step 3 — measure how well it matches.** "As closely as possible" means the scale that **minimizes a statistic**.
We use the **reduced χ²** ("chi-squared"): for each channel, take the difference between data and model, divide it by
the uncertainty, square it, and average over all channels. If the model matched perfectly apart from noise, reduced
χ² would be about 1; bigger means a worse match. **G<sub>k</sub>** (Cushing et al. 2008) is a similar statistic that gives wider
channels more weight. For both, **lower is better**. (Following Rustamkulov et al. 2026, we first add a 3% allowance to
every uncertainty for calibration errors.)

**Step 4 — repeat for every model in a grid**, and rank them. Our grid is Sonora Diamondback (Morley et al. 2024): 1440
models covering T<sub>eff</sub>, log g, [M/H] and clouds (f<sub>sed</sub>, or "nc" = cloud-free).
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
Read the two lower panels with the band atlas in mind. The pale **coloured shading in every panel marks the absorption
bands** (the key above the plot says which colour is which molecule):

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

## 6. Is it the object or the models? Compare with the template

A brown dwarf you look at usually already has a spectral type, and each spectral type has a **template**: a reference
spectrum of that type (here, the reference sequence from notebook 4). Fit both the object and its template with the
same grid, and compare their residuals:

* a residual pattern the template **shares** is a **model problem** — the models get every object of that type wrong
  in the same way;
* a residual pattern only your object shows is something about **the object** worth explaining.

Here we practise with the data spectrum and its neighbours in the sequence, which all play the role of the template.
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

Real spectra contain spurious points even after cleaning (Rustamkulov et al. 2026), and spectra from different
sources are cleaned unevenly. Before interpreting any feature, run a quality check. `bd.quality_report` flags points far from a running
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

You now have the skills to examine a real brown-dwarf spectrum: reading a spectrum, the band atlas, the sequence,
the effect of each parameter, model fits with uncertainties, comparing with the template for its type, indices, and
data-quality checks. The next step, which your instructor will give you, applies them to real SPHEREx spectra and asks
you to explain, in words, where and why an object departs from its best-fit model.

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
An object's CO<sub>2</sub> index is 0.15 ± 0.04 mag larger than its best-fit model's, and the template for its type shows no
such difference. List three explanations other than "more CO<sub>2</sub>".
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
         "Residuals shared with the template are model problems; residuals only your object shows are worth explaining.",
         "Temperature, gravity, metallicity, clouds, mixing, the models, and binarity can all mimic a chemistry difference.",
         "Check for outliers, gaps, uneven sampling, and contamination before interpreting any feature.",
         "Field guide: [Indices](../field_guide/indices.md), [Data problems](../field_guide/data_problems.md)"],
        [("Why is each model averaged onto the data's channels before fitting?",
          "SPHEREx blurs narrow model features together; comparing an unbinned model with SPHEREx data is not fair."),
         ("What does a long dark valley in a χ² map mean?", "The two parameters trade off (a degeneracy); the data do not pin down either alone."),
         ("A residual appears in an object and in its template. What is the likely cause?",
          "The models — they get every object of that type wrong in the same way."),
         ("When is the CH<sub>4</sub> index not meaningful?", "For Y dwarfs (CH<sub>4</sub> undetected at SPHEREx sensitivity)."),
         ("What does an isolated outlier look like in a significance plot?", "A single large spike with normal neighbours, often outside any band.")],
        "ask your instructor for the next step.")
    return f, cells


NOTEBOOKS = [nb00, nb01, nb02, nb03, nb04, nb05, nb06]

NB_LINK = re.compile(r"\]\((0\d_[A-Za-z0-9_]+\.ipynb)\)")
FIELD_GUIDE_LINK = re.compile(r"\]\(\.\./field_guide/([^)\s]+)\)")


def absolute_links(text, owner):
    """Point notebook and field-guide links at GitHub/Colab.

    A relative link such as (01_blackbodies.ipynb) only works in the original
    notebook: in a student's "Copy of ..." in Google Drive it points nowhere.
    Absolute links work from any copy.
    """
    text = NB_LINK.sub(lambda m: f"](https://colab.research.google.com/github/{owner}/{REPO_NAME}/blob/{BRANCH}/"
                                 f"notebooks/{m.group(1)})", text)
    return FIELD_GUIDE_LINK.sub(lambda m: f"](https://github.com/{owner}/{REPO_NAME}/blob/{BRANCH}/"
                                          f"field_guide/{m.group(1)})", text)


def build(owner, execute=False, timeout=600):
    NB_DIR.mkdir(exist_ok=True)
    written = []
    for make in NOTEBOOKS:
        fname, cells = make(owner)
        for c in cells:
            if c.cell_type == "markdown":
                c.source = absolute_links(c.source, owner)
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
