"""The ``Spectrum`` object: wavelengths, fluxes, uncertainties, and units together."""

from dataclasses import dataclass, field, replace

import numpy as np

from .errors import BDToolsError, UnitError
from .units import canonical_flux_unit, flambda_to_fnu_jy, fnu_jy_to_flambda


@dataclass
class Spectrum:
    """A spectrum with its units attached.

    Attributes
    ----------
    wave_um : wavelengths in microns, increasing
    flux : flux values, in ``flux_unit``
    err : 1-sigma flux uncertainties (same unit), or None if there are none
    flux_unit : "W/m2/um" (F_lambda), "Jy" or "mJy" (F_nu)
    name : a short label used in plot legends
    meta : everything else we know (spectral type, distance, model parameters,
        where the file came from, ...)
    chan_lo_um, chan_hi_um : the short and long edges of each SPHEREx channel,
        if known. For a model these are None.
    """

    wave_um: np.ndarray
    flux: np.ndarray
    err: np.ndarray = None
    flux_unit: str = "W/m2/um"
    name: str = ""
    meta: dict = field(default_factory=dict)
    chan_lo_um: np.ndarray = None
    chan_hi_um: np.ndarray = None

    def __post_init__(self):
        self.wave_um = np.asarray(self.wave_um, float)
        self.flux = np.asarray(self.flux, float)
        if self.wave_um.ndim != 1 or self.flux.shape != self.wave_um.shape:
            raise BDToolsError(
                f"Spectrum '{self.name}': wavelength and flux must be 1-D lists of the same length "
                f"(got {self.wave_um.shape} and {self.flux.shape})."
            )
        if self.err is not None:
            self.err = np.asarray(self.err, float)
            if self.err.shape != self.flux.shape:
                raise BDToolsError(f"Spectrum '{self.name}': uncertainty column has the wrong length.")
        unit = canonical_flux_unit(self.flux_unit)
        if unit is None:
            raise UnitError(
                f"Spectrum '{self.name}': flux unit '{self.flux_unit}' is not one bdtools knows. "
                "Use 'W/m2/um', 'Jy', or 'mJy'."
            )
        self.flux_unit = unit
        for attr in ("chan_lo_um", "chan_hi_um"):
            v = getattr(self, attr)
            if v is not None:
                setattr(self, attr, np.asarray(v, float))
        order = np.argsort(self.wave_um)
        if np.any(order != np.arange(order.size)):
            self.wave_um = self.wave_um[order]
            self.flux = self.flux[order]
            if self.err is not None:
                self.err = self.err[order]
            if self.chan_lo_um is not None:
                self.chan_lo_um = self.chan_lo_um[order]
                self.chan_hi_um = self.chan_hi_um[order]

    # ------------------------------------------------------------------ info
    @property
    def has_errors(self):
        return self.err is not None and np.any(np.isfinite(self.err))

    @property
    def kind(self):
        return self.meta.get("kind", "spectrum")

    def __len__(self):
        return self.wave_um.size

    def __repr__(self):
        rng = f"{np.nanmin(self.wave_um):.2f}-{np.nanmax(self.wave_um):.2f} um" if len(self) else "empty"
        bits = [f"'{self.name}'", f"{len(self)} points", rng, self.flux_unit]
        if self.has_errors:
            bits.append("with uncertainties")
        return f"Spectrum({', '.join(bits)})"

    def require_errors(self):
        if not self.has_errors:
            raise BDToolsError(
                f"'{self.name}' has no uncertainty column, so this calculation cannot be done. "
                "(Model spectra have no uncertainties; use a reference spectrum as the 'data'.)"
            )

    # ------------------------------------------------------------- units
    def to_flambda(self):
        """Return a copy in F_lambda, W/m^2/um."""
        if self.flux_unit == "W/m2/um":
            return self.copy()
        scale = 1.0 if self.flux_unit == "Jy" else 1e-3
        f = fnu_jy_to_flambda(self.wave_um, self.flux * scale)
        e = None if self.err is None else fnu_jy_to_flambda(self.wave_um, self.err * scale)
        return self.copy(flux=f, err=e, flux_unit="W/m2/um")

    def to_fnu_jy(self):
        """Return a copy in F_nu, Jy (the unit Rustamkulov et al. 2026 use)."""
        if self.flux_unit == "Jy":
            return self.copy()
        if self.flux_unit == "mJy":
            return self.copy(flux=self.flux * 1e-3,
                             err=None if self.err is None else self.err * 1e-3, flux_unit="Jy")
        f = flambda_to_fnu_jy(self.wave_um, self.flux)
        e = None if self.err is None else flambda_to_fnu_jy(self.wave_um, self.err)
        return self.copy(flux=f, err=e, flux_unit="Jy")

    def to_unit(self, unit):
        unit = canonical_flux_unit(unit)
        if unit == "W/m2/um":
            return self.to_flambda()
        if unit == "Jy":
            return self.to_fnu_jy()
        if unit == "mJy":
            s = self.to_fnu_jy()
            return s.copy(flux=s.flux * 1e3, err=None if s.err is None else s.err * 1e3, flux_unit="mJy")
        raise UnitError(f"Unknown flux unit '{unit}'.")

    # ------------------------------------------------------------- helpers
    def copy(self, **changes):
        """A copy, optionally with some attributes changed: ``s.copy(name='new')``."""
        new = replace(self, **changes)
        new.meta = dict(new.meta)
        return new

    def good(self):
        """Boolean mask of points with a finite wavelength and flux (and uncertainty, if any)."""
        ok = np.isfinite(self.wave_um) & np.isfinite(self.flux)
        if self.err is not None:
            ok &= np.isfinite(self.err) & (self.err > 0)
        return ok

    def _subset(self, mask):
        return self.copy(
            wave_um=self.wave_um[mask], flux=self.flux[mask],
            err=None if self.err is None else self.err[mask],
            chan_lo_um=None if self.chan_lo_um is None else self.chan_lo_um[mask],
            chan_hi_um=None if self.chan_hi_um is None else self.chan_hi_um[mask],
        )

    def select(self, mask):
        """Copy keeping only the points where ``mask`` is True."""
        return self._subset(np.asarray(mask, bool))

    def clean(self):
        """Copy with missing / non-finite points removed."""
        return self._subset(self.good())

    def between(self, wmin_um, wmax_um):
        """Copy keeping only wavelengths between ``wmin_um`` and ``wmax_um``."""
        return self._subset((self.wave_um >= wmin_um) & (self.wave_um <= wmax_um))

    def scaled(self, factor, name=None):
        """Copy with flux (and uncertainty) multiplied by ``factor``."""
        return self.copy(flux=self.flux * factor,
                         err=None if self.err is None else self.err * abs(factor),
                         name=self.name if name is None else name)

    def channel_edges(self):
        """Short and long edge of every channel (microns).

        Uses the stored edges if the file had them. Otherwise edges are placed
        halfway between neighbouring channel centres -- see
        ``binning.edges_from_centers`` for when that approximation fails.
        """
        if self.chan_lo_um is not None and self.chan_hi_um is not None:
            return self.chan_lo_um, self.chan_hi_um
        from .binning import edges_from_centers
        return edges_from_centers(self.wave_um)

    def snr(self):
        """Signal-to-noise ratio of each point."""
        self.require_errors()
        with np.errstate(divide="ignore", invalid="ignore"):
            return self.flux / self.err
