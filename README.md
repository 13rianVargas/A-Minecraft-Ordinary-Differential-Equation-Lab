# AMODEL — A Minecraft Ordinary Differential Equation Lab

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![SciPy](https://img.shields.io/badge/SciPy-1.17-8CAAE6?logo=scipy&logoColor=white)](https://scipy.org/)
[![NumPy](https://img.shields.io/badge/NumPy-2.4-013243?logo=numpy&logoColor=white)](https://numpy.org/)
[![pandas](https://img.shields.io/badge/pandas-3.0-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.10-11557C)](https://matplotlib.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-11%20passing-brightgreen.svg)](tests/)

A reproducible measurement pipeline that turns raw Minecraft server logs into
calibrated ODE parameters, and the experimental result that came out of it.

*A Minecraft Ordinary Differential Equation Lab* — **AMODEL**, which is also
what it produces, and what the experiment ends up correcting.

---

## Executive summary

A Minecraft server is instrumented as a controlled ecology lab. Six fenced
corrals of varying carrying capacity `K` hold a fixed number of sheep `N` that
graze a grass stock `G`. Command-block chains reset each corral, control the
run, count the remaining grass, and emit the counts into the server log. That
log is the raw measurement record.

This repository is the pipeline that turns that record into science:

**ingest → parse → calibrate → integrate → score → report**

Each stage communicates only through files on disk, so any stage can be rerun
in isolation and every intermediate artifact is inspectable. From 27 648
samples across 12 experimental scenarios plus 10 calibration runs, it fits the
two free parameters of the logistic-harvesting model

```
dG/dt = r·G·(1 − G/K) − c·N
```

yielding `r = 0.005037 1/s` and `c = 0.010355 blocks/(sheep·s)`, and from those
the saddle-node bifurcation threshold `N_crit = rK/(4c) = 0.1216·K` that
separates a persistent pasture from a collapsing one.

The pipeline then earned its keep by falsifying the model it was built to fit.
Above `N_crit` the classical model predicts total collapse to zero. The
experiment never collapsed — in all three supercritical scenarios the grass
settled at a stable non-zero plateau. Replacing the constant grazing drain with
a saturating Holling Type II functional response reproduces those plateaus and
cuts the error by 81–91 % exactly where the original model failed, while
performing *worse* where the original was already correct. The two models are
complementary, and locating that boundary is the actual finding.

Full derivations, protocol and results: **[docs/FINDINGS.md](docs/FINDINGS.md)**.

---

## System architecture

```mermaid
flowchart LR
    A["Minecraft server<br/>command blocks + scoreboards"] -->|latest.log| B["extract.sh<br/>ssh · env-configured"]
    B -->|"logs/*.log"| C["parse_log.py<br/>regex + run-scoped state machine"]
    C -->|timeseries.csv| D["analyze.py"]
    D -->|curve_fit| E["calibration.json<br/>r, c"]
    D -->|"solve_ivp + terminal event"| F["figures/*.png"]
    D -->|RMS scoring| G["rms.csv"]
    E --> H["build_report.py"]
    F --> H
    G --> H
    H -->|python-docx| I["deliverables/*.docx"]
```

The contract between stages is a file format, not a function signature:

| Stage | Input | Output |
|---|---|---|
| `extract.sh` | live server log | `logs/<run>.log` |
| `parse_log.py` | `logs/` | `data/timeseries.csv` |
| `analyze.py` | `data/timeseries.csv` | `data/calibration.json`, `data/rms.csv`, `figures/*.png` |
| `build_report.py` | calibration + RMS + figures | `deliverables/*.docx` |

---

## Key features

**Run-scoped parsing of a cumulative log.** The server never rotates
`latest.log`, so it accumulates every run in the session. The parser rewinds to
the final `#running to 1` marker and reads only from there, so an extraction
captures the current replica no matter how much history precedes it
([`parse_log.py:124`](scripts/parse_log.py#L124)).

**Design-derived metadata over observed metadata.** The in-world command block
for corral 6 wrote `Corral to 5`, conflating two corrals. Rather than patch
around the symptom, the parser stops trusting that field entirely and derives
the corral from the scenario number, which is fixed by design. The instrument
has since been repaired, and the parser still ignores it — logs captured before
the fix carry the wrong value, and a quantity fixed by experimental design
should not depend on an instrument being configured correctly
([`parse_log.py:53`](scripts/parse_log.py#L53)).

**Two-stage parameter estimation.** `r` is fitted first from sheep-free runs
where the model reduces to the pure logistic and a closed form exists. `c` is
then fitted against the full ODE trajectory with `r` held fixed, leaving one
free parameter — far more robust at low `N` than the initial-slope estimator it
retains as a fallback ([`analyze.py:207`](scripts/analyze.py#L207)).

**Absorbing boundary as an integration event, not a clamp.** Enforcing `G ≥ 0`
by clamping the derivative makes the right-hand side discontinuous, and
`odeint`'s LSODA driver fails on it: on one scenario it aborted mid-integration
and returned a trajectory diverging to `G ≈ 7540` against a carrying capacity of
225, at a point that varied between runs on identical input. Expressing the
boundary as a terminal event in `solve_ivp` removes the discontinuity from the
solver's path and makes all 12 scenarios deterministic
([`analyze.py:107`](scripts/analyze.py#L107), rationale in
[FINDINGS §9.8](docs/FINDINGS.md#98-the-absorbing-boundary-broke-the-integrator)).

**Closed-form equilibria for both models,** including the quadratic root for
the Holling variant and the bifurcation threshold, so numerical results always
have an analytic check to sit against.

**Deterministic and reproducible.** `analyze.py` regenerates every published
number and figure from the committed CSV. Repeated runs are byte-identical.

---

## Tech stack

| Technology | Role in the architecture |
|---|---|
| **SciPy** | `solve_ivp` integrates both models with event detection; `curve_fit` performs the two-stage parameter estimation |
| **NumPy** | Vectorised trajectory and RMS arithmetic |
| **pandas** | Replica aggregation (mean ± σ per timestamp) and the CSV tables |
| **Matplotlib** | Headless figure generation via the `Agg` backend — no display required in CI |
| **python-docx** | Programmatic report assembly with embedded figures and generated tables |
| **Bash** | Ingestion CLI over SSH, with direct and `docker exec` access modes |
| **pytest** | Parser tests against synthetic fixtures, since real logs cannot be published |

---

## Results

Calibrated from 5 replicas each of `r` and `c`:

| Parameter | Value | Unit |
|---|---|---|
| `r` | 0.005037 | 1/s (in-game second) |
| `c` | 0.010355 | blocks/(sheep·s) |
| `N_crit` | `rK/(4c)` = 0.1216·K | sheep |

Model comparison across the 12 scenarios (RMS in grass blocks, lower is
better):

| Scenario | Regime | RMS original | RMS Holling | Improvement |
|---|---|---|---|---|
| 1 | strongly subcritical | 1.51 | 2.06 | −36.5 % |
| 2 | critical | 4.08 | 3.10 | **+24.0 %** |
| 3 | supercritical | 13.90 | 2.58 | **+81.5 %** |
| 4 | subcritical | 2.91 | 5.86 | −101.3 % |
| 5 | mid subcritical | 8.62 | 6.43 | **+25.4 %** |
| 6 | supercritical | 57.81 | 6.10 | **+89.5 %** |
| 7 | strongly subcritical | 4.40 | 9.03 | −105.1 % |
| 8 | critical | 25.86 | 14.33 | **+44.6 %** |
| 9 | supercritical | 137.94 | 12.72 | **+90.8 %** |
| 10 | C4 water | 8.01 | 8.14 | −1.6 % |
| 11 | C5 leaves | 6.41 | 18.34 | −186.0 % |
| 12 | C6 fences | 18.78 | 31.47 | −67.6 % |
| **mean** | | **24.19** | **10.01** | |

![Model comparison in the supercritical regime](figures/model_comparison.png)

The classical model predicts collapse to zero in all three supercritical
scenarios; the measured trajectories plateau instead. Holling Type II
reproduces the plateaus.

Both models fail on C6 (fences) for a different reason: the obstacle makes part
of the corral physically unreachable, so the effective carrying capacity is
below the geometric one. That is a limitation of `K`, not of the grazing term,
and needs a different correction — see
[FINDINGS §7.3](docs/FINDINGS.md#73-effect-of-the-obstacle).

---

## Installation

```bash
git clone https://github.com/13rianVargas/A-Minecraft-Ordinary-Differential-Equation-Lab.git
cd A-Minecraft-Ordinary-Differential-Equation-Lab
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Reproduce every published number and figure from the committed data — no
server, no network:

```bash
python scripts/analyze.py data/timeseries.csv
```

Calibration only:

```bash
python scripts/analyze.py data/timeseries.csv --calibrate
```

Rebuild the report documents:

```bash
python scripts/build_report.py
```

Run the tests:

```bash
pytest tests/
```

### Live extraction

The ingestion stage needs the lab server and **is not reproducible from
outside it**. The raw logs are deliberately not distributed: Minecraft server
logs record the IP address, username and UUID of every player who connects, so
publishing them would expose personal data belonging to third parties.
`data/timeseries.csv` is the published entry point instead.

With your own server, copy `.env.example` to `.env`, fill it in, then:

```bash
./scripts/extract.sh run 5 2      # scenario 5, replica 2
./scripts/extract.sh calib c 1    # calibration of c, replica 1
./scripts/extract.sh analyze      # re-parse and run the full analysis
./scripts/extract.sh help
```

---

## Project structure

```
.
├── data/
│   ├── timeseries.csv          # 27 648 samples — the pipeline entry point
│   ├── calibration.json        # fitted r and c
│   ├── rms.csv                 # per-scenario model scoring
│   └── archive/                # superseded intermediate datasets
├── figures/                    # 12 per-scenario plots + 4 grouped figures
├── scripts/
│   ├── extract.sh              # ingestion CLI (SSH, env-configured)
│   ├── parse_log.py            # server log -> time series
│   ├── analyze.py              # calibration, integration, scoring, plots
│   └── build_report.py         # report assembly via python-docx
├── tests/
│   ├── fixtures/               # synthetic PII-free logs
│   └── test_parse_log.py
├── docs/
│   ├── FINDINGS.md             # model, protocol, results, known defects
│   └── presentation.html       # self-contained slide deck
├── deliverables/               # generated .docx reports
├── assets/                     # illustration material
├── requirements.txt
└── .env.example                # extraction config template
```

## Data schema

`data/timeseries.csv` — one row per measurement. Column names are kept in
Spanish because they are a stable data contract read by three scripts.

| Column | Type | Meaning |
|---|---|---|
| `escenario` | int | Scenario id, 1–12 by design; see sentinels below |
| `replica` | int | Replica number within the scenario |
| `t_segundos` | float | Elapsed in-game seconds (log ticks ÷ 20) |
| `G` | int | Grass blocks remaining in the active corral |
| `N` | int | Sheep in the corral |
| `K` | int | Carrying capacity of the corral |
| `corral` | int | Corral id 1–6, derived from `escenario`, not from the log |

Two sentinel scenario ids mark the calibration runs:

| Id | Meaning |
|---|---|
| `101` | Calibration of `c` (consumption), run at N=5 |
| `102` | Calibration of `r` (regrowth), run at N=0 |

---

## Authors

Universidad — Ecuaciones Diferenciales, 2026-I, Group 2.

| Author | Role |
|---|---|
| **Lina Andrea Bello Ballén** | Experimental runs, results analysis |
| **Julián David Cristancho Niño** | Experimental runs, model refinement |
| **Mariana Alejandra Gordillo Meneses** | Experimental runs, conclusions |
| **Brian Steven Vargas Clavijo** | Data engineering, measurement pipeline, quantitative analysis |

Under the supervision of **Paul Fernando Camargo Toro**.

## License

Source code is released under the [MIT License](LICENSE). Experimental data,
figures and written documents are the research output of the authors; Minecraft
assets under `assets/` are excluded. See [LICENSE](LICENSE) for details.
