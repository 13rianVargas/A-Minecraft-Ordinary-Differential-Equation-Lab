#!/usr/bin/env python3
"""
parse_log.py — Extract (t_seg, G) trajectories from Minecraft server logs.

The lab tellraw chain (PLAN-AP §4.1) emits two key log lines per cycle:
  - "Successfully cloned <N> block(s)"            -> G (count of grass_block in active corral)
  - "Set [Estado del Lab] for t_seg to <N>"       -> t_seg (game ticks elapsed)

Experiment metadata (set once at LOCAL RESTABLECER):
  - "Set [Estado del Lab] for Corral to <N>"
  - "Set [Estado del Lab] for K to <N>"
  - "Set [Estado del Lab] for ovejas to <N>"

Pairing strategy: each t_seg update is the canonical timestamp; the most-recent
"Successfully cloned" line before it is the matching G value.

Usage:
  python parse_log.py <log_file_or_dir> <output_csv>
  python parse_log.py logs/corrida_esc5_rep2.log data/timeseries.csv  # one file
  python parse_log.py logs/ data/timeseries.csv                       # all logs
"""

from __future__ import annotations

import csv
import gzip
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

RE_CLONED = re.compile(r"Successfully cloned (\d+) block\(s\)")
RE_T_SEG = re.compile(
    r"for t_seg (?:to (\d+)|\(now (-?\d+)\))"
)
RE_CORRAL = re.compile(
    r"for Corral (?:to (\d+)|\(now (-?\d+)\))"
)
RE_K = re.compile(
    r"for K (?:to (\d+)|\(now (-?\d+)\))"
)
RE_OVEJAS = re.compile(
    r"for ovejas (?:to (\d+)|\(now (-?\d+)\))"
)
RE_RUNNING_ON = re.compile(r"for #running to 1")

FILENAME_RE = re.compile(r"esc(\d+)[_-]?rep(\d+)", re.IGNORECASE)
CALIB_RE = re.compile(r"calib[_-]?([cr])[_-]?rep(\d+)", re.IGNORECASE)
ESC_CALIB_C = 101
ESC_CALIB_R = 102


def corral_from_escenario(esc: int) -> int | None:
    """Corral fixed by experimental design, derived from the scenario number.

    The `Corral` scoreboard in the log is NOT trustworthy: a defect in the
    in-world command-block chain records corral 6 as `Corral to 5`, conflating
    C5 and C6. Since every scenario uses a fixed corral by design, deriving it
    here makes the parser immune to both that defect and to an operator
    pressing the wrong button.

    Returns None when the scenario is not part of the design (for example the
    scenario 0 produced by ad-hoc files under `extra/`), in which case the
    value observed in the log is used as a fallback.
    """
    if 1 <= esc <= 9:
        return (esc - 1) // 3 + 1        # 1-3 -> C1, 4-6 -> C2, 7-9 -> C3
    if esc in (10, 11, 12):
        return esc - 6                   # 10 -> C4, 11 -> C5, 12 -> C6
    if esc in (ESC_CALIB_C, ESC_CALIB_R):
        return 2                         # calibration runs use corral C2
    return None


@dataclass
class Sample:
    escenario: int
    replica: int
    t_segundos: float
    G: int
    N: int
    K: int
    corral: int


@dataclass
class RunState:
    escenario: int
    replica: int
    corral: int | None = None
    K: int | None = None
    N: int | None = None
    last_G: int | None = None
    samples: list[Sample] = field(default_factory=list)


def open_log(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def infer_metadata_from_filename(name: str) -> tuple[int, int]:
    """Parse `corrida_esc5_rep2.log`, `calib_c_rep1.log`, `calib_r_rep1.log`."""
    m = CALIB_RE.search(name)
    if m:
        kind = m.group(1).lower()
        rep = int(m.group(2))
        return (ESC_CALIB_C if kind == "c" else ESC_CALIB_R, rep)
    m = FILENAME_RE.search(name)
    if not m:
        return (0, 0)
    return (int(m.group(1)), int(m.group(2)))


def _first_group(m) -> int:
    """Return the first non-None capture group as int."""
    for g in m.groups():
        if g is not None:
            return int(g)
    return 0


def _find_last_run_start(path: Path) -> int:
    """Return the line index where the LAST INICIAR ('#running to 1') occurs.
    If none, returns 0 (parse the entire file)."""
    last = 0
    with open_log(path) as f:
        for i, line in enumerate(f):
            if RE_RUNNING_ON.search(line):
                last = i
    return last


def parse_file(path: Path, only_last_run: bool = True) -> list[Sample]:
    """Parse a Minecraft log into Samples.

    With only_last_run=True (default), discards everything before the last
    INICIAR ('for #running to 1'), so accumulated history doesn't pollute the
    current replica's data.

    Metadata (Corral, K, N) is collected by scanning the WHOLE file (set or
    add patterns) and keeping the most recent value at the moment each t_seg
    sample is emitted.
    """
    esc, rep = infer_metadata_from_filename(path.stem)
    state = RunState(escenario=esc, replica=rep)
    design_corral = corral_from_escenario(esc)

    start_line = _find_last_run_start(path) if only_last_run else 0

    # CALIBRAR R kills sheep entities but does NOT zero `ovejas estado`.
    # When the filename says calib_r, force N=0 regardless of leftover state.
    force_N_zero = state.escenario == ESC_CALIB_R

    with open_log(path) as f:
        for i, line in enumerate(f):
            # Always track metadata so we know N/K/Corral when entering the run.
            m = RE_CORRAL.search(line)
            if m:
                state.corral = _first_group(m)
            m = RE_K.search(line)
            if m:
                state.K = _first_group(m)
            m = RE_OVEJAS.search(line)
            if m:
                state.N = _first_group(m)

            if i < start_line:
                continue

            m = RE_CLONED.search(line)
            if m:
                state.last_G = int(m.group(1))
                continue
            m = RE_T_SEG.search(line)
            if m and state.last_G is not None and state.K and state.N is not None:
                t_ticks = _first_group(m)
                t_segundos = t_ticks / 20.0
                state.samples.append(
                    Sample(
                        escenario=state.escenario,
                        replica=state.replica,
                        t_segundos=t_segundos,
                        G=state.last_G,
                        N=0 if force_N_zero else state.N,
                        K=state.K,
                        corral=(design_corral if design_corral is not None
                                else state.corral or 0),
                    )
                )

    return state.samples


def collect_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        files = sorted(
            list(target.glob("*.log")) + list(target.glob("*.log.gz"))
        )
        return files
    raise FileNotFoundError(f"No such file or directory: {target}")


def write_csv(samples: list[Sample], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["escenario", "replica", "t_segundos", "G", "N", "K", "corral"])
        for s in samples:
            w.writerow([s.escenario, s.replica, s.t_segundos, s.G, s.N, s.K, s.corral])


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    target = Path(argv[1])
    out = Path(argv[2])

    files = collect_files(target)
    all_samples: list[Sample] = []
    for fp in files:
        samples = parse_file(fp)
        print(
            f"[{fp.name}] esc={samples[0].escenario if samples else '?'} "
            f"rep={samples[0].replica if samples else '?'} samples={len(samples)}",
            file=sys.stderr,
        )
        all_samples.extend(samples)

    if not all_samples:
        print("No samples parsed.", file=sys.stderr)
        return 1

    write_csv(all_samples, out)
    print(f"Wrote {len(all_samples)} samples -> {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
