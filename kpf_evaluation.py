"""Kennzahlen, Prüfung der Ergebnisse und Verdikte. Verdikte sind reine Funktionen (Art, Text): Zahlen kommen aus den Zeilen, nie aus dem Text.

Aufgaben sind in der Anzeige ab 1 nummeriert (`label`); im Kern ab 0. Dauern in Tagen."""

from dataclasses import dataclass
from functools import lru_cache

import kpf_algorithm as A
import kpf_constants as C
from kpf_scenario import Instance, durations, make_instance


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    out: float = C.DEFAULT_OUT
    seed: int = C.DEFAULT_SEED
    shape: str = C.DEFAULT_SHAPE
    runs: int = C.DEFAULT_RUNS
    level: int = C.DEFAULT_LEVEL


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    inst: Instance
    dur: tuple[int, ...]
    sch: A.Schedule
    critical: tuple[int, ...]
    path_count: int
    path: tuple[int, ...]
    mc: A.MonteCarlo
    t_mean: float            # Plan der Erwartungswerte
    t_pert: float            # Plan mit der PERT-Dreipunktformel
    t_level: float           # Projekt-Quantil zur gewünschten Sicherheit (Monte-Carlo)
    t_task_level: float      # Plan, in dem jede Aufgabe ihr Quantil der gewünschten Sicherheit dauert

    @property
    def n(self) -> int:
        return self.inst.n

    @property
    def p_keep_ml(self) -> float:
        return A.share_at_most(self.mc.makespans, self.sch.duration)

    @property
    def p_keep_mean(self) -> float:
        return A.share_at_most(self.mc.makespans, self.t_mean)

    @property
    def bias_pct(self) -> float:
        return 100 * (self.mc.mean - self.t_mean) / self.t_mean if self.t_mean else 0.0


def label(v: int) -> str:
    return str(v + 1)


def analyse(settings: Settings) -> Analysis:
    return analyse_plan(make_instance(settings.n, settings.out, 0, settings.seed), durations(settings.n, settings.seed), settings)


def analyse_plan(inst: Instance, dur, settings: Settings) -> Analysis:
    """Alle Kennzahlen auf einem gegebenen Plan (Tests bauen Mini-Pläne von Hand)."""
    adj = inst.adj
    factors = C.SHAPE_FACTORS[settings.shape]
    sch = A.schedule(adj, dur)
    mc = A.monte_carlo(adj, dur, factors, settings.runs, settings.seed, crit_runs=min(C.CRIT_RUNS, settings.runs))
    q = settings.level / 100
    return Analysis(settings, inst, tuple(dur), sch, A.critical_activities(sch), A.critical_path_count(adj, dur), A.one_critical_path(adj, dur), mc,
                    A.plan_with_means(adj, dur, factors), A.plan_with_pert_means(adj, dur, factors), A.quantile(mc.makespans, q), A.plan_with_task_quantile(adj, dur, factors, q))


def _longest_from(adj, dur):
    """Länge des längsten Weges ab jeder Aufgabe (Rekursion mit Merkzettel): zweiter Rechenweg neben Vorwärts-/Rückwärtslauf."""
    memo: dict[int, float] = {}

    def f(v):
        if v not in memo:
            memo[v] = dur[v] + max((f(w) for w in adj[v]), default=0)
        return memo[v]

    for v in range(len(adj)):
        f(v)
    return memo


def validate(a: Analysis) -> list[str]:
    """Unabhängige Prüfung vor der Anzeige: leere Liste, wenn alles stimmt; sonst die verletzten Regeln."""
    import sys
    adj, sch, problems = a.inst.adj, a.sch, []
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 5000))
    longest = _longest_from(adj, a.dur)
    if abs(max(longest.values(), default=0) - sch.duration) > 1e-9:
        problems.append("Die Projektdauer des Vorwärtslaufs weicht vom längsten Weg ab.")
    if any(t < -1e-9 for t in sch.total_float) or any(f > t + 1e-9 for f, t in zip(sch.free_float, sch.total_float)):
        problems.append("Ein Puffer ist negativ, oder der freie Puffer übersteigt den Gesamtpuffer.")
    path = a.path
    if path:
        if abs(sum(a.dur[v] for v in path) - sch.duration) > 1e-9 or any(path[i + 1] not in adj[path[i]] for i in range(len(path) - 1)) or any(v not in a.critical for v in path):
            problems.append("Der kritische Pfad ist keine lückenlose Kette kritischer Aufgaben der Länge der Projektdauer.")
    if not a.critical and a.n:
        problems.append("Es gibt keine kritische Aufgabe.")
    spans = a.mc.makespans
    if list(spans) != sorted(spans) or len(spans) != a.settings.runs:
        problems.append("Die Monte-Carlo-Läufe sind nicht sortiert oder unvollständig.")
    if a.t_mean < sch.duration - 1e-9:
        problems.append("Der Plan der Erwartungswerte ist kürzer als der Plan der wahrscheinlichsten Dauern.")
    if a.t_level < spans[0] - 1e-9 or a.t_level > spans[-1] + 1e-9:
        problems.append("Das Projekt-Quantil liegt außerhalb der Läufe.")
    return problems


# --- Zahlenformat --------------------------------------------------------------------------------------------------------------------------

def _i(x) -> str:
    """Ganze Zahl mit Punkt als Tausendertrenner."""
    return f"{x:,.0f}".replace(",", ".")


def _dec(x, digits=1) -> str:
    """Zahl mit Komma; ganze Werte ohne Nachkommastelle."""
    x = float(x)
    if x == int(x):
        return _i(x)
    return f"{x:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(share, digits=0) -> str:
    """Anteil (0 bis 1) als Prozentzahl mit Komma."""
    return _dec(round(100.0 * share, digits), digits) if digits else _i(round(100.0 * share))


def pfade(k: int) -> str:
    return "einem kritischen Pfad" if k == 1 else f"{_i(k)} kritischen Pfaden"


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------

def verdict_question(a: Analysis) -> tuple[str, str]:
    """Kernfrage: Wie lange dauert das Vorhaben, wie sicher ist die Zahl, wo liegt der Puffer?"""
    if not a.n:
        return "info", "Der Plan ist leer."
    s = a.settings
    crit_share = len(a.critical) / a.n
    text = (f"**Mit den wahrscheinlichsten Dauern dauert das Vorhaben {_dec(a.sch.duration)} Tage**; {_i(len(a.critical))} von {_i(a.n)} Aufgaben ({_pct(crit_share)} %) sind kritisch, auf {pfade(a.path_count)}. "
            f"Mit unsicheren Dauern ({C.SHAPE_NAMES[s.shape]}) liegt der Erwartungswert bei {_dec(a.mc.mean)} Tagen, mit {s.level} % Sicherheit wird das Vorhaben in {_dec(a.t_level)} Tagen fertig. "
            f"Den Plan der wahrscheinlichsten Dauern hält man in {_pct(a.p_keep_ml)} % der Läufe ein, den Plan der Erwartungswerte ({_dec(a.t_mean)} Tage) in {_pct(a.p_keep_mean)} %.")
    return ("warning" if a.p_keep_ml < 0.5 else "info"), text


def verdict_buffers(rows: list[dict]) -> tuple[str, str]:
    """E1: Anteil kritischer Aufgaben gegen Anteil mit freiem Puffer null über der Dichte."""
    lo, hi = min(r["critical_share"] for r in rows), max(r["critical_share"] for r in rows)
    flo, fhi = min(r["free_zero_share"] for r in rows), max(r["free_zero_share"] for r in rows)
    paths, pmax = max(r["paths_median"] for r in rows), max(r["paths_max"] for r in rows)
    text = (f"Bei {_i(rows[0]['n'])} Aufgaben sind im Median nur {_pct(lo)} bis {_pct(hi)} % der Aufgaben kritisch (Ausgangsgrad {_dec(rows[0]['out'])} bis {_dec(rows[-1]['out'])}), im Median auf {pfade(int(paths))} "
            f"(höchstens {_i(pmax)}); freien Puffer null haben dagegen {_pct(flo)} bis {_pct(fhi)} %: kein freier Puffer heißt nicht kritisch.")
    return ("info" if hi < flo else "warning"), text


def verdict_shape(rows: list[dict]) -> tuple[str, str]:
    """E2: Verzerrung und Einhaltungswahrscheinlichkeit je Form der Verteilung."""
    names = {"symmetrisch": "symmetrisch", "rechtsschief": "rechtsschief", "stark": "stark rechtsschief"}
    bias = ", ".join(f"{_dec(r['bias'])} % ({names[r['shape']]})" for r in rows)
    p_mean = " / ".join(_pct(r["p_mean"]) for r in rows)
    p_ml = " / ".join(_pct(r["p_ml"]) for r in rows)
    text = (f"Der Erwartungswert der Projektdauer liegt im Median {bias} über der Dauer des Plans der Erwartungswerte. Diesen Plan hält man in {p_mean} % der Läufe ein, "
            f"den Plan der wahrscheinlichsten Dauern in nur {p_ml} % (jeweils symmetrisch / rechtsschief / stark rechtsschief).")
    return ("info" if rows[-1]["p_mean"] < 0.5 and rows[-1]["bias"] > rows[0]["bias"] else "warning"), text


def verdict_scaling(rows: list[dict]) -> tuple[str, str]:
    """E3: Verzerrung über Dichte (bei der häufigsten Plangröße) und über Plangröße (beim häufigsten Ausgangsgrad), stark rechtsschiefe Dauern."""
    from collections import Counter
    n_ref = Counter(r["n"] for r in rows).most_common(1)[0][0]
    out_ref = Counter(r["out"] for r in rows).most_common(1)[0][0]
    by_density = sorted((r for r in rows if r["n"] == n_ref), key=lambda r: r["out"])
    by_size = sorted((r for r in rows if r["out"] == out_ref), key=lambda r: r["n"])
    d1, d2, s1, s2 = by_density[0], by_density[-1], by_size[0], by_size[-1]
    plo, phi = min(r["p_mean"] for r in rows), max(r["p_mean"] for r in rows)
    text = (f"Mit der Dichte sinkt die Verzerrung: {_dec(d1['bias'])} % bei Ausgangsgrad {_dec(d1['out'])} gegen {_dec(d2['bias'])} % bei {_dec(d2['out'])} (n = {n_ref}). "
            f"Mit der Plangröße ändert sie sich dagegen kaum: {_dec(s1['bias'])} % bei n = {s1['n']} gegen {_dec(s2['bias'])} % bei n = {s2['n']} (Ausgangsgrad {_dec(out_ref)}). "
            f"Die Wahrscheinlichkeit, den Plan der Erwartungswerte einzuhalten, liegt in allen Fällen zwischen {_pct(plo)} und {_pct(phi)} %.")
    return ("info" if d1["bias"] > d2["bias"] and phi < 0.5 else "warning"), text


def verdict_criticality(row: dict) -> tuple[str, str]:
    """E4: Kritikalitätsindex gegen deterministischen Puffer."""
    text = (f"Von {_i(row['with_float'])} Aufgaben mit Puffer größer null sind {_i(row['sometimes_critical'])} ({_pct(row['sometimes_critical'] / row['with_float'])} %) in einzelnen Läufen kritisch, "
            f"{_i(row['often_critical'])} ({_pct(row['often_critical'] / row['with_float'])} %) in mindestens 10 % der Läufe. Von {_i(row['critical'])} deterministisch kritischen Aufgaben sind "
            f"{_i(row['critical_rare'])} in weniger als der Hälfte der Läufe kritisch: der kritische Pfad wandert.")
    return ("info" if row["sometimes_critical"] > 0 else "warning"), text


def verdict_task_buffers(row: dict) -> tuple[str, str]:
    """E5: Sicherheitszuschlag je Aufgabe gegen Projektpuffer."""
    q = round(100 * row["level"])
    text = (f"Plant man jede Aufgabe mit ihrem {q} %-Quantil, ergibt der Vorwärtslauf im Median das {_dec(row['ratio'], 2)}-fache des echten Projekt-{q} %-Quantils "
            f"({_dec(row['ratio_min'], 2)} bis {_dec(row['ratio_max'], 2)}); der Projektpuffer (Projekt-Quantil gegen den Plan der Erwartungswerte) beträgt im Median {_dec(row['project_buffer_pct'])} %.")
    return ("info" if row["ratio_min"] > 1 else "warning"), text


def verdict_pert(rows: list[dict]) -> tuple[str, str]:
    """E6: PERT-Dreipunktformel gegen den Erwartungswert der Dreiecksverteilung."""
    parts = "; ".join(f"{r['shape'] if r['shape'] != 'stark' else 'stark rechtsschief'}: {_dec(r['pert'], 3)} statt {_dec(r['mean'], 3)} ({_dec(r['deviation_pct'])} %)" for r in rows)
    return ("info" if rows[-1]["deviation_pct"] < rows[0]["deviation_pct"] - 1 else "warning"), (
        f"Als Vielfaches der wahrscheinlichsten Dauer liefert die Dreipunktformel (a + 4m + b)/6 gegen den Erwartungswert der Dreiecksverteilung: {parts}. "
        "Sie ist für die Beta-Näherung gemeint, nicht für Dreiecksverteilungen, und unterschätzt hier schon eine einzelne Aufgabe.")
