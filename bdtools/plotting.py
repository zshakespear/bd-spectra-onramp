"""Plots used in every notebook.

All plots share one look: absorption bands from ``data/bands.yaml`` are
shaded behind the data in each molecule's colour, with a key above the plot;
lines use the colour-blind-safe Okabe & Ito palette, and sequences of
spectra use the perceptually uniform 'viridis' colour map.
"""

import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.legend import Legend
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter

from .errors import BDToolsError, MissingDataError
from .paths import BANDS_FILE

#: Okabe & Ito (2008) colour-blind-safe palette (black first).
LINE_COLORS = ["#000000", "#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]
DEFAULT_XLIM = (0.7, 5.1)
UNIT_LABELS = {
    "W/m2/um": r"$F_\lambda$ [W m$^{-2}$ $\mu$m$^{-1}$]",
    "Jy": r"$F_\nu$ [Jy]",
    "mJy": r"$F_\nu$ [mJy]",
}

_BANDS_CACHE = {}


def setup_style():
    """Readable defaults for a laptop screen."""
    plt.rcParams.update({
        "figure.figsize": (9, 4.8), "figure.dpi": 100, "font.size": 11,
        "axes.grid": True, "grid.alpha": 0.25, "axes.prop_cycle": plt.cycler(color=LINE_COLORS),
        "legend.fontsize": 9, "legend.framealpha": 0.85, "lines.linewidth": 1.6,
    })


# ------------------------------------------------------------------ bands
def load_bands(path=None):
    """The band atlas from ``data/bands.yaml`` (cached)."""
    path = BANDS_FILE if path is None else path
    if path not in _BANDS_CACHE:
        try:
            with open(path, encoding="utf-8") as fh:
                _BANDS_CACHE[path] = yaml.safe_load(fh)
        except FileNotFoundError:
            raise MissingDataError(f"Band atlas not found: {path}") from None
    return _BANDS_CACHE[path]


def molecule_color(name):
    """The colour used for an absorber everywhere (e.g. ``molecule_color("CH4")``)."""
    ab = load_bands()["absorbers"]
    if name not in ab:
        raise BDToolsError(f"'{name}' is not in the band atlas. Known: {', '.join(ab)}.")
    return ab[name]["color"]


def _select_absorbers(absorbers, include_uncertain):
    ab = load_bands()["absorbers"]
    if absorbers is None:
        names = [k for k, v in ab.items() if v.get("show_by_default", True) or include_uncertain]
    else:
        names = [absorbers] if isinstance(absorbers, str) else list(absorbers)
        bad = [n for n in names if n not in ab]
        if bad:
            raise BDToolsError(f"Not in the band atlas: {', '.join(bad)}. Known: {', '.join(ab)}.")
    return names, ab


def draw_molecule_bars(ax, absorbers=None, include_uncertain=False, xlim=None):
    """Draw one row of coloured bars per absorber on ``ax`` (a thin axis above a spectrum)."""
    names, ab = _select_absorbers(absorbers, include_uncertain)
    for row, name in enumerate(names):
        y = len(names) - 1 - row
        info = ab[name]
        for b in info["bands"]:
            lo, hi = b["range_um"]
            dashed = b.get("status") == "uncertain"
            ax.plot([lo, hi], [y, y], color=info["color"], lw=6, solid_capstyle="butt",
                    alpha=0.55 if dashed else 1.0, ls=(0, (2, 1)) if dashed else "-")
        ax.text(1.005, y, info.get("label", name), transform=ax.get_yaxis_transform(),
                va="center", ha="left", fontsize=9, color=info["color"], fontweight="bold")
    ax.set_ylim(-0.7, len(names) - 0.3)
    ax.set_yticks([])
    ax.grid(False)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    if xlim is not None:
        ax.set_xlim(*xlim)
    return names


BAND_ALPHA = 0.13
HATCH_ALPHA = 0.45    # strength of hatched bands (H2 CIA); hatching is thin, so it can be stronger than a fill
TITLE_PAD_WITH_KEY = 24      # points: room for the absorption-band key between the axes and the title


def shade_bands(ax, absorbers=None, include_uncertain=False, alpha=BAND_ALPHA):
    """Shade absorption bands behind the data, in each molecule's colour.

    Uncertain bands (only drawn when ``include_uncertain``) are hatched. An absorber with a
    ``hatch`` entry in bands.yaml (H2 CIA) is drawn as hatching only, with no fill, so the
    bands underneath keep their colours.
    """
    names, ab = _select_absorbers(absorbers, include_uncertain)
    for name in names:
        for b in ab[name]["bands"]:
            if ab[name].get("hatch"):
                ax.axvspan(*b["range_um"], facecolor="none", edgecolor=ab[name]["color"], alpha=HATCH_ALPHA,
                           lw=0, hatch=ab[name]["hatch"], zorder=0)
            elif b.get("status") == "uncertain":
                ax.axvspan(*b["range_um"], facecolor=ab[name]["color"], alpha=alpha, lw=0, hatch="//",
                           edgecolor=ab[name]["color"], zorder=0)
            else:
                ax.axvspan(*b["range_um"], color=ab[name]["color"], alpha=alpha, lw=0, zorder=0)
    return names


def add_band_key(ax, absorbers=None, include_uncertain=False):
    """A one-line key above ``ax`` saying what the coloured shading is.

    It is added as a separate artist, so ``ax.legend()`` can still be used for the lines.
    """
    names, ab = _select_absorbers(absorbers, include_uncertain)
    handles = [Patch(facecolor="none", edgecolor="none", label="Shaded = absorption bands:")]
    handles += [Patch(facecolor="none", edgecolor=ab[n]["color"], hatch=ab[n]["hatch"], lw=0,
                      label=ab[n].get("label", n)) if ab[n].get("hatch") else
                Patch(facecolor=ab[n]["color"], edgecolor=ab[n]["color"], alpha=0.45, label=ab[n].get("label", n))
                for n in names]
    key = Legend(ax, handles, [h.get_label() for h in handles], loc="lower left", bbox_to_anchor=(0.0, 1.0),
                 ncol=len(handles), frameon=False, fontsize=8, handlelength=1.1, handletextpad=0.4,
                 columnspacing=0.9, borderaxespad=0.15)
    ax.add_artist(key)
    return key


def _title(ax, title, key):
    """Put the title above the band key (if there is one)."""
    if title:
        ax.set_title(title, pad=TITLE_PAD_WITH_KEY if key else 6)


def _compact_flux_axis(ax):
    """Move a linear axis's power of ten into the axis label.

    Matplotlib otherwise prints e.g. '1e-14' above the axis, where it collides with
    the band key. Tick labels become plain numbers and the label reads
    'F_lambda [10^-14 W m^-2 um^-1]'.
    """
    if ax.get_yscale() != "linear":
        return
    lo, hi = ax.get_ylim()
    big = max(abs(lo), abs(hi))
    if not np.isfinite(big) or big == 0:
        return
    e = int(np.floor(np.log10(big)))
    if -2 <= e <= 3:
        return
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v / 10 ** e:g}"))
    label = ax.get_ylabel()
    scale = f"$10^{{{e}}}$"
    ax.set_ylabel(label.replace("[", f"[{scale} ", 1) if "[" in label else f"{label} [{scale}]")


def label_windows(ax, y=0.97):
    """Write 'J peak', '4 um peak', ... at the top of an axis."""
    for w in load_bands().get("windows", []):
        ax.text(w["center_um"], y, w["name"], transform=ax.get_xaxis_transform(), ha="center",
                va="top", fontsize=8, color="0.35")


# --------------------------------------------------------------- figures
def _figure(n_panels=1, height_ratios=None, figsize=None):
    """A figure with ``n_panels`` stacked axes sharing the wavelength axis."""
    fig, axes = plt.subplots(n_panels, 1, sharex=True, figsize=figsize or (9, 3.6 * n_panels + 0.9),
                             gridspec_kw={"height_ratios": height_ratios or [3] * n_panels, "hspace": 0.08})
    return fig, list(np.atleast_1d(axes))


def _shade_all(axes, bands, absorbers=None, include_uncertain=False):
    """Shade the bands on every panel and put one key above the top panel. Returns the key (or None)."""
    if not bands:
        return None
    for a in axes:
        shade_bands(a, absorbers, include_uncertain)
    return add_band_key(axes[0], absorbers, include_uncertain)


def _as_list(x):
    return list(x) if isinstance(x, (list, tuple)) else [x]


def _robust_peak(flux):
    """Peak of a spectrum, ignoring single-channel spikes.

    The highest level reached by two neighbouring channels (max over i of
    min(f[i], f[i+1])): a lone bad point is ignored, but a real peak only two
    channels wide (the J peak of a T dwarf) is kept.
    """
    f = np.asarray(flux, float)
    f = f[np.isfinite(f)]
    if f.size < 2:
        return float(np.nanmax(f))
    return float(np.max(np.minimum(f[:-1], f[1:])))


def plot_spectrum(spectra, log=False, bands=True, unit=None, normalize_at=None, offset=0.0,
                  errors=True, xlim=DEFAULT_XLIM, title=None, colors=None, absorbers=None,
                  include_uncertain=False, ax=None, labels=None, markers=None, figsize=None,
                  inline_labels=False):
    """Plot one or more spectra, with the absorption bands shaded behind them.

    Parameters
    ----------
    spectra : a Spectrum or a list of them
    log : True for a logarithmic flux axis
    bands : shade the absorption bands from ``data/bands.yaml`` (with a key above the plot)
    unit : convert every spectrum to this flux unit first ("W/m2/um", "Jy")
    normalize_at : (short, long) wavelength range; divide each spectrum by
        its mean flux there, so shapes can be compared
    offset : stack the spectra, first one on top. On a linear axis each spectrum
        is shifted up by ``offset`` from the one below it; on a log axis by
        ``offset`` decades (factors of 10).
    colors, labels : lists to override the defaults
    figsize : (width, height) in inches; make it taller for stacked plots
    inline_labels : write each label at the right-hand end of its curve instead of a legend
    ax : draw on an existing axis instead
    """
    spectra = _as_list(spectra)
    key = None
    if ax is None:
        fig, axes = _figure(figsize=figsize)
        ax = axes[0]
        key = _shade_all([ax], bands, absorbers, include_uncertain)
    else:
        fig = ax.figure
    colors = colors or (LINE_COLORS if len(spectra) <= len(LINE_COLORS)
                        else plt.cm.viridis(np.linspace(0, 0.9, len(spectra))))
    unit = unit or spectra[0].flux_unit
    n = len(spectra)
    any_clipped = False
    for i, s in enumerate(spectra):
        s = s.to_unit(unit)
        f, e = s.flux.copy(), (None if s.err is None else s.err.copy())
        if isinstance(normalize_at, str) and normalize_at == "peak":
            norm = _robust_peak(f)
            f = f / norm
            e = None if e is None else e / norm
        elif normalize_at is not None:
            m = (s.wave_um >= normalize_at[0]) & (s.wave_um <= normalize_at[1]) & np.isfinite(f)
            if not m.any():
                raise BDToolsError(f"'{s.name}' has no data in the normalization range {normalize_at}.")
            norm = np.nanmean(f[m])
            f = f / norm
            e = None if e is None else e / norm
        k = n - 1 - i                      # first spectrum on top
        clipped = np.zeros(f.shape, bool)
        if offset and not log and isinstance(normalize_at, str):
            # stacked, peak-scaled curves: a lone bad point far above the peak would run through the
            # curves above it, so draw it at the clip level and mark it with a triangle instead
            clip = 1.0 + 0.35 * offset
            clipped = np.isfinite(f) & (f > clip)
            f = np.where(clipped, clip, f)
        if offset and log:
            f, e = f * 10 ** (offset * k), (None if e is None else e * 10 ** (offset * k))
        elif offset:
            f = f + offset * k
        label = labels[i] if labels else s.name
        is_model = not s.has_errors
        mk = (markers[i] if markers else (None if is_model else "o"))
        ax.plot(s.wave_um, f, color=colors[i], label=label, marker=mk, ms=3,
                lw=1.4 if is_model else 1.0, drawstyle="default")
        if errors and e is not None:
            ax.fill_between(s.wave_um, f - e, f + e, color=colors[i], alpha=0.2, lw=0)
        if clipped.any():
            ax.plot(s.wave_um[clipped], f[clipped], "^", color=colors[i], ms=7, mec="black", mew=0.6,
                    label="_nolegend_")
            any_clipped = True
        if inline_labels:
            good = np.isfinite(f) & (s.wave_um <= xlim[1])
            if good.any():
                j = np.flatnonzero(good)[-1]
                ax.text(s.wave_um[j] + 0.04, f[j], label, color=colors[i], fontsize=9, fontweight="bold",
                        va="center", ha="left", clip_on=False)
    ax.set_xlim(*xlim)
    ax.set_xlabel(r"Wavelength [$\mu$m]")
    ylabel = UNIT_LABELS.get(unit, unit)
    if isinstance(normalize_at, str):
        ylabel = "Flux / its own peak flux"
    elif normalize_at is not None:
        ylabel = f"Flux / mean flux at {normalize_at[0]}-{normalize_at[1]} $\\mu$m"
    if offset:
        ylabel += "\n(curves shifted apart for clarity)"
    ax.set_ylabel(ylabel)
    if log:
        ax.set_yscale("log")
    if offset:                             # the numbers on a stacked axis mean nothing; hide them
        ax.tick_params(axis="y", which="both", labelleft=False)
    elif not log and normalize_at is None:
        _compact_flux_axis(ax)
    _title(ax, title, key)
    if any_clipped:
        ax.text(0.99, 0.005, "▲ = point far above its curve's peak (off the top; check it)", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=8, color="0.3")
    if inline_labels:
        pass
    elif len(spectra) > 4:
        ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8)
    elif len(spectra) > 1 or spectra[0].name:
        ax.legend(loc="best")
    return fig, ax


def plot_comparison(comp, panel="ratio", bands=True, log=False, title=None):
    """Plot a ``Comparison`` (from ``bdtools.compare``): spectra on top, then a
    ratio and/or residual-significance panel with absorber bands shaded.

    panel : "ratio", "significance", or "both"
    """
    panels = ["ratio", "significance"] if panel == "both" else [panel]
    fig, axes = _figure(n_panels=1 + len(panels), height_ratios=[3] + [1.6] * len(panels),
                        figsize=(9, 4.4 + 2.0 * len(panels)))
    key = _shade_all(axes, bands)
    d, t = comp.data, comp.template
    ax = axes[0]
    ax.errorbar(d.wave_um, d.flux, yerr=d.err, fmt="o", ms=3, color="black", lw=0.8, label=f"data: {d.name}")
    ax.plot(t.wave_um, t.flux, color=LINE_COLORS[2], lw=1.6, label=f"template x {comp.scale:.3g}: {t.name}")
    if comp.windows is not None:
        for lo, hi in np.atleast_2d(comp.windows):
            ax.axvspan(lo, hi, color="0.5", alpha=0.15, lw=0)
    ax.set_ylabel(UNIT_LABELS.get(d.flux_unit, d.flux_unit))
    if log:
        ax.set_yscale("log")
    else:
        _compact_flux_axis(ax)
    ax.legend(loc="best", title=f"reduced $\\chi^2$ = {comp.chi2_red:.1f},  $G_k$ = {comp.gk:.3g}",
              title_fontsize=9)
    for a, p in zip(axes[1:], panels):
        if p == "ratio":
            a.plot(d.wave_um, comp.ratio, "o-", ms=3, color="black", lw=0.8)
            a.axhline(1, color="0.4", lw=1)
            a.set_ylabel("data / template")
        else:
            a.plot(d.wave_um, comp.significance, "o", ms=3, color="black")
            a.axhline(0, color="0.4", lw=1)
            for k in (-3, 3):
                a.axhline(k, color="0.4", lw=0.8, ls="--")
            a.set_ylabel(r"(data $-$ template) / $\sigma$")
    axes[-1].set_xlabel(r"Wavelength [$\mu$m]")
    axes[-1].set_xlim(*DEFAULT_XLIM)
    _title(axes[0], title, key)
    return fig, axes


def plot_index_windows(spectra, names=None, log=False, unit="Jy"):
    """Show where each index's feature and normalization regions fall on the spectra.

    The index regions are the shading here, so the absorption bands are not drawn,
    and the legend sits above the plot so it never hides the region labels.
    """
    from .indices import compute_index, load_index_definitions

    cfg = load_index_definitions()
    names = list(cfg["indices"]) if names is None else _as_list(names)
    spectra = _as_list(spectra)
    fig, ax = plot_spectrum(spectra, log=log, unit=unit, xlim=(2.9, 5.0), bands=False)
    if ax.get_legend() is not None:
        ax.get_legend().remove()
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.01), fontsize=8, frameon=False, ncol=1)
    norm_drawn = set()
    for k, n in enumerate(names):
        d = cfg["indices"][n]
        color = molecule_color(n) if n in load_bands()["absorbers"] else LINE_COLORS[k + 1]
        ax.axvspan(*d["feature_um"], color=color, alpha=0.22, lw=0)
        ax.text(np.mean(d["feature_um"]), 0.02, f"{n}\nfeature", transform=ax.get_xaxis_transform(),
                ha="center", va="bottom", fontsize=8, color=color)
        if tuple(d["norm_um"]) not in norm_drawn:
            ax.axvspan(*d["norm_um"], facecolor="none", edgecolor="0.3", hatch="//", alpha=0.5, lw=0.5)
            ax.text(np.mean(d["norm_um"]), 0.02, "normalization", transform=ax.get_xaxis_transform(),
                    ha="center", va="bottom", fontsize=8, color="0.3")
            norm_drawn.add(tuple(d["norm_um"]))
    if len(spectra) == 1:
        txt = "\n".join(
            (lambda r: f"{n}: {r.value:.2f} $\\pm$ {r.err:.2f}")(compute_index(spectra[0], n, cfg)) for n in names)
        ax.text(0.99, 0.97, txt, transform=ax.transAxes, ha="right", va="top", fontsize=9,
                bbox=dict(boxstyle="round", fc="white", ec="0.7"))
    return fig, ax


def plot_index_plane(spectra, x="CH4", y="CO", highlight=None, ax=None):
    """Plot one index against another (e.g. CO index versus CH4 index).

    ``x`` and ``y`` are index names from data/indices.yaml; each axis is a single
    index, never a combination. ``spectra`` (e.g. the reference sequence) are
    coloured by order; ``highlight`` (one Spectrum) is drawn as a large star.
    Points whose x or y index is flagged "not meaningful" (the CH4 index of
    Y dwarfs) are drawn hollow.
    """
    from .indices import compute_index, load_index_definitions

    known = load_index_definitions()["indices"]
    for name in (x, y):
        if name not in known:
            raise ValueError(f"Unknown index '{name}'. Choose from: {', '.join(known)}.")
    if x == y:
        raise ValueError("Choose two different indices for x and y.")

    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 5.5))
    else:
        fig = ax.figure
    spectra = _as_list(spectra)
    colors = plt.cm.viridis(np.linspace(0, 0.9, max(len(spectra), 1)))

    def point(s):
        a, b = compute_index(s, x), compute_index(s, y)
        hollow = any("Not meaningful" in w for w in a.warnings + b.warnings)
        return a.value, a.err, b.value, b.err, hollow

    for s, c in zip(spectra, colors):
        px, pxe, py, pye, hollow = point(s)
        ax.errorbar(px, py, xerr=pxe, yerr=pye, fmt="o", color=c, mfc="none" if hollow else c, ms=7, capsize=2)
        ax.annotate(s.meta.get("spectral_type", s.name), (px, py), textcoords="offset points", xytext=(5, 4), fontsize=8)
    if highlight is not None:
        px, pxe, py, pye, _ = point(highlight)
        ax.errorbar(px, py, xerr=pxe, yerr=pye, fmt="*", color=LINE_COLORS[2], ms=16, capsize=2,
                    label=f"star: {highlight.name}")
        # below the axes, so it never covers the spectral-type labels on the points
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), frameon=False, fontsize=9)
    tex = lambda n: n.replace("4", "$_4$").replace("2", "$_2$")
    ax.set_xlabel(f"{tex(x)} index [mag]")
    ax.set_ylabel(f"{tex(y)} index [mag]")
    ax.set_title(f"{tex(y)} index vs {tex(x)} index (hollow = an index not meaningful)", fontsize=10)
    return fig, ax


def plot_parameter_stack(baseline, members, parameter, value_label=None, log=False, bands=True,
                         normalize_at=None, title=None, like=None, spherex=True):
    """Notebook 5: models that differ in one parameter, plus their ratio to the baseline model.

    ``members`` are model Spectra (from ``load_sweep``); their parameter value
    is read from ``meta[parameter]``. By default every model is first averaged
    to SPHEREx resolution (using the channels of ``like`` if given), because
    that is the resolution students will compare with.
    """
    from .binning import at_spherex_resolution
    from .compare import ratio_to

    if spherex:
        baseline = at_spherex_resolution(baseline, like)
        members = [at_spherex_resolution(m, like) for m in members]

    fig, axes = _figure(n_panels=2, height_ratios=[3, 1.8], figsize=(9, 8))
    key = _shade_all(axes, bands)
    ax, rax = axes
    cmap = plt.cm.viridis(np.linspace(0, 0.9, len(members)))
    for c, m in zip(cmap, members):
        val = m.meta.get(parameter, "?")
        lab = f"{value_label or parameter} = {val}"
        is_base = m.name == baseline.name
        f = m.flux
        if normalize_at is not None:
            sel = (m.wave_um >= normalize_at[0]) & (m.wave_um <= normalize_at[1])
            f = f / np.nanmean(f[sel])
        ax.plot(m.wave_um, f, color=c, lw=2.4 if is_base else 1.3, label=lab + ("  (baseline)" if is_base else ""))
        rax.plot(m.wave_um, ratio_to(m, baseline), color=c, lw=2.4 if is_base else 1.3,
                 marker="o" if spherex else None, ms=2)
    rax.axhline(1, color="0.3", lw=1)
    lo, hi = rax.get_ylim()
    if lo > 0 and hi / lo > 4:
        rax.set_yscale("log")
    rax.set_ylabel("model / baseline")
    rax.set_xlabel(r"Wavelength [$\mu$m]")
    ax.set_ylabel(UNIT_LABELS.get(baseline.flux_unit, "flux") if normalize_at is None else "normalized flux")
    if log:
        ax.set_yscale("log")
    else:
        _compact_flux_axis(ax)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8)
    ax.set_xlim(*DEFAULT_XLIM)
    if spherex:
        ax.text(0.01, 0.02, "models averaged to SPHEREx resolution", transform=ax.transAxes, fontsize=8, color="0.4")
    _title(ax, title, key)
    return fig, axes


def plot_contribution_function(toy, wave_index=None, ax=None):
    """Toy model: where in the atmosphere each wavelength's light comes from."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 4.8))
    else:
        fig = ax.figure
    cf = toy["contribution"]
    cf = cf / np.nanmax(cf, axis=1, keepdims=True)
    pc = ax.pcolormesh(toy["wave_um"], toy["pressure_bar"], cf.T, cmap="magma_r", shading="auto", vmin=0, vmax=1)
    ax.plot(toy["wave_um"], toy["photosphere_bar"], color=LINE_COLORS[6], lw=2, label=r"$\tau = 2/3$ level")
    ax.set_yscale("log")
    ax.invert_yaxis()
    ax.set_xlabel(r"Wavelength [$\mu$m]")
    ax.set_ylabel("Pressure [bar]\n(higher pressure = deeper; deeper is down)")
    fig.colorbar(pc, ax=ax, label="contribution (scaled to 1 at each wavelength)")
    ax.legend(loc="lower right")
    ax.set_title("TOY MODEL - not a real brown dwarf", fontsize=10, color="0.3")
    return fig, ax


# ------------------------------------------------------------------ model fits (notebook 6)
def plot_chi2_map(fit, x="teff", y="logg", ax=None):
    """Best (lowest) reduced chi^2 for each pair of ``x`` and ``y`` values in a ``FitResult``.

    The other parameters are free: each cell shows the best model with those
    x and y values. The overall best fit is marked with a star.
    """
    from matplotlib.colors import LogNorm

    from .fitting import PARAM_LABELS, PARAMETERS, _sort_key

    for p in (x, y):
        if p not in PARAMETERS:
            raise BDToolsError(f"Unknown parameter '{p}'. Choose from: {', '.join(PARAMETERS)}.")
    if x == y:
        raise BDToolsError("Choose two different parameters for x and y.")
    t = fit.table
    xs = sorted(t[x].unique(), key=_sort_key)
    ys = sorted(t[y].unique(), key=_sort_key)
    best = t.groupby([x, y])["chi2_red"].min()
    img = np.full((len(ys), len(xs)), np.nan)
    for (vx, vy), v in best.items():
        img[ys.index(vy), xs.index(vx)] = v
    if ax is None:
        fig, ax = plt.subplots(figsize=(7.5, 4.8))
    else:
        fig = ax.figure
    im = ax.imshow(img, origin="lower", aspect="auto", cmap="viridis_r",
                   norm=LogNorm(vmin=np.nanmin(img), vmax=np.nanmax(img)))
    fig.colorbar(im, ax=ax, label=r"best reduced $\chi^2$ (log scale)")
    ax.set_xticks(range(len(xs)), [str(v) for v in xs], rotation=90 if len(xs) > 8 else 0)
    ax.set_yticks(range(len(ys)), [str(v) for v in ys])
    b = fit.best
    ax.plot(xs.index(b[x]), ys.index(b[y]), "*", color="white", mec="black", ms=18)
    ax.set_xlabel(PARAM_LABELS.get(x, x))
    ax.set_ylabel(PARAM_LABELS.get(y, y))
    others = [p for p in PARAMETERS if p not in (x, y)]
    ax.set_title(fit.data.name + r": best $\chi^2_{red}$ over " + ", ".join(others), fontsize=10)
    return fig, ax


def plot_fit_parameters(table, parameters=("teff", "logg", "clouds", "chi2_red")):
    """Best-fit parameters against spectral type, from ``bd.fits_table(fits)``."""
    from .fitting import PARAM_LABELS, _sort_key

    parameters = list(parameters)
    fig, axes = plt.subplots(len(parameters), 1, sharex=True, figsize=(7, 1.9 * len(parameters) + 0.6))
    axes = np.atleast_1d(axes)
    xpos = np.arange(len(table))
    for ax, p in zip(axes, parameters):
        vals = table[p]
        if vals.dtype == object:          # categorical (clouds): put the categories on the y axis in order
            cats = sorted(vals.unique(), key=_sort_key)
            ax.plot(xpos, [cats.index(v) for v in vals], "o-", color=LINE_COLORS[0])
            ax.set_yticks(range(len(cats)), cats)
        else:
            ax.plot(xpos, vals, "o-", color=LINE_COLORS[0])
            if p == "chi2_red":
                ax.set_yscale("log")
        ax.set_ylabel(PARAM_LABELS.get(p, r"$\chi^2_{red}$" if p == "chi2_red" else p))
        ax.grid(alpha=0.3)
    axes[-1].set_xticks(xpos, table["spectral_type"])
    axes[-1].set_xlabel("spectral type (reference)")
    axes[0].set_title("Best-fit model parameters along the sequence", fontsize=10)
    return fig, axes


def plot_fit_residuals(fits, bands=True, labels=None, title=None):
    """Data / best-fit model for several fits on one plot.

    If several objects show the *same* pattern, the misfit comes from the models,
    not from anything peculiar about one object.
    """
    fits = _as_list(fits)
    fig, axes = _figure(n_panels=1, height_ratios=[3], figsize=(9, 5.2))
    ax = axes[0]
    key = _shade_all(axes, bands)
    colors = plt.cm.viridis(np.linspace(0, 0.9, max(len(fits), 1)))
    for k, (f, c) in enumerate(zip(fits, colors)):
        comp = f.comparison()
        lab = labels[k] if labels else f.data.meta.get("spectral_type", f.data.name)
        ax.plot(comp.data.wave_um, comp.ratio, "o-", ms=3, lw=1, color=c, label=f"{lab} (χ²red {comp.chi2_red:.0f})")
    ax.axhline(1, color="0.4", lw=1)
    ax.set_ylabel("data / best-fit model")
    ax.set_xlabel(r"Wavelength [$\mu$m]")
    ax.set_xlim(*DEFAULT_XLIM)
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=8) if len(fits) > 4 else ax.legend(fontsize=8)
    _title(ax, title, key)
    return fig, ax
