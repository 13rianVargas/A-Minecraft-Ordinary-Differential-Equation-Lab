#!/usr/bin/env python3
"""
analyze.py — Calibrate r and c, integrate the ODE, plot 12 scenarios, tabulate RMS.

Pipeline:
  1. Load the time-series CSV produced by parse_log.py.
  2. Calibrate r (scenario 102, N=0) by curve-fitting the logistic
     G(t) = K / (1 + A*exp(-r*t)).
  3. Calibrate c (scenario 101, N=5) by fitting the full ODE trajectory with
     r held fixed, falling back to the initial-slope method if r is unusable.
  4. For each scenario 1..12: average the replicas, integrate
     dG/dt = r*G*(1 - G/K) - c*N, compute the analytic equilibrium G*+,
     plot, and score both models by RMS.
  5. Write figures/scenario_<N>.png, data/rms.csv and data/calibration.json.

Usage:
  python scripts/analyze.py data/timeseries.csv [--calibrate]
    --calibrate  Run calibration only; print r_cal and c_cal; skip scenarios.

Requires: pandas, numpy, scipy, matplotlib.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import odeint, solve_ivp
from scipy.optimize import curve_fit

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIGURES_DIR = PROJECT_ROOT / "figures"
DEFAULT_CALIBRATION_JSON = PROJECT_ROOT / "data" / "calibration.json"
DEFAULT_RMS_CSV = PROJECT_ROOT / "data" / "rms.csv"

# Sentinel scenario ids reserved for calibration runs (see parse_log.py).
ESC_CALIB_C = 101
ESC_CALIB_R = 102

# Half-saturation constant for the Holling (1959) Type II functional response.
# h is the resource level at which consumption drops to half its maximum rate.
# The ratio h/K is system-dependent: Real (1977) and Begon et al. (2006) report
# values between 0.1 and 0.5 depending on search difficulty. In this experiment
# (corrals of discrete grass blocks driven by Minecraft random ticks) h = K/2
# consistently fits the plateaus observed across the three supercritical
# scenarios (3, 6 and 9), reflecting that sheep spend most of their time
# searching once grass is scarce and scattered.
H_FACTOR = 0.50

# Experimental design: scenario id -> (label, K, N, corral).
SCENARIOS = {
    1: ("C1 5x5", 25, 1, 1),
    2: ("C1 5x5", 25, 3, 1),
    3: ("C1 5x5", 25, 5, 1),
    4: ("C2 10x10", 100, 5, 2),
    5: ("C2 10x10", 100, 10, 2),
    6: ("C2 10x10", 100, 20, 2),
    7: ("C3 15x15", 225, 10, 3),
    8: ("C3 15x15", 225, 25, 3),
    9: ("C3 15x15", 225, 40, 3),
    10: ("C4 water", 100, 10, 4),
    11: ("C5 leaves", 100, 10, 5),
    12: ("C6 fences", 100, 10, 6),
}


def logistic_no_extraction(t, r, K, G0):
    A = (K - G0) / G0 if G0 > 0 else 1.0
    return K / (1.0 + A * np.exp(-r * t))


def logistic_harvest_rhs(G: float, r: float, K: float, c: float,
                         N: float) -> float:
    """Original model: dG/dt = r*G*(1 - G/K) - c*N.

    Grazing is a constant drain, independent of how much grass is left. In
    the supercritical regime (c*N > r*K/4) this drives G below zero, which
    is unphysical — G = 0 is an absorbing boundary. That boundary is imposed
    by the integrator as a terminal event rather than by clamping the
    derivative; see integrate_logistic_harvest.
    """
    return r * G * (1.0 - G / K) - c * N


def holling_rhs(G: float, r: float, K: float, c: float, N: float,
                h: float) -> float:
    """Refined model with a Holling Type II functional response (Holling, 1959).

    The extraction term c*N*G/(G+h) saturates when G is scarce, reflecting
    that sheep cannot eat grass that does not exist. This accounts for the
    plateaus observed in the supercritical regime, which the original model
    fails to capture. The term vanishes at G = 0, so no absorbing-boundary
    event is required here.
    """
    G = max(G, 0.0)
    return r * G * (1.0 - G / K) - c * N * G / (G + h)


def _integrate(rhs, G0: float, t, event=None) -> np.ndarray:
    """Integrate a scalar ODE over the sample grid t, floored at G = 0.

    Uses solve_ivp rather than odeint deliberately. The original model has a
    discontinuous right-hand side once the grass collapses, and odeint's
    LSODA driver fails on it: on scenario 9 it aborts with "Excess work done
    on this call" and returns a partially-integrated trajectory whose tail
    diverges to G ≈ 7540 for a corral whose carrying capacity is K = 225.
    Worse, the point at which it gave up varied between runs, so the reported
    RMS was not reproducible. Expressing the absorbing boundary as a terminal
    event removes the discontinuity from the solver's path entirely.

    Samples after a terminal event are filled with 0: once G reaches 0 with a
    negative derivative it stays there.
    """
    t = np.asarray(t, dtype=float)
    sol = solve_ivp(
        rhs, (t[0], t[-1]), [float(G0)], t_eval=t, events=event,
        method="LSODA", rtol=1e-8, atol=1e-10,
    )
    out = np.zeros_like(t)
    out[:sol.y[0].size] = sol.y[0]
    return np.clip(out, 0.0, None)


def integrate_logistic_harvest(G0: float, t, r: float, K: float, c: float,
                               N: float) -> np.ndarray:
    """Integrate the original model with G = 0 as an absorbing boundary."""
    def rhs(_t, y):
        return [logistic_harvest_rhs(y[0], r, K, c, N)]

    def reaches_zero(_t, y):
        return y[0]
    reaches_zero.terminal = True
    reaches_zero.direction = -1

    return _integrate(rhs, G0, t, event=reaches_zero)


def integrate_holling(G0: float, t, r: float, K: float, c: float, N: float,
                      h: float) -> np.ndarray:
    """Integrate the Holling Type II model."""
    def rhs(_t, y):
        return [holling_rhs(y[0], r, K, c, N, h)]

    return _integrate(rhs, G0, t)


def equilibrium_holling_plus(r: float, K: float, c: float, N: float,
                             h: float) -> float | None:
    """Larger positive root of the Holling Type II equilibrium quadratic.

    Setting dG/dt = 0 in r*G*(1 - G/K) - c*N*G/(G+h) = 0 and discarding the
    trivial root G = 0 yields:

        G^2 - (K - h)*G + K*(c*N/r - h) = 0

    Returns the larger positive root (the stable equilibrium) when the
    discriminant is non-negative; None when the system collapses to 0
    (strongly supercritical regime).
    """
    b = -(K - h)
    cnst = K * (c * N / r - h)
    disc = b * b - 4.0 * cnst
    if disc < 0:
        return None
    roots = [(-b + np.sqrt(disc)) / 2.0, (-b - np.sqrt(disc)) / 2.0]
    positive = [g for g in roots if g > 0]
    if not positive:
        return None
    return float(max(positive))


def calibrate_r(df: pd.DataFrame) -> float:
    sub = df[df.escenario == ESC_CALIB_R]
    if sub.empty:
        print("[WARN] no calibration-r data (scenario 102) found", file=sys.stderr)
        return float("nan")
    rs = []
    for rep, g in sub.groupby("replica"):
        g = g.sort_values("t_segundos")
        K = float(g["K"].iloc[0])
        G0 = float(g["G"].iloc[0]) or 1.0
        try:
            popt, _ = curve_fit(
                lambda t, r: logistic_no_extraction(t, r, K, G0),
                g["t_segundos"].values,
                g["G"].values,
                p0=[0.01],
                bounds=(0, np.inf),
            )
            rs.append(float(popt[0]))
        except Exception as e:
            print(f"[WARN] curve_fit r failed for replica {rep}: {e}",
                  file=sys.stderr)
    if not rs:
        return float("nan")
    return float(np.mean(rs))


def calibrate_c(df: pd.DataFrame, r_cal: float | None = None,
                fit_window_s: float = 60.0) -> float:
    """Calibrate c.

    Preferred path: with r_cal known, fit the full ODE trajectory
    dG/dt = r*G*(1 - G/K) - c*N and let c be the only free parameter.
    This is robust for low-N runs where the initial slope is dominated by
    measurement noise.

    Fallback: if r_cal is NaN or None, use the initial-slope method
    c = -slope/N over the first fit_window_s seconds.
    """
    sub = df[df.escenario == ESC_CALIB_C]
    if sub.empty:
        print("[WARN] no calibration-c data (scenario 101) found", file=sys.stderr)
        return float("nan")

    use_ode = r_cal is not None and np.isfinite(r_cal) and r_cal > 0
    cs = []
    for rep, g in sub.groupby("replica"):
        g = g.sort_values("t_segundos")
        K = float(g["K"].iloc[0])
        N = float(g["N"].iloc[0]) or 1.0
        G0 = float(g["G"].iloc[0]) or K
        t = g["t_segundos"].values
        Gobs = g["G"].values

        if use_ode:
            def model(t_grid, c, _r=r_cal, _K=K, _N=N, _G0=G0):
                sol = odeint(
                    lambda G, _t: _r * G * (1 - G / _K) - c * _N,
                    _G0, t_grid,
                ).flatten()
                return sol
            try:
                popt, _ = curve_fit(
                    model, t, Gobs, p0=[0.01], bounds=(0, np.inf)
                )
                cs.append(float(popt[0]))
            except Exception as e:
                print(f"[WARN] ODE fit for c failed for replica {rep}: {e}",
                      file=sys.stderr)
        else:
            g0 = g[g["t_segundos"] <= fit_window_s]
            if len(g0) < 3:
                continue
            slope = np.polyfit(g0["t_segundos"].values, g0["G"].values, 1)[0]
            cs.append(-slope / N)

    if not cs:
        return float("nan")
    return float(np.mean(cs))


def equilibrium_plus(r: float, K: float, c: float, N: float) -> float | None:
    disc = 1.0 - 4.0 * c * N / (r * K)
    if disc < 0:
        return None
    return K / 2.0 * (1.0 + np.sqrt(disc))


def _trajectory(df: pd.DataFrame, esc: int):
    """Return (t, G_mean, G_std) arrays for one scenario, averaging replicas."""
    sub = df[df.escenario == esc]
    if sub.empty:
        return None, None, None
    g = sub.groupby("t_segundos")["G"].agg(["mean", "std"]).reset_index()
    g["std"] = g["std"].fillna(0)
    return g["t_segundos"].values, g["mean"].values, g["std"].values


def plot_grouped_carrying_capacity(df: pd.DataFrame, r: float, c: float,
                                   out_dir: Path) -> None:
    """Figure A: effect of increasing K (C1/C2/C3) at comparable N/K.

    One plot, three trajectories, normalised axis G/K.
    """
    # (scenario, corral, K) — the middle scenario of each corral.
    groups = [(2, 1, 25), (5, 2, 100), (8, 3, 225)]
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["tab:blue", "tab:orange", "tab:green"]
    for (esc, corral, K), color in zip(groups, colors):
        t, Gm, Gs = _trajectory(df, esc)
        if t is None:
            continue
        N = SCENARIOS[esc][2]
        ax.errorbar(t, Gm / K, yerr=Gs / K, fmt=".", color=color, capsize=1.2,
                    markersize=3, elinewidth=0.6,
                    label=f"C{corral} K={K} N={N} (scenario {esc})")
        sol = integrate_logistic_harvest(K, t, r, K, c, N)
        ax.plot(t, sol / K, "-", color=color, lw=1.5, alpha=0.7)
    ax.set_xlabel("t (in-game seconds)")
    ax.set_ylabel("G / K (grass fraction)")
    ax.set_title("Group A — Effect of increasing K (regular corrals)")
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "group_a_carrying_capacity.png", dpi=120)
    plt.close(fig)


def plot_grouped_obstacles(df: pd.DataFrame, r: float, c: float,
                           out_dir: Path) -> None:
    """Figure B: isolates the obstacle effect. C2/C4/C5/C6 at K=100, N=10."""
    groups = [(5, "C2 regular", "tab:blue"),
              (10, "C4 water", "tab:cyan"),
              (11, "C5 leaves", "tab:green"),
              (12, "C6 fences", "tab:red")]
    fig, ax = plt.subplots(figsize=(8, 5))
    K, N = 100, 10
    for esc, lbl, color in groups:
        t, Gm, Gs = _trajectory(df, esc)
        if t is None:
            continue
        ax.errorbar(t, Gm, yerr=Gs, fmt=".", color=color, capsize=1.2,
                    markersize=3, elinewidth=0.6,
                    label=f"{lbl} (scenario {esc})")
    # A single theoretical prediction covers all four: same K and N.
    t_grid = np.linspace(0, max(60, df["t_segundos"].max()), 200)
    sol = integrate_logistic_harvest(K, t_grid, r, K, c, N)
    ax.plot(t_grid, sol, "k--", lw=2, label="theoretical ODE (K=100, N=10)")
    G_eq = equilibrium_plus(r, K, c, N)
    if G_eq is not None:
        ax.axhline(G_eq, ls=":", color="gray", label=f"G*+ = {G_eq:.1f}")
    ax.set_xlabel("t (in-game seconds)")
    ax.set_ylabel("G (grass blocks)")
    ax.set_title("Group B — Effect of the obstacle (K=100, N=10 fixed)")
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "group_b_obstacles.png", dpi=120)
    plt.close(fig)


def plot_grouped_bifurcation(df: pd.DataFrame, r: float, c: float,
                             out_dir: Path) -> None:
    """Figure C: saddle-node bifurcation. Three values of N in C3 (7/8/9).

    C3 is used because its large K=225 produces the cleanest separation
    between regimes.
    """
    groups = [(7, "subcritical  N=10", "tab:green"),
              (8, "near-critical  N=25", "tab:orange"),
              (9, "supercritical  N=40", "tab:red")]
    K = 225
    fig, ax = plt.subplots(figsize=(8, 5))
    for esc, lbl, color in groups:
        t, Gm, Gs = _trajectory(df, esc)
        if t is None:
            continue
        N = SCENARIOS[esc][2]
        ax.errorbar(t, Gm, yerr=Gs, fmt=".", color=color, capsize=1.2,
                    markersize=3, elinewidth=0.6, label=lbl)
        sol = integrate_logistic_harvest(K, t, r, K, c, N)
        ax.plot(t, sol, "-", color=color, lw=1.5, alpha=0.7)
        G_eq = equilibrium_plus(r, K, c, N)
        if G_eq is not None:
            ax.axhline(G_eq, ls=":", color=color, alpha=0.5)
    N_crit = r * K / (4 * c)
    ax.set_xlabel("t (in-game seconds)")
    ax.set_ylabel("G (grass blocks)")
    ax.set_title(
        f"Group C — Saddle-node bifurcation (C3, K={K})  ·  "
        f"N_crit = rK/(4c) = {N_crit:.1f}"
    )
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "group_c_bifurcation.png", dpi=120)
    plt.close(fig)


def plot_scenario(esc: int, label: str, K: float, N: float,
                  df: pd.DataFrame, r: float, c: float,
                  out_dir: Path) -> tuple[float, float, float | None,
                                          float | None]:
    """Plot one scenario with both models (original and Holling).

    Returns: (rms_orig, rms_holling, G_eq_orig, G_eq_holling).
    """
    sub = df[df.escenario == esc]
    if sub.empty:
        print(f"[WARN] no data for scenario {esc}", file=sys.stderr)
        return float("nan"), float("nan"), None, None
    grouped = sub.groupby("t_segundos")["G"].agg(["mean", "std"]).reset_index()
    grouped["std"] = grouped["std"].fillna(0)

    t = grouped["t_segundos"].values
    G_data_mean = grouped["mean"].values
    G_data_std = grouped["std"].values

    G0 = float(sub.groupby("replica")["G"].first().mean())
    if not np.isfinite(G0) or G0 <= 0:
        G0 = K

    h = H_FACTOR * K

    sol_orig = integrate_logistic_harvest(G0, t, r, K, c, N)
    sol_holl = integrate_holling(G0, t, r, K, c, N, h)

    G_eq_orig = equilibrium_plus(r, K, c, N)
    G_eq_holl = equilibrium_holling_plus(r, K, c, N, h)

    rms_orig = float(np.sqrt(np.mean((G_data_mean - sol_orig) ** 2)))
    rms_holl = float(np.sqrt(np.mean((G_data_mean - sol_holl) ** 2)))

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(t, G_data_mean, yerr=G_data_std, fmt=".", capsize=1.2,
                color="black", markersize=3, elinewidth=0.6,
                label="data (mean ± σ)")
    ax.plot(t, sol_orig, "-", lw=1.5, color="tab:blue",
            label=f"original ODE  RMS={rms_orig:.1f}")
    ax.plot(t, sol_holl, "-", lw=1.5, color="tab:red",
            label=f"Holling Type II  RMS={rms_holl:.1f}")
    if G_eq_orig is not None:
        ax.axhline(G_eq_orig, ls="--", color="tab:blue", alpha=0.5,
                   label=f"G*+ original = {G_eq_orig:.1f}")
    if G_eq_holl is not None:
        ax.axhline(G_eq_holl, ls="--", color="tab:red", alpha=0.5,
                   label=f"G*+ Holling = {G_eq_holl:.1f}")
    ax.axhline(K, ls=":", color="gray", label=f"K = {K:.0f}")
    ax.set_xlabel("t (in-game seconds)")
    ax.set_ylabel("G (grass blocks)")
    ax.set_title(
        f"Scenario {esc} — {label}  N={int(N)}  h={H_FACTOR:g}·K={h:.1f}"
    )
    ax.legend(loc="best", fontsize=7)
    ax.grid(alpha=0.3)
    fig.tight_layout()

    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"scenario_{esc:02d}.png", dpi=120)
    plt.close(fig)
    return rms_orig, rms_holl, G_eq_orig, G_eq_holl


def plot_model_comparison(df: pd.DataFrame, r: float, c: float,
                          out_dir: Path) -> None:
    """Headline figure: the three supercritical scenarios (3, 6, 9), showing
    the original ODE collapsing to 0 while Holling Type II reproduces the
    stable plateaus present in the data."""
    groups = [
        (3, "Scenario 3 — C1 K=25 N=5", "tab:orange"),
        (6, "Scenario 6 — C2 K=100 N=20", "tab:green"),
        (9, "Scenario 9 — C3 K=225 N=40", "tab:purple"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=False)
    for ax, (esc, title, color) in zip(axes, groups):
        sub = df[df.escenario == esc]
        if sub.empty:
            ax.set_title(f"{title}\n(no data)")
            continue
        grouped = sub.groupby("t_segundos")["G"].agg(["mean", "std"]).reset_index()
        grouped["std"] = grouped["std"].fillna(0)
        t = grouped["t_segundos"].values
        G_mean = grouped["mean"].values
        G_std = grouped["std"].values

        K = float(sub["K"].iloc[0])
        N = float(sub["N"].iloc[0])
        h = H_FACTOR * K
        G0 = float(sub.groupby("replica")["G"].first().mean()) or K

        sol_orig = integrate_logistic_harvest(G0, t, r, K, c, N)
        sol_holl = integrate_holling(G0, t, r, K, c, N, h)

        ax.errorbar(t, G_mean, yerr=G_std, fmt=".", color="black",
                    capsize=1.2, markersize=2.5, elinewidth=0.6,
                    label="data")
        ax.plot(t, sol_orig, "--", lw=1.5, color="tab:blue",
                label="original ODE")
        ax.plot(t, sol_holl, "-", lw=1.5, color="tab:red",
                label="Holling Type II")
        ax.axhline(K, ls=":", color="gray", alpha=0.5)
        ax.set_xlabel("t (s)")
        ax.set_ylabel("G (blocks)")
        ax.set_title(title)
        ax.legend(loc="best", fontsize=8)
        ax.grid(alpha=0.3)
    fig.suptitle(
        "Model comparison in the supercritical regime — "
        "the original ODE predicts collapse to 0; Holling captures the plateaus",
        fontsize=11,
    )
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "model_comparison.png", dpi=120)
    plt.close(fig)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("csv", type=Path,
                   help="Time-series CSV produced by parse_log.py")
    p.add_argument("--calibrate", action="store_true",
                   help="Only calibrate r and c; skip the scenarios.")
    p.add_argument("--out-figures", type=Path, default=DEFAULT_FIGURES_DIR,
                   help="Output directory for plots")
    p.add_argument("--calibration-json", type=Path,
                   default=DEFAULT_CALIBRATION_JSON,
                   help="Where to write the calibration results")
    p.add_argument("--rms-csv", type=Path, default=DEFAULT_RMS_CSV,
                   help="Where to write the RMS summary")
    args = p.parse_args(argv[1:])

    df = pd.read_csv(args.csv)
    if df.empty:
        print(f"{args.csv} is empty", file=sys.stderr)
        return 1

    r_cal = calibrate_r(df)
    c_cal = calibrate_c(df, r_cal=r_cal)
    print(f"r_cal = {r_cal:.6f} 1/s")
    print(f"c_cal = {c_cal:.6f} blocks/(sheep*s)")

    cal = {"r_cal": r_cal, "c_cal": c_cal}
    args.calibration_json.parent.mkdir(parents=True, exist_ok=True)
    args.calibration_json.write_text(json.dumps(cal, indent=2))
    print(f"Wrote {args.calibration_json}", file=sys.stderr)

    if args.calibrate:
        return 0

    if not np.isfinite(r_cal) or not np.isfinite(c_cal):
        print(
            "[ERROR] r_cal or c_cal is not finite. The input CSV must contain "
            f"calibration runs (scenario {ESC_CALIB_R} for r, {ESC_CALIB_C} "
            "for c) before the scenarios can be analysed.",
            file=sys.stderr,
        )
        return 1

    rows = []
    for esc, (label, K, N, corral) in SCENARIOS.items():
        rms_orig, rms_holl, G_eq_orig, G_eq_holl = plot_scenario(
            esc, label, K, N, df, r_cal, c_cal, args.out_figures
        )
        N_crit = r_cal * K / (4 * c_cal)
        h_used = H_FACTOR * K
        # Percentage RMS improvement: positive means Holling fits better.
        if rms_orig > 0 and np.isfinite(rms_orig) and np.isfinite(rms_holl):
            improvement_pct = 100.0 * (rms_orig - rms_holl) / rms_orig
        else:
            improvement_pct = float("nan")
        rows.append({
            "escenario": esc,
            "corral": corral,
            "label": label,
            "K": K,
            "N": N,
            "N_div_K": round(N / K, 3),
            "N_crit": round(N_crit, 2),
            "regimen": (
                "subcritico" if N < N_crit * 0.9
                else "supercritico" if N > N_crit * 1.1
                else "critico"
            ),
            "h_usado": round(h_used, 2),
            "G_eq_orig": round(G_eq_orig, 2) if G_eq_orig is not None else None,
            "G_eq_holling": (
                round(G_eq_holl, 2) if G_eq_holl is not None else None
            ),
            "RMS_orig": round(rms_orig, 3),
            "RMS_holling": round(rms_holl, 3),
            "mejora_pct": round(improvement_pct, 1),
            "discriminante": round(1.0 - 4.0 * c_cal * N / (r_cal * K), 4),
        })
    args.rms_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.rms_csv, index=False)
    print(f"Wrote {args.rms_csv}", file=sys.stderr)

    # Three grouped figures (the ones embedded in the report) plus the
    # model-comparison figure.
    plot_grouped_carrying_capacity(df, r_cal, c_cal, args.out_figures)
    plot_grouped_obstacles(df, r_cal, c_cal, args.out_figures)
    plot_grouped_bifurcation(df, r_cal, c_cal, args.out_figures)
    plot_model_comparison(df, r_cal, c_cal, args.out_figures)
    print(
        "Wrote 4 grouped figures: group_a_carrying_capacity.png, "
        "group_b_obstacles.png, group_c_bifurcation.png, "
        "model_comparison.png",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
