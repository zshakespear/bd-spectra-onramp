"""bdtools: small helpers for the brown dwarf spectra on-ramp notebooks.

Students: you should almost never need to read this code. Every function has
a short description -- type ``help(bd.function_name)`` or ``bd.function_name?``
in a cell to see it.

Quick tour
----------
Loading      load_reference, load_sequence, list_references, load_model,
             list_models, load_sweep, load_toy, read_spectrum
Physics      planck_lambda, blackbody_surface_flux, wien_peak_um,
             brightness_temperature, observed_to_surface, surface_to_observed
Units        Spectrum.to_flambda(), Spectrum.to_fnu_jy(), flambda_to_fnu_jy,
             fnu_jy_to_flambda, fnu_mjy_to_flambda
Binning      bin_to_spectrum (model -> a spectrum's own SPHEREx channels),
             at_spherex_resolution
Comparing    compare, rank_templates, ratio_to
Fitting      load_grid, fit_models, fits_table
Indices      compute_index, index_table, index_difference
Quality      quality_report, running_median_outliers, find_gaps
Plotting     plot_spectrum, plot_comparison, plot_index_windows, plot_index_plane,
             plot_parameter_stack, plot_contribution_function, molecule_color,
             plot_chi2_map, plot_fit_parameters, plot_fit_residuals, shade_bands, add_band_key
"""

from .binning import (at_spherex_resolution, bin_mean, bin_to_spectrum, edges_from_centers, log_wavelength_grid,
                      resample_to_resolution, spherex_like_channels)
from .compare import Comparison, compare, fit_scale, rank_templates, ratio_to, total_error
from .errors import BDToolsError, MissingDataError, UnitError
from .fitting import FitResult, ModelGrid, fit_models, fits_table, load_grid
from .indices import compute_index, index_difference, index_table, load_index_definitions
from .io import (list_models, list_references, list_toys, load_model, load_reference, load_sequence,
                 load_sweep, load_toy, models_available, read_spectrum, references_available,
                 write_spectrum)
from .planck import blackbody_surface_flux, brightness_temperature, planck_lambda, wien_peak_um
from .plotting import (LINE_COLORS, add_band_key, draw_molecule_bars, load_bands, molecule_color,
                       plot_chi2_map, plot_comparison, plot_contribution_function, plot_fit_parameters,
                       plot_fit_residuals, plot_index_plane, plot_index_windows,
                       plot_parameter_stack, plot_spectrum, setup_style, shade_bands)
from .quality import find_gaps, quality_report, running_median_outliers
from .spectrum import Spectrum
from .units import (dilution_factor, flambda_to_fnu_jy, fnu_jy_to_flambda, fnu_mjy_to_flambda,
                    observed_to_surface, surface_to_observed)

__version__ = "0.1.0"


def _friendly_errors():
    """Show BDToolsError as one plain message instead of a long traceback."""
    try:
        ip = get_ipython()  # noqa: F821  (defined inside Jupyter/Colab)
    except NameError:
        return

    def handler(shell, etype, evalue, tb, tb_offset=None):
        print(f"\n⚠️  {etype.__name__}: {evalue}\n")
        return None

    ip.set_custom_exc((BDToolsError,), handler)


def optional(func, *args, **kwargs):
    """Call ``func``; if its data is not installed yet, print a note and return None.

    Lets a notebook keep running when, for example, the T-dwarf reference
    spectra or the model library have not been supplied yet.
    """
    try:
        return func(*args, **kwargs)
    except MissingDataError as e:
        print(f"⏳ Not available yet: {e}")
        return None


def setup_notebook(verbose=True):
    """Run once at the top of every notebook: plot style, friendly errors, data check."""
    setup_style()
    _friendly_errors()
    if verbose:
        refs = "yes" if references_available() else "NOT YET (ask your instructor)"
        mods = "yes" if models_available() else "NOT YET (ask your instructor)"
        toys = "yes" if list_toys() else "NOT YET (ask your instructor)"
        print(f"bdtools {__version__} ready.  Reference spectra: {refs}.  Model library: {mods}.  Toy model: {toys}.")
