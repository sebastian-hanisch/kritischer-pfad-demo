"""Jede Zahl im README (Abschnitt „Befunde“) wird hier über dieselben Auswertungsfunktionen wie in der App nachgerechnet (DEMO-PLAYBOOK §4).

Mediane über feste Pläne, nie ein einzelner Zufalls-Seed. Zählungen und Puffer (ganze Tage) stehen exakt da; Monte-Carlo-Werte (feste Seeds, nur `random()`/`triangular()`)
mit Toleranz von einer Einheit der letzten angegebenen Stelle."""

import pytest

import kpf_algorithm as A
import kpf_constants as C
import kpf_evaluation as ev

from conftest import MINI, cached


def test_few_tasks_are_critical_and_free_float_zero_is_not_critical():
    rows = cached("buffer_rows")
    assert [(r["n"], r["out"], r["instances"]) for r in rows] == [(60, 1.0, 30), (60, 2.0, 30), (60, 3.0, 30)]
    assert [round(100 * r["critical_share"], 1) for r in rows] == [10.0, 13.3, 18.3] and [r["paths_median"] for r in rows] == [1, 1, 1] and [r["paths_max"] for r in rows] == [4, 2, 3]
    assert [round(100 * r["free_zero_share"], 1) for r in rows] == [43.3, 51.7, 55.0]
    assert [r["total_float_median"] for r in rows] == [16, 16.75, 11.5]


def test_the_expected_plan_is_kept_in_at_most_half_of_the_runs_and_the_plan_of_the_likeliest_durations_almost_never():
    rows = {r["shape"]: r for r in cached("shape_rows")}
    assert {r["instances"] for r in rows.values()} == {15} and {r["runs"] for r in rows.values()} == {1000}
    assert [round(rows[k]["bias"], 1) for k in C.SHAPES] == [0.1, 0.9, 5.2] and [round(rows[k]["bias_max"], 1) for k in C.SHAPES] == [1.6, 5.9, 13.5]
    assert [rows[k]["p_mean"] for k in C.SHAPES] == pytest.approx([0.501, 0.452, 0.345], abs=1e-9)
    assert [rows[k]["p_ml"] for k in C.SHAPES] == pytest.approx([0.501, 0.008, 0.0], abs=1e-9)
    assert [rows[k]["p_pert"] for k in C.SHAPES] == pytest.approx([0.501, 0.131, 0.03], abs=1e-9)


def test_the_bias_falls_with_density_and_does_not_grow_with_size():
    rows = cached("scaling_rows")
    assert [(r["n"], r["out"], round(r["bias"], 1)) for r in rows] == [(20, 2.0, 4.9), (40, 1.0, 8.8), (40, 2.0, 4.7), (40, 3.0, 4.7), (40, 4.0, 3.8), (80, 2.0, 5.5)]
    assert [r["p_mean"] for r in rows] == pytest.approx([0.4, 0.2875, 0.385, 0.36875, 0.36125, 0.345], abs=1e-9)


def test_the_critical_path_wanders():
    row = cached("criticality_rows")
    assert (row["tasks"], row["with_float"], row["sometimes_critical"], row["often_critical"], row["critical"], row["critical_rare"]) == (600, 468, 114, 41, 132, 12)
    assert row["with_float"] + row["critical"] == row["tasks"]


def test_a_buffer_per_task_plans_too_much():
    row = cached("task_buffer_rows")
    assert round(row["ratio"], 2) == 1.15 and round(row["ratio_min"], 2) == 1.1 and round(row["ratio_max"], 2) == 1.2 and round(row["project_buffer_pct"], 1) == 16.2


def test_the_pert_formula_misses_the_triangular_mean():
    rows = cached("pert_rows")
    assert [(r["shape"], round(r["pert"], 3), round(r["mean"], 3), round(r["deviation_pct"], 1)) for r in rows] == [
        ("symmetrisch", 1.0, 1.0, 0.0), ("rechtsschief", 1.083, 1.167, -7.1), ("stark", 1.25, 1.5, -16.7)]


def test_verdict_texts_quote_the_readme_numbers():
    assert "nur 10 bis 18 % der Aufgaben kritisch" in ev.verdict_buffers(cached("buffer_rows"))[1] and "43 bis 55 %" in ev.verdict_buffers(cached("buffer_rows"))[1]
    assert "0,1 % (symmetrisch), 0,9 % (rechtsschief), 5,2 % (stark rechtsschief)" in ev.verdict_shape(cached("shape_rows"))[1]
    assert "8,8 % bei Ausgangsgrad 1 gegen 3,8 % bei 4" in ev.verdict_scaling(cached("scaling_rows"))[1]
    assert "Von 468 Aufgaben mit Puffer größer null sind 114 (24 %)" in ev.verdict_criticality(cached("criticality_rows"))[1]
    assert "das 1,15-fache" in ev.verdict_task_buffers(cached("task_buffer_rows"))[1]


def test_the_hand_computed_mini_instances_are_the_documented_ones():
    """Kette 9 Tage, Parallelzweig mit 2 Tagen Puffer, Raute mit zwei kritischen Pfaden, Aufgabe mit freiem Puffer null und Gesamtpuffer 6."""
    assert [A.schedule(*MINI[k][:2]).duration for k in ("kette", "parallel", "raute_gleich", "ff_null")] == [9, 8, 6, 11]
    assert A.schedule(*MINI["ff_null"][:2]).total_float[1] == 6 and A.schedule(*MINI["ff_null"][:2]).free_float[1] == 0
    assert A.critical_path_count(*MINI["raute_gleich"][:2]) == 2


def test_the_slider_maximum_has_the_documented_edge_count():
    from kpf_scenario import edge_count
    assert edge_count(C.N_MAX, C.OUT_MAX) == 320 and C.RUNS[-1] == 5000
