"""Auswertung: Analyse von Mini-Plänen, Prüfung vor der Anzeige, Formate."""

import dataclasses

import kpf_algorithm as A
import kpf_constants as C
import kpf_evaluation as ev
import kpf_scenario as S

from conftest import MINI


def _analysis(name, **kw):
    adj, dur = MINI[name][:2]
    inst = S.Instance(tuple(tuple(w) for w in adj), tuple(range(len(adj))), frozenset())
    settings = ev.Settings(runs=kw.pop("runs", 400), **kw)
    return ev.analyse_plan(inst, dur, settings)


def test_analysis_of_the_parallel_plan():
    a = _analysis("parallel", shape="symmetrisch")
    assert a.sch.duration == 8 and a.critical == (0, 1, 3) and a.path == (0, 1, 3) and a.path_count == 1 and a.n == 4
    assert a.t_mean == 8 and a.t_pert == 8 and ev.validate(a) == []                              # symmetrisch: Erwartungswert gleich wahrscheinlichste Dauer
    assert 0 < a.p_keep_ml <= 1 and a.p_keep_mean == a.p_keep_ml


def test_analysis_with_a_skewed_shape_has_a_longer_expected_plan_and_a_longer_task_quantile_plan():
    a = _analysis("parallel", shape="stark", level=80)
    assert a.t_mean == 8 * 1.5 and a.t_task_level > a.t_mean * 0.9 and a.t_mean > a.sch.duration and a.bias_pct > -5 and ev.validate(a) == []
    assert a.p_keep_ml < a.p_keep_mean


def test_validate_names_every_kind_of_error():
    a = _analysis("parallel")
    bad_dur = dataclasses.replace(a, sch=dataclasses.replace(a.sch, duration=9.0))
    assert any("weicht vom längsten Weg ab" in p for p in ev.validate(bad_dur))
    neg = dataclasses.replace(a, sch=dataclasses.replace(a.sch, total_float=(0, 0, -1, 0)))
    assert any("Puffer ist negativ" in p for p in ev.validate(neg))
    bad_free = dataclasses.replace(a, sch=dataclasses.replace(a.sch, free_float=(0, 0, 5, 0)))
    assert any("freie Puffer übersteigt" in p for p in ev.validate(bad_free))
    bad_path = dataclasses.replace(a, path=(0, 2, 3))
    assert any("lückenlose Kette" in p for p in ev.validate(bad_path))
    no_crit = dataclasses.replace(a, critical=())
    assert any("keine kritische Aufgabe" in p for p in ev.validate(no_crit))
    unsorted = dataclasses.replace(a, mc=dataclasses.replace(a.mc, makespans=tuple(reversed(a.mc.makespans))))
    assert any("nicht sortiert" in p for p in ev.validate(unsorted))
    short = dataclasses.replace(a, t_mean=a.sch.duration - 1)
    assert any("kürzer als der Plan der wahrscheinlichsten" in p for p in ev.validate(short))
    far = dataclasses.replace(a, t_level=a.mc.makespans[-1] + 5)
    assert any("außerhalb der Läufe" in p for p in ev.validate(far))


def test_the_independent_longest_path_recursion_agrees_with_the_forward_pass_on_all_minis():
    for name, (adj, dur, total, *_rest) in MINI.items():
        if adj:
            assert max(ev._longest_from(adj, dur).values()) == total


def test_labels_and_plurals():
    assert ev.label(0) == "1" and ev.pfade(1) == "einem kritischen Pfad" and ev.pfade(2) == "2 kritischen Pfaden"


def test_number_formats():
    assert ev._i(1234567) == "1.234.567" and ev._dec(12.5) == "12,5" and ev._dec(12.0) == "12" and ev._dec(1.08333, 3) == "1,083" and ev._dec(1234.5) == "1.234,5"
    assert ev._pct(0.4567) == "46" and ev._pct(0.4567, 1) == "45,7" and ev._pct(1.0) == "100" and ev._pct(0.0) == "0"


def test_settings_defaults_are_the_constants():
    s = ev.Settings()
    assert (s.n, s.out, s.seed, s.shape, s.runs, s.level) == (C.DEFAULT_N, C.DEFAULT_OUT, C.DEFAULT_SEED, C.DEFAULT_SHAPE, C.DEFAULT_RUNS, C.DEFAULT_LEVEL)


def test_the_empty_plan_has_a_defined_verdict():
    inst = S.Instance((), (), frozenset())
    a = ev.analyse_plan(inst, (), ev.Settings(n=0, runs=200))
    assert ev.verdict_question(a)[1] == "Der Plan ist leer."
