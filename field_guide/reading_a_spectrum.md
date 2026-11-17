# Reading a spectrum in five steps

[← Field guide](README.md)

**0. Check the data first.** Isolated outlier points, gaps, uneven sampling, contamination?
→ [Spotting data problems](data_problems.md). Don't interpret a feature built on one bad point.

**1. Where is the flux?** Plot linear *and* log. Where is most of the light (linear)? How fast does
it fall toward 5 µm (log)? A bluer spectrum is hotter; Y dwarfs are detected reliably only beyond ~3.9 µm.
*(Notebooks 0–1)*

**2. Find the window peaks.** Y (~1.08 µm), J (~1.27 µm), H (~1.58 µm), K (~2.1 µm), and the 4 µm peak.
Compare their heights: is K below H (T0 and later)? Is H below J (T4 and later)? Is the 4 µm peak sharp
(L/T transition) or shifted redward (late T, Y)? *(Notebook 4)*

**3. Name the main troughs.** Use the [band atlas](band_atlas.md). H<sub>2</sub>O is everywhere; a downward curve at
3–3.6 µm means CH<sub>4</sub> (after L4); notches at 4.15–4.3 µm and 4.4–4.9 µm are CO<sub>2</sub> and CO (beyond L3).
Check *every* absorber that overlaps a region. *(Notebook 3)*

**4. Estimate the rough type.** Match steps 1–3 to the [sequence cheat sheet](spectral_sequence.md).
Give a range (e.g. "L6–L8") rather than one subtype; adjacent subtypes differ by only a few percent.

**5. Anything odd?** Compare with the reference of that type (ratio and significance plots). Is a difference
local (one absorber) or global (many bands and the slope)? List what could cause it —
[parameters](parameters/README.md), clouds, binarity, data problems — before naming one. Say "more absorption",
not "more abundance".
