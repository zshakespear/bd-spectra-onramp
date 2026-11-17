"""Basic tests for bdtools: units, resampling, brightness temperature, indices, comparison.

Run with ``pytest tests/`` or, without pytest, ``python tests/test_bdtools.py``.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bdtools as bd  # noqa: E402


# ------------------------------------------------------------------ units
def test_fnu_flambda_roundtrip():
    w = np.linspace(0.75, 5.0, 50)
    flam = 1e-15 * np.ones_like(w)
    back = bd.fnu_jy_to_flambda(w, bd.flambda_to_fnu_jy(w, flam))
    assert np.allclose(back, flam, rtol=1e-12)


def test_fnu_known_value():
    # 1 Jy at 1 um: F_lambda = 1e-26 * c / lambda^2 = 2.998e-12 W/m^2/m = 2.998e-18 W/m^2/um
    assert np.isclose(bd.fnu_jy_to_flambda(1.0, 1.0), 2.99792458e-12 * 1e-6, rtol=1e-9)
    assert np.isclose(bd.fnu_mjy_to_flambda(1.0, 1000.0), bd.fnu_jy_to_flambda(1.0, 1.0))


def test_spectrum_unit_roundtrip_with_errors():
    w = np.linspace(1, 4, 20)
    s = bd.Spectrum(w, np.full(20, 2e-16), np.full(20, 1e-17), "W/m2/um", "t")
    s2 = s.to_fnu_jy().to_flambda()
    assert np.allclose(s2.flux, s.flux) and np.allclose(s2.err, s.err)
    assert s.to_unit("mJy").flux_unit == "mJy"


def test_bad_unit_is_plain_error():
    try:
        bd.Spectrum([1, 2], [1, 1], flux_unit="furlongs")
    except bd.UnitError as e:
        assert "furlongs" in str(e)
    else:
        raise AssertionError("expected UnitError")


def test_observed_surface_roundtrip():
    f = bd.surface_to_observed(1.0, distance_pc=10, radius_rjup=1.0)
    assert np.isclose(bd.observed_to_surface(f, 10, 1.0), 1.0)
    assert np.isclose(f, (bd.units.R_JUP_M / (10 * bd.units.PARSEC_M)) ** 2)


# ----------------------------------------------------------------- planck
def test_brightness_temperature_inverts_planck():
    w = np.linspace(0.75, 5.0, 40)
    for t in (250.0, 800.0, 2500.0):
        tb = bd.brightness_temperature(w, bd.blackbody_surface_flux(w, t))
        assert np.allclose(tb, t, rtol=1e-8)


def test_brightness_temperature_handles_bad_flux():
    tb = bd.brightness_temperature([1.0, 2.0, 3.0], [0.0, -1.0, np.nan])
    assert np.all(np.isnan(tb))


def test_wien_and_stefan_boltzmann():
    t = 1000.0
    w = np.linspace(0.3, 200, 400000)
    b = bd.planck_lambda(w, t)
    assert abs(w[np.argmax(b)] - bd.wien_peak_um(t)) < 0.01
    total = np.trapezoid(np.pi * b, w) if hasattr(np, "trapezoid") else np.trapz(np.pi * b, w)
    assert np.isclose(total, 5.670374419e-8 * t**4, rtol=2e-3)


# ---------------------------------------------------------------- binning
def test_bin_mean_exact_for_linear_flux():
    x = np.linspace(1, 5, 1001)
    y = 3 * x + 2
    lo, hi = np.array([1.5, 2.0]), np.array([1.7, 3.0])
    assert np.allclose(bd.bin_mean(x, y, lo, hi), 3 * (lo + hi) / 2 + 2)


def test_bin_mean_outside_range_is_nan():
    out = bd.bin_mean([1, 2, 3], [1, 1, 1], [0.5, 1.5], [1.2, 2.5])
    assert np.isnan(out[0]) and np.isclose(out[1], 1)


def test_bin_conserves_flux_of_narrow_feature():
    x = np.linspace(1, 2, 20001)
    y = np.ones_like(x)
    y[(x > 1.495) & (x < 1.505)] = 0.0       # a 0.01 um-wide dip
    out = bd.bin_mean(x, y, np.array([1.45]), np.array([1.55]))
    assert np.isclose(out[0], 0.9, atol=1e-3)


def test_edges_from_centers_and_gap():
    w = np.array([1.0, 1.1, 1.2, 1.3, 2.0, 2.1])
    lo, hi = bd.edges_from_centers(w)
    assert np.allclose(lo[1:3], [1.05, 1.15]) and np.allclose(hi[1:3], [1.15, 1.25])
    # channel next to the gap is made symmetric instead of spanning the gap
    assert np.isclose(hi[3] - w[3], w[3] - lo[3]) and hi[3] < 1.4
    assert np.isclose(lo[4], 1.95)


def test_bin_to_spectrum_units():
    model = bd.Spectrum(np.linspace(0.5, 5.5, 5000), np.full(5000, 1e-15), name="flat model")
    w = np.linspace(1, 4, 30)
    data_jy = bd.Spectrum(w, bd.flambda_to_fnu_jy(w, 1e-15), np.full(30, 1e-6), "Jy", "data")
    b = bd.bin_to_spectrum(model, data_jy)
    assert b.flux_unit == "Jy" and np.allclose(b.flux, data_jy.flux, rtol=1e-6)


def test_resample_to_resolution():
    x = np.linspace(0.6, 5.5, 200000)
    c, f = bd.resample_to_resolution(x, np.ones_like(x), 500, 0.7, 5.2)
    assert np.allclose(f, 1.0) and np.isclose(np.median(c[1:] / np.diff(c)), 500, rtol=0.01)


# ---------------------------------------------------------------- compare
def _fake_data(scale=2.0, noise=0.0, seed=1):
    rng = np.random.default_rng(seed)
    w = np.linspace(0.8, 5.0, 100)
    model_w = np.linspace(0.6, 5.3, 20000)
    model_f = 1e-15 * (1 + 0.5 * np.sin(model_w * 3))
    model = bd.Spectrum(model_w, model_f, name="model")
    truth = bd.bin_to_spectrum(model, bd.Spectrum(w, np.ones(100), np.ones(100) * 1e-17)).flux * scale
    err = 0.02 * truth
    data = bd.Spectrum(w, truth + noise * err * rng.standard_normal(100), err, name="data")
    return data, model


def test_compare_recovers_scale():
    data, model = _fake_data(scale=3.7)
    c = bd.compare(data, model)
    assert np.isclose(c.scale, 3.7, rtol=1e-6)
    assert c.chi2_red < 1e-10 and np.allclose(c.ratio, 1)


def test_compare_with_noise_and_gk():
    data, model = _fake_data(scale=1.0, noise=1.0)
    c = bd.compare(data, model, systematic=0.0)
    assert 0.6 < c.chi2_red < 1.5
    assert np.isfinite(c.gk)
    c2 = bd.compare(data, model, windows=[(1.0, 1.3)])
    assert np.isfinite(c2.scale)


def test_compare_requires_errors():
    _, model = _fake_data()
    try:
        bd.compare(model, model)
    except bd.BDToolsError as e:
        assert "uncertaint" in str(e)
    else:
        raise AssertionError("expected BDToolsError")


# ---------------------------------------------------------------- indices
def _index_spec(depth_mag, sigma=None):
    w = np.linspace(3.0, 5.0, 200)
    fnu = np.ones_like(w)
    feat = (w >= 3.20) & (w <= 3.65)
    fnu[feat] = 10 ** (-0.4 * depth_mag)
    err = None if sigma is None else np.full_like(w, sigma)
    return bd.Spectrum(w, fnu, err, "Jy", "index test", {"spectral_type": "T5"})


def test_index_value():
    r = bd.compute_index(_index_spec(0.75, sigma=0.01), "CH4")
    assert np.isclose(r.value, 0.75)
    # in F_nu the normalization region is exactly 1, so the others are 0
    assert np.isclose(bd.compute_index(_index_spec(0.75, 0.01), "CO2").value, 0.0)


def test_index_uncertainty_formula():
    s = _index_spec(0.0, sigma=0.05)
    r = bd.compute_index(s, "CH4")
    wv = s.wave_um
    nb = ((wv >= 3.20) & (wv <= 3.65)).sum()
    nn = ((wv >= 3.70) & (wv <= 4.14)).sum()
    expect = 2.5 / np.log(10) * np.hypot(0.05 * np.sqrt(nb) / nb, 0.05 * np.sqrt(nn) / nn)
    assert np.isclose(r.err, expect) and r.n_feature == nb and r.n_norm == nn


def test_index_independent_of_scaling():
    s = _index_spec(0.4, 0.01)
    assert np.isclose(bd.compute_index(s, "CH4").value, bd.compute_index(s.scaled(123.0), "CH4").value)


def test_index_warns_for_y_dwarf_ch4():
    s = _index_spec(0.4, 0.01)
    s.meta["spectral_type"] = "Y1"
    assert any("Not meaningful" in w for w in bd.compute_index(s, "CH4").warnings)


def test_index_definitions_match_paper_table5():
    d = bd.load_index_definitions()["indices"]
    assert d["CH4"]["feature_um"] == [3.20, 3.65]
    assert d["CO2"]["feature_um"] == [4.18, 4.35]
    assert d["CO"]["feature_um"] == [4.55, 4.80]
    assert all(v["norm_um"] == [3.70, 4.14] for v in d.values())


def test_index_plane_uses_single_indices():
    import matplotlib
    matplotlib.use("Agg")
    s = _index_spec(0.6, 0.01)
    fig, ax = bd.plot_index_plane([s], x="CH4", y="CO2")
    x, y = ax.lines[0].get_data()
    assert np.isclose(x[0], 0.6) and np.isclose(y[0], 0.0)
    assert "CO" in ax.get_ylabel() and "-" not in ax.get_ylabel().replace("$_", "")
    for bad in [dict(x="CH4", y="CH4"), dict(x="CH4", y="H2O")]:
        try:
            bd.plot_index_plane([s], **bad)
        except ValueError:
            continue
        raise AssertionError(f"accepted {bad}")



# ---------------------------------------------------------------- fitting
def _toy_grid():
    import pandas as pd
    edges = bd.log_wavelength_grid(0.65, 5.3, 300)
    w = np.sqrt(edges[:-1] * edges[1:])
    rows, flux = [], []
    for teff in (1000.0, 1500.0, 2000.0):
        for logg in (4.0, 5.0):
            for clouds in ("2", "nc"):
                f = bd.planck_lambda(w, teff) * (1 + 0.1 * (logg - 4) * w) * ((0.6 + 0.1 * w) if clouds == "2" else 1.0)
                f = f * (1 - 0.5 * np.exp(-0.5 * ((w - 1.4) / 0.05) ** 2) * teff / 2000)
                rows.append({"teff": teff, "logg": logg, "mh": 0.0, "clouds": clouds}); flux.append(f)
    params = pd.DataFrame(rows).astype({"clouds": object})
    return bd.ModelGrid("toy", w, edges[:-1], edges[1:], np.array(flux, np.float32), params, {})


def _grid_data(grid, i, scale=3e-20, noise=0.01, seed=0):
    rng = np.random.default_rng(seed)
    wc = np.linspace(0.75, 5.0, 90)
    s = bd.Spectrum(wc, np.ones_like(wc), np.ones_like(wc), "W/m2/um", "fake", {"spectral_type": "L5"})
    true = grid.binned_to(s)[i] * scale
    return s.copy(flux=true * (1 + noise * rng.standard_normal(wc.size)), err=noise * true)


def test_fit_models_recovers_input_and_matches_compare():
    g = _toy_grid()
    i = g.find(teff=1500, logg=5.0, mh=0.0, clouds="nc")
    data = _grid_data(g, i)
    fit = bd.fit_models(data, grid=g)
    assert int(fit.best["model"]) == i
    assert np.isclose(fit.best["scale"], 3e-20, rtol=0.02)
    c = fit.comparison()
    assert np.isclose(c.chi2_red, fit.best["chi2_red"], rtol=1e-6)
    assert np.isclose(c.gk, fit.best["G_k"], rtol=1e-6)
    assert np.isclose(c.scale, fit.best["scale"], rtol=1e-6)


def test_fit_models_fixed_parameters():
    g = _toy_grid()
    data = _grid_data(g, g.find(teff=1500, logg=5.0, mh=0, clouds=2))
    fit = bd.fit_models(data, grid=g, clouds="nc")
    assert set(fit.table["clouds"]) == {"nc"} and len(fit.table) == 6
    fit2 = bd.fit_models(data, grid=g, clouds=2)
    assert set(fit2.table["clouds"]) == {"2"}
    table = bd.fits_table([fit, fit2])
    assert list(table["spectral_type"]) == ["L5", "L5"]


def test_chi2_map_and_fit_plots():
    import matplotlib
    matplotlib.use("Agg")
    g = _toy_grid()
    fit = bd.fit_models(_grid_data(g, 3), grid=g)
    fig, ax = bd.plot_chi2_map(fit, "teff", "clouds")
    assert ax.images[0].get_array().shape == (2, 3)
    bd.plot_fit_parameters(bd.fits_table([fit, fit]))
    bd.plot_fit_residuals([fit])


def test_index_difference_against_model_uses_data_error_only():
    s = _index_spec(0.6, 0.01)
    m = s.copy(err=None)
    m = m.copy(flux=s.flux.copy())
    d = bd.index_difference(s, m, "CH4")
    assert np.isclose(d["err"], bd.compute_index(s, "CH4").err) and np.isclose(d["difference"], 0)


# -------------------------------------------------------------------- io
def test_write_read_roundtrip(tmp_path=None):
    import tempfile
    tmp = Path(tmp_path or tempfile.mkdtemp())
    s = bd.Spectrum(np.linspace(1, 2, 5), np.arange(5.0) + 1, np.full(5, 0.1), "Jy", "round trip",
                    {"spectral_type": "T4", "distance_pc": 13.89, "source": "test: a colon"})
    p = bd.write_spectrum(s, tmp / "x.csv")
    r = bd.read_spectrum(p)
    assert np.allclose(r.flux, s.flux) and r.flux_unit == "Jy"
    assert r.meta["distance_pc"] == 13.89 and r.meta["spectral_type"] == "T4"
    assert r.meta["source"] == "test: a colon"


def test_bands_file_is_consistent():
    bands = bd.load_bands()
    for name, ab in bands["absorbers"].items():
        assert ab["color"].startswith("#")
        for b in ab["bands"]:
            lo, hi = b["range_um"]
            assert 0.7 <= lo < hi <= 5.2, name
            assert b["status"] in ("spec", "to_verify", "checked", "uncertain"), name


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for n, f in tests:
        try:
            f()
            print(f"PASS  {n}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL  {n}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
