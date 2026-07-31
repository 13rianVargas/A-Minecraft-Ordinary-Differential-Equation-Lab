#!/usr/bin/env bash
#
# extract.sh — Pull a Minecraft server log from the lab host, parse it into the
# project time-series CSV, and run the calibration or full analysis.
#
# Usage:
#   scripts/extract.sh calib {c|r} <replica>   Calibration run for c or r
#   scripts/extract.sh run <scenario> <replica> Scenario run (scenario 1..12)
#   scripts/extract.sh check                    Inspect the remote log only
#   scripts/extract.sh status                   Replica counts in the CSV
#   scripts/extract.sh analyze                  Re-parse and run the full analysis
#   scripts/extract.sh help                     Show this help
#
# Configuration is read from the environment, or from a .env file in the repo
# root if one exists. See .env.example for the required variables.
#
# The experimental protocol each run follows is documented in
# docs/FINDINGS.md, section 3.
#
# Exit codes:
#   0  success
#   1  usage or argument error
#   2  cannot reach the remote log
#   3  copying the log failed
#   4  parse_log.py failed
#   5  calibration failed
#   6  full analysis failed
#   7  the requested run produced no samples

set -euo pipefail

# Repo root, derived from this script's own location — no absolute paths.
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

CSV="$PROJECT_ROOT/data/timeseries.csv"
LOGS_DIR="$PROJECT_ROOT/logs"

# ── configuration ──────────────────────────────────────────────────────
if [ -f "$PROJECT_ROOT/.env" ]; then
    # shellcheck disable=SC1091
    set -a && source "$PROJECT_ROOT/.env" && set +a
fi

# ACCESS_MODE selects how the log is reached on the host:
#   direct  — the log path is readable by SSH_USER directly
#   docker  — the server runs in a container; read it via `docker exec`
ACCESS_MODE="${ACCESS_MODE:-direct}"
SSH_HOST="${SSH_HOST:-}"
SSH_USER="${SSH_USER:-}"
SSH_KEY="${SSH_KEY:-}"
MC_CONTAINER="${MC_CONTAINER:-}"
REMOTE_LOG="${REMOTE_LOG:-}"

# ── logging ────────────────────────────────────────────────────────────
if [ -t 1 ]; then
    C_OK="$(printf '\033[1;32m')"
    C_WARN="$(printf '\033[1;33m')"
    C_ERR="$(printf '\033[1;31m')"
    C_INFO="$(printf '\033[1;36m')"
    C_RESET="$(printf '\033[0m')"
else
    C_OK=""; C_WARN=""; C_ERR=""; C_INFO=""; C_RESET=""
fi

log_ok()   { printf "%s[OK]%s %s\n"   "$C_OK"   "$C_RESET" "$*"; }
log_warn() { printf "%s[WARN]%s %s\n" "$C_WARN" "$C_RESET" "$*" >&2; }
log_err()  { printf "%s[ERR]%s %s\n"  "$C_ERR"  "$C_RESET" "$*" >&2; }
log_info() { printf "%s[--]%s %s\n"   "$C_INFO" "$C_RESET" "$*"; }

show_help() {
    sed -n '3,26p' "$0" | sed 's/^# \{0,1\}//'
}

require_config() {
    local missing=()
    [ -n "$SSH_HOST" ]   || missing+=("SSH_HOST")
    [ -n "$REMOTE_LOG" ] || missing+=("REMOTE_LOG")
    if [ "$ACCESS_MODE" = "docker" ] && [ -z "$MC_CONTAINER" ]; then
        missing+=("MC_CONTAINER")
    fi
    if [ ${#missing[@]} -gt 0 ]; then
        log_err "Missing configuration: ${missing[*]}"
        log_err "Copy .env.example to .env and fill it in, or export the variables."
        exit 1
    fi
}

# ── remote access ──────────────────────────────────────────────────────
remote_exec() {
    local ssh_args=(-o BatchMode=yes -o ConnectTimeout=20
                    -o StrictHostKeyChecking=accept-new)
    [ -n "$SSH_KEY" ] && ssh_args+=(-i "$SSH_KEY")
    local target="$SSH_HOST"
    [ -n "$SSH_USER" ] && target="$SSH_USER@$SSH_HOST"
    ssh -C "${ssh_args[@]}" "$target" "$@"
}

# Run a shell snippet against the log, wrapping it for the configured mode.
log_exec() {
    local snippet="$1"
    if [ "$ACCESS_MODE" = "docker" ]; then
        remote_exec "docker exec $MC_CONTAINER sh -c $(printf '%q' "$snippet")"
    else
        remote_exec "$snippet"
    fi
}

# ── sanity check of the remote log ─────────────────────────────────────
check_remote() {
    require_config
    log_info "Inspecting $SSH_HOST:$REMOTE_LOG (mode: $ACCESS_MODE) ..."
    local out
    if ! out=$(log_exec "wc -l $REMOTE_LOG && tail -3 $REMOTE_LOG" 2>&1); then
        log_err "Could not read the remote log:"
        printf '%s\n' "$out"
        log_err "Check network access and that the server is up. Aborting."
        exit 2
    fi
    printf '%s\n' "$out"

    local last_running
    last_running=$(log_exec \
        "grep -E 'for #running to [01]' $REMOTE_LOG | tail -1" 2>/dev/null || true)
    if [[ "$last_running" == *"to 1"* ]]; then
        log_warn "The last #running transition was '-> 1' (START)."
        log_warn "The run is probably still in progress. Stop it in-world first."
    fi
}

# ── copy the remote log under a canonical name ─────────────────────────
copy_log() {
    local target="$1"
    local dest="$LOGS_DIR/$target"
    log_info "Copying remote log -> $dest"
    mkdir -p "$LOGS_DIR"
    if ! log_exec "cat $REMOTE_LOG" > "$dest"; then
        log_err "Copy failed. Aborting."
        rm -f "$dest"
        exit 3
    fi
    log_ok "Copied ($(wc -l <"$dest") lines)."
}

# ── python environment ─────────────────────────────────────────────────
activate_venv() {
    if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
        # shellcheck disable=SC1091
        source "$PROJECT_ROOT/.venv/bin/activate"
    elif [ -f "$PROJECT_ROOT/.venv/Scripts/activate" ]; then
        # shellcheck disable=SC1091
        source "$PROJECT_ROOT/.venv/Scripts/activate"
    else
        log_warn "No .venv found — falling back to the system python."
        log_warn "  python -m venv .venv && source .venv/bin/activate"
        log_warn "  pip install -r requirements.txt"
    fi
}

# ── pipeline stages ────────────────────────────────────────────────────
reparse() {
    log_info "Parsing $LOGS_DIR -> $CSV ..."
    activate_venv
    if ! python "$PROJECT_ROOT/scripts/parse_log.py" "$LOGS_DIR" "$CSV"; then
        log_err "parse_log.py failed."
        exit 4
    fi
}

calibrate() {
    log_info "Calibrating r and c ..."
    activate_venv
    if ! python "$PROJECT_ROOT/scripts/analyze.py" --calibrate "$CSV"; then
        log_err "analyze.py --calibrate failed."
        exit 5
    fi
    local cal="$PROJECT_ROOT/data/calibration.json"
    if [ -f "$cal" ]; then
        log_ok "$cal:"
        cat "$cal"
        echo
    fi
}

analyze_full() {
    log_info "Full analysis (figures + rms.csv) ..."
    activate_venv
    if ! python "$PROJECT_ROOT/scripts/analyze.py" "$CSV"; then
        log_err "analyze.py failed."
        exit 6
    fi
    log_ok "Done. Figures in figures/, data/rms.csv regenerated."
}

status() {
    if [ ! -f "$CSV" ]; then
        log_warn "$CSV does not exist yet."
        return
    fi
    activate_venv
    CSV="$CSV" python - <<'PY'
import os
import pandas as pd
df = pd.read_csv(os.environ["CSV"])
print(f"Total samples: {len(df)}")
print(f"Scenarios present: {sorted(df.escenario.unique().tolist())}")
print()
print("Replicas per scenario:")
print(df.groupby('escenario')['replica'].nunique().to_string())
PY
}

summarize_run() {
    local esc="$1" rep="$2"
    activate_venv
    CSV="$CSV" ESC="$esc" REP="$rep" python - <<'PY'
import os, sys
import pandas as pd
df = pd.read_csv(os.environ["CSV"])
esc, rep = int(os.environ["ESC"]), int(os.environ["REP"])
sub = df[(df.escenario == esc) & (df.replica == rep)]
if sub.empty:
    print(f"[ERR] No samples for scenario {esc} replica {rep}. Check the log.",
          file=sys.stderr)
    raise SystemExit(7)
print(f"scenario {esc} replica {rep}: {len(sub)} samples")
print(f"  G_initial={sub.iloc[0].G}, G_final={sub.iloc[-1].G}, "
      f"dG={sub.iloc[0].G - sub.iloc[-1].G}")
print(f"  N={sub.N.iloc[0]}, K={sub.K.iloc[0]}, corral={sub.corral.iloc[0]}")
print(f"  t_max={sub.t_segundos.max()}s")
PY
}

# ── argument validation ────────────────────────────────────────────────
validate_int() {
    local val="$1" name="$2" lo="$3" hi="$4"
    if ! [[ "$val" =~ ^[0-9]+$ ]]; then
        log_err "$name must be an integer. Got: '$val'."
        exit 1
    fi
    if [ "$val" -lt "$lo" ] || [ "$val" -gt "$hi" ]; then
        log_err "$name out of range [$lo..$hi]. Got: $val."
        exit 1
    fi
}

# ── dispatch ───────────────────────────────────────────────────────────
case "${1:-help}" in
    help|-h|--help)
        show_help
        ;;

    check)
        check_remote
        ;;

    status)
        status
        ;;

    calib)
        [ $# -eq 3 ] || { log_err "usage: $0 calib {c|r} <replica>"; exit 1; }
        kind="$2"
        rep="$3"
        if [ "$kind" != "c" ] && [ "$kind" != "r" ]; then
            log_err "calibration kind must be 'c' or 'r'. Got: '$kind'."
            exit 1
        fi
        validate_int "$rep" "replica" 1 99
        check_remote
        copy_log "calib_${kind}_rep${rep}.log"
        reparse
        calibrate
        log_ok "Done: calib $kind replica $rep."
        ;;

    run)
        [ $# -eq 3 ] || { log_err "usage: $0 run <scenario> <replica>"; exit 1; }
        esc="$2"
        rep="$3"
        validate_int "$esc" "scenario" 1 12
        validate_int "$rep" "replica" 1 99
        check_remote
        copy_log "corrida_esc${esc}_rep${rep}.log"
        reparse
        summarize_run "$esc" "$rep"
        log_ok "Done: scenario $esc replica $rep."
        log_info "When all runs are collected: $0 analyze"
        ;;

    analyze)
        reparse
        calibrate
        analyze_full
        ;;

    *)
        log_err "Unknown command: '$1'"
        show_help
        exit 1
        ;;
esac
