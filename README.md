# Kritischer Pfad, Puffer und Unsicherheit – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-kritischer-pfad-demo.streamlit.app/)** -->

Viertes Stück der Reihe **Ordnung und Abhängigkeit** (Arbeitstitel der Linie `dag-abhaengigkeiten`) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, Bereich Graphentheorie. Setzt einen **kreisfreien** Plan voraus, wie ihn die Stücke 1 bis 3 liefern (`di-kreis-demo`, `alle-kreise-demo`, `kreise-aufloesen-demo`); derselbe Generator, dieselbe Nummerierung, hier ohne Widersprüche und mit Dauern. Vehikel: **Aufgabenabhängigkeiten** mit wahrscheinlichsten Dauern von 1 bis 10 Tagen und, für die Unsicherheit, Dreiecksverteilungen um diese Dauern. Die Demo fragt: Wie lange dauert das Vorhaben, welche Aufgaben sind **kritisch**, wie viel **Puffer** haben die übrigen, und was bedeutet das, wenn die Dauern unsicher sind?

Nachbarn: `rcpsp-demo` plant mit knappen Ressourcen (dort stehen CPM-Schranken nur als Handrechnung in einem Test); Zeitabstände zwischen Aufgaben und das Beschleunigen gegen Geld sind noch nicht gebaut.

## Warum dieses Problem

Die Lehrbuchrechnung (CPM) liefert eine Zahl und einen kritischen Pfad. Mit unsicheren Dauern ist beides weniger, als es aussieht: Der Plan der Erwartungswerte wird häufiger überschritten als gehalten, der kritische Pfad wandert von Lauf zu Lauf, und wer jeder Aufgabe einen Sicherheitszuschlag gibt, plant mehr Puffer ein, als das Projekt braucht.

## Befunde und Korrekturen gegenüber dem Plan

- **Zahlen des Einzelplans neu gemessen.** Mit dem Demo-Code und den festen Plänen der Demo weichen die Werte der Vormessung leicht ab (andere Seeds): kritische Aufgaben 10 bis 18 % statt 8 bis 18 %, Verzerrung 0,1 / 0,9 / 5,2 % statt 0,2 / 1,5 / 4,8 %, Plan der Erwartungswerte eingehalten in 50 / 45 / 34 % statt 48 / 44 / 36 %, Puffer je Aufgabe 1,15-fach statt 1,16-fach. Die Aussagen bleiben.
- **Korrektur zur Dichte.** Der Einzelplan hatte „nicht klar mit Größe **und Dichte**“. Gemessen: Mit der **Dichte sinkt** die Verzerrung (stark rechtsschiefe Dauern, 40 Aufgaben: 8,8 % bei Ausgangsgrad 1 gegen 3,8 % bei Grad 4); mit der **Plangröße** bleibt sie ungefähr gleich (4,9 % bei 20, 5,5 % bei 80 Aufgaben).
- **Neu gegenüber dem Plan:** der Plan der **wahrscheinlichsten Dauern** wird bei schiefen Dauern fast nie gehalten (1 % bzw. 0 % der Läufe), und die PERT-Dreipunktformel liegt auf Dreiecksverteilungen schon für eine einzelne Aufgabe 7 bis 17 % unter dem Erwartungswert (Experiment 6). Die Demo trennt diesen Fehler vom Merge-Effekt.
- **Zeitabstände und Beschleunigen** sind, wie im Einzelplan vorgeschlagen, nicht Teil dieses Stücks.

## Modell

Plan wie in den Stücken 1 bis 3 (Aufgaben mit zufälligen Nummern, Beziehungen „A vor B“, hier ohne Widersprüche, also ein DAG), dazu eine **wahrscheinlichste Dauer** je Aufgabe (ganze Tage von 1 bis 10, fest aus dem Zufalls-Seed). Unsicherheit: Dreiecksverteilung mit Gipfel bei der wahrscheinlichsten Dauer und den Grenzen als Faktoren davon: **symmetrisch** 0,8 / 1 / 1,2, **rechtsschief** 0,7 / 1 / 1,8, **stark rechtsschief** 0,5 / 1 / 3. Dauern sind **unabhängig**. Der Zufall kommt nur aus `random.Random(seed)` mit `random()` und `triangular()` (plattformstabil). Details und Formeln: Expander „📐 Mathematische Formulierung“ in der App.

## Methodik

- **Vorwärts- und Rückwärtslauf** (CPM): frühester Start und Ende, spätester Start und Ende, **Gesamtpuffer** (spätester minus frühester Start) und **freier Puffer**; **kritisch** heißt Gesamtpuffer null. **Zahl und Auswahl der kritischen Pfade** über die lückenlos anschließenden kritischen Aufgaben (bei Gleichstand die kleinere Aufgabennummer).
- **Verspätungssatz:** Eine Verspätung um t Tage verschiebt das Projektende um max(0, t − Gesamtpuffer) (Spielwiese im Tab „Puffer“).
- **Monte-Carlo:** alle Dauern würfeln, Vorwärtslauf, Quantile der Projektdauer; der **Kritikalitätsindex** zählt in den ersten Läufen, wie oft eine Aufgabe Gesamtpuffer null hat.
- **Pläne zum Vergleich:** Plan der wahrscheinlichsten Dauern, Plan der Erwartungswerte (Dreieck), Plan mit der PERT-Dreipunktformel (a + 4m + b)/6, Plan, in dem jede Aufgabe ihr Quantil dauert.
- **Unabhängige Prüfer:** längster Weg per Rekursion mit Merkzettel (zweiter Weg neben Vorwärts- und Rückwärtslauf), Pufferbedingungen, kritischer Pfad als lückenlose Kette; die App prüft jedes Ergebnis vor der Anzeige.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`; Mediane über feste Pläne, nie ein einzelner Zufalls-Seed.

| Frage | Befund |
|---|---|
| Wie viele Aufgaben sind kritisch? (60 Aufgaben, 30 Pläne je Dichte) | Bei Ausgangsgrad 1 / 2 / 3 im Median nur **10 / 13,3 / 18,3 %** der Aufgaben, auf **einem** kritischen Pfad (höchstens 4 / 2 / 3); **freien Puffer null** haben dagegen **43,3 / 51,7 / 55 %**: kein freier Puffer heißt nicht kritisch. Gesamtpuffer im Median 16 / 16,75 / 11,5 Tage. |
| Wird der Plan gehalten? (40 Aufgaben, Grad 2, 15 Pläne mit je 1 000 Läufen) | Plan der **Erwartungswerte** eingehalten in **50 / 45 / 34 %** der Läufe (symmetrisch / rechtsschief / stark rechtsschief); Plan der **wahrscheinlichsten Dauern** in **50 / 1 / 0 %**; Plan mit PERT-Formel in 50 / 13 / 3 %. |
| Wie groß ist die Merge-Verzerrung? | Der Erwartungswert der Projektdauer liegt im Median **0,1 / 0,9 / 5,2 %** über dem Plan der Erwartungswerte (im ungünstigsten Plan bis 1,6 / 5,9 / 13,5 %). |
| Hängt sie an Dichte und Größe? (stark rechtsschief, 15 Pläne je Fall) | Mit der Dichte **sinkt** sie: 40 Aufgaben, Grad 1 / 2 / 3 / 4: **8,8 / 4,7 / 4,7 / 3,8 %**; mit der Größe bleibt sie ungefähr gleich: Grad 2, n = 20 / 40 / 80: **4,9 / 4,7 / 5,5 %**. Der Plan der Erwartungswerte wird in allen Fällen nur in 29 bis 40 % der Läufe gehalten. |
| Wandert der kritische Pfad? (40 Aufgaben, 15 Pläne, 400 Läufe, rechtsschief) | Von **468** Aufgaben mit Puffer größer null sind **114 (24 %)** in einzelnen Läufen kritisch, **41 (9 %)** in mindestens 10 % der Läufe; von **132** deterministisch kritischen Aufgaben sind **12** in weniger als der Hälfte der Läufe kritisch. |
| Puffer je Aufgabe oder Projektpuffer? (40 Aufgaben, 15 Pläne, stark rechtsschief) | Jede Aufgabe mit ihrem 80 %-Quantil geplant ergibt im Median das **1,15-fache** des echten Projekt-80 %-Quantils (1,10 bis 1,20); der nötige Projektpuffer beträgt **16,2 %** über dem Plan der Erwartungswerte. |
| Wie gut ist die PERT-Dreipunktformel? | Gegen den Erwartungswert der Dreiecksverteilung (als Vielfaches der wahrscheinlichsten Dauer): symmetrisch 1 gegen 1 (0 %), rechtsschief **1,083 gegen 1,167 (−7,1 %)**, stark rechtsschief **1,25 gegen 1,5 (−16,7 %)**. |
| Ist die Rechnung korrekt? | Projektdauer gleich dem längsten Weg nach Aufzählung aller Pfade und nach `networkx` auf **160** festen Plänen und gleich der Lösung eines linearen Programms (`scipy`, **60** Pläne); Gesamtpuffer gleich Projektdauer minus längster Weg durch die Aufgabe (**120** Pläne); Verspätungssatz auf 100 Plänen. `tests/test_oracle_kritischer_pfad.py` |

## Ehrliche Grenzen

- **Unabhängige Dauern.** Korrelierte Dauern (gleiches Team, gleiche Lieferung) streuen stärker; die Demo würfelt jede Aufgabe für sich.
- **Dreiecksverteilung mit drei festen Formen.** Echte Dauern haben andere Formen; die Zahlen gelten für diese Beispiele.
- **Keine Ressourcen, keine Zeitabstände, kein Beschleunigen.** Der kritische Pfad ist hier nur ein Pfad der Abhängigkeiten.
- **Synthetische Pläne** mit 1 bis 10 Tagen je Aufgabe; wie viele Aufgaben in echten Projekten kritisch sind, zeigt die Demo nicht.
- **Verzerrung hier klein bis mäßig:** bis 5,2 % im Median, bei einzelnen Plänen über 13 %. Die Demo behauptet nicht, dass PERT in der Praxis um ein bestimmtes Maß zu optimistisch ist; sie misst nur diesen Effekt unter diesen Annahmen.
- **Größe:** bis 80 Aufgaben und 5 000 Läufe.

## Tests

Das Verzeichnis `tests/` enthält zurzeit 123 Tests (Laufzeit unter einer Minute auf dem Entwicklungsrechner):

- **Kern:** jede Einheit an von Hand gerechneten Mini-Plänen (Kette, Parallelzweig mit Puffer, Raute mit zwei kritischen Pfaden, unabhängige Aufgaben, mehrere Quellen und Senken, Meilenstein mit Dauer null, freier Puffer null bei Gesamtpuffer 6); Dreiecksformeln und Quantile von Hand; Monte-Carlo deterministisch.
- **Orakel** (`test_oracle_kritischer_pfad.py`): Aufzählung aller Pfade, `networkx`, lineares Programm; Gesamtpuffer, kritische Aktivitäten und Pfade; Verspätungssatz; Invarianten (Nummerierung, Verkürzen und Verlängern).
- **Zweige** (`test_branches.py`): jedes Preset löst seine Beschreibung ein (ein und zwei kritische Pfade, freier Puffer null ohne Kritikalität, Plan selten gehalten, wandernder Pfad, Puffer je Aufgabe, symmetrische Dauern); eine Kette hat keinen Merge-Effekt.
- **Verdikte** (`test_verdicts.py`) an handgesetzten Werten; **Befunde** (`test_claims.py`) für jede Zahl dieses README.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Layout (Schnellstart oben, aktives Preset hervorgehoben), Footer, Laufzeit-Importe, Worst-Case am Reglermaximum (n = 80, Grad 4, 5 000 Läufe) ohne Zeit-Assertion.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Kritischer Pfad, Puffer, Unsicherheit, sechs Experimente |
| `kpf_algorithm.py` | Kern: Vor- und Rückwärtslauf, Puffer, kritische Pfade, Verspätung, Dreiecksformeln, Monte-Carlo |
| `kpf_constants.py` | Regler-Grenzen, Verteilungsformen, Raster der Experimente, Farben, Presets |
| `kpf_evaluation.py` | Analyse, Prüfung vor der Anzeige, Verdikte |
| `kpf_experiments.py` | Experimente über feste Pläne |
| `kpf_layout.py` | Fester Kopf (Stylesheet) |
| `kpf_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `kpf_scenario.py` | Pläne mit verdeckter Wunschreihenfolge (derselbe Generator wie in den Stücken 1 bis 3) und Dauern |
| `kpf_visualization.py` | Plotly-Abbildungen (Gantt, Bogendiagramm, Puffer, Histogramm, Experimente; Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest, networkx und scipy (Gegenproben) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Mini-Pläne, Orakel, Zweige, Verdikte, Befunde, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Zeitabstände zwischen Aufgaben** (Mindest- und Höchstabstände, positive Kreise als unmöglicher Plan) und **Zeit-Kosten-Abwägung** (Beschleunigen): eigene Stücke der Reihe.
- **Ressourcenbeschränkungen:** `rcpsp-demo`.
- **Korrelierte Dauern, andere Verteilungen, Beta-PERT-Sampling:** nicht Thema; die Dreipunktformel kommt nur als Befund vor.
- **Echte Pläne oder Dateiimport:** die Pläne sind synthetisch.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
