"""Tests for scripts/parse_log.py.

The raw server logs are not distributed — they contain player IP addresses,
usernames and UUIDs. These tests run against synthetic fixtures in
tests/fixtures/ that reproduce the log line formats the parser matches.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import parse_log  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="module")
def scenario_samples():
    return parse_log.parse_file(FIXTURES / "corrida_esc5_rep1.log")


def test_metadata_inferred_from_filename():
    assert parse_log.infer_metadata_from_filename("corrida_esc5_rep1") == (5, 1)
    assert parse_log.infer_metadata_from_filename("calib_c_rep3") == (101, 3)
    assert parse_log.infer_metadata_from_filename("calib_r_rep2") == (102, 2)
    assert parse_log.infer_metadata_from_filename("unrelated") == (0, 0)


def test_corral_derived_from_scenario_not_from_log():
    # Scenarios 1-9 map onto corrals C1-C3 in blocks of three.
    assert [parse_log.corral_from_escenario(e) for e in range(1, 10)] == [
        1, 1, 1, 2, 2, 2, 3, 3, 3
    ]
    # The irregular corrals.
    assert parse_log.corral_from_escenario(10) == 4
    assert parse_log.corral_from_escenario(11) == 5
    # Scenario 12 must resolve to C6 even though the scoreboard reports C5.
    assert parse_log.corral_from_escenario(12) == 6
    # Calibration runs happen in C2.
    assert parse_log.corral_from_escenario(101) == 2
    assert parse_log.corral_from_escenario(102) == 2
    # Off-design files fall back to the logged value.
    assert parse_log.corral_from_escenario(0) is None


def test_parses_expected_sample_count(scenario_samples):
    assert len(scenario_samples) == 6


def test_ticks_are_converted_to_seconds(scenario_samples):
    # t_seg is logged in ticks; 20 ticks make one in-game second.
    assert [s.t_segundos for s in scenario_samples] == [0.0, 5.0, 10.0, 15.0,
                                                        20.0, 25.0]


def test_grass_counts_pair_with_the_following_timestamp(scenario_samples):
    assert [s.G for s in scenario_samples] == [100, 98, 95, 91, 88, 86]


def test_metadata_is_carried_onto_every_sample(scenario_samples):
    assert {s.escenario for s in scenario_samples} == {5}
    assert {s.replica for s in scenario_samples} == {1}
    assert {s.K for s in scenario_samples} == {100}
    assert {s.corral for s in scenario_samples} == {2}


def test_added_form_updates_the_sheep_count(scenario_samples):
    # The fixture sets ovejas to 4, then uses the "Added 6 ... (now 10)" form.
    # Both spellings must be understood, so N is 4 up to that point and 10 after.
    assert [s.N for s in scenario_samples] == [4, 10, 10, 10, 10, 10]


def test_calibrate_r_runs_force_zero_sheep():
    # CALIBRATE R kills the sheep but leaves the scoreboard at its old value;
    # the fixture deliberately reports 7. The parser must override it.
    samples = parse_log.parse_file(FIXTURES / "calib_r_rep1.log")
    assert samples, "fixture produced no samples"
    assert {s.N for s in samples} == {0}
    assert {s.escenario for s in samples} == {parse_log.ESC_CALIB_R}


def test_only_the_last_run_is_parsed(tmp_path):
    # A cumulative log holding two runs must yield only the second.
    log = tmp_path / "corrida_esc1_rep1.log"
    log.write_text(
        "[@: Set [Estado del Lab] for #running to 1]\n"
        "[@: Set [Estado del Lab] for Corral to 1]\n"
        "[@: Set [Estado del Lab] for K to 25]\n"
        "[@: Set [Estado del Lab] for ovejas to 1]\n"
        "[@: Successfully cloned 25 block(s)]\n"
        "[@: Set [Estado del Lab] for t_seg to 0]\n"
        "[@: Successfully cloned 24 block(s)]\n"
        "[@: Set [Estado del Lab] for t_seg to 20]\n"
        "[@: Set [Estado del Lab] for #running to 0]\n"
        "[@: Set [Estado del Lab] for #running to 1]\n"
        "[@: Successfully cloned 25 block(s)]\n"
        "[@: Set [Estado del Lab] for t_seg to 0]\n"
        "[@: Successfully cloned 23 block(s)]\n"
        "[@: Set [Estado del Lab] for t_seg to 40]\n",
        encoding="utf-8",
    )
    samples = parse_log.parse_file(log)
    assert [s.G for s in samples] == [25, 23]
    assert [s.t_segundos for s in samples] == [0.0, 2.0]


def test_collect_files_ignores_subdirectories(tmp_path):
    # logs/extra/ holds off-design runs and must stay out of the dataset.
    (tmp_path / "corrida_esc1_rep1.log").write_text("", encoding="utf-8")
    extra = tmp_path / "extra"
    extra.mkdir()
    (extra / "ad_hoc.log").write_text("", encoding="utf-8")
    found = parse_log.collect_files(tmp_path)
    assert [p.name for p in found] == ["corrida_esc1_rep1.log"]


def test_missing_target_raises():
    with pytest.raises(FileNotFoundError):
        parse_log.collect_files(Path("does-not-exist"))
