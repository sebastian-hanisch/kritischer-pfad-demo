"""Jede Einheit an den von Hand gerechneten Mini-Instanzen (conftest.MINI), DEMO-PLAYBOOK §1b.

Handrechnungen stehen als Kommentar neben dem erwarteten Wert."""

import pytest

import kpf_algorithm as A

from conftest import MINI


@pytest.mark.parametrize("name", [k for k in MINI if k != "leer"])
def test_duration_floats_and_critical_path_count_of_every_mini_instance(name):
    adj, dur, total, tf, ff, paths = MINI[name]
    sch = A.schedule(adj, dur)
    assert sch.duration == total and sch.total_float == tuple(float(x) for x in tf) and sch.free_float == tuple(float(x) for x in ff)
    assert A.critical_path_count(adj, dur) == paths
    assert A.critical_activities(sch) == tuple(v for v in range(len(adj)) if tf[v] == 0)


def test_the_empty_plan_has_duration_zero():
    sch = A.schedule((), ())
    assert sch.duration == 0 and sch.es == () and A.critical_activities(sch) == () and A.critical_path_count((), ()) == 0 and A.one_critical_path((), ()) == ()


def test_forward_and_backward_pass_of_the_chain_and_the_parallel_plan():
    sch = A.schedule(*MINI["kette"][:2])
    assert sch.es == (0, 3, 7) and sch.ef == (3, 7, 9) and sch.ls == (0, 3, 7) and sch.lf == (3, 7, 9)
    par = A.schedule(*MINI["parallel"][:2])
    assert par.es == (0, 2, 2, 7) and par.ef == (2, 7, 5, 8) and par.ls == (0, 2, 4, 7) and par.lf == (2, 7, 7, 8)       # Aufgabe 2: 2 bis 5, spätestens 4 bis 7


def test_free_float_zero_does_not_mean_critical():
    adj, dur = MINI["ff_null"][:2]
    sch = A.schedule(adj, dur)
    assert sch.free_float[1] == 0 and sch.total_float[1] == 6 and 1 not in A.critical_activities(sch)


def test_one_critical_path_is_a_gapless_chain_from_a_source_to_a_sink():
    assert A.one_critical_path(*MINI["kette"][:2]) == (0, 1, 2)
    assert A.one_critical_path(*MINI["parallel"][:2]) == (0, 1, 3)
    assert A.one_critical_path(*MINI["raute_gleich"][:2]) == (0, 1, 3)                 # Gleichstand: kleinere Aufgabennummer
    assert A.one_critical_path(*MINI["mehrere_enden"][:2]) == (1, 2, 4)
    assert A.one_critical_path(*MINI["meilenstein"][:2]) == (0, 1, 2)
    assert A.one_critical_path(*MINI["unabhaengig"][:2]) == (0,)


def test_a_cycle_is_rejected():
    with pytest.raises(ValueError):
        A.schedule(((1,), (0,)), (1, 1))
    with pytest.raises(ValueError):
        A.monte_carlo(((1,), (0,)), (1, 1), (0.8, 1.2), 10, 1)


def test_delay_effect_follows_the_total_float():
    adj, dur = MINI["parallel"][:2]
    assert A.delay_effect(adj, dur, 2, 2) == 8 and A.delay_effect(adj, dur, 2, 3) == 9       # Puffer 2: bis 2 Tage Verspätung kosten nichts
    assert A.delay_effect(adj, dur, 1, 4) == 12 and A.delay_effect(adj, dur, 1, 0) == 8      # kritische Aufgabe: jede Verspätung wirkt voll


def test_triangular_formulas_by_hand():
    assert A.triangular_mean(0, 1, 2) == 1 and A.triangular_mean(0, 1, 3) == pytest.approx(4 / 3)
    assert A.pert_mean(0.7, 1, 1.8) == pytest.approx(6.5 / 6) and A.pert_mean(0, 1, 2) == 1
    assert A.triangular_quantile(0, 1, 2, 0.5) == 1 and A.triangular_quantile(0, 1, 2, 0.125) == pytest.approx(0.5) and A.triangular_quantile(0, 1, 2, 0.875) == pytest.approx(1.5)
    assert A.triangular_quantile(0, 1, 3, 1 / 3) == pytest.approx(1) and A.triangular_quantile(0, 1, 3, 1.0) == 3 and A.triangular_quantile(0, 1, 3, 0.0) == 0
    assert A.triangular_quantile(2, 2, 2, 0.7) == 2


def test_the_pert_formula_misses_the_triangular_mean_for_skewed_shapes():
    for factors, expected in (((0.8, 1.2), 0.0), ((0.7, 1.8), 1.0833333333333333 / 1.1666666666666667 - 1), ((0.5, 3.0), 1.25 / 1.5 - 1)):
        pert = A.pert_mean(factors[0], 1, factors[1])
        tri = A.triangular_mean(factors[0], 1, factors[1])
        assert pert / tri - 1 == pytest.approx(expected)


def test_plans_with_means_and_task_quantiles():
    adj, dur = MINI["parallel"][:2]
    assert A.plan_with_means(adj, dur, (1.0, 1.0)) == 8                                  # ohne Streuung: der Plan selbst
    assert A.plan_with_task_quantile(adj, dur, (1.0, 1.0), 0.8) == 8
    assert A.plan_with_means(adj, dur, (0.5, 3.0)) == pytest.approx(1.5 * 8)             # Erwartungswert 1,5 d: alle Dauern mal 1,5
    assert A.plan_with_task_quantile(adj, dur, (0.5, 3.0), 0.8) > A.plan_with_task_quantile(adj, dur, (0.5, 3.0), 0.5)
    assert A.plan_with_pert_means(adj, dur, (0.5, 3.0)) == pytest.approx(1.25 * 8)


def test_empirical_quantile_uses_the_nearest_rank_and_the_share_helper():
    values = [1, 2, 3, 4, 5]
    assert A.quantile(values, 0.0) == 1 and A.quantile(values, 0.5) == 3 and A.quantile(values, 0.8) == 5 and A.quantile(values, 1.0) == 5
    assert A.share_at_most(values, 3) == 0.6 and A.share_at_most(values, 0) == 0.0 and A.share_at_most([], 3) == 0.0


def test_monte_carlo_is_deterministic_sorted_and_respects_the_bounds():
    adj, dur = MINI["parallel"][:2]
    a = A.monte_carlo(adj, dur, (0.5, 3.0), 300, 7, crit_runs=100)
    b = A.monte_carlo(adj, dur, (0.5, 3.0), 300, 7, crit_runs=100)
    c = A.monte_carlo(adj, dur, (0.5, 3.0), 300, 8, crit_runs=100)
    assert a == b and a.makespans != c.makespans and list(a.makespans) == sorted(a.makespans) and len(a.makespans) == 300
    assert 0.5 * 6 <= a.makespans[0] and a.makespans[-1] <= 3.0 * 8 and a.mean == pytest.approx(sum(a.makespans) / 300)


def test_criticality_index_is_a_share_and_the_chain_is_always_critical():
    adj, dur = MINI["kette"][:2]
    mc = A.monte_carlo(adj, dur, (0.5, 3.0), 200, 3, crit_runs=50)
    assert mc.criticality == (1.0, 1.0, 1.0) and mc.crit_runs == 50
    par = A.monte_carlo(*MINI["parallel"][:2], (0.5, 3.0), 400, 3, crit_runs=400)
    assert all(0.0 <= x <= 1.0 for x in par.criticality) and par.criticality[0] == 1.0 and par.criticality[3] == 1.0 and 0 < par.criticality[2] < 1
    assert A.monte_carlo(adj, dur, (0.8, 1.2), 10, 1).criticality == (0.0, 0.0, 0.0)        # ohne crit_runs wird nichts gezählt


def test_a_chain_of_parallel_branches_shows_the_merge_bias():
    """Sechs gleich lange Zweige aus je drei Aufgaben, die am Ende zusammenlaufen: Das Maximum der Zweige liegt über dem Zweig mit Erwartungswerten."""
    adj = tuple([(1,), (2,), (18,)] * 6 + [()])
    adj = tuple(tuple(w + 3 * (i // 3) if w != 18 else 18 for w in adj[i]) for i in range(18)) + ((),)
    dur = (4, 4, 4) * 6 + (1,)
    mean_plan = A.plan_with_means(adj, dur, (0.5, 3.0))
    mc = A.monte_carlo(adj, dur, (0.5, 3.0), 1500, 5)
    assert mc.mean > 1.03 * mean_plan and A.share_at_most(mc.makespans, mean_plan) < 0.4


def test_topological_order_and_predecessors():
    assert A.topological_order(((1,), (0,))) is None and A.topological_order(MINI["parallel"][0]) is not None
    assert A.predecessors(MINI["parallel"][0]) == [[], [0], [0], [1, 2]]


def test_triangular_quantile_with_a_positive_lower_bound():
    """Dreieck (1, 2, 4): Gipfel bei einem Drittel der Fläche; q = 0,1 liegt links, q = 0,5 rechts vom Gipfel (von Hand: 1 + sqrt(0,3) und 4 - sqrt(3))."""
    assert A.triangular_quantile(1, 2, 4, 0.1) == pytest.approx(1 + 0.3 ** 0.5)
    assert A.triangular_quantile(1, 2, 4, 0.5) == pytest.approx(4 - 3 ** 0.5)
    assert A.triangular_quantile(1, 2, 4, 1 / 3) == pytest.approx(2)
    assert A.triangular_mean(1, 2, 4) == pytest.approx(7 / 3)
