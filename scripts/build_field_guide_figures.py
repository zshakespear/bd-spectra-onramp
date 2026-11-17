"""Render the small figures used by the field guide (field_guide/img/).

    python scripts/build_field_guide_figures.py

Draws whatever reference spectra are installed. Re-run after new references
arrive; groups with no spectra yet are skipped and listed.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import bdtools as bd  # noqa: E402

IMG = REPO / "field_guide" / "img"
GROUPS = {
    "early_L": ["L0", "L1", "L2", "L3"],
    "late_L": ["L4", "L5", "L6", "L7", "L8"],
    "LT_transition": ["L8", "L9", "T0", "T1", "T2"],
    "early_T": ["T2", "T3", "T4", "T5"],
    "late_T": ["T6", "T7", "T8", "T9"],
    "Y": ["Y0", "Y1", "Y2", "Y4"],
}
J_PEAK = (1.2, 1.3)
NORMALIZE = {"Y": (3.95, 4.15)}   # Y dwarfs have almost no flux at J (S/N ~ 1); use their 4 um peak


def thumbnail(name, types):
    seq = bd.load_sequence(types)
    if not seq:
        return False
    win = NORMALIZE.get(name, J_PEAK)
    fig, ax = bd.plot_spectrum(seq, log=True, normalize_at=win, errors=False,
                               colors=list(plt.cm.viridis(np.linspace(0, 0.9, len(seq)))),
                               labels=[s.meta["spectral_type"] for s in seq],
                               title=f"{name.replace('_', ' ')} (normalized at {win[0]}-{win[1]} um)")
    # one noisy near-zero channel would otherwise stretch the log axis over many decades
    vals = np.concatenate([s.flux / np.nanmean(s.flux[(s.wave_um >= win[0]) & (s.wave_um <= win[1])])
                           for s in seq])
    vals = vals[np.isfinite(vals) & (vals > 0)]
    ax.set_ylim(np.percentile(vals, 1) / 1.5, np.percentile(vals, 99.5) * 1.5)
    fig.savefig(IMG / f"seq_{name}.png", dpi=90, bbox_inches="tight")
    plt.close(fig)
    return True


def data_problem_examples():
    """Real flagged points in installed references (for the data-problems page)."""
    written = []
    for t in ["L3", "L7", "L0"]:
        s = bd.optional(bd.load_reference, t)
        if s is None:
            continue
        flags = bd.running_median_outliers(s)
        gaps = bd.find_gaps(s)
        if not flags.any() and not gaps:
            continue
        fig, ax = bd.plot_spectrum(s, log=True, title=f"{s.name}: flagged points (red) and gaps (grey)")
        ax.plot(s.wave_um[flags], s.flux[flags], "o", mfc="none", mec="red", ms=11, mew=2)
        for a, b in gaps:
            ax.axvspan(a, b, color="0.6", alpha=0.4)
        fig.savefig(IMG / f"problem_{t}.png", dpi=90, bbox_inches="tight")
        plt.close(fig)
        written.append(t)
    return written


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    bd.setup_style()
    missing = [g for g, types in GROUPS.items() if not thumbnail(g, types)]
    probs = data_problem_examples()
    print(f"thumbnails written to {IMG}")
    if missing:
        print("no spectra installed yet for:", ", ".join(missing))
    print("data-problem examples:", ", ".join(probs) or "none")


if __name__ == "__main__":
    main()
