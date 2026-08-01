# AMODEL — Findings

Technical record of the model, the experimental protocol, the calibration
results and the instrumentation defects discovered while running the lab.
Numbers here are reproduced by `scripts/analyze.py` from `data/timeseries.csv`;
see [Reproducing these numbers](#15-reproducing-these-numbers).

---

## 1. Model formulation

The system is a balance between two opposing forces: grass that regrows on its
own, and sheep that consume it.

```
dG/dt = r·G·(1 − G/K)  −  c·N
        └─ regrowth ─┘    └ grazing ┘
```

| Term | Meaning |
|---|---|
| `dG/dt` | Rate of change of the grass stock `G` over time |
| `r` | Intrinsic regrowth rate of the grass (1/s) |
| `K` | Carrying capacity — the maximum grass the corral can hold (blocks) |
| `(1 − G/K)` | Self-limiting brake: growth is fast when the corral is empty and tends to zero as `G → K` |
| `c` | Consumption rate per sheep (blocks per sheep per second) |
| `N` | Number of sheep |

The regrowth half is the classical logistic term. The grazing half is a
**constant drain**: the model assumes `N` sheep always remove `c·N` blocks per
second regardless of how much grass is left. That assumption is the one this
project ends up falsifying (section 8).

The equation is **first order** and **autonomous** — time does not appear
explicitly, only through `G`. Despite that simplicity it exhibits multiple
equilibria, a bifurcation, and finite-time collapse.

---

## 2. Analytical treatment

### 2.1 Existence and uniqueness

The right-hand side `f(G) = r·G·(1 − G/K) − c·N` is a polynomial, hence smooth
with continuous derivative. By the Picard–Lindelöf theorem, for any initial
stock `G₀` there exists exactly one solution curve `G(t)`. Solutions never
cross and there is no ambiguity.

### 2.2 Closed form

The equation is separable and can be integrated analytically. The form of the
solution depends on the discriminant `Δ = 1 − 4cN/(rK)`:

| Case | Behaviour | Analytic solution |
|---|---|---|
| `N = 0` | Pure logistic | `G(t) = K / (1 + A·e^(−rt))`, `A = (K − G₀)/G₀` — the classical S-curve |
| Subcritical (`Δ > 0`) | Stabilises | Generalised logistic tending to `G*₊` |
| Supercritical (`Δ < 0`) | Collapse | The integral yields an arctangent — grass reaches 0 in **finite time** |

### 2.3 Why the project integrates numerically anyway

A closed form exists, and the project still solves the system numerically. The
reasons are practical:

1. **Parameter estimation.** Fitting `r` and `c` to noisy measurements
   evaluates the model hundreds of times inside an optimiser.
2. **The refined model has no elementary primitive.** Once the grazing term
   becomes `c·N·G/(G+h)` (section 8), the closed form is gone.
3. **Uniformity.** All 12 scenarios are handled by the same code path
   regardless of regime.

The integration itself is subtler than it looks; see section 9.8.

### 2.4 The result that matters

The ODE has a perfectly good mathematical solution — it exists, it is unique,
and it can be written down. The contribution of this project is showing that
**the solution does not always match reality**. In the supercritical regime the
solution predicts collapse to zero, and the experiment shows the grass never
collapses. The mathematics is not wrong; the physical assumption behind the
grazing term is.

---

## 3. Experimental design and protocol

### 3.1 Apparatus

A Minecraft server hosts six fenced corrals. Command-block chains reset a
corral, spawn a controlled number of sheep, start and stop a run, and count the
grass blocks remaining. Counts and elapsed time are written to scoreboards,
which the server echoes into its log — that log is the raw measurement record.

| Corral | Geometry | K | Feature |
|---|---|---|---|
| C1 | 5×5 | 25 | regular |
| C2 | 10×10 | 100 | regular; calibration is performed here |
| C3 | 15×15 | 225 | regular |
| C4 | 12×12 | 100 | water |
| C5 | 12×12 | 100 | leaves |
| C6 | 12×12 | 100 | fences |

### 3.2 Time base and run cap

Runs are accelerated with `/tick rate 5000`. One in-game second is 20 ticks, so
`t_seg` in the data is always ticks/20 — the model's time unit is the in-game
second, never wall-clock time.

The server does **not** actually reach 5000 TPS. Under command-block load it
sustains roughly 450–1000 real TPS, and more sheep means more lag and fewer
TPS. Raising the tick rate further changes little.

Every run is capped at `t_seg = 150 000` ticks. A run is stopped at whichever
comes first: grass collapses to 0, grass visibly stabilises, or the cap is
reached. A truncated run is still usable — the fit works on the partial curve.

### 3.3 Calibration of `c` — one replica

Grazing is measured in C2 with N=5. At N=5 the corral stays subcritical
(`N_crit ≈ 12.16`), so the run settles at an equilibrium rather than collapsing,
which gives the fit a much better-conditioned target than a collapse curve.

1. **LOCAL RESET C2** — fills the 10×10 corral with grass, sets K=100, G=100.
   Wait 1–2 real seconds for the redstone chain to finish propagating.
2. **+5 sheep** — spawns 5 sheep, initially frozen (`NoAI:1b`).
3. `/tick rate 5000`.
4. **START** — wakes the sheep (`NoAI:0b`), raises `#running=1`, resets `t_seg=0`.
5. When `t_seg ≥ 30 000` (= 1500 in-game seconds, roughly 6 real seconds),
   press **STOP**.
6. `/tick rate 20`.
7. `scripts/extract.sh calib c <replica>`.

Repeated 5 times.

### 3.4 Calibration of `r` — one replica

Regrowth is measured with **no sheep at all**, which reduces the ODE to the
pure logistic and lets `r` be fitted directly.

1. **CALIBRATE R** — removes all sheep, fills C2 with dirt, places a single
   grass block at the centre, sets K=100, G=1. Wait for the chain to finish.
2. `/tick freeze` — pause the world with the setup already in place.
3. **START** — raises `#running=1`.
4. `/tick rate 5000`, then `/tick unfreeze`.
5. Press **STOP** at `t_seg ≥ 30 000`, or once G plateaus near K.
6. `/tick rate 20`.
7. `scripts/extract.sh calib r <replica>`.

Repeated 5 times.

**Ordering constraint:** LOCAL RESET and CALIBRATE R drive redstone chains that
need live ticks to propagate. They must run *before* `/tick freeze`, with 1–2
real seconds allowed for the chain to complete. Freezing first leaves the reset
half-applied (section 9.5).

### 3.5 Scenario runs

Each of the 12 scenarios fixes a `(corral, N)` pair:

1. **LOCAL RESET C\<corral\>** for the scenario's corral.
2. Press **+1 / +5 / +10** until the sheep count reaches `N`.
3. `/tick rate 5000`, then **START**.
4. Press **STOP** on collapse, on a visible plateau (G near-constant for
   ~600–1200 in-game ticks), or at the 150 000-tick cap.
5. `/tick rate 20`.
6. `scripts/extract.sh run <scenario> <replica>`.

### 3.6 Log filename convention

`parse_log.py` derives the scenario and replica **from the filename**, so the
convention is mandatory — a wrong name silently corrupts the dataset.

| Pattern | Purpose | Example |
|---|---|---|
| `calib_c_rep<R>.log` | Calibration of `c` | `calib_c_rep3.log` |
| `calib_r_rep<R>.log` | Calibration of `r` | `calib_r_rep3.log` |
| `corrida_esc<E>_rep<R>.log` | Design scenario, E = 1..12 | `corrida_esc6_rep2.log` |

Rules:

1. No leading zero on `E` (`esc6`, not `esc06`).
2. No spaces, parentheses or ` (1)` suffixes. One file, one run.
3. All replicas of a scenario must share the same `N`. A run with an off-design
   `N` is not that scenario.
4. Off-design and trial runs go in `logs/extra/`. `parse_log.py` does not
   recurse into subdirectories, so they stay out of the dataset.

---

## 4. Parameter calibration

### 4.1 Regrowth rate `r`

With N=0 the model reduces to the pure logistic, whose closed form is fitted
directly with `scipy.optimize.curve_fit` (`p0=[0.01]`, `bounds=(0, ∞)`):

```
G(t) = K / (1 + A·e^(−rt)),    A = (K − G₀)/G₀
```

Five replicas in C2 (N=0, G₀=1, K=100, 1500 in-game seconds):

| Replica | G_final | t(G=50) |
|---|---|---|
| 1 | 78 | 1265 s |
| 2 | 81 | 1055 s |
| 3 | 96 | 835 s |
| 4 | 88 | 750 s |
| 5 | 98 | 715 s |
| **μ ± σ** | **88.2 ± 7.9** | **924 ± 208 s** |
| CV | 9 % | 22 % |

### 4.2 Consumption rate `c`

The naive estimator starts from `G = K`, where the logistic term vanishes and
`dG/dt|₀ ≈ −cN`, giving `c = −(1/N)·dG/dt|₀`. In practice that initial slope is
dominated by noise (section 9.6).

The implementation instead fits the **full ODE trajectory** with `r_cal` held
fixed and `c` as the only free parameter, via `curve_fit` wrapping a numerical
integration. The initial-slope estimator remains as a fallback for the case
where `r` has not been calibrated yet.

Five replicas in C2 (N=5, K=100, 1500 in-game seconds):

| Replica | G_start | G_end | ΔG |
|---|---|---|---|
| 1 | 100 | 88 | 12 |
| 2 | 100 | 91 | 9 |
| 3 | 99 | 92 | 7 |
| 4 | 99 | 87 | 12 |
| 5 | 100 | 93 | 7 |
| **μ ± σ** | **99.6 ± 0.5** | **90.2 ± 2.3** | **9.4 ± 2.2** |

### 4.3 Calibrated parameters

| Parameter | Value | Unit | Replicas |
|---|---|---|---|
| `r_cal` | **0.005037** | 1/s (in-game second) | 5 |
| `c_cal` | **0.010355** | blocks/(sheep·s) | 5 |
| `h` | **K/2** | blocks | assumed from literature (section 8.3) |

The calibrated equation, and the quantitative answer to the original question:

```
dG/dt = 0.005037·G·(1 − G/100) − 0.010355·N
```

### 4.4 Internal validation

The calibration predicts an equilibrium of `G*₊ = 88.4` for the C2 N=5 setup.
The five replicas ended at `90.2 ± 2.3`. The 1.8-block gap sits inside one
standard deviation, so the parameters are mutually consistent.

---

## 5. Saddle-node bifurcation and the critical stocking density

Setting `dG/dt = 0` gives the equilibria:

```
G*± = (K/2)·(1 ± √(1 − 4cN/(rK)))
```

The discriminant `Δ = 1 − 4cN/(rK)` selects the regime:

| Δ | Regime | Behaviour |
|---|---|---|
| `Δ > 0` | Subcritical | Stable equilibrium at `G*₊` |
| `Δ = 0` | Critical | Saddle-node bifurcation at `G* = K/2` |
| `Δ < 0` | Supercritical | Collapse predicted |

Solving `Δ = 0` for `N` gives the critical stocking density:

```
N_crit = r·K / (4·c) = 0.1216·K
```

| Corral | K | N_crit | N values chosen |
|---|---|---|---|
| C1 | 25 | **3.04** | 1, 3, 5 |
| C2 | 100 | **12.16** | 5, 10, 20 |
| C3 | 225 | **27.36** | 10, 25, 40 |
| C4 / C5 / C6 | 100 | **12.16** | 10 |

The values of `N` were chosen to straddle `N_crit` deliberately. Scenario 2
(C1, N=3) lands almost exactly on the bifurcation at `0.99·N_crit`, and
scenario 8 (C3, N=25) sits just below it at `0.91·N_crit` — those two are the
cleanest tests of the theory. Pushing `N/K` far above 1 is pointless: the run
collapses immediately and the curve carries no fittable information.

---

## 6. Predicted equilibria across the 12 scenarios

| Scenario | Corral | K | N | N/N_crit | Δ | G*₊ predicted | Regime |
|---|---|---|---|---|---|---|---|
| 1 | C1 | 25 | 1 | 0.33 | 0.672 | 22.7 | strongly subcritical |
| 2 | C1 | 25 | 3 | 0.99 | 0.013 | 13.9 | **critical (bifurcation)** |
| 3 | C1 | 25 | 5 | 1.65 | < 0 | collapse to 0 | supercritical |
| 4 | C2 | 100 | 5 | 0.41 | 0.589 | 88.4 | subcritical |
| 5 | C2 | 100 | 10 | 0.82 | 0.178 | 71.1 | mid subcritical |
| 6 | C2 | 100 | 20 | 1.64 | < 0 | collapse to 0 | supercritical |
| 7 | C3 | 225 | 10 | 0.37 | 0.635 | 202.1 | strongly subcritical |
| 8 | C3 | 225 | 25 | 0.91 | 0.086 | 145.6 | near critical |
| 9 | C3 | 225 | 40 | 1.46 | < 0 | collapse to 0 | supercritical |
| 10 | C4 water | 100 | 10 | 0.82 | 0.178 | 71.1 | mid subcritical |
| 11 | C5 leaves | 100 | 10 | 0.82 | 0.178 | 71.1 | mid subcritical |
| 12 | C6 fences | 100 | 10 | 0.82 | 0.178 | 71.1 | mid subcritical |

Scenarios 10–12 share identical parameters with scenario 5 by construction, so
any divergence between them isolates the effect of the obstacle rather than of
the stocking density.

---

## 7. Experimental results

### 7.1 Subcritical regime

The original model performs well below `N_crit`. Scenario 4 predicts `G*₊ =
88.4` against a measured plateau of `90.2 ± 2.3`, and RMS across the strongly
subcritical scenarios stays in the 1.5–4.4 block range on stocks of 25 to 225
blocks. Within its stated assumptions the model is accurate.

### 7.2 Supercritical regime — the model fails

The original model predicts collapse to zero whenever `cN > rK/4`. The
experiment never collapsed:

| Scenario | Prediction | Observed plateau |
|---|---|---|
| 3 (C1, N=5) | 0 | ≈ 11.8 |
| 6 (C2, N=20) | 0 | ≈ 54.8 |
| 9 (C3, N=40) | 0 | ≈ 155.0 |

In every supercritical case the grass settled at a stable non-zero level. This
is the central experimental finding, and it motivates the refinement in
section 8.

### 7.3 Effect of the obstacle

Scenarios 5, 10, 11 and 12 share `K = 100` and `N = 10`, so they differ only in
what is inside the corral:

| Scenario | Corral | Observed plateau | Against the C2 baseline |
|---|---|---|---|
| 5 | C2 regular | ≈ 77.6 | baseline |
| 10 | C4 water | ≈ 76.2 | indistinguishable |
| 11 | C5 leaves | ≈ 63.6 | lower |
| 12 | C6 fences | ≈ 53.6 | markedly lower |

Fences depress the equilibrium furthest. The interpretation is that fenced-off
patches are physically unreachable, so the corral's effective carrying capacity
is below its geometric one: `K_effective < K`. This is a different failure mode
from the one in section 7.2 — it is not about how sheep graze but about how
much of the corral they can reach — and neither model handles it (section 8.2).

---

## 8. Model refinement — Holling Type II functional response

### 8.1 The correction

The constant drain `−c·N` assumes sheep graze at full rate no matter how little
grass remains. In reality, as grass gets scarce and scattered, sheep spend most
of their time searching. Replacing the drain with a saturating Type II
functional response (Holling, 1959) captures that:

```
dG/dt = r·G·(1 − G/K) − c·N·G/(G + h)
```

`h` is the half-saturation constant — the stock at which consumption falls to
half its maximum rate. The term vanishes at `G = 0`, so collapse is no longer
forced.

Imposing `dG/dt = 0` and discarding the trivial root gives the equilibrium
quadratic:

```
G² − (K − h)·G + K·(c·N/r − h) = 0
```

### 8.2 Model comparison

RMS in grass blocks, lower is better. `improvement` is positive where Holling
fits better.

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

Reading the table:

- **Holling wins decisively exactly where the original model failed** — all
  three supercritical scenarios improve by 81–91 %, and both near-critical
  scenarios improve by 24–45 %.
- **Holling loses in the strongly subcritical scenarios.** When `G ≈ K` the
  saturating factor `G/(G+h)` is still below 1, so it underestimates
  consumption where the constant drain was already correct. The two models are
  complementary rather than one superseding the other.
- **Both models fail on C6 (fences).** That is consistent with section 7.3: the
  problem there is not the functional response but unreachable area. It needs a
  model with a reduced effective `K`, not a different grazing term.

### 8.3 Justification for `h = K/2`

Real (1977) and Turchin (2003) report `h/K` between 0.1 and 0.5 depending on
how hard the resource is to find. The upper end of that range applies here: the
corral holds discrete, individually scattered blocks, so search time dominates
once grass is scarce. `h = K/2` fits all three observed supercritical plateaus
consistently, and is set by a single constant, `H_FACTOR`, in
`scripts/analyze.py`.

---

## 9. Instrumentation notes and known measurement defects

Each defect below is handled defensively in code; the cross-references point at
the handling.

### 9.1 `latest.log` is cumulative

The server log is not rotated between runs, so it accumulates the history of
every run in the session.

**Handling:** `parse_log.py` locates the last `for #running to 1` (START)
marker and parses only from there (`_find_last_run_start`). Every extraction
therefore captures only the most recent run regardless of how much history the
log carries.

### 9.2 CALIBRATE R does not zero the sheep scoreboard

The CALIBRATE R button kills the sheep entities but never issues
`scoreboard players set ovejas estado 0`, so the score keeps its value from the
previous run and misreports `N`.

**Handling:** `parse_log.py` forces `N = 0` for any file named `calib_r_*`
(`force_N_zero`). The in-game sidebar still shows a stale count during `r`
calibration, but the dataset is correct.

### 9.3 Sheep-spawn buttons emit `Added`, not `Set`

The +1 / +5 / +10 buttons run `scoreboard players add`, which logs as
`Added N to [...] for ovejas (now M)` rather than `Set ... to N`. The original
regex matched only the `Set` form and silently missed these.

**Handling:** the pattern was widened to
`for ovejas (?:to (\d+)|\(now (-?\d+)\))`, and the same treatment applied to
`Corral`, `K` and `t_seg`.

### 9.4 The `Corral` scoreboard conflates C5 and C6

The corral-6 command block wrote `Corral to 5` instead of `Corral to 6`. The
separate `#corral_activo` scoreboard is correct, but the parser was reading
`Corral`, so C6 runs were recorded as C5 and the two became indistinguishable.

**Handling:** `parse_log.py` no longer trusts the log for this field. It
derives the corral from the scenario number (`corral_from_escenario`), which is
fixed by design, making the parser immune both to this defect and to an
operator pressing the wrong button. Files with no scenario in their name fall
back to the logged value.

*Resolved in-world:* the C6 button now writes `Corral to 6` correctly. The
parser deliberately keeps deriving the corral from the scenario anyway. Two
reasons: the logs already recorded before the fix still carry the wrong value,
so the dataset would not be reproducible without it; and a value fixed by
experimental design should not depend on an instrument being correctly
configured in the first place.

### 9.5 LOCAL RESET requires live ticks

LOCAL RESET and CALIBRATE R trigger redstone chains that need running ticks to
propagate. Under `/tick freeze` the chain never completes and the reset is left
half-applied.

**Handling:** protocol change, not code — run them before freezing and allow
1–2 real seconds for the chain to finish (section 3.4).

### 9.6 Calibrating `c` with N=1 gives almost no signal

With a single sheep in C2, total ΔG over 1500 s is 3–5 blocks. The fit
converges but replica variance is high.

**Handling:** the protocol moved to N=5, where ΔG ≈ 12 blocks and the
equilibrium sits clearly below K. The ODE fit is `N`-aware, since `c·N` appears
explicitly, so replicas at different `N` can be mixed.

### 9.7 The initial-slope estimator for `c` is fragile

The original estimator used `c = −slope/N` over a 60-second window. At low `N`
the grass barely moves in 60 s, the slope is approximately zero, and `c`
collapses toward zero with it.

**Handling:** `calibrate_c` fits the full ODE with `r_cal` fixed and `c` as the
only free parameter, keeping the slope method only as a fallback (section 4.2).

### 9.8 The absorbing boundary broke the integrator

The original model drives `G` below zero in the supercritical regime, which is
unphysical — `G = 0` is an absorbing state. The first implementation enforced
that by clamping the derivative to zero once `G ≤ 0`, which made the
right-hand side discontinuous.

`scipy.integrate.odeint` (LSODA) could not handle that discontinuity. On
scenario 9 it aborted with `Excess work done on this call` and returned a
partially-integrated trajectory whose tail diverged to `G ≈ 7540` — for a
corral whose carrying capacity is 225. Worse, the point at which it gave up
varied between runs on identical input, so the reported RMS for scenario 9 was
not reproducible: repeated runs produced 25.094 or 137.943 depending on the run.

**Handling:** the clamp was removed from the derivative and the absorbing
boundary expressed as a **terminal event** at `G = 0`, integrated with
`solve_ivp`; samples after the event are filled with zero. This removes the
discontinuity from the solver's path entirely. All 12 scenarios are now
deterministic and warning-free, and the other 11 RMS values are unchanged. The
corrected scenario-9 value is 137.943, consistent with the other two
supercritical scenarios.

---

## 10. Design decisions

1. **Calibrate only in C2.** `r` and `c` are treated as properties of the
   system rather than of a particular corral, and applied unchanged to all 12
   scenarios. Stated explicitly as an assumption in section 11.
2. **Derive metadata from design, not from observation.** Where the
   experimental design fixes a value, the parser uses the design value and
   ignores the instrument (section 9.4).
3. **Parse only the last run.** Given a cumulative log, the most recent START
   marker defines the run boundary (section 9.1).
4. **Grouped figures over per-scenario figures.** Three grouped figures carry
   the argument; the 12 individual plots remain available for inspection.
5. **File-based stage boundaries.** Each pipeline stage communicates only
   through files on disk (`.log` → `.csv` → `.json`/`.png` → `.docx`), so any
   stage can be rerun in isolation.

---

## 11. Assumptions and limitations

1. `r` and `c` are calibrated only in C2 and assumed constant across all 12
   scenarios. This is most likely to break in C4 and C6, where movement is
   restricted.
2. The continuous model approximates Minecraft's discrete random ticks. The
   approximation is good for large `G` and `N` and degrades for small ones —
   C1 with K=25 is the weakest case.
3. Sheep start uniformly distributed and then move freely; no spatial structure
   is modelled.
4. In C6 the effective carrying capacity for consumption is below the geometric
   one because of unreachable zones. Neither model represents this
   (sections 7.3, 8.2).
5. The calibration is specific to the Minecraft version used; grass-spread
   mechanics differ between versions.
6. **Replication is thinner than designed.** The intended protocol was 3
   replicas per scenario. The dataset contains 1–2: scenarios 3, 4, 5, 6 and 11
   have 2 replicas, and the remaining 7 have 1. Error bars in the per-scenario
   figures are correspondingly weak, and no meaningful standard deviation is
   available for the single-replica scenarios. The calibration itself is the
   exception, with 5 replicas each for `r` and `c`.

---

## 12. Terminology

| Term | Meaning |
|---|---|
| ODE | Equation relating a quantity to its rate of change |
| Autonomous | Time does not appear explicitly, only through `G` |
| Equilibrium | A value at which the stock stops changing (`dG/dt = 0`) |
| Stable / unstable | Stable: perturbations decay. Unstable: perturbations grow |
| Carrying capacity `K` | Maximum grass the corral can sustain |
| Saddle-node bifurcation | Point where two equilibria collide and annihilate, producing an abrupt change in behaviour |
| Discriminant `Δ` | The term under the root; decides whether real equilibria exist |
| `N_crit` | Stocking density separating persistence from collapse, `rK/(4c)` |
| RMS | Root-mean-square error between model and data, in grass blocks |
| Functional response (Holling II) | Consumption saturates: scarcity makes feeding slow |
| Calibration | Measuring `r` and `c` from data rather than assuming them |

---

## 13. Authorship

Conducted for the Differential Equations course, 2026-I, Group 2, by Lina
Andrea Bello Ballén, Julián David Cristancho Niño, Mariana Alejandra Gordillo
Meneses and Brian Steven Vargas Clavijo, under the supervision of Paul Fernando
Camargo Toro.

---

## 14. References

- Holling, C. S. (1959). Some characteristics of simple types of predation and
  parasitism. *The Canadian Entomologist*, 91(7), 385–398.
- Real, L. A. (1977). The kinetics of functional response. *The American
  Naturalist*, 111(978), 289–300.
- Turchin, P. (2003). *Complex Population Dynamics: A Theoretical/Empirical
  Synthesis*. Princeton University Press.
- Begon, M., Townsend, C. R., & Harper, J. L. (2006). *Ecology: From
  Individuals to Ecosystems* (4th ed.). Blackwell Publishing.

---

## 15. Reproducing these numbers

```bash
python scripts/analyze.py data/timeseries.csv
```

Regenerates `data/calibration.json`, `data/rms.csv` and all 16 figures from the
committed time series. Output is deterministic: repeated runs are byte-identical.

The raw server logs are **not** distributed — they contain player IP addresses,
usernames and UUIDs. `data/timeseries.csv` is the published entry point, and
`parse_log.py` is exercised against a synthetic fixture in `tests/`.
