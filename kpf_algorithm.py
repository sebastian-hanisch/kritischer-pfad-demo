"""Kern der Demo (nur Standardbibliothek): kritischer Pfad, Puffer und Monte-Carlo über unsichere Dauern.

Aktivität auf dem Knoten: `adj[v]` sind die Aufgaben, die nach v kommen sollen, `dur[v]` die Dauer von v. Der Plan muss kreisfrei sein (Stücke 1 bis 3).
Vorwärtslauf: frühester Start ES und frühestes Ende EF; Rückwärtslauf: spätestes Ende LF und spätester Start LS. Gesamtpuffer = LS - ES, freier Puffer =
frühester Start der Nachfolger minus EF. Kritisch heißt Gesamtpuffer null. Jede Regel ist eine eigene Funktion (DEMO-PLAYBOOK §1b). Zufall nur über
`random.Random.random()` bzw. `triangular()` mit festem Seed (versionsstabil)."""

import random
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Schedule:
    duration: float                 # Projektdauer T
    es: tuple[float, ...]
    ef: tuple[float, ...]
    ls: tuple[float, ...]
    lf: tuple[float, ...]
    total_float: tuple[float, ...]  # Gesamtpuffer LS - ES
    free_float: tuple[float, ...]   # freier Puffer


@dataclass(frozen=True)
class MonteCarlo:
    makespans: tuple[float, ...]    # aufsteigend sortiert
    mean: float
    criticality: tuple[float, ...]  # Anteil der (ersten) `crit_runs` Läufe, in denen die Aufgabe Gesamtpuffer null hatte
    crit_runs: int


def topological_order(adj):
    """Kahn-Abbau; None, wenn der Graph einen Kreis hat."""
    n = len(adj)
    indeg = [0] * n
    for v in range(n):
        for w in adj[v]:
            indeg[w] += 1
    queue = deque(v for v in range(n) if indeg[v] == 0)
    order = []
    while queue:
        v = queue.popleft()
        order.append(v)
        for w in adj[v]:
            indeg[w] -= 1
            if indeg[w] == 0:
                queue.append(w)
    return order if len(order) == n else None


def predecessors(adj):
    pred: list[list[int]] = [[] for _ in range(len(adj))]
    for a in range(len(adj)):
        for b in adj[a]:
            pred[b].append(a)
    return pred


def schedule(adj, dur) -> Schedule:
    """Vorwärts- und Rückwärtslauf mit Puffern. Mehrere Quellen starten bei 0, mehrere Senken enden spätestens bei der Projektdauer."""
    n = len(adj)
    order = topological_order(adj)
    if order is None:
        raise ValueError("Der Plan hat einen Kreis")
    pred = predecessors(adj)
    es = [0.0] * n
    ef = [0.0] * n
    for v in order:
        es[v] = max((ef[u] for u in pred[v]), default=0.0)
        ef[v] = es[v] + dur[v]
    total = max(ef, default=0.0)
    lf = [total] * n
    ls = [0.0] * n
    for v in reversed(order):
        lf[v] = min((ls[w] for w in adj[v]), default=total)
        ls[v] = lf[v] - dur[v]
    tf = [ls[v] - es[v] for v in range(n)]
    ff = [min((es[w] for w in adj[v]), default=total) - ef[v] for v in range(n)]
    return Schedule(total, tuple(es), tuple(ef), tuple(ls), tuple(lf), tuple(tf), tuple(ff))


def project_duration(adj, dur, order=None, pred=None) -> float:
    """Nur die Projektdauer (Vorwärtslauf), für Monte-Carlo."""
    order = order if order is not None else topological_order(adj)
    pred = pred if pred is not None else predecessors(adj)
    ef = [0.0] * len(adj)
    for v in order:
        ef[v] = max((ef[u] for u in pred[v]), default=0.0) + dur[v]
    return max(ef, default=0.0)


def critical_activities(sch: Schedule, eps=1e-9) -> tuple[int, ...]:
    """Aufgaben mit Gesamtpuffer null (innerhalb der Rundungsgrenze), aufsteigend."""
    return tuple(v for v in range(len(sch.total_float)) if sch.total_float[v] <= eps)


def _gapless_successors(adj, sch, crit, v, eps):
    """Kritische Nachfolger, die lückenlos an v anschließen (Start gleich Ende von v). Jede kritische Aufgabe mit Nachfolgern hat mindestens einen."""
    return [w for w in sorted(adj[v]) if w in crit and abs(sch.es[w] - sch.ef[v]) <= eps]


def critical_path_count(adj, dur, eps=1e-9) -> int:
    """Zahl der kritischen Pfade: Wege von einer Quelle zu einer Senke über kritische Aufgaben, die lückenlos aneinander anschließen."""
    sch = schedule(adj, dur)
    crit = set(critical_activities(sch, eps))
    pred = predecessors(adj)
    ways: dict[int, int] = {}
    for v in topological_order(adj):
        if v not in crit:
            continue
        ways[v] = (1 if not pred[v] else 0) + sum(ways[u] for u in pred[v] if u in crit and abs(sch.ef[u] - sch.es[v]) <= eps)
    return sum(ways[v] for v in crit if not adj[v])


def one_critical_path(adj, dur, eps=1e-9) -> tuple[int, ...]:
    """Ein kritischer Pfad von einer Quelle bis zu einer Senke; bei Gleichstand gewinnt immer die kleinere Aufgabennummer."""
    sch = schedule(adj, dur)
    crit = set(critical_activities(sch, eps))
    pred = predecessors(adj)
    starts = [v for v in sorted(crit) if not pred[v]]
    if not starts:
        return ()
    path = [starts[0]]
    while adj[path[-1]]:
        path.append(_gapless_successors(adj, sch, crit, path[-1], eps)[0])
    return tuple(path)


def delay_effect(adj, dur, v, extra) -> float:
    """Projektdauer, wenn Aufgabe v um `extra` Tage länger dauert (Neuberechnung des Vorwärtslaufs)."""
    longer = list(dur)
    longer[v] = longer[v] + extra
    return project_duration(adj, longer)


# --- Dreiecksverteilung ----------------------------------------------------------------------------------------------------------------------

def triangular_mean(low, mode, high) -> float:
    return (low + mode + high) / 3


def pert_mean(low, mode, high) -> float:
    """PERT-Dreipunktformel (a + 4m + b) / 6: Erwartungswert einer Beta-Näherung, nicht der einer Dreiecksverteilung."""
    return (low + 4 * mode + high) / 6


def triangular_quantile(low, mode, high, q) -> float:
    """Quantil der Dreiecksverteilung auf [low, high] mit Gipfel `mode`."""
    if high == low:
        return low
    split = (mode - low) / (high - low)
    if q < split:
        return low + ((high - low) * (mode - low) * q) ** 0.5
    return high - ((high - low) * (high - mode) * (1 - q)) ** 0.5


def bounds_for(dur, factors):
    """Untere und obere Grenze je Aufgabe aus den Faktoren der Verteilung."""
    low_f, high_f = factors
    return [low_f * d for d in dur], [high_f * d for d in dur]


def plan_with_means(adj, dur, factors) -> float:
    """Projektdauer des Plans, in dem jede Aufgabe ihren Erwartungswert (Dreieck) dauert."""
    low, high = bounds_for(dur, factors)
    return project_duration(adj, [triangular_mean(low[v], dur[v], high[v]) for v in range(len(adj))])


def plan_with_pert_means(adj, dur, factors) -> float:
    """Projektdauer des Plans mit der PERT-Dreipunktformel je Aufgabe."""
    low, high = bounds_for(dur, factors)
    return project_duration(adj, [pert_mean(low[v], dur[v], high[v]) for v in range(len(adj))])


def plan_with_task_quantile(adj, dur, factors, q) -> float:
    """Projektdauer des Plans, in dem **jede Aufgabe** ihr Quantil q dauert (Sicherheitszuschlag je Aufgabe)."""
    low, high = bounds_for(dur, factors)
    return project_duration(adj, [triangular_quantile(low[v], dur[v], high[v], q) for v in range(len(adj))])


def quantile(sorted_values, q) -> float:
    """Empirisches Quantil (Nächster-Rang): kleinster Wert, bei dem mindestens ein Anteil q der Läufe erreicht ist."""
    index = min(len(sorted_values) - 1, int(q * len(sorted_values)))
    return sorted_values[index]


def monte_carlo(adj, dur, factors, runs, seed, crit_runs=0) -> MonteCarlo:
    """`runs` Läufe mit zufälligen Dauern (Dreieck um die wahrscheinlichste Dauer); in den ersten `crit_runs` Läufen wird zusätzlich der Gesamtpuffer jeder Aufgabe
    bestimmt (Kritikalitätsindex = Anteil der Läufe mit Gesamtpuffer null). Fester Seed: gleiche Eingabe, gleiche Läufe."""
    n = len(adj)
    order = topological_order(adj)
    if order is None:
        raise ValueError("Der Plan hat einen Kreis")
    pred = predecessors(adj)
    low, high = bounds_for(dur, factors)
    rng = random.Random(seed)
    spans = []
    hits = [0] * n
    crit_runs = min(crit_runs, runs)
    for run in range(runs):
        sample = [rng.triangular(low[v], high[v], dur[v]) for v in range(n)]
        if run < crit_runs:
            sch = schedule(adj, sample)
            spans.append(sch.duration)
            for v in range(n):
                if sch.total_float[v] <= 1e-9:
                    hits[v] += 1
        else:
            spans.append(project_duration(adj, sample, order, pred))
    spans.sort()
    crit = tuple(h / crit_runs for h in hits) if crit_runs else tuple(0.0 for _ in range(n))
    return MonteCarlo(tuple(spans), sum(spans) / len(spans) if spans else 0.0, crit, crit_runs)


def share_at_most(sorted_values, limit) -> float:
    """Anteil der Läufe mit Projektdauer höchstens `limit` (mit Rundungsgrenze)."""
    return sum(1 for x in sorted_values if x <= limit + 1e-9) / len(sorted_values) if sorted_values else 0.0
