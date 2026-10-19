"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Spezifikationen."""

import kpf_constants as C
import kpf_evaluation as ev
import kpf_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds_and_choices():
    for name, p in C.PRESETS.items():
        assert C.N_MIN <= p["n"] <= C.N_MAX, name
        assert C.OUT_MIN <= p["out"] <= C.OUT_MAX and abs(p["out"] / C.OUT_STEP - round(p["out"] / C.OUT_STEP)) < 1e-9, name   # auf dem Reglerraster
        assert 0 <= p["seed"] <= C.SEED_MAX and p["shape"] in C.SHAPES and p["runs"] in C.RUNS, name
        assert C.LEVEL_MIN <= p["level"] <= C.LEVEL_MAX and (p["level"] - C.LEVEL_MIN) % C.LEVEL_STEP == 0, name


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS.values()))
    assert ev.Settings(**first) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_choice_specs_name_their_allowed_values_and_the_steps_snap_permalink_values():
    assert P.SETTING_SPECS["shape_select"].choices == C.SHAPES and P.SETTING_SPECS["runs_select"].choices == C.RUNS
    assert set(C.SHAPE_NAMES) == set(C.SHAPES) == set(C.SHAPE_FACTORS) and C.DEFAULT_RUNS in C.RUNS and list(C.RUNS) == sorted(C.RUNS)
    assert P.SETTING_SPECS["level_slider"].step == C.LEVEL_STEP and P.SETTING_SPECS["out_slider"].step == C.OUT_STEP


def test_shape_factors_are_ordered_and_the_mean_never_falls_below_the_mode():
    for shape, (low, high) in C.SHAPE_FACTORS.items():
        assert 0 < low < 1 < high and (low + 1 + high) / 3 >= 1, shape


def test_crit_runs_do_not_exceed_the_smallest_run_count_by_construction():
    assert C.CRIT_RUNS <= C.RUNS[2] and C.DEFAULT_LEVEL % C.LEVEL_STEP == 0
