"""Orakel-Test kritischer-pfad-demo: Projektdauer, Puffer, kritische Pfade und Verspätungssatz gegen Aufzählung aller Pfade, networkx und eine LP-Formulierung (DEMO-PLAYBOOK §12).

Unabhängiger Rechenweg: die Länge jedes Quelle-Senke-Weges durch Aufzählung (n <= 14), `networkx.dag_longest_path_length` und `scipy.optimize.linprog`
(minimiere die Projektdauer unter den Vorrangbedingungen). Feste Instanzen (range, kein Zufall), zusammen weit unter 10 Sekunden."""

import random

import pytest

import kpf_algorithm as A
import kpf_scenario as S

from conftest import all_path_lengths

nx = pytest.importorskip("networkx")


def _plans(count=160, nmin=5, nspan=10):
    for s in range(count):
        n = nmin + s % nspan
        adj = S.make_instance(n, (1.0, 2.0, 3.0)[s % 3], 0, 300 + s).adj
        yield adj, S.durations(n, s)


def test_project_duration_equals_the_longest_path_by_enumeration_and_networkx():
    for adj, dur in _plans():
        longest = max(length for _, length in all_path_lengths(adj, dur))
        g = nx.DiGraph()
        g.add_nodes_from(range(len(adj)))
        g.add_edges_from((a, b) for a in range(len(adj)) for b in adj[a])
        g.add_node("s")
        for v in range(len(adj)):
            if not any(v in adj[u] for u in range(len(adj))):
                g.add_edge("s", v)
        for u, v in g.edges:
            g[u][v]["w"] = dur[v] if v != "s" else 0
        assert A.schedule(adj, dur).duration == longest == nx.dag_longest_path_length(g, weight="w")


def test_project_duration_equals_the_linear_program():
    linprog = pytest.importorskip("scipy.optimize").linprog
    for adj, dur in list(_plans(60)):
        n = len(adj)
        rows, rhs = [], []
        for u in range(n):
            for v in adj[u]:
                row = [0.0] * (n + 1)
                row[u], row[v] = 1.0, -1.0                       # start_u + d_u <= start_v
                rows.append(row)
                rhs.append(-dur[u])
        for v in range(n):
            row = [0.0] * (n + 1)
            row[v], row[n] = 1.0, -1.0                           # start_v + d_v <= T
            rows.append(row)
            rhs.append(-dur[v])
        res = linprog([0.0] * n + [1.0], A_ub=rows, b_ub=rhs, bounds=[(0, None)] * (n + 1), method="highs")
        assert res.status == 0 and res.fun == pytest.approx(A.schedule(adj, dur).duration)


def test_total_float_equals_the_project_duration_minus_the_longest_path_through_the_task():
    for adj, dur in _plans(120):
        sch = A.schedule(adj, dur)
        paths = all_path_lengths(adj, dur)
        for v in range(len(adj)):
            through = max(length for path, length in paths if v in path)
            assert sch.total_float[v] == pytest.approx(sch.duration - through)


def test_critical_activities_and_paths_equal_the_enumeration():
    multi = 0
    for adj, dur in _plans(120):
        sch = A.schedule(adj, dur)
        paths = all_path_lengths(adj, dur)
        longest = [p for p, length in paths if length == sch.duration]
        assert A.critical_path_count(adj, dur) == len(longest)
        assert set(A.critical_activities(sch)) == {v for p in longest for v in p}
        assert A.one_critical_path(adj, dur) in longest and A.one_critical_path(adj, dur) == min(longest)       # kleinste Folge bei Gleichstand
        multi += len(longest) > 1
    assert multi >= 5                                                                  # beide Zweige kommen vor


def test_free_float_is_between_zero_and_the_total_float():
    for adj, dur in _plans(100):
        sch = A.schedule(adj, dur)
        assert all(0 <= f <= t + 1e-9 for f, t in zip(sch.free_float, sch.total_float))


def test_a_delay_changes_the_project_duration_exactly_by_the_part_above_the_total_float():
    rng = random.Random(4)
    for adj, dur in _plans(100):
        sch = A.schedule(adj, dur)
        v = rng.randrange(len(adj))
        extra = rng.randrange(0, 12)
        assert A.delay_effect(adj, dur, v, extra) == pytest.approx(sch.duration + max(0.0, extra - sch.total_float[v]))


def test_shortening_a_non_critical_task_changes_nothing_and_lengthening_a_critical_one_adds_fully():
    for adj, dur in _plans(80):
        sch = A.schedule(adj, dur)
        crit = set(A.critical_activities(sch))
        for v in range(len(adj)):
            if v not in crit and dur[v] > 1:
                shorter = list(dur)
                shorter[v] -= 1
                assert A.schedule(adj, shorter).duration == sch.duration
            if v in crit:
                longer = list(dur)
                longer[v] += 2
                assert A.schedule(adj, longer).duration == sch.duration + 2


def test_the_answer_does_not_depend_on_the_numbering_of_tasks():
    rng = random.Random(8)
    for adj, dur in _plans(60):
        n = len(adj)
        perm = list(range(n))
        rng.shuffle(perm)
        renamed = [[] for _ in range(n)]
        new_dur = [0] * n
        for a in range(n):
            new_dur[perm[a]] = dur[a]
            for b in adj[a]:
                renamed[perm[a]].append(perm[b])
        renamed = tuple(tuple(sorted(w)) for w in renamed)
        s1, s2 = A.schedule(adj, dur), A.schedule(renamed, tuple(new_dur))
        assert s1.duration == s2.duration and len(A.critical_activities(s1)) == len(A.critical_activities(s2))
        assert A.critical_path_count(adj, dur) == A.critical_path_count(renamed, tuple(new_dur))


def test_every_monte_carlo_run_lies_between_the_plan_with_all_lower_and_all_upper_bounds():
    for adj, dur in list(_plans(30)):
        factors = (0.5, 3.0)
        low = A.project_duration(adj, [factors[0] * d for d in dur])
        high = A.project_duration(adj, [factors[1] * d for d in dur])
        mc = A.monte_carlo(adj, dur, factors, 100, 5)
        assert low - 1e-9 <= mc.makespans[0] and mc.makespans[-1] <= high + 1e-9


def test_monte_carlo_quantiles_grow_with_the_confidence_level():
    for adj, dur in list(_plans(20)):
        mc = A.monte_carlo(adj, dur, (0.5, 3.0), 400, 9)
        values = [A.quantile(mc.makespans, q) for q in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95)]
        assert values == sorted(values)
