"""Experimente E1 bis E6 über feste Pläne (nie ein einzelner Zufalls-Seed). Jede Funktion liefert Zeilen für Tabelle, Diagramm und Verdikt.

E1 Puffer und kritische Pfade über der Dichte, E2 Plan der Erwartungswerte gegen Monte-Carlo über der Schiefe, E3 dasselbe über Größe und Dichte, E4 Kritikalitätsindex gegen
deterministischen Puffer, E5 Sicherheitszuschlag je Aufgabe gegen Projektpuffer, E6 PERT-Dreipunktformel gegen den Erwartungswert (reine Formel, kein Zufall).
Plan-Seed, Dauern und Monte-Carlo-Seed sind je Plan derselbe Zufalls-Seed."""

from statistics import median

import kpf_algorithm as A
import kpf_constants as C
import kpf_scenario as S


def _plan(n, out, seed):
    return S.make_instance(n, out, 0, seed).adj, S.durations(n, seed)


def buffer_rows(n=C.E1_N, outs=C.E1_OUTS, seeds=C.E1_SEEDS) -> list[dict]:
    """E1: Anteil kritischer Aufgaben, Zahl kritischer Pfade, Gesamtpuffer und Anteil mit freiem Puffer null je Dichte (Mediane über feste Pläne)."""
    rows = []
    for out in outs:
        crit, paths, tf, ff0 = [], [], [], []
        for s in seeds:
            adj, dur = _plan(n, out, s)
            sch = A.schedule(adj, dur)
            crit.append(len(A.critical_activities(sch)) / n)
            paths.append(A.critical_path_count(adj, dur))
            tf.append(median(sch.total_float))
            ff0.append(sum(1 for x in sch.free_float if x <= C.EPS) / n)
        rows.append({"n": n, "out": out, "instances": len(seeds), "critical_share": median(crit), "paths_median": median(paths), "paths_max": max(paths),
                     "total_float_median": median(tf), "free_zero_share": median(ff0)})
    return rows


def _bias_row(n, out, seeds, runs, shape):
    factors = C.SHAPE_FACTORS[shape]
    bias, p_mean, p_ml, p_pert = [], [], [], []
    for s in seeds:
        adj, dur = _plan(n, out, s)
        t_ml = A.schedule(adj, dur).duration
        t_mean = A.plan_with_means(adj, dur, factors)
        t_pert = A.plan_with_pert_means(adj, dur, factors)
        mc = A.monte_carlo(adj, dur, factors, runs, s)
        bias.append(100 * (mc.mean - t_mean) / t_mean)
        p_mean.append(A.share_at_most(mc.makespans, t_mean))
        p_ml.append(A.share_at_most(mc.makespans, t_ml))
        p_pert.append(A.share_at_most(mc.makespans, t_pert))
    return {"shape": shape, "n": n, "out": out, "instances": len(seeds), "runs": runs, "bias": median(bias), "bias_max": max(bias),
            "p_mean": median(p_mean), "p_ml": median(p_ml), "p_pert": median(p_pert)}


def shape_rows(n=C.E2_N, out=C.E2_OUT, seeds=C.E2_SEEDS, runs=C.E2_RUNS) -> list[dict]:
    """E2: je Form der Dreiecksverteilung die Verzerrung des Erwartungswerts der Projektdauer gegen den Plan der Erwartungswerte und die Wahrscheinlichkeit, einen Plan zu halten."""
    return [_bias_row(n, out, seeds, runs, shape) for shape in C.SHAPES]


def scaling_rows(cases=C.E3_CASES, seeds=C.E3_SEEDS, runs=C.E3_RUNS, shape=C.E3_SHAPE) -> list[dict]:
    """E3: dieselbe Verzerrung über Plangröße und Dichte bei stark rechtsschiefen Dauern."""
    return [_bias_row(n, out, seeds, runs, shape) for n, out in cases]


def criticality_rows(n=C.E4_N, out=C.E4_OUT, seeds=C.E4_SEEDS, shape=C.E4_SHAPE, runs=C.CRIT_RUNS) -> dict:
    """E4: über alle Aufgaben aller Pläne: wie oft sind Aufgaben mit Puffer größer null in Läufen kritisch, und wie oft sind kritische Aufgaben es nicht?"""
    factors = C.SHAPE_FACTORS[shape]
    total = with_float = sometimes = often = critical = rare = 0
    for s in seeds:
        adj, dur = _plan(n, out, s)
        sch = A.schedule(adj, dur)
        ci = A.monte_carlo(adj, dur, factors, runs, s, crit_runs=runs).criticality
        for v in range(n):
            total += 1
            if sch.total_float[v] > C.EPS:
                with_float += 1
                sometimes += ci[v] > 0
                often += ci[v] >= 0.10
            else:
                critical += 1
                rare += ci[v] < 0.5
    return {"n": n, "out": out, "instances": len(seeds), "runs": runs, "shape": shape, "tasks": total, "with_float": with_float, "sometimes_critical": sometimes,
            "often_critical": often, "critical": critical, "critical_rare": rare}


def task_buffer_rows(n=C.E5_N, out=C.E5_OUT, seeds=C.E5_SEEDS, runs=C.E5_RUNS, shape=C.E5_SHAPE, level=0.8) -> dict:
    """E5: Projektdauer, wenn **jede Aufgabe** ihr Quantil `level` dauert, gegen das echte Projekt-Quantil; dazu der nötige Projektpuffer gegen den Plan der Erwartungswerte."""
    factors = C.SHAPE_FACTORS[shape]
    ratios, buffers = [], []
    for s in seeds:
        adj, dur = _plan(n, out, s)
        mc = A.monte_carlo(adj, dur, factors, runs, s)
        q = A.quantile(mc.makespans, level)
        ratios.append(A.plan_with_task_quantile(adj, dur, factors, level) / q)
        buffers.append(100 * (q - A.plan_with_means(adj, dur, factors)) / A.plan_with_means(adj, dur, factors))
    return {"n": n, "out": out, "instances": len(seeds), "runs": runs, "shape": shape, "level": level, "ratio": median(ratios), "ratio_min": min(ratios), "ratio_max": max(ratios),
            "project_buffer_pct": median(buffers)}


def pert_rows(shapes=C.SHAPES) -> list[dict]:
    """E6: PERT-Dreipunktformel (a + 4m + b)/6 gegen den Erwartungswert der Dreiecksverteilung, als Vielfaches der wahrscheinlichsten Dauer."""
    rows = []
    for shape in shapes:
        low, high = C.SHAPE_FACTORS[shape]
        pert, tri = A.pert_mean(low, 1.0, high), A.triangular_mean(low, 1.0, high)
        rows.append({"shape": shape, "pert": pert, "mean": tri, "deviation_pct": 100 * (pert - tri) / tri})
    return rows
