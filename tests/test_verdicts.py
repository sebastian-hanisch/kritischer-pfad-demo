"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Seeds; ohne diese Datei überleben fast alle Mutanten der Verdikt-Arithmetik."""

import dataclasses

import kpf_algorithm as A
import kpf_evaluation as ev
import kpf_scenario as S

from conftest import MINI


def _analysis(name="parallel", **kw):
    adj, dur = MINI[name][:2]
    inst = S.Instance(tuple(tuple(w) for w in adj), tuple(range(len(adj))), frozenset())
    return ev.analyse_plan(inst, dur, ev.Settings(runs=200, **kw))


# --- Kernfrage ---------------------------------------------------------------------------------------------------------------------------

def test_question_text_and_the_threshold_between_warning_and_info():
    a = _analysis(shape="symmetrisch", level=80)
    below = dataclasses.replace(a, mc=dataclasses.replace(a.mc, makespans=tuple([9.0] * 100), mean=9.0), t_level=9.0)               # 0 % halten den Plan (8)
    above = dataclasses.replace(a, mc=dataclasses.replace(a.mc, makespans=tuple([7.0] * 100), mean=7.0), t_level=7.0)               # 100 % halten ihn
    k1, t1 = ev.verdict_question(below)
    k2, _ = ev.verdict_question(above)
    assert k1 == "warning" and k2 == "info"
    assert "**Mit den wahrscheinlichsten Dauern dauert das Vorhaben 8 Tage**; 3 von 4 Aufgaben (75 %) sind kritisch, auf einem kritischen Pfad." in t1
    assert "Mit unsicheren Dauern (symmetrisch (0,8 / 1 / 1,2)) liegt der Erwartungswert bei 9 Tagen, mit 80 % Sicherheit wird das Vorhaben in 9 Tagen fertig." in t1
    assert "Den Plan der wahrscheinlichsten Dauern hält man in 0 % der Läufe ein, den Plan der Erwartungswerte (8 Tage) in 0 %." in t1


def test_question_with_exactly_half_the_runs_within_the_plan_is_informational():
    a = _analysis(shape="symmetrisch")
    half = dataclasses.replace(a, mc=dataclasses.replace(a.mc, makespans=tuple([7.0] * 50 + [9.0] * 50), mean=8.0))
    assert ev.verdict_question(half)[0] == "info"


# --- E1 ---------------------------------------------------------------------------------------------------------------------------------

def _b(out, crit, paths, pmax, free):
    return {"n": 60, "out": out, "instances": 30, "critical_share": crit, "paths_median": paths, "paths_max": pmax, "total_float_median": 15, "free_zero_share": free}


def test_buffers_names_the_ranges_and_that_free_float_zero_is_not_critical():
    rows = [_b(1.0, 0.10, 1.0, 4, 0.4333), _b(2.0, 0.1333, 1.0, 2, 0.5167), _b(3.0, 0.1833, 1.0, 3, 0.55)]
    kind, text = ev.verdict_buffers(rows)
    assert kind == "info"
    assert "Bei 60 Aufgaben sind im Median nur 10 bis 18 % der Aufgaben kritisch (Ausgangsgrad 1 bis 3), im Median auf einem kritischen Pfad (höchstens 4); freien Puffer null haben dagegen 43 bis 55 %" in text
    assert ev.verdict_buffers([_b(1.0, 0.6, 2.0, 5, 0.5)])[0] == "warning" and "auf 2 kritischen Pfaden" in ev.verdict_buffers([_b(1.0, 0.6, 2.0, 5, 0.5)])[1]


# --- E2 ---------------------------------------------------------------------------------------------------------------------------------

def _s(shape, bias, p_mean, p_ml):
    return {"shape": shape, "n": 40, "out": 2.0, "instances": 15, "runs": 1000, "bias": bias, "bias_max": 5, "p_mean": p_mean, "p_ml": p_ml, "p_pert": p_mean}


def test_shape_names_bias_and_probabilities_in_order():
    rows = [_s("symmetrisch", 0.11, 0.501, 0.501), _s("rechtsschief", 0.8993, 0.452, 0.008), _s("stark", 5.19, 0.345, 0.0)]
    kind, text = ev.verdict_shape(rows)
    assert kind == "info"
    assert "im Median 0,1 % (symmetrisch), 0,9 % (rechtsschief), 5,2 % (stark rechtsschief) über der Dauer des Plans der Erwartungswerte" in text
    assert "Diesen Plan hält man in 50 / 45 / 34 % der Läufe ein, den Plan der wahrscheinlichsten Dauern in nur 50 / 1 / 0 %" in text
    assert ev.verdict_shape([_s("symmetrisch", 0.1, 0.5, 0.5), _s("stark", 0.05, 0.6, 0.0)])[0] == "warning"


# --- E3 ---------------------------------------------------------------------------------------------------------------------------------

def _g(n, out, bias, p):
    return {"shape": "stark", "n": n, "out": out, "instances": 15, "runs": 800, "bias": bias, "bias_max": 12, "p_mean": p, "p_ml": 0.0, "p_pert": 0.02}


def test_scaling_separates_the_effect_of_density_from_the_effect_of_size():
    rows = [_g(20, 2.0, 4.885, 0.4), _g(40, 1.0, 8.844, 0.2875), _g(40, 2.0, 4.717, 0.385), _g(40, 3.0, 4.689, 0.3688), _g(40, 4.0, 3.822, 0.3613), _g(80, 2.0, 5.456, 0.345)]
    kind, text = ev.verdict_scaling(rows)
    assert kind == "info"
    assert "Mit der Dichte sinkt die Verzerrung: 8,8 % bei Ausgangsgrad 1 gegen 3,8 % bei 4 (n = 40)." in text
    assert "Mit der Plangröße ändert sie sich dagegen kaum: 4,9 % bei n = 20 gegen 5,5 % bei n = 80 (Ausgangsgrad 2)." in text
    assert "zwischen 29 und 40 %" in text


def test_scaling_warns_when_density_does_not_lower_the_bias():
    rows = [_g(20, 2.0, 4.0, 0.4), _g(40, 1.0, 3.0, 0.3), _g(40, 2.0, 4.0, 0.3), _g(40, 4.0, 6.0, 0.3), _g(80, 2.0, 5.0, 0.3)]
    assert ev.verdict_scaling(rows)[0] == "warning"


# --- E4 / E5 / E6 -----------------------------------------------------------------------------------------------------------------------

def test_criticality_names_the_counts_and_shares():
    row = {"tasks": 600, "with_float": 468, "sometimes_critical": 114, "often_critical": 41, "critical": 132, "critical_rare": 12}
    kind, text = ev.verdict_criticality(row)
    assert kind == "info"
    assert "Von 468 Aufgaben mit Puffer größer null sind 114 (24 %) in einzelnen Läufen kritisch, 41 (9 %) in mindestens 10 % der Läufe." in text
    assert "Von 132 deterministisch kritischen Aufgaben sind 12 in weniger als der Hälfte der Läufe kritisch" in text
    assert ev.verdict_criticality({**row, "sometimes_critical": 0})[0] == "warning"


def test_task_buffers_names_ratio_range_and_project_buffer():
    row = {"ratio": 1.1472, "ratio_min": 1.0969, "ratio_max": 1.1982, "project_buffer_pct": 16.2268, "level": 0.8}
    kind, text = ev.verdict_task_buffers(row)
    assert kind == "info"
    assert "ergibt der Vorwärtslauf im Median das 1,15-fache des echten Projekt-80 %-Quantils (1,10 bis 1,20)" in text and "im Median 16,2 %" in text
    assert ev.verdict_task_buffers({**row, "ratio_min": 0.99})[0] == "warning"


def test_pert_names_the_deviation_per_shape():
    rows = [{"shape": "symmetrisch", "pert": 1.0, "mean": 1.0, "deviation_pct": 0.0}, {"shape": "rechtsschief", "pert": 1.0833, "mean": 1.1667, "deviation_pct": -7.1429},
            {"shape": "stark", "pert": 1.25, "mean": 1.5, "deviation_pct": -16.6667}]
    kind, text = ev.verdict_pert(rows)
    assert kind == "info"
    assert "symmetrisch: 1 statt 1 (0 %); rechtsschief: 1,083 statt 1,167 (-7,1 %); stark rechtsschief: 1,250 statt 1,500 (-16,7 %)" in text
    assert ev.verdict_pert([rows[0], dict(rows[0], shape="stark")])[0] == "warning"
