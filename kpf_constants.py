"""Konstanten: Regler-Grenzen, Dreiecksverteilungen, Raster der Experimente, Farben und Presets."""

# Rechenbudget am Regler-Maximum (n = 80, Ausgangsgrad 4, also m = 320 Beziehungen, 5 000 Monte-Carlo-Läufe):
#   Vorwärts- und Rückwärtslauf O(n + m); Monte-Carlo O(Läufe * (n + m)); Kritikalitätsindex mit eigener, kleinerer Lauf-Zahl (zwei Läufe je Durchgang).
N_MIN, N_MAX, DEFAULT_N = 6, 80, 12
OUT_MIN, OUT_MAX, OUT_STEP, DEFAULT_OUT = 0.5, 4.0, 0.5, 2.0   # mittlerer Ausgangsgrad
SEED_MAX, DEFAULT_SEED = 999999, 6
RUNS = (200, 500, 1000, 2000, 5000)                            # Monte-Carlo-Läufe
DEFAULT_RUNS = 1000
CRIT_RUNS = 400                                                # Läufe für den Kritikalitätsindex (höchstens so viele wie Läufe)
LEVEL_MIN, LEVEL_MAX, LEVEL_STEP, DEFAULT_LEVEL = 50, 95, 5, 80  # gewünschte Sicherheit in Prozent
SHAPES = ("symmetrisch", "rechtsschief", "stark")
SHAPE_FACTORS = {"symmetrisch": (0.8, 1.2), "rechtsschief": (0.7, 1.8), "stark": (0.5, 3.0)}   # (unten, oben) als Faktor der wahrscheinlichsten Dauer
SHAPE_NAMES = {"symmetrisch": "symmetrisch (0,8 / 1 / 1,2)", "rechtsschief": "rechtsschief (0,7 / 1 / 1,8)", "stark": "stark rechtsschief (0,5 / 1 / 3)"}
DEFAULT_SHAPE = "rechtsschief"
EPS = 1e-9                                                     # Rundungsgrenze: Puffer bis hierhin gilt als null
DELAY_MAX = 30                                                 # größte Verspätung in der Spielwiese (Tage)

# Feste Instanzen und Raster der Experimente (nie ein einzelner Zufalls-Seed als Befund)
E1_N, E1_OUTS, E1_SEEDS = 60, (1.0, 2.0, 3.0), tuple(range(400, 430))
E2_N, E2_OUT, E2_SEEDS, E2_RUNS = 40, 2.0, tuple(range(500, 515)), 1000
E3_CASES, E3_SEEDS, E3_RUNS, E3_SHAPE = ((20, 2.0), (40, 1.0), (40, 2.0), (40, 3.0), (40, 4.0), (80, 2.0)), tuple(range(700, 715)), 800, "stark"
E4_N, E4_OUT, E4_SEEDS, E4_SHAPE = 40, 2.0, tuple(range(600, 615)), "rechtsschief"
E5_N, E5_OUT, E5_SEEDS, E5_RUNS, E5_SHAPE = 40, 2.0, tuple(range(800, 815)), 1000, "stark"

# Farben
COLOR_CRITICAL = "#d62728"
COLOR_TASK = "#4c78a8"
COLOR_FLOAT = "rgba(150,150,150,0.35)"
COLOR_BAR = "#2F6B65"
COLOR_BAR2 = "#ff9f1c"
COLOR_BAR3 = "#59a14f"
COLOR_FORWARD = "rgba(76,120,168,0.45)"

PRESETS = {
    "Lehrbeispiel (12 Aufgaben)": {"n": DEFAULT_N, "out": DEFAULT_OUT, "seed": DEFAULT_SEED, "shape": DEFAULT_SHAPE, "runs": DEFAULT_RUNS, "level": DEFAULT_LEVEL},
    "Zwei kritische Pfade": {"n": 12, "out": 2.0, "seed": 7, "shape": DEFAULT_SHAPE, "runs": DEFAULT_RUNS, "level": DEFAULT_LEVEL},
    "Kein Puffer ist nicht kritisch": {"n": 30, "out": 2.0, "seed": 1, "shape": DEFAULT_SHAPE, "runs": DEFAULT_RUNS, "level": DEFAULT_LEVEL},
    "Der Plan wird selten gehalten": {"n": 40, "out": 2.0, "seed": 8, "shape": "stark", "runs": DEFAULT_RUNS, "level": DEFAULT_LEVEL},
    "Der kritische Pfad wandert": {"n": 40, "out": 2.0, "seed": 10, "shape": DEFAULT_SHAPE, "runs": DEFAULT_RUNS, "level": DEFAULT_LEVEL},
    "Puffer je Aufgabe ist zu viel": {"n": 40, "out": 2.0, "seed": 17, "shape": "stark", "runs": DEFAULT_RUNS, "level": DEFAULT_LEVEL},
    "Symmetrisch: kaum Verzerrung": {"n": 40, "out": 2.0, "seed": 1, "shape": "symmetrisch", "runs": DEFAULT_RUNS, "level": DEFAULT_LEVEL},
}
PRESET_HELP = {
    "Lehrbeispiel (12 Aufgaben)": "Zwölf Aufgaben mit rechtsschiefen Dauern: ein kritischer Pfad, die übrigen Aufgaben haben Puffer. Das ist die Voreinstellung.",
    "Zwei kritische Pfade": "Zwei gleich lange längste Pfade: mehr als ein kritischer Pfad.",
    "Kein Puffer ist nicht kritisch": "Aufgaben mit freiem Puffer null, die trotzdem Gesamtpuffer haben: kein freier Puffer heißt nicht kritisch.",
    "Der Plan wird selten gehalten": "Stark rechtsschiefe Dauern: der Plan der Erwartungswerte wird in den meisten Läufen überschritten.",
    "Der kritische Pfad wandert": "Aufgaben mit Puffer sind in einzelnen Läufen kritisch, kritische Aufgaben in manchen Läufen nicht.",
    "Puffer je Aufgabe ist zu viel": "Jede Aufgabe mit Sicherheitszuschlag zu planen ergibt eine Projektdauer deutlich über dem echten Projekt-Quantil.",
    "Symmetrisch: kaum Verzerrung": "Symmetrische Dauern: der Plan der Erwartungswerte ist fast unverzerrt, aber trotzdem nur in etwa der Hälfte der Läufe zu halten.",
}
