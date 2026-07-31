#!/usr/bin/env python3
"""
analizar.py — Fit r and c, integrate EDO, plot 12 scenarios + RMS table.

Pipeline:
  1. Load datos.csv (output of parse_log.py).
  2. Calibrate r (esc=102, N=0): curve_fit on logistic G(t)=K/(1+A·exp(-rt)).
  3. Calibrate c (esc=101, N=1): initial slope c = -(1/N)·dG/dt at t->0.
  4. For each scenario 1..12: average replicas, integrate dG/dt=rG(1-G/K)-cN,
     compute analytic equilibrium G*_+, plot, compute RMS.
  5. Write graficas/esc_<N>.png, rms.csv, cal.json.

Usage:
  python analizar.py datos.csv [--calibrar]
    --calibrar  Run only calibration; print r_cal and c_cal; skip 1..12.

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
from scipy.integrate import odeint
from scipy.optimize import curve_fit

ESC_CALIB_C = 101
ESC_CALIB_R = 102

# Constante de semi-saturación para la respuesta funcional Tipo II
# de Holling (1959). h es la cantidad de recurso a la que el consumo cae
# a la mitad de su tasa máxima. El factor (h/K) depende del sistema:
# Real (1977) y Begon et al. (2006) reportan valores entre 0.1 y 0.5 según
# la dificultad de búsqueda. En este experimento (corrales con grass
# discreto + random ticks de Minecraft), h ≈ K/2 ajusta consistentemente
# las mesetas observadas en los 3 escenarios supercríticos (esc 3, 6, 9),
# reflejando que las ovejas pierden mucho tiempo buscando cuando el
# pasto es escaso y disperso por el corral.
H_FACTOR = 0.50

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
    10: ("C4 agua", 100, 10, 4),
    11: ("C5 hojas", 100, 10, 5),
    12: ("C6 vallas", 100, 10, 6),
}


def logistic_no_extraction(t, r, K, G0):
    A = (K - G0) / G0 if G0 > 0 else 1.0
    return K / (1.0 + A * np.exp(-r * t))


def edo(G, t, r, K, c, N):
    # G no puede ser negativo: el cesped colapsa a 0 y ahi se queda
    # (equilibrio absorbente). Sin este tope, en los escenarios
    # supercriticos odeint diverge a -infinito y el RMS sale sin sentido.
    G = max(G, 0.0)
    d = r * G * (1.0 - G / K) - c * N
    return d if (G > 0.0 or d > 0.0) else 0.0


def edo_holling(G, t, r, K, c, N, h):
    """EDO refinada con respuesta funcional Tipo II (Holling, 1959).

    El término de extracción `c·N·G/(G+h)` se satura cuando G es escaso,
    reflejando que las ovejas no pueden comer pasto que no existe. Esto
    explica las mesetas observadas en régimen supercrítico que la EDO
    original no captura.
    """
    G = max(G, 0.0)
    d = r * G * (1.0 - G / K) - c * N * G / (G + h)
    return d


def equilibrium_holling_plus(r: float, K: float, c: float, N: float,
                              h: float) -> float | None:
    """Raíz positiva mayor de la cuadrática de equilibrio Holling Tipo II.

    Imponer dG/dt = 0 en `r·G·(1-G/K) - c·N·G/(G+h) = 0` y descartar G=0
    da la cuadrática:

        G² - (K - h)·G + K·(c·N/r - h) = 0

    Retorna la raíz positiva mayor (equilibrio estable) si el discriminante
    es ≥ 0; None si el sistema colapsa a 0 (régimen muy supercrítico).
    """
    b = -(K - h)
    cnst = K * (c * N / r - h)
    disc = b * b - 4.0 * cnst
    if disc < 0:
        return None
    raices = [(-b + np.sqrt(disc)) / 2.0, (-b - np.sqrt(disc)) / 2.0]
    positivas = [g for g in raices if g > 0]
    if not positivas:
        return None
    return float(max(positivas))


def calibrate_r(df: pd.DataFrame) -> float:
    sub = df[df.escenario == ESC_CALIB_R]
    if sub.empty:
        print("[WARN] no calibration-r data (esc=102) found", file=sys.stderr)
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
            print(f"[WARN] curve_fit r failed rep={rep}: {e}", file=sys.stderr)
    if not rs:
        return float("nan")
    return float(np.mean(rs))


def calibrate_c(df: pd.DataFrame, r_cal: float | None = None,
                 fit_window_s: float = 60.0) -> float:
    """Calibrate c.

    Preferred path: with r_cal known, fit the FULL EDO trajectory
    `dG/dt = r·G·(1-G/K) − c·N` and let c be the only free parameter.
    Robust for low-N runs where the initial slope is dominated by noise.

    Fallback: if r_cal is NaN/None, use the initial-slope method
    `c = -slope/N` over `fit_window_s` seconds.
    """
    sub = df[df.escenario == ESC_CALIB_C]
    if sub.empty:
        print("[WARN] no calibration-c data (esc=101) found", file=sys.stderr)
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
                print(f"[WARN] ODE fit c failed rep={rep}: {e}", file=sys.stderr)
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


def _trayectoria(df: pd.DataFrame, esc: int):
    """Return (t, G_mean, G_std) arrays for a given scenario, averaging replicas."""
    sub = df[df.escenario == esc]
    if sub.empty:
        return None, None, None
    g = sub.groupby("t_segundos")["G"].agg(["mean", "std"]).reset_index()
    g["std"] = g["std"].fillna(0)
    return g["t_segundos"].values, g["mean"].values, g["std"].values


def plot_grouped_K_creciente(df: pd.DataFrame, r: float, c: float,
                              out_dir: Path) -> None:
    """Figura A: efecto de K creciente (C1/C2/C3) con N tal que N/K es comparable.
    Una sola gráfica con 3 trayectorias, eje normalizado G/K."""
    pares = [(2, 1, 25), (5, 2, 100), (8, 3, 225)]  # (esc, corral, K) — esc del medio de cada corral
    fig, ax = plt.subplots(figsize=(8, 5))
    colores = ["tab:blue", "tab:orange", "tab:green"]
    for (esc, corral, K), color in zip(pares, colores):
        t, Gm, Gs = _trayectoria(df, esc)
        if t is None:
            continue
        N = SCENARIOS[esc][2]
        ax.errorbar(t, Gm / K, yerr=Gs / K, fmt=".", color=color, capsize=1.2,
                    markersize=3, elinewidth=0.6,
                    label=f"C{corral} K={K} N={N} (esc {esc})")
        sol = odeint(edo, K, t, args=(r, K, c, N)).flatten()
        ax.plot(t, sol / K, "-", color=color, lw=1.5, alpha=0.7)
    ax.set_xlabel("t (s de juego)")
    ax.set_ylabel("G / K (fracción de césped)")
    ax.set_title("Grupo A — Efecto de K creciente (corrales regulares)")
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "grupo_A_K_creciente.png", dpi=120)
    plt.close(fig)


def plot_grouped_obstaculos(df: pd.DataFrame, r: float, c: float,
                             out_dir: Path) -> None:
    """Figura B: aísla el efecto del obstáculo. C2/C4/C5/C6 con K=100, N=10."""
    pares = [(5, "C2 regular", "tab:blue"),
             (10, "C4 agua", "tab:cyan"),
             (11, "C5 hojas", "tab:green"),
             (12, "C6 vallas", "tab:red")]
    fig, ax = plt.subplots(figsize=(8, 5))
    K, N = 100, 10
    for esc, lbl, color in pares:
        t, Gm, Gs = _trayectoria(df, esc)
        if t is None:
            continue
        ax.errorbar(t, Gm, yerr=Gs, fmt=".", color=color, capsize=1.2,
                    markersize=3, elinewidth=0.6,
                    label=f"{lbl} (esc {esc})")
    # Solo una predicción teórica (única para los 4, mismo K y N)
    t_grid = np.linspace(0, max(60, df["t_segundos"].max()), 200)
    sol = odeint(edo, K, t_grid, args=(r, K, c, N)).flatten()
    ax.plot(t_grid, sol, "k--", lw=2, label="EDO teórica (K=100, N=10)")
    G_eq = equilibrium_plus(r, K, c, N)
    if G_eq is not None:
        ax.axhline(G_eq, ls=":", color="gray", label=f"G*₊={G_eq:.1f}")
    ax.set_xlabel("t (s de juego)")
    ax.set_ylabel("G (bloques de césped)")
    ax.set_title("Grupo B — Efecto del obstáculo (K=100, N=10 fijo)")
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "grupo_B_obstaculos.png", dpi=120)
    plt.close(fig)


def plot_grouped_bifurcacion(df: pd.DataFrame, r: float, c: float,
                              out_dir: Path) -> None:
    """Figura C: bifurcación silla-nodo. Tres N en C2 (esc 4/5/6) o C3 (esc 7/8/9).
    Usa C3 por defecto porque tiene K=225 grande → bifurcación más limpia."""
    pares = [(7, "subcrítico  N=10", "tab:green"),
             (8, "≈ crítico  N=25", "tab:orange"),
             (9, "supercrítico  N=40", "tab:red")]
    K = 225
    fig, ax = plt.subplots(figsize=(8, 5))
    for esc, lbl, color in pares:
        t, Gm, Gs = _trayectoria(df, esc)
        if t is None:
            continue
        N = SCENARIOS[esc][2]
        ax.errorbar(t, Gm, yerr=Gs, fmt=".", color=color, capsize=1.2,
                    markersize=3, elinewidth=0.6, label=lbl)
        sol = odeint(edo, K, t, args=(r, K, c, N)).flatten()
        ax.plot(t, sol, "-", color=color, lw=1.5, alpha=0.7)
        G_eq = equilibrium_plus(r, K, c, N)
        if G_eq is not None:
            ax.axhline(G_eq, ls=":", color=color, alpha=0.5)
    N_crit = r * K / (4 * c)
    ax.set_xlabel("t (s de juego)")
    ax.set_ylabel("G (bloques de césped)")
    ax.set_title(
        f"Grupo C — Bifurcación silla-nodo (C3 K={K})  ·  "
        f"N_crit = rK/(4c) = {N_crit:.1f}"
    )
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "grupo_C_bifurcacion.png", dpi=120)
    plt.close(fig)


def plot_scenario(esc: int, label: str, K: float, N: float, corral: int,
                  df: pd.DataFrame, r: float, c: float,
                  out_dir: Path) -> tuple[float, float, float | None,
                                          float | None]:
    """Plot one scenario with BOTH models (original and Holling).

    Returns: (rms_orig, rms_holling, G_eq_orig, G_eq_holling).
    """
    sub = df[df.escenario == esc]
    if sub.empty:
        print(f"[WARN] no data for esc={esc}", file=sys.stderr)
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

    sol_orig = odeint(edo, G0, t, args=(r, K, c, N)).flatten()
    sol_holl = odeint(edo_holling, G0, t, args=(r, K, c, N, h)).flatten()

    G_eq_orig = equilibrium_plus(r, K, c, N)
    G_eq_holl = equilibrium_holling_plus(r, K, c, N, h)

    rms_orig = float(np.sqrt(np.mean((G_data_mean - sol_orig) ** 2)))
    rms_holl = float(np.sqrt(np.mean((G_data_mean - sol_holl) ** 2)))

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(t, G_data_mean, yerr=G_data_std, fmt=".", capsize=1.2,
                color="black", markersize=3, elinewidth=0.6,
                label="datos (media ± σ)")
    ax.plot(t, sol_orig, "-", lw=1.5, color="tab:blue",
            label=f"EDO original  RMS={rms_orig:.1f}")
    ax.plot(t, sol_holl, "-", lw=1.5, color="tab:red",
            label=f"Holling Tipo II  RMS={rms_holl:.1f}")
    if G_eq_orig is not None:
        ax.axhline(G_eq_orig, ls="--", color="tab:blue", alpha=0.5,
                   label=f"G*₊ orig = {G_eq_orig:.1f}")
    if G_eq_holl is not None:
        ax.axhline(G_eq_holl, ls="--", color="tab:red", alpha=0.5,
                   label=f"G*₊ Holling = {G_eq_holl:.1f}")
    ax.axhline(K, ls=":", color="gray", label=f"K = {K:.0f}")
    ax.set_xlabel("t (s de juego)")
    ax.set_ylabel("G (bloques de césped)")
    ax.set_title(f"Esc {esc} — {label}  N={int(N)}  h=K/10={h:.1f}")
    ax.legend(loc="best", fontsize=7)
    ax.grid(alpha=0.3)
    fig.tight_layout()

    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"esc_{esc:02d}.png", dpi=120)
    plt.close(fig)
    return rms_orig, rms_holl, G_eq_orig, G_eq_holl


def plot_comparacion_modelos(df: pd.DataFrame, r: float, c: float,
                              out_dir: Path) -> None:
    """Figura central del paper: 3 supercríticos (esc 3, 6, 9) mostrando
    cómo la EDO original colapsa a 0 mientras Holling Tipo II reproduce las
    mesetas estables observadas en los datos."""
    pares = [
        (3, "Esc 3 — C1 K=25 N=5", "tab:orange"),
        (6, "Esc 6 — C2 K=100 N=20", "tab:green"),
        (9, "Esc 9 — C3 K=225 N=40", "tab:purple"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=False)
    for ax, (esc, title, color) in zip(axes, pares):
        sub = df[df.escenario == esc]
        if sub.empty:
            ax.set_title(f"{title}\n(sin datos)")
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

        sol_orig = odeint(edo, G0, t, args=(r, K, c, N)).flatten()
        sol_holl = odeint(edo_holling, G0, t, args=(r, K, c, N, h)).flatten()

        ax.errorbar(t, G_mean, yerr=G_std, fmt=".", color="black",
                    capsize=1.2, markersize=2.5, elinewidth=0.6,
                    label="datos")
        ax.plot(t, sol_orig, "--", lw=1.5, color="tab:blue",
                label="EDO original")
        ax.plot(t, sol_holl, "-", lw=1.5, color="tab:red",
                label="Holling Tipo II")
        ax.axhline(K, ls=":", color="gray", alpha=0.5)
        ax.set_xlabel("t (s)")
        ax.set_ylabel("G (bloques)")
        ax.set_title(title)
        ax.legend(loc="best", fontsize=8)
        ax.grid(alpha=0.3)
    fig.suptitle(
        "Comparación de modelos en régimen supercrítico — "
        "la EDO original predice colapso a 0; Holling captura las mesetas",
        fontsize=11,
    )
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "comparacion_modelos.png", dpi=120)
    plt.close(fig)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv", type=Path, help="datos.csv path")
    p.add_argument("--calibrar", action="store_true",
                   help="Only calibrate r and c; skip scenarios.")
    p.add_argument("--out-graficas", type=Path,
                   default=Path("graficas"), help="Output dir for plots")
    p.add_argument("--cal-json", type=Path, default=Path("cal.json"),
                   help="Where to write/read calibration results")
    p.add_argument("--rms-csv", type=Path, default=Path("rms.csv"),
                   help="Where to write RMS summary")
    args = p.parse_args(argv[1:])

    df = pd.read_csv(args.csv)
    if df.empty:
        print("datos.csv vacío", file=sys.stderr)
        return 1

    r_cal = calibrate_r(df)
    c_cal = calibrate_c(df, r_cal=r_cal)
    print(f"r_cal = {r_cal:.6f} 1/s")
    print(f"c_cal = {c_cal:.6f} bloques/(oveja·s)")

    cal = {"r_cal": r_cal, "c_cal": c_cal}
    args.cal_json.write_text(json.dumps(cal, indent=2))
    print(f"Wrote {args.cal_json}", file=sys.stderr)

    if args.calibrar:
        return 0

    if not np.isfinite(r_cal) or not np.isfinite(c_cal):
        print("[ERROR] r_cal o c_cal no son finitos. Ejecuta calibración antes.",
              file=sys.stderr)
        return 1

    rows = []
    for esc, (label, K, N, corral) in SCENARIOS.items():
        rms_orig, rms_holl, G_eq_orig, G_eq_holl = plot_scenario(
            esc, label, K, N, corral, df, r_cal, c_cal, args.out_graficas
        )
        N_crit = r_cal * K / (4 * c_cal)
        h_usado = H_FACTOR * K
        # mejora porcentual del RMS: positiva si Holling es mejor.
        if rms_orig > 0 and np.isfinite(rms_orig) and np.isfinite(rms_holl):
            mejora_pct = 100.0 * (rms_orig - rms_holl) / rms_orig
        else:
            mejora_pct = float("nan")
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
            "h_usado": round(h_usado, 2),
            "G_eq_orig": round(G_eq_orig, 2) if G_eq_orig is not None else None,
            "G_eq_holling": (
                round(G_eq_holl, 2) if G_eq_holl is not None else None
            ),
            "RMS_orig": round(rms_orig, 3),
            "RMS_holling": round(rms_holl, 3),
            "mejora_pct": round(mejora_pct, 1),
            "discriminante": round(1.0 - 4.0 * c_cal * N / (r_cal * K), 4),
        })
    pd.DataFrame(rows).to_csv(args.rms_csv, index=False)
    print(f"Wrote {args.rms_csv}", file=sys.stderr)

    # 3 figuras agrupadas (las que van al docx) + comparación de modelos
    plot_grouped_K_creciente(df, r_cal, c_cal, args.out_graficas)
    plot_grouped_obstaculos(df, r_cal, c_cal, args.out_graficas)
    plot_grouped_bifurcacion(df, r_cal, c_cal, args.out_graficas)
    plot_comparacion_modelos(df, r_cal, c_cal, args.out_graficas)
    print(
        "Wrote 4 figuras: grupo_A_K_creciente.png, grupo_B_obstaculos.png, "
        "grupo_C_bifurcacion.png, comparacion_modelos.png",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
