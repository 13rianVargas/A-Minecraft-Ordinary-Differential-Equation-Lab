#!/usr/bin/env bash
# extraer-lina.sh — Wrapper de extracción para la cuenta `lina`.
#
# Versión propia (NO modifica extraer.sh, que es del administrador).
# Diferencia clave: la cuenta `lina` no puede leer el log por la ruta
# directa del admin (`~/minecraft-server/data_edo/...`, modo 0700).
# En su lugar accede al log DENTRO del contenedor Docker `mc_edo`
# vía `docker exec`, usando la pertenencia de `lina` al grupo `docker`.
#
# Uso:
#   ./extraer-lina.sh calib c <N>          # calibración de c, réplica N (1..99)
#   ./extraer-lina.sh calib r <N>          # calibración de r, réplica N
#   ./extraer-lina.sh corrida <esc> <rep>  # escenario esc (1..12), réplica rep
#   ./extraer-lina.sh check                # solo inspecciona el log remoto (sanity)
#   ./extraer-lina.sh analizar             # re-parse + análisis completo (genera figuras)
#   ./extraer-lina.sh status               # cuántas réplicas hay en datos.csv
#   ./extraer-lina.sh help                 # muestra esta ayuda
#
# Workflow típico por réplica:
#   1. Termina la corrida en Minecraft (presionar DETENER, /tick rate 20).
#   2. ./extraer-lina.sh calib c 2  (o el trigger que corresponda).
#   3. Lee la salida: r_cal, c_cal actualizados.

set -euo pipefail

# ── configuración ──────────────────────────────────────────────────────
# Raíz del repo = carpeta donde vive este script (sin rutas hardcodeadas).
PROJ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SSH_KEY="$HOME/.ssh/REDACTED-KEY"   # clave generada para el VPS
SSH_USER="REDACTED-USER"
SSH_HOST="REDACTED-HOST"               # IP Tailscale de omiru
MC_CONTAINER="mc_edo"                 # contenedor del servidor EDO
REMOTE_LOG="/data/logs/latest.log"    # ruta DENTRO del contenedor

# Colors (solo si stdout es tty)
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
    sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//'
}

# ── helper ssh hacia omiru ─────────────────────────────────────────────
ssh_omiru() {
    ssh -C -i "$SSH_KEY" \
        -o BatchMode=yes \
        -o ConnectTimeout=20 \
        -o StrictHostKeyChecking=accept-new \
        "$SSH_USER@$SSH_HOST" "$@"
}

# ── activar el entorno virtual de Python (Windows o Linux) ─────────────
activate_venv() {
    if [ -f "$PROJ/.venv/Scripts/activate" ]; then
        # shellcheck disable=SC1091
        source "$PROJ/.venv/Scripts/activate"
    elif [ -f "$PROJ/.venv/bin/activate" ]; then
        # shellcheck disable=SC1091
        source "$PROJ/.venv/bin/activate"
    else
        log_warn "No hay .venv en $PROJ — usando el 'python' del sistema."
        log_warn "Si falla por falta de pandas/matplotlib, crea el entorno:"
        log_warn "  python -m venv .venv && source .venv/Scripts/activate && pip install pandas numpy matplotlib scipy"
    fi
}

# ── sanity check del log remoto ────────────────────────────────────────
check_remote() {
    log_info "Inspeccionando $MC_CONTAINER:$REMOTE_LOG en omiru …"
    local out
    if ! out=$(ssh_omiru "docker exec $MC_CONTAINER sh -c 'wc -l $REMOTE_LOG && tail -3 $REMOTE_LOG'" 2>&1); then
        log_err "ssh/docker falló:"
        printf '%s\n' "$out"
        log_err "Verifica VPN/Tailscale y que el contenedor $MC_CONTAINER esté arriba. Aborta."
        exit 2
    fi
    printf '%s\n' "$out"

    # último #running
    local last_running
    last_running=$(ssh_omiru "docker exec $MC_CONTAINER sh -c \"grep -E 'for #running to [01]' $REMOTE_LOG | tail -1\"" 2>/dev/null || true)
    if [[ "$last_running" == *"to 1"* ]]; then
        log_warn "Última transición de #running es '→ 1' (INICIAR). El lab probablemente sigue CORRIENDO."
        log_warn "Si seguro detuviste el lab, ignora. Si no, primero presiona DETENER en el mundo."
    fi
}

# ── copia del log remoto con nombre objetivo ───────────────────────────
copy_log() {
    local target="$1"
    local dest="$PROJ/logs/$target"
    log_info "Copiando log de $MC_CONTAINER → $dest"
    mkdir -p "$PROJ/logs"
    if ! ssh_omiru "docker exec $MC_CONTAINER cat $REMOTE_LOG" > "$dest"; then
        log_err "Copia falló. Aborta."
        rm -f "$dest"
        exit 3
    fi
    log_ok "Copiado ($(wc -l <"$dest") líneas)."
}

# ── parse logs/ → datos.csv ────────────────────────────────────────────
reparse() {
    log_info "Parseando logs/ → datos.csv …"
    cd "$PROJ"
    activate_venv
    if ! python scripts/parse_log.py logs/ datos.csv; then
        log_err "parse_log.py falló."
        exit 4
    fi
}

# ── calibración (solo imprime r_cal, c_cal) ────────────────────────────
calibrar() {
    log_info "Calibrando r y c …"
    cd "$PROJ"
    activate_venv
    if ! python scripts/analizar.py --calibrar datos.csv; then
        log_err "analizar.py --calibrar falló."
        exit 5
    fi
    if [ -f cal.json ]; then
        log_ok "cal.json:"
        cat cal.json
        echo
    fi
}

# ── análisis completo (gráficas + rms.csv) ─────────────────────────────
analizar_full() {
    log_info "Análisis completo (gráficas + rms.csv) …"
    cd "$PROJ"
    activate_venv
    if ! python scripts/analizar.py datos.csv; then
        log_err "analizar.py falló."
        exit 6
    fi
    log_ok "Listo. Gráficas en graficas/ — rms.csv generado."
}

# ── status de datos.csv ────────────────────────────────────────────────
status() {
    cd "$PROJ"
    if [ ! -f datos.csv ]; then
        log_warn "datos.csv no existe todavía."
        return
    fi
    activate_venv
    python - <<'PY'
import pandas as pd
df = pd.read_csv('datos.csv')
print(f"Total samples: {len(df)}")
print(f"Escenarios únicos: {sorted(df.escenario.unique().tolist())}")
print()
print("Réplicas por escenario:")
print(df.groupby('escenario')['replica'].nunique().to_string())
PY
}

# ── validación de argumentos ───────────────────────────────────────────
validate_int() {
    local val="$1"
    local name="$2"
    local lo="$3"
    local hi="$4"
    if ! [[ "$val" =~ ^[0-9]+$ ]]; then
        log_err "$name debe ser un entero. Recibido: '$val'."
        exit 1
    fi
    if [ "$val" -lt "$lo" ] || [ "$val" -gt "$hi" ]; then
        log_err "$name fuera de rango [$lo..$hi]. Recibido: $val."
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
        if [ $# -ne 3 ]; then
            log_err "uso: $0 calib {c|r} <N>"
            exit 1
        fi
        kind="$2"
        rep="$3"
        if [ "$kind" != "c" ] && [ "$kind" != "r" ]; then
            log_err "calib kind debe ser 'c' o 'r'. Recibido: '$kind'."
            exit 1
        fi
        validate_int "$rep" "réplica" 1 99
        target="calib_${kind}_rep${rep}.log"
        check_remote
        copy_log "$target"
        reparse
        calibrar
        log_ok "Hecho: calib $kind rep $rep."
        ;;

    corrida)
        if [ $# -ne 3 ]; then
            log_err "uso: $0 corrida <esc> <rep>"
            exit 1
        fi
        esc="$2"
        rep="$3"
        validate_int "$esc" "escenario" 1 12
        validate_int "$rep" "réplica" 1 99
        target="corrida_esc${esc}_rep${rep}.log"
        check_remote
        copy_log "$target"
        reparse
        # análisis ligero: muestreo de la réplica
        cd "$PROJ"
        activate_venv
        python - <<PY
import pandas as pd
df = pd.read_csv('datos.csv')
sub = df[(df.escenario == ${esc}) & (df.replica == ${rep})]
if sub.empty:
    print("[ERR] No samples for esc=${esc} rep=${rep}. Revisa el log.")
    raise SystemExit(7)
print(f"esc=${esc} rep=${rep}: {len(sub)} samples")
print(f"  G_inicial={sub.iloc[0].G}, G_final={sub.iloc[-1].G}, ΔG={sub.iloc[0].G - sub.iloc[-1].G}")
print(f"  N={sub.N.iloc[0]}, K={sub.K.iloc[0]}, corral={sub.corral.iloc[0]}")
print(f"  t_seg max={sub.t_segundos.max()}s")
PY
        log_ok "Hecho: corrida esc $esc rep $rep."
        log_info "Cuando termines las 36 corridas, corre: $0 analizar"
        ;;

    analizar)
        reparse
        calibrar
        analizar_full
        ;;

    *)
        log_err "Comando desconocido: '$1'"
        show_help
        exit 1
        ;;
esac
