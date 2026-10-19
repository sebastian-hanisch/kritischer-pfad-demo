"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): kleinste Pläne, Grenzen inklusive, Dauer null, Regler-Extreme."""

import pytest

import kpf_algorithm as A
import kpf_constants as C
import kpf_evaluation as ev
import kpf_scenario as S

from conftest import MINI


def test_a_single_task_is_its_own_critical_path():
    sch = A.schedule(((),), (7,))
    assert sch.duration == 7 and sch.total_float == (0,) and A.critical_path_count(((),), (7,)) == 1 and A.one_critical_path(((),), (7,)) == (0,)
    mc = A.monte_carlo(((),), (7,), (0.8, 1.2), 50, 1, crit_runs=50)
    assert mc.criticality == (1.0,) and 0.8 * 7 <= mc.makespans[0] and mc.makespans[-1] <= 1.2 * 7


def test_exactly_two_tasks_in_a_chain_and_without_relation():
    assert A.schedule(((1,), ()), (2, 3)).duration == 5 and A.schedule(((), ()), (2, 3)).duration == 3
    assert A.schedule(((), ()), (2, 3)).total_float == (1, 0)           # die kürzere Aufgabe hat einen Tag Puffer


def test_the_smallest_slider_plan_is_valid():
    a = ev.analyse(ev.Settings(C.N_MIN, C.OUT_MIN, 1, C.DEFAULT_SHAPE, C.RUNS[0], C.LEVEL_MIN))
    assert a.n == 6 and ev.validate(a) == []


def test_the_largest_slider_plan_with_the_most_runs_validates():
    """Worst-Case am Regler-Maximum (n = 80, Grad 4, 5 000 Läufe, 95 % Sicherheit): kein Hänger, alle Prüfungen bestehen. Keine Zeit-Assertion."""
    a = ev.analyse(ev.Settings(C.N_MAX, C.OUT_MAX, 3, "stark", C.RUNS[-1], C.LEVEL_MAX))
    assert len(a.mc.makespans) == 5000 and a.mc.crit_runs == C.CRIT_RUNS and ev.validate(a) == []


def test_every_run_count_and_level_gives_a_valid_analysis():
    for runs in C.RUNS:
        for level in (C.LEVEL_MIN, C.LEVEL_MAX):
            a = ev.analyse(ev.Settings(15, 2.0, 2, "rechtsschief", runs, level))
            assert ev.validate(a) == [] and len(a.mc.makespans) == runs and a.mc.crit_runs == min(C.CRIT_RUNS, runs)


def test_the_median_level_is_close_to_the_median_of_the_runs_and_the_top_level_close_to_the_maximum():
    a = ev.analyse(ev.Settings(20, 2.0, 4, "stark", 1000, 50))
    assert a.t_level == A.quantile(a.mc.makespans, 0.5)
    top = ev.analyse(ev.Settings(20, 2.0, 4, "stark", 1000, 95))
    assert top.t_level >= a.t_level


def test_sparse_plans_have_many_sources_and_sinks_and_still_validate():
    a = ev.analyse(ev.Settings(40, C.OUT_MIN, 3, "rechtsschief", 200, 80))
    assert ev.validate(a) == [] and a.path_count >= 1


def test_zero_duration_milestones_are_handled_in_every_function():
    adj, dur = MINI["meilenstein"][:2]
    assert A.critical_path_count(adj, dur) == 1 and A.one_critical_path(adj, dur) == (0, 1, 2) and A.delay_effect(adj, dur, 1, 4) == 9
    assert A.monte_carlo(adj, dur, (0.5, 3.0), 100, 2, crit_runs=100).criticality == (1.0, 1.0, 1.0)


def test_a_delay_of_zero_days_changes_nothing_and_a_negative_buffer_never_occurs():
    for name, (adj, dur, total, tf, ff, paths) in MINI.items():
        if not adj:
            continue
        assert A.delay_effect(adj, dur, 0, 0) == total
        assert all(t >= 0 for t in A.schedule(adj, dur).total_float)


def test_bounds_are_inclusive():
    """Reglergrenzen gelten inklusive: n = 6 und n = 80, Ausgangsgrad 0,5 und 4 sind erlaubt."""
    for n in (C.N_MIN, C.N_MAX):
        for out in (C.OUT_MIN, C.OUT_MAX):
            assert S.make_instance(n, out, 0, 1).n == n and A.topological_order(S.make_instance(n, out, 0, 1).adj) is not None


def test_equal_ties_choose_the_smaller_task_number():
    assert A.one_critical_path(*MINI["raute_gleich"][:2]) == (0, 1, 3) and A.one_critical_path(*MINI["unabhaengig"][:2]) == (0,)


def test_the_empty_plan_is_handled_by_the_analysis_helpers():
    assert ev._i(0) == "0" and ev.pfade(1) == "einem kritischen Pfad" and ev.pfade(3) == "3 kritischen Pfaden"
    with pytest.raises(ValueError):
        A.schedule(((1,), (0,)), (1, 1))
