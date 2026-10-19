"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben.

Hauptbild ist ein Gantt-Diagramm (frühester Start, Dauer, Gesamtpuffer als grauer Anhang, kritische Aufgaben rot); Nebenansicht ist das Bogendiagramm der Abhängigkeiten
aus den Stücken 1 bis 3 (Aufgaben in der verdeckten Wunschreihenfolge auf einer Linie, Beziehungen oben nach vorn)."""

import math

import plotly.graph_objects as go

import kpf_constants as C
from kpf_evaluation import _dec, label

ARC_POINTS = 14


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_gantt_figure(sch, dur, critical):
    """Gantt: je Aufgabe ein Balken ab frühestem Start; grauer Anhang = Gesamtpuffer (so weit könnte sie später enden); kritische Aufgaben rot."""
    n = len(dur)
    crit = set(critical)
    order = sorted(range(n), key=lambda v: (sch.es[v], v))
    ys = [f"Aufgabe {label(v)}" for v in order]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=ys, x=[dur[v] for v in order], base=[sch.es[v] for v in order], orientation="h", name="Dauer", marker_color=[C.COLOR_CRITICAL if v in crit else C.COLOR_TASK for v in order],
        customdata=[[sch.es[v], sch.ef[v], sch.ls[v], sch.lf[v], sch.total_float[v], sch.free_float[v]] for v in order],
        hovertemplate="%{y}: Start %{customdata[0]}, Ende %{customdata[1]}; spätester Start %{customdata[2]}, spätestes Ende %{customdata[3]}; Gesamtpuffer %{customdata[4]}, freier Puffer %{customdata[5]}<extra></extra>"))
    fig.add_trace(go.Bar(y=ys, x=[sch.total_float[v] for v in order], base=[sch.ef[v] for v in order], orientation="h", name="Gesamtpuffer", marker_color=C.COLOR_FLOAT, hoverinfo="skip"))
    fig.update_layout(barmode="overlay")
    fig.update_yaxes(autorange="reversed", type="category", showgrid=False)
    fig.update_xaxes(title_text="Tage", range=[0, sch.duration * 1.02 if sch.duration else 1])
    _base(fig, min(900, 120 + 16 * n))
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=40), legend=dict(orientation="h", y=1.04))
    return fig


def _arc(xa, xb, n, upward, points=ARC_POINTS):
    span = abs(xb - xa)
    h = max(0.07, span / max(1, n - 1)) * (1 if upward else -1)
    xs = [xa + (xb - xa) * i / points for i in range(points + 1)]
    ys = [h * math.sin(math.pi * i / points) for i in range(points + 1)]
    return xs, ys


def _trace(edges, pos, n, color, width):
    xs, ys = [], []
    for a, b in edges:
        ax, ay = _arc(pos[a], pos[b], n, pos[a] < pos[b])
        xs += ax + [None]
        ys += ay + [None]
    if not xs:
        return None
    return go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=width), hoverinfo="skip", showlegend=False)


def build_arc_figure(inst, path=()):
    """Bogendiagramm der Abhängigkeiten in der verdeckten Wunschreihenfolge; ein kritischer Pfad rot."""
    n = inst.n
    pos = inst.position()
    path_edges = {(path[i], path[i + 1]) for i in range(len(path) - 1)}
    fig = go.Figure()
    plain = [(a, b) for a in range(n) for b in inst.adj[a] if (a, b) not in path_edges]
    tr = _trace(plain, pos, n, C.COLOR_FORWARD, 1.2 if n <= 40 else 0.7)
    if tr:
        fig.add_trace(tr)
    tr = _trace(sorted(path_edges), pos, n, C.COLOR_CRITICAL, 3.4)
    if tr:
        fig.add_trace(tr)
    labelled = n <= 40
    nodes = list(range(n))
    on_path = set(path)
    fig.add_trace(go.Scatter(
        x=[pos[v] for v in nodes], y=[0] * n, mode="markers+text" if labelled else "markers",
        marker=dict(size=22 if labelled else 8, color="#f2f2f2", line=dict(color=[C.COLOR_CRITICAL if v in on_path else "#333" for v in nodes], width=[3 if v in on_path else 1 for v in nodes])),
        text=[label(v) for v in nodes] if labelled else None, textposition="middle center", textfont=dict(color="#222", size=11),
        hovertext=[f"Aufgabe {label(v)}: Platz {pos[v] + 1} der Wunschreihenfolge" for v in nodes], hoverinfo="text", showlegend=False))
    fig.update_xaxes(title_text="Wunschreihenfolge (verdeckt) →", range=[-0.8, n - 0.2], showticklabels=False, showgrid=False, zeroline=False)
    fig.update_yaxes(range=[-0.2, 1.12], showticklabels=False, showgrid=False, zeroline=True, zerolinecolor="rgba(128,128,128,0.35)")
    _base(fig, 320)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=40))
    return fig


def build_float_figure(sch, critical):
    """Gesamtpuffer (x) gegen freien Puffer (y) je Aufgabe: Aufgaben auf der x-Achse mit Gesamtpuffer größer null haben freien Puffer null, sind aber nicht kritisch."""
    crit = set(critical)
    n = len(sch.total_float)
    groups = (
        ("kritisch (Gesamtpuffer 0)", [v for v in range(n) if v in crit], C.COLOR_CRITICAL),
        ("freier Puffer 0, aber nicht kritisch", [v for v in range(n) if v not in crit and sch.free_float[v] <= C.EPS], C.COLOR_BAR2),
        ("mit freiem Puffer", [v for v in range(n) if v not in crit and sch.free_float[v] > C.EPS], C.COLOR_TASK),
    )
    fig = go.Figure()
    for name, nodes, color in groups:
        if nodes:
            fig.add_trace(go.Scatter(x=[sch.total_float[v] for v in nodes], y=[sch.free_float[v] for v in nodes], mode="markers", name=name, marker=dict(size=10, color=color, opacity=0.8),
                                     hovertext=[f"Aufgabe {label(v)}" for v in nodes], hoverinfo="text+x+y"))
    top = max(max(sch.total_float, default=0), 1)
    fig.add_trace(go.Scatter(x=[0, top], y=[0, top], mode="lines", line=dict(color="rgba(128,128,128,0.5)", dash="dash"), name="freier = Gesamtpuffer", hoverinfo="skip"))
    fig.update_xaxes(title_text="Gesamtpuffer (Tage)")
    fig.update_yaxes(title_text="freier Puffer (Tage)")
    return _base(fig, 380)


def build_histogram_figure(spans, marks):
    """Verteilung der Projektdauer aus Monte-Carlo mit Marken: `marks` ist eine Liste (Wert, Beschriftung, Farbe)."""
    fig = go.Figure(go.Histogram(x=list(spans), nbinsx=40, marker_color="rgba(76,120,168,0.55)", hovertemplate="%{x} Tage: %{y} Läufe<extra></extra>", showlegend=False))
    ymax = 0
    for i, (x, text, color) in enumerate(marks):
        fig.add_vline(x=x, line_color=color, line_dash="dash" if i % 2 else "solid", line_width=2)
        fig.add_annotation(x=x, y=1.0 - 0.09 * (i % 4), yref="paper", text=text, showarrow=False, font=dict(color=color, size=11), xanchor="left", bgcolor="rgba(255,255,255,0.6)")
    fig.update_xaxes(title_text="Projektdauer (Tage)")
    fig.update_yaxes(title_text="Läufe")
    return _base(fig, 380)


def build_criticality_figure(criticality, critical, limit=25):
    """Kritikalitätsindex der Aufgaben mit dem höchsten Wert; rot = auch deterministisch kritisch."""
    crit = set(critical)
    order = sorted(range(len(criticality)), key=lambda v: (-criticality[v], v))[:limit]
    fig = go.Figure(go.Bar(x=[f"Aufgabe {label(v)}" for v in order], y=[100 * criticality[v] for v in order], marker_color=[C.COLOR_CRITICAL if v in crit else C.COLOR_TASK for v in order],
                           hovertemplate="%{x}: in %{y:.0f} % der Läufe kritisch<extra></extra>"))
    fig.update_xaxes(type="category", tickangle=-60)
    fig.update_yaxes(title_text="in Läufen kritisch (%)", range=[0, 105])
    return _base(fig, 360)


def build_buffers_figure(rows):
    """E1: Anteil kritischer Aufgaben gegen Anteil mit freiem Puffer null (Median) je Dichte."""
    xs = [f"Ausgangsgrad {r['out']:g}" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[100 * r["critical_share"] for r in rows], name="kritisch (Gesamtpuffer 0)", marker_color=C.COLOR_CRITICAL))
    fig.add_trace(go.Bar(x=xs, y=[100 * r["free_zero_share"] for r in rows], name="freier Puffer 0", marker_color=C.COLOR_BAR2))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Anteil der Aufgaben (%, Median)", range=[0, 100])
    return _base(fig, 340)


def build_shape_figure(rows):
    """E2: Wahrscheinlichkeit, einen Plan einzuhalten (Median), je Form der Verteilung."""
    names = {"symmetrisch": "symmetrisch", "rechtsschief": "rechtsschief", "stark": "stark rechtsschief"}
    xs = [names[r["shape"]] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[100 * r["p_ml"] for r in rows], name="Plan der wahrscheinlichsten Dauern", marker_color=C.COLOR_BAR2))
    fig.add_trace(go.Bar(x=xs, y=[100 * r["p_pert"] for r in rows], name="Plan mit PERT-Formel", marker_color=C.COLOR_BAR3))
    fig.add_trace(go.Bar(x=xs, y=[100 * r["p_mean"] for r in rows], name="Plan der Erwartungswerte", marker_color=C.COLOR_BAR))
    fig.add_hline(y=50, line_dash="dot", line_color="rgba(128,128,128,0.6)")
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Läufe, die den Plan einhalten (%)", range=[0, 100])
    return _base(fig, 360)


def build_scaling_figure(rows):
    """E3: Verzerrung (Balken) und Einhaltungswahrscheinlichkeit des Plans der Erwartungswerte (Linie) über Plangröße und Dichte."""
    xs = [f"n = {r['n']}, Grad {r['out']:g}" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["bias"] for r in rows], name="Verzerrung (%)", marker_color=C.COLOR_BAR2, yaxis="y"))
    fig.add_trace(go.Scatter(x=xs, y=[100 * r["p_mean"] for r in rows], name="Plan der Erwartungswerte eingehalten (%)", mode="lines+markers", line=dict(color=C.COLOR_BAR, width=3), yaxis="y2"))
    fig.update_layout(yaxis=dict(title="Verzerrung (%)", rangemode="tozero"), yaxis2=dict(title="Läufe, die den Plan einhalten (%)", overlaying="y", side="right", range=[0, 100]))
    fig.update_xaxes(type="category")
    return _base(fig, 360)


def build_task_buffer_figure(row):
    """E5: Projektdauer relativ zum echten Projekt-Quantil: Plan der Erwartungswerte, Projekt-Quantil, jede Aufgabe mit Quantil."""
    mean_plan = 100 / (1 + row["project_buffer_pct"] / 100)
    q = round(100 * row["level"])
    names = ["Plan der Erwartungswerte", f"Projekt-{q} %-Quantil (Monte-Carlo)", f"jede Aufgabe mit ihrem {q} %-Quantil"]
    ys = [mean_plan, 100.0, 100 * row["ratio"]]
    fig = go.Figure(go.Bar(x=names, y=ys, marker_color=[C.COLOR_BAR3, C.COLOR_BAR, C.COLOR_CRITICAL], text=[f"{y:.0f}" for y in ys], textposition="outside", cliponaxis=False))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Projektdauer (Projekt-Quantil = 100)", range=[0, max(ys) * 1.18])
    return _base(fig, 340)


def build_pert_figure(rows):
    """E6: PERT-Dreipunktformel gegen den Erwartungswert der Dreiecksverteilung (Vielfaches der wahrscheinlichsten Dauer)."""
    names = {"symmetrisch": "symmetrisch", "rechtsschief": "rechtsschief", "stark": "stark rechtsschief"}
    xs = [names[r["shape"]] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["pert"] for r in rows], name="Dreipunktformel (a + 4m + b)/6", marker_color=C.COLOR_BAR2, text=[_dec(r["pert"], 3) for r in rows], textposition="outside"))
    fig.add_trace(go.Bar(x=xs, y=[r["mean"] for r in rows], name="Erwartungswert (Dreieck)", marker_color=C.COLOR_BAR, text=[_dec(r["mean"], 3) for r in rows], textposition="outside"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="mal wahrscheinlichste Dauer", range=[0, 1.8])
    return _base(fig, 340)
