"""Reproducibility tests for scripts/analyze.py.

The claim the README makes is that every published number regenerates from
`data/timeseries.csv`. These tests are what makes that claim checkable rather
than merely stated: they recompute the calibration and the RMS table from the
committed time series and compare against the committed results.

Outputs are written to a temporary directory — running the tests never mutates
the repository.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import analyze  # noqa: E402

TIMESERIES = PROJECT_ROOT / "data" / "timeseries.csv"
COMMITTED_CALIBRATION = PROJECT_ROOT / "data" / "calibration.json"
COMMITTED_RMS = PROJECT_ROOT / "data" / "rms.csv"

# The calibration is a curve fit, so allow for last-bit floating point
# differences across platforms and library builds while still pinning the
# value to far more precision than the 6 significant figures ever quoted.
CALIBRATION_TOLERANCE = 1e-9
# RMS values are reported to 3 decimals; anything above this would show up in
# the published table.
RMS_TOLERANCE = 5e-4


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(TIMESERIES)


@pytest.fixture(scope="module")
def committed_calibration():
    return json.loads(COMMITTED_CALIBRATION.read_text())


@pytest.fixture(scope="module")
def regenerated_rms(tmp_path_factory):
    """Run the full analysis into a temp dir and return the RMS table."""
    out = tmp_path_factory.mktemp("analysis")
    rc = analyze.main([
        "analyze.py", str(TIMESERIES),
        "--out-figures", str(out / "figures"),
        "--calibration-json", str(out / "calibration.json"),
        "--rms-csv", str(out / "rms.csv"),
    ])
    assert rc == 0, "analyze.py exited non-zero"
    return pd.read_csv(out / "rms.csv"), out


def test_timeseries_is_present_and_numeric(df):
    assert len(df) == 27648
    assert list(df.columns) == [
        "escenario", "replica", "t_segundos", "G", "N", "K", "corral"
    ]
    # No stray text anywhere: the published dataset must carry no identifiers.
    for col in df.columns:
        assert pd.api.types.is_numeric_dtype(df[col]), f"{col} is not numeric"


def test_calibration_reproduces(df, committed_calibration):
    r_cal = analyze.calibrate_r(df)
    c_cal = analyze.calibrate_c(df, r_cal=r_cal)
    assert r_cal == pytest.approx(
        committed_calibration["r_cal"], abs=CALIBRATION_TOLERANCE
    )
    assert c_cal == pytest.approx(
        committed_calibration["c_cal"], abs=CALIBRATION_TOLERANCE
    )


def test_critical_stocking_density_matches_documentation(committed_calibration):
    # N_crit = rK/(4c) = 0.1216*K, quoted throughout the README and FINDINGS.
    r = committed_calibration["r_cal"]
    c = committed_calibration["c_cal"]
    assert r / (4 * c) == pytest.approx(0.1216, abs=5e-5)


def test_rms_table_reproduces(regenerated_rms):
    fresh, _ = regenerated_rms
    committed = pd.read_csv(COMMITTED_RMS)
    assert len(fresh) == len(committed) == 12
    for col in ("RMS_orig", "RMS_holling", "N_crit", "mejora_pct"):
        for i in range(len(committed)):
            assert fresh[col][i] == pytest.approx(
                committed[col][i], abs=RMS_TOLERANCE
            ), f"{col} row {i + 1} drifted"


def test_holling_wins_in_every_supercritical_scenario(regenerated_rms):
    """The project's headline claim, asserted rather than asserted-in-prose."""
    fresh, _ = regenerated_rms
    supercritical = fresh[fresh.regimen == "supercritico"]
    assert len(supercritical) == 3
    assert (supercritical.mejora_pct > 80).all(), (
        "Holling should improve RMS by >80% in every supercritical scenario"
    )


def test_integration_is_deterministic(df):
    """Guards the bug that motivated moving off odeint.

    The original clamp made the ODE right-hand side discontinuous, and odeint
    aborted mid-integration at a point that varied between runs, so scenario 9
    produced a different RMS depending on the run. See FINDINGS section 9.8.
    """
    label, K, N, corral = analyze.SCENARIOS[9]
    sub = df[df.escenario == 9]
    t = sub.groupby("t_segundos")["G"].mean().reset_index()["t_segundos"].values
    G0 = float(sub.groupby("replica")["G"].first().mean())
    r = 0.005037386512659262
    c = 0.010355305867325599

    runs = [analyze.integrate_logistic_harvest(G0, t, r, K, c, N)
            for _ in range(3)]
    for other in runs[1:]:
        assert (runs[0] == other).all(), "integration is not deterministic"


def test_supercritical_trajectory_stays_physical(df):
    """The old failure produced G ~ 7540 for a corral with K = 225."""
    label, K, N, corral = analyze.SCENARIOS[9]
    sub = df[df.escenario == 9]
    t = sub.groupby("t_segundos")["G"].mean().reset_index()["t_segundos"].values
    sol = analyze.integrate_logistic_harvest(float(K), t, 0.005037386512659262,
                                             K, 0.010355305867325599, N)
    assert sol.min() >= 0.0, "grass went negative"
    assert sol.max() <= K + 1e-6, f"grass exceeded carrying capacity K={K}"


def test_all_figures_are_produced(regenerated_rms):
    _, out = regenerated_rms
    figures = sorted(p.name for p in (out / "figures").glob("*.png"))
    assert len(figures) == 16, figures
    for expected in ("group_a_carrying_capacity.png", "group_b_obstacles.png",
                     "group_c_bifurcation.png", "model_comparison.png"):
        assert expected in figures
