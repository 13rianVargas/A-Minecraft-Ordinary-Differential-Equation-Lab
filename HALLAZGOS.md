# HALLAZGOS — Datos y descubrimientos del laboratorio EDO

> Documento de contexto persistente. Recopila todos los resultados, valores numéricos, bugs encontrados y predicciones del proyecto final EDO 2026-I (G2). Se actualiza progresivamente conforme avanzan las corridas.

## 1. Parámetros calibrados del modelo

**EDO**: `dG/dt = r·G·(1 − G/K) − c·N`

| Parámetro | Valor | Unidad | Réplicas |
|---|---|---|---|
| **r_cal** | **0.005037** | 1/s (game-segundo) | 5 (esc=102) |
| **c_cal** | **0.010355** | bloques/(oveja·s) | 5 (esc=101, N=5) |

**Ecuación calibrada final**:

$$\frac{dG}{dt} = 0.005037 \cdot G \cdot \left(1 - \frac{G}{K}\right) - 0.010355 \cdot N$$

### Estadísticas de calibración

**5 réplicas r (esc=102, N=0, G₀=1, K=100, t=1500 s)**:
| Rep | G_final | t(G=50) |
|---|---|---|
| 1 | 78 | 1265 s |
| 2 | 81 | 1055 s |
| 3 | 96 | 835 s |
| 4 | 88 | 750 s |
| 5 | 98 | 715 s |
| **μ ± σ** | 88.2 ± 7.9 | 924 ± 208 s |
| CV | 9% | 22% |

**5 réplicas c (esc=101, N=5, K=100, t=1500 s)**:
| Rep | G_ini | G_fin | ΔG |
|---|---|---|---|
| 1 | 100 | 88 | 12 |
| 2 | 100 | 91 | 9 |
| 3 | 99 | 92 | 7 |
| 4 | 99 | 87 | 12 |
| 5 | 100 | 93 | 7 |
| **μ ± σ** | 99.6 ± 0.5 | 90.2 ± 2.3 | 9.4 ± 2.2 |

**Validación**: G*₊ predicho con c y r = **88.4**. G_fin observado = **90.2 ± 2.3**. Diferencia 1.8 bloques (dentro ±1σ). Modelo coherente.

## 2. N crítico por corral (bifurcación silla-nodo)

`N_crit = r·K / (4·c) = 0.121 · K`

| Corral | Tamaño | K | **N_crit** |
|---|---|---|---|
| C1 | 5×5 | 25 | **3.04** |
| C2 | 10×10 | 100 | **12.16** |
| C3 | 15×15 | 225 | **27.36** |
| C4 | 12×12 agua | 100 | **12.16** |
| C5 | 12×12 hojas | 100 | **12.16** |
| C6 | 12×12 vallas | 100 | **12.16** |

## 3. Equilibrios teóricos y régimen esperado de los 12 escenarios

`G*₊ = (K/2)·(1 + √(1 − 4cN/(rK)))`

| Esc | Corral | K | N | N/N_crit | Δ = 1 − 4cN/(rK) | **G*₊ predicho** | Régimen |
|---|---|---|---|---|---|---|---|
| 1 | C1 | 25 | 1 | 0.33 | 0.672 | **22.7** | Subcrítico fuerte |
| 2 | C1 | 25 | 3 | 0.99 | 0.015 | **14.0** | **Crítico exacto** (bifurcación) |
| 3 | C1 | 25 | 5 | 1.65 | < 0 | colapso a 0 | Supercrítico |
| 4 | C2 | 100 | 5 | 0.41 | 0.589 | **88.4** | Subcrítico |
| 5 | C2 | 100 | 10 | 0.82 | 0.179 | **71.2** | Subcrítico medio |
| 6 | C2 | 100 | 20 | 1.64 | < 0 | colapso a 0 | Supercrítico |
| 7 | C3 | 225 | 10 | 0.37 | 0.635 | **202.2** | Subcrítico fuerte |
| 8 | C3 | 225 | 25 | 0.91 | 0.086 | **145.6** | Cerca crítico |
| 9 | C3 | 225 | 40 | 1.46 | < 0 | colapso a 0 | Supercrítico |
| 10 | C4 | 100 | 10 | 0.82 | 0.179 | **71.2** | Subcrítico medio |
| 11 | C5 | 100 | 10 | 0.82 | 0.179 | **71.2** | Subcrítico medio |
| 12 | C6 | 100 | 10 | 0.82 | 0.179 | **71.2** | Subcrítico medio (esperado, posible desviación por zonas inaccesibles) |

**Hallazgos clave**:
- **Esc 2 (C1 N=3)**: N exactamente en bifurcación (3 vs N_crit=3.04). Caso de prueba teórico ideal.
- **Esc 8 (C3 N=25)**: cerca crítico (0.91·N_crit). Bueno para Grupo C.
- **Esc 10-12 (irregulares)**: TODOS subcríticos. La diferencia entre obstáculos se medirá en (a) tiempo a equilibrio, (b) G*₊ observado vs predicho 71.2, (c) si C6 muestra `K_efectivo < K` por zonas inaccesibles.

## 4. Datos experimentales (se actualizan conforme avanzan las corridas)

### 4.1 Calibración

✅ **5 réplicas de r completas** (ver §1).
✅ **5 réplicas de c completas con N=5** (ver §1).

### 4.2 Escenarios — Resultados por réplica

> Tabla a completar cuando se hagan las corridas. Una fila por réplica de cada escenario.

| Esc | Corral | N | Rep | G_inicial | G_final | t a G*₊ (s) | t a colapso (s) | Notas |
|---|---|---|---|---|---|---|---|---|
| 1 | C1 | 1 | 1 | — | — | — | — | |
| 1 | C1 | 1 | 2 | — | — | — | — | |
| 1 | C1 | 1 | 3 | — | — | — | — | |
| 2 | C1 | 3 | 1 | — | — | — | — | |
| 2 | C1 | 3 | 2 | — | — | — | — | |
| 2 | C1 | 3 | 3 | — | — | — | — | |
| ... | | | | | | | | |

### 4.3 RMS por escenario (datos vs EDO)

> Se llena automáticamente al correr `analizar.py datos.csv`. Tabla resumen.

| Esc | Corral | K | N | G*₊ predicho | G*₊ observado | RMS |
|---|---|---|---|---|---|---|
| ... | | | | | | |

## 5. Infraestructura del sistema

### 5.1 VPS OMIRU
- Hostname: `REDACTED-HOST`
- Usuario SSH: `REDACTED-USER` (alias `omiru`)
- Mundo Minecraft: `~/minecraft-server/data_edo/world-edo/`
- Log activo: `~/minecraft-server/data_edo/logs/latest.log`
- Versión Minecraft: 26.1.2

### 5.2 Tools locales
- Proyecto: `/Users/13rianvargas/Development/2-University/EDO-Project/`
- Venv: `.venv/` (Python 3.14.5 + pandas/numpy/scipy/matplotlib/python-docx)
- Logs descargados: `logs/`
- CSV agregado: `datos.csv`
- Gráficas: `graficas/`
- Skill: `~/.claude/skills/edo-extract/SKILL.md`

### 5.3 Pipeline de extracción
```
VPS OMIRU ~/minecraft-server/data_edo/logs/latest.log
  ↓ ssh + scp (skill edo-extract)
logs/{corrida_esc<N>_rep<R>|calib_c_rep<R>|calib_r_rep<R>}.log
  ↓ parse_log.py
datos.csv (acumulativo)
  ↓ analizar.py
3 figuras agrupadas + rms.csv + cal.json + 12 PNG individuales
```

### 5.4 Tick rate y tope de corrida
- **Calibración** (r y c): `/tick rate 5000` → target `t_seg ≥ 30000`.
- **Escenarios Fase B**: `/tick rate 5000`.
- **TPS efectivos reales**: el servidor **no alcanza 5000 TPS**. Por la carga de command blocks corre a **~450-1000 TPS reales** (medido: corridas de C4 a ~440 TPS, C2 a ~870-1040). Más ovejas = más lag = menos TPS. Subir el tick rate por encima de eso casi no cambia el tiempo real.
- **Tope máximo por corrida: `t_seg = 150 000` ticks.** Presionar DETENER cuando ocurra lo primero: G colapsa a 0, G se estabiliza, o `t_seg` llega a 150 000. A ~700 TPS son ~3.5 min reales como máximo por corrida. Una corrida cortada en el tope sigue siendo útil: `analizar.py` ajusta la EDO a la curva parcial.

## 6. Bugs y gotchas descubiertos

### 6.1 `latest.log` es acumulativo
**Problema**: el log del server NO se rota entre corridas. Contiene historial de TODAS las corridas previas en una sola sesión.

**Fix**: `parse_log.py` busca el último `for #running to 1` (INICIAR) y parsea solo desde ahí (función `_find_last_run_start`).

**Implicación**: cada skill `extrae ...` siempre obtiene SOLO la última corrida, sin importar cuánto historial tenga el log.

### 6.2 Botón CALIBRAR R no resetea `ovejas estado`
**Problema**: `CALIBRAR R` ejecuta `kill @e[type=sheep,tag=lab_sheep]` (mata entidades) pero NO `scoreboard players set ovejas estado 0`. El score queda con el valor de la corrida anterior, confundiendo al parser.

**Fix**: `parse_log.py` detecta si filename es `calib_r_*` y fuerza `N=0` en los samples emitidos (variable `force_N_zero`).

**Implicación**: el sidebar in-game mostrará un valor de ovejas incorrecto durante calibración r, pero el CSV final es correcto.

### 6.3 Botones spawn ovejas emiten `Added` no `Set`
**Problema**: el botón +1 (y +5, +10) ejecuta `scoreboard players add ovejas estado N`, que se loguea como `[@: Added N to [Estado del Lab] for ovejas (now M)]`. La regex original buscaba `Set ... to N` y no capturaba este formato.

**Fix**: regex extendida `for ovejas (?:to (\d+)|\(now (-?\d+)\))` que captura ambas variantes. Aplicada también a `Corral`, `K`, `t_seg`.

### 6.4 Calibración c con N=1 da señal mínima
**Problema**: con N=1 oveja en C2 (K=100), ΔG total en 1500 s ≈ 3-5 bloques. El ODE-fit funciona pero la varianza entre réplicas es alta.

**Fix aplicado**: cambiar protocolo a **N=5** ovejas. ΔG observable ≈ 12 bloques. Equilibrio G*≈88 (claramente por debajo de K=100). Varianza entre réplicas baja (CV ≈ 2.5%).

**Compatibilidad**: el ODE-fit es N-aware (modelo tiene `c·N` explícito). Mezclar réplicas con N=1 y N=5 funciona — `calibrate_c` usa la EDO completa con r_cal previamente calibrado.

### 6.5 LOCAL RESTABLECER necesita ticks activos
**Problema**: `LOCAL RESTABLECER` y `CALIBRAR R` disparan cadenas LOCAL→GLOBAL via redstone (`fill -5 -59 3 -5 -59 3 redstone_block`). Con `/tick freeze` activo, la cadena no propaga y el reset queda incompleto.

**Fix protocolo**: ejecutar `LOCAL RESTABLECER` o `CALIBRAR R` ANTES de `/tick freeze`. Esperar 1-2 s reales a que la cadena complete (sidebar muestra Corral/K/G actualizados), recién entonces freezear para configurar el resto.

### 6.6 Ventana de calibración de c con N=1
**Problema**: la calibración inicial de c usaba `c = −slope/N` con ventana `t ≤ 60 s`. Con N=1, G casi no baja en 60 s, slope ≈ 0, c ≈ 0.

**Fix**: cambiar a fit de la EDO completa cuando `r_cal` ya está disponible:
- Modelo: `dG/dt = r_cal·G·(1−G/K) − c·N`
- `c` único parámetro libre.
- `scipy.optimize.curve_fit` con `odeint` interno.
- Fallback a slope inicial si `r_cal` no está calibrado todavía.

Implementado en `calibrate_c(df, r_cal=...)`.

### 6.7 El scoreboard `Corral` confunde C5 y C6
**Problema**: el command-block del corral 6 escribe mal el scoreboard `Estado del Lab → Corral`: registra `Corral to 5` en vez de `Corral to 6`. El scoreboard `#corral_activo` sí queda en 6, pero `parse_log.py` leía `Corral` → las corridas de C6 quedaban con `corral=5` en `datos.csv` (C5 y C6 indistinguibles).

**Fix**: `parse_log.py` ya no lee el `corral` del log. Lo deduce del **escenario** (`corral_from_escenario`): esc 1-3→C1, 4-6→C2, 7-9→C3, 10→C4, 11→C5, 12→C6, calib→C2. Inmune a este bug y a errores de botón. Para archivos sin escenario (`extra/`, esc 0) usa como fallback el valor del log.

**Pendiente in-game**: corregir el botón de C6 para que escriba `Corral to 6`.

## 7. Decisiones de diseño documentadas

1. **Calibrar solo en C2**: r y c asumidos propiedades del sistema, no del corral. Aplica a todos los escenarios. Asunción explícita en §8 de la guía.
2. **3 réplicas por escenario** (reducido de 5 a 3 por restricción de tiempo de entrega; con n=3 el σ es más ruidoso —CV >15% típico— lo cual se asume como limitación conocida, ver sección Mejoras del artículo).
3. **3 figuras agrupadas** en el docx (no 12 individuales). Densidad informativa mejor para 7-12 págs.
4. **Tick rate 5000 en calibración** (no 10000). Compromise entre velocidad y reacción humana.
5. **Skill `edo-extract` orquesta todo**: SSH/scp/parse/analyze sin que el equipo toque terminales.

## 8. Predicciones a verificar empíricamente

Cuando se ejecuten los escenarios, contrastar contra:

### Esc 1-3 (C1 5×5 K=25, bifurcación apretada)
- Esc 1 N=1: G → 22.7. Equilibrio alto, casi K.
- **Esc 2 N=3: G → 14 (bifurcación)**. Curva debería ser muy lenta cerca del equilibrio.
- Esc 3 N=5: colapso. Tiempo a G=0 estimado: ~500 s.

### Esc 4-6 (C2 10×10 K=100)
- Esc 4 N=5: G → 88. Mismo equilibrio que la calibración (ya verificado).
- Esc 5 N=10: G → 71.
- Esc 6 N=20: colapso. Tiempo estimado: ~500 s.

### Esc 7-9 (C3 15×15 K=225)
- Esc 7 N=10: G → 202.
- **Esc 8 N=25: G → 145** (cerca crítico).
- Esc 9 N=40: colapso. Tiempo estimado: ~600 s.

### Esc 10-12 (irregulares C4/C5/C6, K=100, N=10)
- Todos predicen G → 71.2 (mismo que esc 5).
- **Si C6 (vallas) da G* significativamente menor** que 71 → confirma `K_efectivo < K` por zonas inaccesibles. Hallazgo fuerte.
- **Si C4 (agua) da G* mayor** → ovejas pierden tiempo nadando, consumo efectivo `c·N_efectivo` menor.
- **Si C5 (hojas) ≈ esc 5** → confirma hojas no son obstáculo real.

## 9. Cosas pendientes / TODO

- [x] Tick rate de Fase B definido en 5000 (unificado con la calibración — ver §5.4).
- [ ] Ejecutar 36 corridas de escenarios (3 réplicas × 12 escenarios).
- [ ] Verificar predicciones §8 contra datos.
- [ ] Actualizar §6.5 de GUIA con `N_crit` definitivos.
- [ ] Considerar comparar dinámica de C5 con C2 (esc 5 vs esc 11) para confirmar hipótesis "hojas saltables".

## 10. Referencias rápidas

- Guía operativa: [GUIA-PROYECTO-FINAL.md](GUIA-PROYECTO-FINAL.md)
- Protocolo del lab Minecraft: `OneDrive/.../PLAN-AP.md`
- Anteproyecto: `OneDrive/.../ANTE-PROYECTO.md`
- Plantilla artículo: `templates/PF-G2-...docx`
- Plantilla bitácora video: `templates/BEPF-G2-...docx`
- Scripts: `scripts/parse_log.py`, `scripts/analizar.py`, `scripts/generar_plantilla_pf.py`
- Skill SSH: `~/.claude/skills/edo-extract/SKILL.md`
