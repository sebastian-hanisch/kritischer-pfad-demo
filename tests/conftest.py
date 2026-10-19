"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b).

Teure Experimente laufen einmal je Testlauf (`lru_cache`) und werden von Claims-, Verdikt- und Mutationstests gemeinsam genutzt."""

import sys
from functools import lru_cache
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Von Hand gerechnete Mini-Instanzen: Name -> (Adjazenz, Dauern, Projektdauer, Gesamtpuffer, freier Puffer, Zahl kritischer Pfade)
MINI = {
    "kette": (((1,), (2,), ()), (3, 4, 2), 9, (0, 0, 0), (0, 0, 0), 1),                             # 3 + 4 + 2, alles kritisch
    "parallel": (((1, 2), (3,), (3,), ()), (2, 5, 3, 1), 8, (0, 0, 2, 0), (0, 0, 2, 0), 1),         # Pfad 0-1-3 = 8, Pfad 0-2-3 = 6: Aufgabe 2 hat 2 Tage Puffer
    "raute_gleich": (((1, 2), (3,), (3,), ()), (1, 4, 4, 1), 6, (0, 0, 0, 0), (0, 0, 0, 0), 2),     # zwei gleich lange Pfade
    "unabhaengig": (((), ()), (3, 3), 3, (0, 0), (0, 0), 2),                                       # zwei Aufgaben ohne Beziehung, beide kritisch
    "mehrere_enden": (((2,), (2,), (3, 4), (), ()), (2, 5, 1, 2, 4), 10, (3, 0, 0, 2, 0), (3, 0, 0, 2, 0), 1),   # zwei Quellen, zwei Senken
    "meilenstein": (((1,), (2,), ()), (3, 0, 2), 5, (0, 0, 0), (0, 0, 0), 1),                       # Aufgabe mit Dauer null
    "ff_null": (((3,), (2,), (3,), ()), (10, 2, 2, 1), 11, (0, 6, 6, 0), (0, 0, 6, 0), 1),          # Aufgabe 1 hat freien Puffer 0, aber Gesamtpuffer 6
    "leer": ((), (), 0, (), (), 0),
}


@pytest.fixture
def mini():
    return MINI


@lru_cache(maxsize=None)
def cached(name):
    """Einmal je Testlauf berechnete Experimente (Name der Funktion in kpf_experiments)."""
    import kpf_experiments as ex
    return getattr(ex, name)()


def all_path_lengths(adj, dur):
    """Orakel: Länge jedes Weges von einer Quelle zu einer Senke durch Aufzählung (n <= 14); Wege als Tupel."""
    n = len(adj)
    has_pred = [False] * n
    for a in range(n):
        for b in adj[a]:
            has_pred[b] = True
    paths = []

    def extend(path):
        v = path[-1]
        if not adj[v]:
            paths.append(tuple(path))
            return
        for w in adj[v]:
            extend(path + [w])

    for s in range(n):
        if not has_pred[s]:
            extend([s])
    return [(p, sum(dur[v] for v in p)) for p in paths]
