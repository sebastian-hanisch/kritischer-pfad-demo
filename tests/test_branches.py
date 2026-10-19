"""Zweige der Hauptansicht (Nullspalte-Lehre): Jeder Weg, den die App zeigt, kommt in mindestens einem Preset oder einer festen Instanz vor.

Ein Preset, das seine Beschreibung nicht einlöst (z. B. „Zwei kritische Pfade“ mit einem Pfad), fällt hier auf."""

import pytest

import kpf_algorithm as A
import kpf_constants as C
import kpf_evaluation as ev


def _a(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def _zero_free_but_not_critical(a):
    return [v for v in range(a.n) if v not in a.critical and a.sch.free_float[v] <= C.EPS]


def test_lehrbeispiel_has_one_critical_path_and_some_buffer():
    a = _a("Lehrbeispiel (12 Aufgaben)")
    assert a.path_count == 1 and 3 <= len(a.critical) <= 8 and a.p_keep_ml < 0.1 and len(a.path) >= 2


def test_two_critical_paths():
    a = _a("Zwei kritische Pfade")
    assert a.path_count >= 2 and len(a.critical) > len(a.path)


def test_free_float_zero_without_being_critical():
    a = _a("Kein Puffer ist nicht kritisch")
    assert len(_zero_free_but_not_critical(a)) >= 5


def test_the_plan_of_the_expected_durations_is_rarely_kept():
    a = _a("Der Plan wird selten gehalten")
    assert a.p_keep_mean <= 0.30 and a.p_keep_ml == 0.0 and a.bias_pct > 8


def test_the_critical_path_wanders():
    a = _a("Der kritische Pfad wandert")
    crit = set(a.critical)
    often = [v for v in range(a.n) if v not in crit and a.mc.criticality[v] >= 0.2]
    rare = [v for v in a.critical if a.mc.criticality[v] < 0.6]
    assert len(often) >= 4 and len(rare) >= 1


def test_a_buffer_per_task_is_far_too_much():
    a = _a("Puffer je Aufgabe ist zu viel")
    assert a.t_task_level / a.t_level >= 1.17


def test_symmetric_durations_are_nearly_unbiased_but_still_a_coin_flip():
    a = _a("Symmetrisch: kaum Verzerrung")
    assert abs(a.bias_pct) <= 0.3 and 0.45 <= a.p_keep_mean <= 0.55 and a.sch.duration == pytest.approx(a.t_mean)


def test_every_shape_is_used_by_some_preset():
    assert {p["shape"] for p in C.PRESETS.values()} == set(C.SHAPES)


def test_a_chain_has_no_merge_event_and_no_buffer():
    """Eine Kette hat nur einen Pfad: alle Aufgaben kritisch, Kritikalitätsindex 1; die Verzerrung ist Rauschen (Summe unabhängiger Dauern, Mittel gleich Erwartungswert)."""
    adj = tuple((v + 1,) for v in range(19)) + ((),)
    dur = (3,) * 20
    mc = A.monte_carlo(adj, dur, C.SHAPE_FACTORS["stark"], 2000, 5, crit_runs=200)
    assert A.critical_path_count(adj, dur) == 1 and mc.criticality == (1.0,) * 20
    mean_plan = A.plan_with_means(adj, dur, C.SHAPE_FACTORS["stark"])
    assert abs(mc.mean - mean_plan) / mean_plan < 0.02


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_passes_the_validation(name):
    assert ev.validate(_a(name)) == []
