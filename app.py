"""Kritischer Pfad, Puffer und Unsicherheit - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Viertes Stück der Reihe „Ordnung und Abhängigkeit“: Wie lange dauert ein kreisfreier Plan, welche Aufgaben sind kritisch, wie viel Puffer haben die übrigen, und was bedeutet das,
wenn die Dauern unsicher sind (Plan der Erwartungswerte gegen Monte-Carlo, Kritikalitätsindex, Puffer je Aufgabe gegen Projektpuffer)?

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import kpf_algorithm as A
import kpf_constants as C
import kpf_evaluation as ev
import kpf_experiments as ex
from kpf_layout import dunkles_design, kopf_css
from kpf_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from kpf_visualization import (
    build_arc_figure,
    build_buffers_figure,
    build_criticality_figure,
    build_float_figure,
    build_gantt_figure,
    build_histogram_figure,
    build_pert_figure,
    build_scaling_figure,
    build_shape_figure,
    build_task_buffer_figure,
)

st.set_page_config(page_title="Kritischer Pfad, Puffer und Unsicherheit – Sebastian Hanisch", layout="wide")

_i, _dec = ev._i, ev._dec


def _show(verdict):
    kind, text = verdict
    {"success": st.success, "info": st.info, "warning": st.warning}[kind](text)


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner=False)
def _buffers():
    return ex.buffer_rows()


@st.cache_data(show_spinner=False)
def _shapes():
    return ex.shape_rows()


@st.cache_data(show_spinner=False)
def _scaling():
    return ex.scaling_rows()


@st.cache_data(show_spinner=False)
def _criticality():
    return ex.criticality_rows()


@st.cache_data(show_spinner=False)
def _task_buffers():
    return ex.task_buffer_rows()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in kpf_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("📅 Kritischer Pfad, Puffer und Unsicherheit")
st.markdown(
    """
Ein Plan ohne Kreise hat eine Reihenfolge, aber noch keine **Dauer**. Der **kritische Pfad** ist die längste Kette von Aufgaben: Sie bestimmt die Projektdauer, und jede Verspätung auf ihr verschiebt das Ende.
Alle anderen Aufgaben haben **Puffer**. Soweit die Lehrbuchrechnung (**CPM**). Sind die Dauern aber **unsicher**, stimmt sie in drei Punkten nicht mehr: Der Plan mit Erwartungswerten wird häufiger überschritten als gehalten,
der kritische Pfad **wandert**, und ein Sicherheitszuschlag je Aufgabe plant weit mehr Puffer ein, als das Projekt braucht.

Das ist das vierte Stück der Reihe **Ordnung und Abhängigkeit**; es setzt einen kreisfreien Plan voraus (Stücke 1 bis 3: **di-kreis-demo**, **alle-kreise-demo**, **kreise-aufloesen-demo**).
Wer zusätzlich knappe Ressourcen planen will, findet das in der Demo **rcpsp-demo**. Weiter unten: die Experimente **🔬**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So rechnet man den kritischen Pfad", expanded=True):
    st.markdown(
        """
1. **Vorwärtslauf:** Jede Aufgabe startet, sobald alle Vorgänger fertig sind (**frühester Start**), und endet nach ihrer Dauer (**frühestes Ende**). Das späteste frühestes Ende ist die **Projektdauer**.
2. **Rückwärtslauf:** Vom Projektende aus rückwärts: **spätestes Ende** und **spätester Start**, ohne das Projekt zu verlängern.
3. **Puffer:** Der **Gesamtpuffer** (spätester minus frühester Start) ist die Verspätung, die eine Aufgabe verträgt, ohne das Projekt zu verlängern. Der **freie Puffer** lässt dabei auch alle Nachfolger unberührt. **Kritisch** heißt Gesamtpuffer null.
4. **Unsicherheit:** Jede Dauer ist eine **Dreiecksverteilung** um die wahrscheinlichste Dauer. **Monte-Carlo** würfelt alle Dauern, rechnet den Vorwärtslauf und zählt: Projektdauer als Verteilung, **Quantile** (Sicherheit), **Kritikalitätsindex** (Anteil der Läufe, in denen die Aufgabe kritisch ist).
5. **Warum der Erwartungswert-Plan zu kurz ist:** Wo Pfade zusammenlaufen, zählt der **spätere** von mehreren Zweigen; das Maximum zufälliger Dauern liegt über dem Maximum ihrer Erwartungswerte (**Merge-Ereignis**).

| Begriff | Bedeutung |
|---|---|
| **Kritischer Pfad** | lückenlose Kette kritischer Aufgaben von einer Quelle zu einer Senke; es kann mehrere geben |
| **Gesamtpuffer** | Verspätung, die eine Aufgabe verträgt, ohne das Projektende zu verschieben |
| **Freier Puffer** | Verspätung, die auch alle Nachfolger unberührt lässt; null heißt nicht kritisch |
| **Erwartungswert-Plan** | der Plan, in dem jede Aufgabe ihren Erwartungswert dauert |
| **Quantil** | Projektdauer, die in einem Anteil der Läufe nicht überschritten wird (80 % Sicherheit = P80) |
| **Kritikalitätsindex** | Anteil der Läufe, in denen die Aufgabe Gesamtpuffer null hat |
| **Dreipunktformel** | PERT-Konvention (a + 4m + b)/6 für den Erwartungswert aus unterer, wahrscheinlichster und oberer Dauer |
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Plan**")
    n = st.slider("Aufgaben n", *bounds("n_slider"), key="n_slider", help="Wie viele Aufgaben der Plan hat. Dauern: 1 bis 10 Tage je Aufgabe (wahrscheinlichste Dauer), fest aus dem Zufalls-Seed.")
    out = st.slider("Beziehungen je Aufgabe", *bounds("out_slider"), key="out_slider", step=C.OUT_STEP,
                    help="Mittlerer Ausgangsgrad: Zahl der Beziehungen „A vor B“ geteilt durch die Zahl der Aufgaben. Der Plan ist kreisfrei.")
    seed = st.number_input("Zufalls-Seed des Plans", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Plan erzeugen", width="stretch", on_click=randomize_seed)
    st.markdown("**Unsicherheit**")
    shape = st.selectbox("Verteilung der Dauern", list(C.SHAPES), format_func=C.SHAPE_NAMES.get, key="shape_select",
                         help="Dreiecksverteilung um die wahrscheinlichste Dauer; die Zahlen sind die Faktoren für untere und obere Grenze. Rechtsschief heißt: Verspätungen sind größer als Verfrühungen.")
    runs = st.selectbox("Monte-Carlo-Läufe", list(C.RUNS), format_func=_i, key="runs_select", help="Wie oft die Dauern gewürfelt werden (fester Seed: gleiche Eingabe, gleiche Läufe).")
    level = st.slider("Gewünschte Sicherheit (%)", *bounds("level_slider"), key="level_slider", step=C.LEVEL_STEP, help="Mit dieser Wahrscheinlichkeit soll das Projekt höchstens so lange dauern (Quantil).")

sync_query_params({"n_slider": int(n), "out_slider": float(out), "seed_input": int(seed), "shape_select": shape, "runs_select": int(runs), "level_slider": int(level)})

settings = ev.Settings(int(n), float(out), int(seed), shape, int(runs), int(level))
with st.spinner("Rechne den Plan und die Monte-Carlo-Läufe..."):
    a = _analysis(settings)
inst, sch = a.inst, a.sch
problems = ev.validate(a)
for p in problems:
    st.error(f"Prüfung fehlgeschlagen: {p}")
signature = f"{inst.n}_{settings.out}_{settings.seed}"

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
st.caption(f"{_i(inst.n)} Aufgaben, {_i(inst.m)} Beziehungen, Dauern in Tagen. Aufgaben sind ab 1 nummeriert.")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Projektdauer (Plan)", f"{_dec(sch.duration)} Tage", delta=f"{_i(len(a.critical))} von {_i(a.n)} Aufgaben kritisch", delta_color="off")
m2.metric("Kritische Pfade", _i(a.path_count), delta="lückenlose Ketten ohne Puffer", delta_color="off")
# Delta immer „mein Wert minus Referenz“; eine längere Projektdauer ist schlechter, deshalb delta_color="inverse".
m3.metric("Erwartete Dauer (Läufe)", f"{_dec(a.mc.mean)} Tage", delta=f"{a.mc.mean - sch.duration:+.1f} Tage gegen den Plan".replace(".", ",") if a.n else None, delta_color="inverse")
m4.metric(f"Dauer mit {settings.level} % Sicherheit", f"{_dec(a.t_level)} Tage", delta=f"Plan wird in {ev._pct(a.p_keep_ml)} % der Läufe gehalten", delta_color="off")

tab_cpm, tab_float, tab_mc = st.tabs(["📅 Kritischer Pfad", "🧯 Puffer", "🎲 Unsicherheit"])

# --- Tab 1: Kritischer Pfad ----------------------------------------------------------------------------------------------------------------

with tab_cpm:
    st.plotly_chart(build_gantt_figure(sch, a.dur, a.critical), width="stretch", key="gantt")
    st.caption("Jeder Balken beginnt am frühesten Start; der graue Anhang ist der Gesamtpuffer. **Rot:** kritische Aufgaben, also Gesamtpuffer null.")
    st.markdown("**Ein kritischer Pfad:** " + " → ".join(ev.label(v) for v in a.path) + f" (Summe der Dauern: {_dec(sum(a.dur[v] for v in a.path))} Tage = Projektdauer)." if a.path else "**Kein kritischer Pfad** (leerer Plan).")
    table = pd.DataFrame({
        "Aufgabe": [ev.label(v) for v in range(a.n)], "Dauer": [a.dur[v] for v in range(a.n)], "Frühester Start": list(sch.es), "Frühestes Ende": list(sch.ef),
        "Spätester Start": list(sch.ls), "Spätestes Ende": list(sch.lf), "Gesamtpuffer": list(sch.total_float), "Freier Puffer": list(sch.free_float),
        "Kritisch": ["ja" if v in a.critical else "nein" for v in range(a.n)]})
    with st.expander("Alle Aufgaben mit Start, Ende und Puffer"):
        st.dataframe(table, hide_index=True, width="stretch", height=min(500, 40 + 35 * a.n))
    with st.expander("Die Abhängigkeiten als Bogendiagramm"):
        st.plotly_chart(build_arc_figure(inst, a.path), width="stretch", key="arc_cpm")
        st.caption("Aufgaben in der verdeckten Wunschreihenfolge; Beziehungen laufen oben von links nach rechts. Der kritische Pfad ist rot.")

# --- Tab 2: Puffer -------------------------------------------------------------------------------------------------------------------------

with tab_float:
    st.markdown("#### Was eine Verspätung kostet")
    options = list(range(a.n))
    d1, d2 = st.columns(2)
    with d1:
        task = st.selectbox("Aufgabe, die sich verspätet", options, key=f"delay_task_{signature}", format_func=lambda v: f"Aufgabe {ev.label(v)} (Gesamtpuffer {_dec(sch.total_float[v])} Tage)")
    with d2:
        extra = st.slider("Verspätung (Tage)", 0, C.DELAY_MAX, 3, key=f"delay_days_{signature}")
    new_total = A.delay_effect(inst.adj, a.dur, task, extra)
    shift = new_total - sch.duration
    p1, p2, p3 = st.columns(3)
    p1.metric("Neue Projektdauer", f"{_dec(new_total)} Tage", delta=f"{shift:+.1f} Tage".replace(".", ",") if shift else "unverändert", delta_color="inverse" if shift else "off")
    p2.metric("Verbrauchter Puffer", f"{_dec(min(extra, sch.total_float[task]))} von {_dec(sch.total_float[task])} Tagen")
    p3.metric("Verschiebt das Projektende?", "ja" if shift > 0 else "nein", delta="Verspätung über dem Gesamtpuffer" if shift > 0 else "innerhalb des Gesamtpuffers", delta_color="off")
    st.caption("Satz: Eine Verspätung um t Tage verschiebt das Projektende um das, was über dem Gesamtpuffer der Aufgabe liegt (nie um weniger als null).")
    st.plotly_chart(build_float_figure(sch, a.critical), width="stretch", key="chart_float")
    n_ff0 = sum(1 for v in range(a.n) if v not in a.critical and sch.free_float[v] <= C.EPS)
    st.caption(f"Jeder Punkt ist eine Aufgabe. {_i(n_ff0)} Aufgaben haben freien Puffer null, aber Gesamtpuffer größer null: Sie blockieren ihre Nachfolger, sind aber nicht kritisch.")

# --- Tab 3: Unsicherheit -------------------------------------------------------------------------------------------------------------------

with tab_mc:
    marks = [(sch.duration, f"wahrscheinlichste Dauern {_dec(sch.duration)}", "#d62728"), (a.t_mean, f"Erwartungswert-Plan {_dec(a.t_mean)}", "#59a14f"),
             (a.mc.mean, f"Mittel der Läufe {_dec(a.mc.mean)}", "#2F6B65"), (a.t_level, f"{settings.level} % Sicherheit {_dec(a.t_level)}", "#ff9f1c")]
    st.plotly_chart(build_histogram_figure(a.mc.makespans, marks), width="stretch", key="hist")
    st.caption(f"Verteilung der Projektdauer in {_i(settings.runs)} Läufen ({C.SHAPE_NAMES[settings.shape]}).")
    u1, u2, u3, u4 = st.columns(4)
    u1.metric("Plan der wahrscheinlichsten Dauern gehalten", f"{ev._pct(a.p_keep_ml)} %", delta=f"{_dec(sch.duration)} Tage", delta_color="off")
    u2.metric("Plan der Erwartungswerte gehalten", f"{ev._pct(a.p_keep_mean)} %", delta=f"{_dec(a.t_mean)} Tage", delta_color="off")
    u3.metric("Verzerrung des Erwartungswerts", f"{_dec(a.bias_pct)} %", delta="Mittel der Läufe gegen Erwartungswert-Plan", delta_color="off")
    u4.metric("Plan mit Quantil je Aufgabe", f"{_dec(a.t_task_level)} Tage", delta=f"{_dec(a.t_task_level / a.t_level, 2)}-fach das Projekt-Quantil", delta_color="off")
    st.plotly_chart(build_criticality_figure(a.mc.criticality, a.critical), width="stretch", key="chart_crit")
    st.caption(f"Kritikalitätsindex der Aufgaben mit dem höchsten Wert (aus {_i(a.mc.crit_runs)} Läufen). Rot sind auch deterministisch kritische Aufgaben; blaue Aufgaben haben Puffer und sind trotzdem oft kritisch.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie lange dauert das Vorhaben, wie sicher ist die Zahl, und wo liegt der Puffer?")
_show(ev.verdict_question(a))

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

with st.spinner("Rechne die Experimente (einmalig, einige Sekunden)..."):
    rows_b, rows_s, rows_g, row_c, row_t = _buffers(), _shapes(), _scaling(), _criticality(), _task_buffers()
rows_p = ex.pert_rows()

st.subheader("🔬 Experiment 1: Wie viele Aufgaben sind kritisch?")
st.caption(f"{C.E1_N} Aufgaben, je Dichte {len(C.E1_SEEDS)} feste Pläne; Median. Kritisch heißt Gesamtpuffer null.")
st.plotly_chart(build_buffers_figure(rows_b), width="stretch", key="chart_buffers")
_show(ev.verdict_buffers(rows_b))

st.subheader("🔬 Experiment 2: Wird der Plan der Erwartungswerte gehalten?")
st.caption(f"{C.E2_N} Aufgaben, mittlerer Ausgangsgrad {C.E2_OUT:g}, je Form {len(C.E2_SEEDS)} feste Pläne mit je {_i(C.E2_RUNS)} Läufen; Median. Die Linie bei 50 % ist die Münze.")
st.plotly_chart(build_shape_figure(rows_s), width="stretch", key="chart_shape")
_show(ev.verdict_shape(rows_s))

st.subheader("🔬 Experiment 3: Hängt die Verzerrung an Plangröße und Dichte?")
st.caption(f"Stark rechtsschiefe Dauern, je Fall {len(C.E3_SEEDS)} feste Pläne mit je {_i(C.E3_RUNS)} Läufen; Median.")
st.plotly_chart(build_scaling_figure(rows_g), width="stretch", key="chart_scaling")
_show(ev.verdict_scaling(rows_g))

st.subheader("🔬 Experiment 4: Der kritische Pfad wandert")
st.caption(f"{C.E4_N} Aufgaben, mittlerer Ausgangsgrad {C.E4_OUT:g}, {len(C.E4_SEEDS)} feste Pläne ({_i(row_c['tasks'])} Aufgaben), je {_i(C.CRIT_RUNS)} Läufe, {C.SHAPE_NAMES[C.E4_SHAPE]}.")
_show(ev.verdict_criticality(row_c))

st.subheader("🔬 Experiment 5: Puffer je Aufgabe oder Projektpuffer?")
st.caption(f"{C.E5_N} Aufgaben, mittlerer Ausgangsgrad {C.E5_OUT:g}, {len(C.E5_SEEDS)} feste Pläne mit je {_i(C.E5_RUNS)} Läufen, {C.SHAPE_NAMES[C.E5_SHAPE]}; Median.")
st.plotly_chart(build_task_buffer_figure(row_t), width="stretch", key="chart_task_buffers")
_show(ev.verdict_task_buffers(row_t))

st.subheader("🔬 Experiment 6: Wie gut ist die PERT-Dreipunktformel?")
st.caption("Reine Rechnung ohne Zufall: Erwartungswert aus unterer, wahrscheinlichster und oberer Dauer, als Vielfaches der wahrscheinlichsten Dauer.")
st.plotly_chart(build_pert_figure(rows_p), width="stretch", key="chart_pert")
_show(ev.verdict_pert(rows_p))

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    f"""
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Unabhängige Dauern** | Sind Dauern korreliert (gleiches Team, gleiche Lieferung), streuen Projektdauer und Puffer stärker; die Demo würfelt jede Aufgabe für sich. | - |
| **Dreiecksverteilung** | Echte Dauern haben andere Formen (lange Tails, Ausreißer); die Formen hier sind drei feste Beispiele. | - |
| **Keine Ressourcen** | Teilen sich Aufgaben ein Team oder eine Maschine, ist der kritische Pfad nicht mehr nur ein Pfad der Abhängigkeiten. | rcpsp-demo |
| **Keine Zeitabstände** | Mindest- und Höchstabstände zwischen Aufgaben (Anschlussfristen) kennt die Demo nicht; ein positiver Kreis darin wäre ein unmöglicher Plan. | Folgestück der Reihe |
| **Kein Beschleunigen** | Dauern lassen sich hier nicht gegen Geld verkürzen; die Zeit-Kosten-Abwägung ist ein eigenes Problem. | Folgestück der Reihe |
| **Synthetische Pläne** | Zufallspläne mit 1 bis 10 Tagen je Aufgabe; wie viele Aufgaben in echten Projekten kritisch sind, zeigt die Demo nicht. | - |
| **Größe** | Bis {C.N_MAX} Aufgaben und {C.RUNS[-1]} Läufe; die Verzerrung wächst in den gemessenen Plänen nicht klar mit der Größe (Experiment 3). | - |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben** ein kreisfreier Graph $G = (V, E)$ mit Dauern $d_v \ge 0$. Frühester Start $ES$, frühestes Ende $EF$, spätestes Ende $LF$ und spätester Start $LS$:

| Symbol | Bedeutung |
|---|---|
| $ES_v$, $EF_v$ | frühester Start und frühestes Ende von $v$ |
| $LS_v$, $LF_v$ | spätester Start und spätestes Ende von $v$ |
| $T$ | Projektdauer |
| $TF_v$ | Gesamtpuffer von $v$ |

**Vorwärtslauf.** Mit $ES_v = 0$ für Aufgaben ohne Vorgänger:

$$ES_v = \max_{(u, v) \in E} EF_u, \qquad EF_v = ES_v + d_v, \qquad T = \max_{v \in V} EF_v.$$

**Rückwärtslauf und Puffer.** Mit $LF_v = T$ für Aufgaben ohne Nachfolger:

$$LF_v = \min_{(v, w) \in E} LS_w, \qquad LS_v = LF_v - d_v, \qquad TF_v = LS_v - ES_v.$$

**Kritisch** heißt $TF_v = 0$. Der Gesamtpuffer ist die Differenz zur längsten Kette durch die Aufgabe:

$$TF_v = T - \ell_v,$$

wobei $\ell_v$ die Länge des längsten Weges durch $v$ ist. Eine Verspätung um $t$ verschiebt das Projektende um

$$\Delta T = \max\{0,\; t - TF_v\}.$$

**Unsicherheit.** Mit zufälligen Dauern $D_v$ gilt für die zufällige Projektdauer $T(D)$ (Maximum über alle Pfade $P$ der Summe der Dauern) die Ungleichung

$$\mathbb{E}[T(D)] \;=\; \mathbb{E}\Big[\max_{P} \sum_{v \in P} D_v\Big] \;\ge\; \max_{P} \sum_{v \in P} \mathbb{E}[D_v] \;=\; T(\mathbb{E}[D]).$$

**Dreiecksverteilung** mit unterer Grenze $a$, Gipfel $m$ und oberer Grenze $b$:

$$\mathbb{E}[D] = \frac{a + m + b}{3}.$$

**PERT-Dreipunktformel** (Beta-Näherung, nicht der Erwartungswert der Dreiecksverteilung):

$$\hat{\mu} = \frac{a + 4m + b}{6}.$$

**Literatur.** J. E. Kelley Jr., M. R. Walker: *Critical-path planning and scheduling*, Proceedings of the Eastern Joint Computer Conference, 1959. D. G. Malcolm, J. H. Roseboom, C. E. Clark, W. Fazar: *Application of a technique for research and development program evaluation*, Operations Research 7 (5), 1959, S. 646–669. K. R. MacCrimmon, C. A. Ryavec: *An analytical study of the PERT assumptions*, Operations Research 12 (1), 1964, S. 16–37. Die Ungleichung zum Maximum zufälliger Größen ist die Jensen-Ungleichung für das (konvexe) Maximum; die Größen in den Experimenten sind eigene Messungen.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
