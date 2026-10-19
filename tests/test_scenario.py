"""Szenario: Erzeugung ist deterministisch, Dauern sind ganze Zahlen von 1 bis 10, ohne Widersprüche ist der Plan ein DAG."""

import kpf_algorithm as A
import kpf_scenario as S


def test_same_input_gives_the_same_instance_and_the_seed_matters():
    a = S.make_instance(30, 2.0, 0, 17)
    assert a == S.make_instance(30, 2.0, 0, 17) and a != S.make_instance(30, 2.0, 0, 18)


def test_number_of_relations_is_n_times_degree_capped_by_all_pairs():
    assert S.make_instance(12, 2.0, 0, 1).m == 24 and S.edge_count(6, 6.0) == 15 and S.edge_count(80, 4.0) == 320


def test_a_plan_without_contradictions_is_acyclic_and_every_relation_points_forward():
    inst = S.make_instance(50, 3.0, 0, 4)
    pos = inst.position()
    assert A.topological_order(inst.adj) is not None and all(pos[a] < pos[b] for a in range(inst.n) for b in inst.adj[a])


def test_durations_are_whole_days_from_one_to_ten_and_deterministic():
    d = S.durations(500, 3)
    assert set(d) == set(range(1, 11)) and d == S.durations(500, 3) and d != S.durations(500, 4) and len(S.durations(7, 3)) == 7
    assert S.durations(0, 1) == ()


def test_durations_are_a_prefix_stable_stream():
    """Die ersten Dauern bleiben gleich, wenn man mehr Aufgaben anlegt (eigene Zufallsquelle, unabhängig von den Beziehungen)."""
    assert S.durations(12, 5)[:6] == S.durations(6, 5)


def test_plan_is_a_permutation_and_there_are_no_self_loops_or_duplicates():
    inst = S.make_instance(40, 4.0, 0, 2)
    assert sorted(inst.plan) == list(range(40))
    for a in range(inst.n):
        assert a not in inst.adj[a] and len(set(inst.adj[a])) == len(inst.adj[a]) and list(inst.adj[a]) == sorted(inst.adj[a])


def test_same_generator_as_the_first_pieces_of_the_series():
    """Dieselbe Instanz wie im Lehrbeispiel von di-kreis-demo (12 Aufgaben, Grad 2, Seed 7), hier mit 0 Widersprüchen: 24 Beziehungen."""
    assert S.make_instance(12, 2.0, 0, 7).m == 24 and S.make_instance(12, 2.0, 1, 7).m == 24
