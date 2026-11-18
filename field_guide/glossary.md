# Glossary

[← Field guide](README.md)

**Absorption (vs abundance).** A deeper band means *more absorption*. That can come from more of a molecule,
a different temperature profile, or both — and saturated bands hide abundance changes. Say "absorption".

**Band / window.** A band is a wavelength range where a molecule absorbs strongly (a trough). A window is a
range between bands with little absorption (a peak: Y, J, H, K, 4 µm), where we see deep, hot layers.

**Baseline model.** In notebook 5, the starting model of a sweep; each sweep changes one parameter from it.

**Blueward / redward.** Toward shorter / longer wavelengths (used even in the infrared).

**Collision-induced absorption (CIA).** Absorption by *pairs* of colliding molecules (here H<sub>2</sub>–H<sub>2</sub> and
H<sub>2</sub>–He) that a single molecule cannot do. Needs collisions, so it is strongest in dense gas (deep, high gravity).
Broad and smooth, ~1.7–3 µm.

**Core / wings.** A band absorbs most strongly at its core; its wings are the weaker absorption that extends to either
side, often into neighbouring windows.

**Brightness temperature (T<sub>b</sub>).** The temperature a blackbody would need to emit the observed surface flux
at one wavelength. ≈ the temperature of the layer you see there. *(Notebook 1)*

**Contribution function.** How much of the light at a wavelength comes from each layer. *(Notebook 2)*

**Degeneracy.** Two different parameter changes that change the spectrum in nearly the same way, so the data
cannot tell them apart (e.g. cooler vs higher gravity in some bands). *(Notebook 5)*

**Disequilibrium chemistry.** Chemistry set by mixing faster than reactions can keep up (see vertical mixing).

**Effective temperature (T<sub>eff</sub>).** Temperature of a blackbody emitting the same total power per area.

**F<sub>λ</sub>, F<sub>ν</sub>.** Flux per unit wavelength (W m⁻² µm⁻¹) and per unit frequency (Jy, 1 Jy = 10⁻²⁶ W m⁻² Hz⁻¹).

**G<sub>k</sub>.** A goodness-of-fit statistic (Cushing et al. 2008) like χ², but weighting each channel by its width.

**f<sub>sed</sub> (sedimentation efficiency).** How quickly cloud particles settle (rain out). Large f<sub>sed</sub> = thin,
compact clouds; small f<sub>sed</sub> = thick clouds extending high up. *(Notebook 5)*

**Index (spectral index).** One number for one band: a magnitude comparing the mean flux in a band with a nearby
reference region, I = −2.5 log<sub>10</sub>(F<sub>band</sub>/F<sub>ref</sub>); 0 = no band, bigger = deeper. Comes with an uncertainty, and is
computed the same way for data and models. *(Notebook 4, Indices page)*

**Opacity.** How strongly gas absorbs at a given wavelength.

**Optical depth (τ).** Number of absorption lengths between a layer and space; light from depth τ escapes with
probability ~e<sup>−τ</sup>. The flux at a wavelength tells you the approximate temperature where τ = 2/3.

**Photosphere.** The layer we see at a given wavelength, roughly where τ ≈ 2/3. It is at different heights at
different wavelengths.

**Pressure (as depth).** Atmospheres are described by pressure instead of height: higher pressure = deeper.

**Pressure broadening.** Frequent collisions (high pressure) widen a band, pushing more absorption into its wings.

**Ratio plot.** Data divided by a scaled template. Its look depends on how the template was scaled.

**Reduced χ².** Sum of squared (residual/σ) divided by the degrees of freedom; ≈ 1 for a perfect model with
correct errors. Brown dwarf model fits are typically ≥ 10.

**Residual / significance.** Residual = data − template. Significance = residual / σ (in units of the uncertainty).

**Resolution (R).** λ/Δλ: how finely a spectrum separates wavelengths. SPHEREx has R ~ 40 below ~4 µm and
~110–120 at 4–5 µm. Models must be averaged to SPHEREx resolution before comparing.

**Saturation.** When a band is so strong that adding more absorber barely deepens it.

**Template.** A spectrum (reference or model) compared with the data. Each spectral type has a template: the
reference spectrum of that type.

**χ² map.** For each pair of parameter values, the best χ²<sub>red</sub> of any model with those values. *(Model fits page)*

**Best-fit model.** The grid model with the lowest χ²<sub>red</sub> after scaling. *(Model fits page)*

**Thermal inversion.** Temperature rising with height; turns strong absorption bands into emission.

**Vertical mixing (K<sub>zz</sub>).** Convection and turbulence carrying gas up and down; K<sub>zz</sub> says how fast. Fast mixing
brings deep-layer molecules (CO) up before they can convert (to CH<sub>4</sub>): disequilibrium chemistry.

**Toy model.** A deliberately simplified calculation for ideas, never for numbers about real objects.
