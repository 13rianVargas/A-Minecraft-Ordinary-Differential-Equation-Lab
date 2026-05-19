# GUÍA DEL PROYECTO FINAL — Ecuaciones Diferenciales 2026-I — G2

> Dos PDF al aula virtual, **miércoles 20 de mayo 11:55 p.m.** Lo carga **un solo miembro**.

## 1. Estado actual

- ✅ Infra Minecraft en VPS OMIRU: 6 corrales, command blocks, scoreboards, auto-colapso.
- ✅ Anteproyecto entregado.
- ✅ **Calibración completa**: `r_cal = 0.005037 1/s`, `c_cal = 0.010355 bloques/(oveja·s)` (5 réplicas r + 5 réplicas c con N=5).
- ❌ Falta: 60 corridas de escenarios (12 × 5 réplicas), análisis, redacción de 3 secciones nuevas, video, ensamblar los 2 PDF.

El trabajo se reparte en cuatro roles complementarios: ingeniería de datos y producción audiovisual, redacción de Resultados, redacción de Mejoras, edición y redacción de Conclusiones.

## 2. Los 2 entregables

| Archivo  | Nombre EXACTO                                                                 | Contenido                                    |
| -------- | ----------------------------------------------------------------------------- | -------------------------------------------- |
| **PF**   | `PF-G2-Bello Ballen, Cristancho Niño, Gordillo Meneses, Vargas Clavijo.pdf`   | Artículo 7-12 págs                           |
| **BEPF** | `BEPF-G2-Bello Ballen, Cristancho Niño, Gordillo Meneses, Vargas Clavijo.pdf` | PDF con solo el link al video                |
| Video    | Sube a YouTube no-listado o Drive público                                     | MP4 13-17 min, los 4 aparecen y se presentan |

**Formato del PF**: PDF, Arial 12, doble espacio, justificado, una columna, hoja carta, sin hoja de presentación, citas y referencias en APA.

## 3. Secciones del artículo

Reglas del profesor: **secciones 1-7 vienen del anteproyecto** (con verbos en pretérito). Solo cambian Resultados, Mejoras y Conclusiones.

| #   | Sección                      | Quién                                                        |
| --- | ---------------------------- | ------------------------------------------------------------ |
| 1   | Título y Autores             | (ya en plantilla)                                            |
| 2   | Introducción                 | (ya en plantilla)                                            |
| 3   | Estado del arte              | (ya en plantilla)                                            |
| 4   | Planteamiento                | (ya en plantilla)                                            |
| 5   | Objetivos                    | (ya en plantilla)                                            |
| 6   | Metodología                  | Mariana revisa al integrar                                   |
| 7   | Justificación                | (ya en plantilla)                                            |
| 8   | **Resultados**               | **Lina** (parte A, esc 1-6) + **Julián** (parte B, esc 7-12) |
| 9   | **Mejoras y trabajo futuro** | **Julián**                                                   |
| 10  | **Conclusiones**             | **Mariana**                                                  |
| 11  | Referencias APA              | Mariana verifica                                             |

La plantilla `templates/PF-G2-...docx` ya tiene 1-7 + placeholders en 8-10.

## 4. Roles y responsabilidades

Cada miembro asume un rol con peso comparable. La carga se distribuye entre laboratorio, redacción y producción audiovisual.

| Persona     | Rol                               | Lab                                                                                                      | Artículo                                                                                                                             | Video                                                                                                                  |
| ----------- | --------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| **Brian**   | Ingeniería de datos + audiovisual | Calibración r/c en C2 (6 corridas) · extracción continua con skill `edo-extract` · análisis cuantitativo | Genera los insumos (CSV, gráficas, RMS, ecuación calibrada) para que el equipo redacte sobre datos sólidos                           | Graba pantalla con OBS · edita y monta el video final · explica reloj de medición §4.1 + skill SSH + EDO + bifurcación |
| **Lina**    | Redacción Resultados A            | Corral C5 hojas (3 réplicas) + apoyo en C1/C2/C3 regulares                                               | Sección 8.A — Resultados de los escenarios 1-6 (corrales regulares con K creciente)                                                  | Explica las cadenas FORMATEAR + INICIAR + DETENER + comportamiento de ovejas en C5                                     |
| **Julián**  | Redacción Resultados B + Mejoras  | Corral C4 agua (3 réplicas) + apoyo en C1/C2/C3 regulares                                                | Sección 8.B — Resultados de los escenarios 7-12 (comparación de obstáculos) · Sección 9 — Mejoras y trabajo futuro                   | Explica los botones de spawn de ovejas (+1/+5/+10) + comportamiento en C4                                              |
| **Mariana** | Edición + Conclusiones            | Corral C6 vallas (3 réplicas) + apoyo en C1/C2/C3 regulares                                              | Sección 10 — Conclusiones · integración y revisión final del docx (formato Arial 12, doble espacio, justificado, APA) · export a PDF | Explica RESTABLECER LOCAL→GLOBAL via redstone + auto-colapso + CALIBRAR R + zonas inaccesibles en C6                   |

## 5. Fases

> **Convención de tipografía**: `/comando` = se tipea en el chat del juego. **BOTÓN** = se presiona el botón físico en el mundo. `skill` = se le dice a Claude Code en el chat de la terminal.
>
> **Por qué tick freeze**: con tick rate 10000, cada segundo real son 500 segundos de juego. Si configurás el escenario sin freezear, perdés varios segundos de experimento mientras presionás botones. `tick freeze` pausa el mundo durante el setup; `tick unfreeze` arranca el experimento desde t=0 limpio.

### Fase A — Calibración de r y c (corral C2)

> Una sola vez al cargar el mundo: presionar **FORMATEAR**. Esto resetea scoreboards y aplica gamerules. No volver a presionarlo durante toda la sesión.

> **Tick rate de calibración**: usar `/tick rate 5000` (no 10000). A 5000 TPS, el target de 30 000 game-ticks toma ~6 segundos reales, lo que da tiempo de observar el sidebar y presionar **DETENER**. A 10 000 TPS sería 3 s reales, demasiado rápido para reaccionar.

#### Procedimiento de UNA réplica de c (consumo)

> **Nota**: con N=1 el sistema no colapsa (queda en equilibrio subcrítico). La calibración usa solo la pendiente inicial (`t ≤ 60 game-seconds`). El experimento se corre por **30 000 ticks de juego** (= 1500 game-seconds, ~6 s reales a tick rate 5000) y se detiene manualmente al alcanzar el target.
>
> **Orden crítico**: `LOCAL RESTABLECER` y `CALIBRAR R` disparan cadenas LOCAL→GLOBAL via redstone que necesitan ticks activos. Ejecutarlos **antes** de `/tick freeze`. Después de que la cadena GLOBAL termine (~1-2 s reales), recién entonces freezeás para configurar el resto.

1. **LOCAL RESTABLECER C2** — llena el corral 10×10 con grass, setea K=100, G=100, Corral=2. Espera 1-2 s reales a que la cadena GLOBAL via redstone termine (sidebar muestra Corral=2, G=100, K=100).
2. **+1 oveja** (botón del corral C2) — spawnea 1 oveja congelada (NoAI:1b).
3. `/tick rate 5000` — velocidad de calibración.
4. **INICIAR** — despierta la oveja (NoAI:0b), levanta `#running=1`, resetea t_seg=0.
5. Observar el sidebar. Cuando `t_seg` ≥ **30000**, presionar **DETENER**. A tick rate 5000 esto toma ~6 s reales.
6. `/tick rate 20` — vuelve a normal.
7. Claude Code: `extrae calib c rep<N>` (siendo N = 1..5).

**Repetir el procedimiento 5 veces** (rep1..rep5).

#### Procedimiento de UNA réplica de r (regeneración)

> **Nota**: la saturación G→K depende del valor real de r. Con r típica del rango [0.01, 0.1] 1/s, G alcanza ≥ 98 dentro de 5 000-20 000 ticks de juego. Correr hasta `t_seg ≥ 30 000` garantiza saturación completa con margen.

1. **CALIBRAR R** — limpia ovejas existentes, fills el corral C2 con dirt, coloca un único bloque grass en el centro, setea K=100, G=1. Espera 1-2 s reales a que la cadena termine (sidebar muestra G=1, K=100).
2. `/tick freeze` — pausa el mundo ya con el setup listo.
3. **INICIAR** — levanta `#running=1` (sin ovejas porque CALIBRAR R ya las eliminó).
4. `/tick rate 5000`.
5. `/tick unfreeze`.
6. Observar el sidebar. Cuando `t_seg` ≥ **30 000** (o cuando G se estanque cerca de K, lo que ocurra primero), presionar **DETENER**.
7. `/tick rate 20`.
8. Claude Code: `extrae calib r rep<N>`.

**Repetir 5 veces**.

#### Cierre de calibración (Brian)

```bash
python scripts/analizar.py --calibrar datos.csv
```

Esto imprime `r_cal` y `c_cal` y los escribe en `cal.json`. Compartir los dos valores con el equipo.

### Fase B — Los 12 escenarios

> Cada escenario tiene un `(corral, N)` distinto y se repite **5 veces**. Total: 60 corridas. Tiempo real estimado por corrida con tick rate 10000: ~2-5 min (escenarios supercríticos colapsan rápido; subcríticos requieren esperar a equilibrio estable). En la reunión nocturna se reparten las regulares; las irregulares las hace cada quien según su asignación.

#### Tabla de los 12 escenarios

Calculado con la calibración: `N_crit` = C1: **3.04** · C2/C4/C5/C6: **12.16** · C3: **27.36** ovejas. `G*₊` es el equilibrio teórico predicho por la EDO.

| Esc | Corral          | K   | N   | N/N_crit | G\*₊ predicho | Régimen                                                        | Quién          |
| --- | --------------- | --- | --- | -------- | ------------- | -------------------------------------------------------------- | -------------- |
| 1   | C1 5×5          | 25  | 1   | 0.33     | 22.7          | Subcrítico fuerte                                              | los 4 reparten |
| 2   | C1 5×5          | 25  | 3   | **0.99** | 14.0          | **Crítico (bifurcación)**                                      | los 4 reparten |
| 3   | C1 5×5          | 25  | 5   | 1.65     | colapso       | Supercrítico                                                   | los 4 reparten |
| 4   | C2 10×10        | 100 | 5   | 0.41     | 88.4          | Subcrítico                                                     | los 4 reparten |
| 5   | C2 10×10        | 100 | 10  | 0.82     | 71.2          | Subcrítico medio                                               | los 4 reparten |
| 6   | C2 10×10        | 100 | 20  | 1.64     | colapso       | Supercrítico                                                   | los 4 reparten |
| 7   | C3 15×15        | 225 | 10  | 0.37     | 202.2         | Subcrítico fuerte                                              | los 4 reparten |
| 8   | C3 15×15        | 225 | 25  | **0.91** | 145.6         | Cerca crítico                                                  | los 4 reparten |
| 9   | C3 15×15        | 225 | 40  | 1.46     | colapso       | Supercrítico                                                   | los 4 reparten |
| 10  | C4 12×12 agua   | 100 | 10  | 0.82     | 71.2          | Subcrítico medio                                               | Julián         |
| 11  | C5 12×12 hojas  | 100 | 10  | 0.82     | 71.2          | Subcrítico medio                                               | Lina           |
| 12  | C6 12×12 vallas | 100 | 10  | 0.82     | 71.2\*        | Subcrítico medio (\*posible desviación por zonas inaccesibles) | Mariana        |

#### Procedimiento de UNA réplica de un escenario

1. **LOCAL RESTABLECER C\<corral\>** — el botón del corral del escenario (ej. LOCAL RESTABLECER C3 para los esc 7-9). Espera 1-2 s reales a que la cadena GLOBAL via redstone termine (sidebar muestra Corral, K, G actualizados).
2. Combinación de **+1**, **+5**, **+10** del mismo corral hasta llegar al N del escenario. Ejemplo: N=25 en C3 → presionar **+10** dos veces y **+5** una vez (10+10+5=25).
3. `/tick rate 10000`.
4. **INICIAR**.
5. Esperar al evento de cierre:
   - **Si el escenario es supercrítico** (cN > rK/4): el sistema auto-colapsa cuando G=0. No tocar nada.
   - **Si el escenario es subcrítico** (cN < rK/4): el sistema llega a equilibrio. Esperar ~600-1200 game-ticks de juego en estabilidad (sidebar muestra G casi constante) y presionar **DETENER**.
6. `/tick rate 20`.
7. Claude Code: `extrae corrida esc<N> rep<R>` (ej. `extrae corrida esc7 rep2`).

**Repetir 5 veces** por escenario (rep1..rep5).

### Fase C — Análisis (Brian)

Una vez todas las 70 corridas estén en `datos.csv` (la skill lo va actualizando), correr:

```bash
python scripts/analizar.py datos.csv
```

Esto produce:

- **3 figuras agrupadas** (las que van al docx):
  - `graficas/grupo_A_K_creciente.png` — efecto K creciente (Lina la usa en Resultados A).
  - `graficas/grupo_B_obstaculos.png` — comparación C2/C4/C5/C6 con K=100 y N=10 (Julián la usa en Resultados B).
  - `graficas/grupo_C_bifurcacion.png` — subcrítico / crítico / supercrítico.
- `rms.csv` — tabla con RMS, G\*₊, N_crit y régimen por escenario.
- `cal.json` — valores numéricos de `r_cal` y `c_cal`.
- 12 PNG individuales en `graficas/esc_*.png` (verificación interna, no van al docx).

Brian comparte con el equipo: CSV, las 3 figuras agrupadas, `rms.csv` y `cal.json`.

### Fase D — Redacción y armado del docx

1. Lina y Julián abren `templates/PF-G2-...docx` y escriben encima de los placeholders en cursiva (Resultados parte A, Resultados parte B, Mejoras).
2. Mariana escribe Conclusiones, integra los tres textos, inserta las 3 figuras agrupadas + tabla RMS resumida, verifica formato (Arial 12, doble espacio, justificado, 7-12 págs, citas APA in-line, sin hoja de presentación).
3. Lectura cruzada de los tres (Lina, Julián y Mariana revisan los textos de los demás).
4. Mariana exporta a PDF con el nombre exacto.

### Fase E — Video

1. Reunión Discord/Zoom con los 4 en cámara activa.
2. Brian configura OBS: escena con Minecraft fullscreen + grilla pequeña de 4 webcams en la esquina.
3. Presentación inicial de 60 s con las 4 cámaras en grande: cada uno dice nombre, código y rol.
4. Brian narra el screencast y llama por nombre a cada uno cuando toca su parte (ver §7).
5. Brian recorta en edición a 13-17 min, exporta MP4, sube a YouTube no-listado o Drive público.

### Fase F — Entrega

1. Mariana abre `templates/BEPF-G2-...docx`, reemplaza `[REEMPLAZAR_CON_URL_DEL_VIDEO]` con el link del video, exporta a PDF.
2. Verificación carácter por carácter de los dos nombres (acentos, comas, guiones).
3. Confirmación de que ambos archivos son PDF.
4. Un solo miembro del grupo carga los dos PDF al aula virtual.

## 6. La matemática del proyecto

### 6.1 Calibrar c (consumo)

Con `G = K` al inicio el término logístico se anula, entonces `dG/dt|₀ ≈ −cN`. De ahí:

$$c = -\frac{1}{N}\,\frac{dG}{dt}\bigg|_{t\to 0}$$

`analizar.py` ajusta una recta a los datos con `t ≤ 60 s` (N=1, C2) y calcula `c = −slope/N`. Promedio de 3 réplicas → `c_cal` (unidad: bloques/(oveja·s)).

### 6.2 Calibrar r (regeneración)

Con N=0 la EDO se vuelve logística pura, solución analítica:

$$G(t) = \frac{K}{1 + A\,e^{-rt}}, \quad A = \frac{K - G_0}{G_0}$$

`analizar.py` ajusta con `scipy.optimize.curve_fit` (`p0=[0.01]`, `bounds=(0, ∞)`). Promedio de 3 réplicas → `r_cal` (unidad: 1/s).

### 6.3 Ecuación calibrada (la respuesta del proyecto)

$$\boxed{\dfrac{dG}{dt} = r_{cal}\,G\left(1 - \dfrac{G}{K}\right) - c_{cal}\,N}$$

Esta es la respuesta cuantitativa a _"qué tan rápido consumen césped las ovejas"_. Para cada escenario se integra con `odeint` y se compara contra los datos.

### 6.4 Punto silla y N crítico

Los equilibrios cumplen `dG/dt = 0`:

$$G^*_{\pm} = \frac{K}{2}\left(1 \pm \sqrt{1 - \frac{4cN}{rK}}\right)$$

El discriminante `Δ = 1 − 4cN/(rK)` decide el régimen:

| Δ     | Régimen      | Comportamiento                      |
| ----- | ------------ | ----------------------------------- |
| Δ > 0 | Subcrítico   | Equilibrio estable en G\*₊          |
| Δ = 0 | **Crítico**  | Bifurcación silla-nodo en G\* = K/2 |
| Δ < 0 | Supercrítico | Colapso garantizado                 |

Despejando, la cantidad crítica de ovejas:

$$\boxed{N_{crit} = \dfrac{r_{cal}\,K}{4\,c_{cal}}}$$

`analizar.py` la calcula automáticamente y la agrega a `rms.csv` (columna `N_crit` + `regimen`).

### 6.5 N crítico calibrado y selección de N por corral

Con `r_cal = 0.005037 1/s` y `c_cal = 0.010355 bloques/(oveja·s)`, el N crítico se calcula como `N_crit = r·K/(4·c) = 0.1216·K`:

| Corral             | K   | **N_crit** | N planeado (subcrítico, mid, supercrítico) | Comentario                                                                           |
| ------------------ | --- | ---------- | ------------------------------------------ | ------------------------------------------------------------------------------------ |
| C1 5×5             | 25  | **3.04**   | 1, 3, 5                                    | Esc 2 (N=3) cae EXACTO en bifurcación — caso teórico perfecto.                       |
| C2 10×10           | 100 | **12.16**  | 5, 10, 20                                  | Esc 6 (N=20) supercrítico fuerte. Calibración hecha aquí.                            |
| C3 15×15           | 225 | **27.36**  | 10, 25, 40                                 | Esc 8 (N=25) cerca crítico (0.91·N_crit) — la "estrella" del Grupo C.                |
| C4 / C5 / C6 12×12 | 100 | **12.16**  | 10                                         | Los 3 irregulares: subcrítico medio. La diferencia entre obstáculos se mide en G\*₊. |

**Por qué importan estos valores**:

1. **N < N_crit → subcrítico**: el sistema estabiliza en `G*₊` predecible. La curva G(t) descende y se asienta.
2. **N ≈ N_crit → bifurcación silla-nodo**: estabilización muy lenta cerca de `G* = K/2`. Visualmente impactante.
3. **N > N_crit → supercrítico**: colapso a G=0 en tiempo finito (auto-colapso lo detecta).

**Advertencia operativa**: una corrida con `N/K > 1` (ej. 250 ovejas en C3) produce colapso instantáneo y curva sin información ajustable. No subir N arbitrariamente.

**Validación cruzada**: la calibración c en C2 con N=5 predijo `G*₊ = 88.4`; el experimento dio `G_final = 90.2 ± 2.3` (5 réplicas). Modelo confirmado dentro de ±1σ.

## 7. Ideas para el video (no es guion)

### Cadenas de command blocks (1-2 min cada uno)

- **Lina**: FORMATEAR + INICIAR + DETENER.
- **Julián**: botones spawn ovejas (+1/+5/+10).
- **Mariana**: RESTABLECER LOCAL→GLOBAL via redstone + auto-colapso + CALIBRAR R.
- **Brian**: reloj §4.1 (`store result run clone … filtered grass_block`) + skill SSH + EDO + bifurcación.

### Cada uno habla de su corral irregular

- **Julián — C4 agua**: ovejas nadan o se estancan. Grass NO crece sobre agua → 44 bloques fuera de K. ¿Modelo simple predice esto?
- **Lina — C5 hojas**: hojas son escalables, ovejas pasan sin obstáculo real. Hipótesis: comportamiento ≈ C2.
- **Mariana — C6 vallas**: NO saltables, ovejas rodean. Posibles zonas físicamente inaccesibles → `K_efectivo_consumo < K_geométrico` → modelo asimétrico (hallazgo fuerte).
- **Brian**: por qué calibrar solo en C2; `curve_fit` y `odeint`; pipeline SSH→VPS→Python (**Ingeniería de Sistemas**); mostrar bifurcación en esc 8.

### Presentación inicial (60 s)

Los 4 en cámara grande: nombre, código, rol.

## 8. Pipeline

```
VPS OMIRU
  └─ ~/minecraft-server/data_edo/logs/latest.log
       ↓ skill edo-extract (ssh + scp)
Mac: logs/{corrida_esc<N>_rep<R>|calib_c_rep<R>|calib_r_rep<R>}.log
       ↓ parse_log.py
datos.csv
       ↓ analizar.py
3 figuras agrupadas + rms.csv + cal.json
```

El equipo no toca terminales. Solo Brian.

Triggers de la skill: `extrae calib c rep1`, `extrae calib r rep2`, `extrae corrida esc5 rep2`, `regenera gráficas`.

Fallback manual:

```bash
cd /Users/13rianvargas/Development/2-University/EDO-Project
source .venv/bin/activate
scp omiru:~/minecraft-server/data_edo/logs/latest.log logs/corrida_esc<N>_rep<R>.log
python scripts/parse_log.py logs/ datos.csv
python scripts/analizar.py datos.csv
```

## 9. Asunciones del modelo (para sección Mejoras)

1. r y c calibrados solo en C2, asumidos constantes en los 12 escenarios. Puede fallar en C4/C6 por restricciones de movimiento.
2. Modelo continuo aproxima random ticks discretos (válido con G y N grandes).
3. Ovejas inicialmente uniformes (`spreadplayers`), luego se mueven libres.
4. En C6, `K_efectivo_consumo < K_geométrico` por zonas inaccesibles.
5. Calibración válida solo para Minecraft 26.1.2.

## 10. Riesgos

| Riesgo                          | Mitigación                                               |
| ------------------------------- | -------------------------------------------------------- |
| VPS lento o log incompleto      | Skill verifica tamaño/tail antes de scp; aborta y avisa. |
| `curve_fit` diverge             | `p0=[0.01]`, `bounds=(0,∞)`. Repetir réplica si falla.   |
| Compañero no entrega su sección | Mariana puede asumir parte. Brian no redacta.            |
| Docx > 12 págs                  | Mariana reduce tamaño de figuras + comprime tabla RMS.   |

## 11. Pre-submission checklist

- [ ] Nombre exacto `PF-G2-...pdf` y `BEPF-G2-...pdf` (acentos, comas, guiones).
- [ ] Ambos PDF (no docx).
- [ ] PF: 7-12 págs, Arial 12, doble espacio, justificado, una columna, sin hoja de presentación.
- [ ] PF: citas APA in-line + referencias APA al final.
- [ ] BEPF: solo el link.
- [ ] Video: 13-17 min, los 4 en cámara al inicio, link público (probar en incógnito).
- [ ] Un solo miembro sube.

## 12. Comandos rápidos

```bash
ssh omiru                                                # conectar al server

# Skill (en Claude Code chat)
extrae calib c rep1 | extrae calib r rep1
extrae corrida esc5 rep2
regenera gráficas

# Manual
cd /Users/13rianvargas/Development/2-University/EDO-Project && source .venv/bin/activate
python scripts/parse_log.py logs/ datos.csv
python scripts/analizar.py --calibrar datos.csv          # solo calibración
python scripts/analizar.py datos.csv                     # análisis completo
```

In-game (chat):

- `/tick rate 10000` — acelera 500×. `/tick rate 20` — vuelve a normal.
- `/scoreboard objectives list` — debe mostrar solo `contador` y `estado`.

## 13. Archivos clave

- `ANTE-PROYECTO.md` (OneDrive) — fuente de secciones 1-7.
- `PLAN-AP.md` (OneDrive) — protocolo completo del lab (calibración, escenarios, troubleshooting CB).
- `templates/PF-G2-...docx` — plantilla del artículo.
- `templates/BEPF-G2-...docx` — plantilla del PDF del video.
- `scripts/parse_log.py`, `scripts/analizar.py` — pipeline de datos.
- `~/.claude/skills/edo-extract/SKILL.md` — skill de extracción.
