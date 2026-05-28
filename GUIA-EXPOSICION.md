# Guía de exposición — Proyecto Final de Ecuaciones Diferenciales (G2)

> **Documento formal (anexo):** `PF-G2-Bello Ballen, Cristancho Niño, Gordillo Meneses, Vargas Clavijo.pdf`
> **Apoyo visual:** `presentacion.html` (16 diapositivas)
> **Esta guía:** lo que hay que *decir* y *entender* para exponer con seguridad frente a los profesores.

---

## 0. El proyecto en 30 segundos (el "elevator pitch")

> "Construimos un laboratorio dentro de Minecraft para responder una pregunta simple: **¿qué tan rápido las ovejas se comen el césped frente a la velocidad con que el césped vuelve a crecer?** Modelamos esa competencia con una **Ecuación Diferencial Ordinaria**, medimos sus parámetros con experimentos reales, y descubrimos que el modelo clásico funciona en algunos casos pero **falla justo donde predice un colapso** — y entender *por qué* falla es el corazón del proyecto."

---

## 1. CÓMO EXPLICAR LA EDO (lo más importante)

### La idea en una frase
> "Es una balanza entre dos fuerzas opuestas: el césped que **crece solo** y las ovejas que lo **consumen**."

### La ecuación
$$\frac{dG}{dt} \;=\; \underbrace{r\,G\left(1-\frac{G}{K}\right)}_{\text{crece}} \;-\; \underbrace{c\,N}_{\text{se lo comen}}$$

### Término por término (decirlo así, despacio)
- **`dG/dt`** → "qué tan rápido cambia la cantidad de césped *G* a lo largo del tiempo".
- **`r·G·(1 − G/K)`** → **regeneración logística**. El césped se reproduce, pero **se autolimita**:
  - `r` = qué tan rápido se reproduce.
  - `K` = el máximo de césped que cabe en el corral (**capacidad de carga**).
  - El factor `(1 − G/K)` es un **freno**: si el corral está casi vacío el césped crece rápido; cuando está casi lleno (`G ≈ K`), el freno tiende a 0 y casi no crece.
- **`c·N`** → **consumo**. Cada oveja come `c` bloques por segundo, y hay `N` ovejas, así que en total comen `c·N`.

### La analogía que el público entiende al toque (¡úsenla!)
> "Piénsenlo como una **cuenta bancaria**: el banco te da **intereses** (eso es el césped creciendo) pero tú **retiras una cantidad fija cada mes** (eso son las ovejas comiendo). Si retiras poco, el saldo sube y se estabiliza. Si retiras demasiado, el saldo se va a **cero**. La pregunta del proyecto es: *¿cuál es el límite de retiro antes del colapso?*"

### Por qué es una EDO "interesante" (para sonar sólidos)
- Es de **primer orden** (solo aparece la primera derivada) y **autónoma** (el tiempo no aparece explícito, solo a través de *G*).
- A pesar de ser simple, tiene **equilibrios múltiples**, una **bifurcación** y **colapso** — comportamientos no triviales.

---

## 2. ¿TIENE SOLUCIÓN LA EDO?

**Respuesta corta: SÍ, y de tres maneras distintas. Hay que separarlas para no confundirse.**

### (a) ¿Existe solución? — Sí, garantizado
Por el **Teorema de Existencia y Unicidad (Picard–Lindelöf)**: el lado derecho
`f(G) = rG(1 − G/K) − cN` es un **polinomio** (suave y con derivada continua), por lo que para **cualquier** cantidad inicial de césped `G₀` existe **una única** curva solución `G(t)`. *No hay ambigüedad ni soluciones que se crucen.*

### (b) ¿Tiene fórmula cerrada (solución analítica)? — Sí, es separable
La EDO se puede **separar variables** e integrar. La forma de la solución depende del **discriminante** `Δ = 1 − 4cN/(rK)`:

| Caso | Qué pasa | Solución analítica |
|---|---|---|
| `N = 0` | Logística pura | $G(t)=\dfrac{K}{1+A\,e^{-rt}}$ (la clásica curva en S) |
| Subcrítico (`Δ > 0`) | El césped se estabiliza | Logística "generalizada" que tiende a $G^{*}_{+}$ |
| Supercrítico (`Δ < 0`) | Colapso | La integral da un **arcotangente** → el césped llega a **0 en tiempo finito** |

> Frase para el profe: *"La EDO es separable, así que sí tiene solución analítica; en el caso sin ovejas es la logística clásica, y en el caso supercrítico la solución predice un colapso en tiempo finito."*

### (c) ¿Cómo la resolvimos en el proyecto? — Numéricamente (y con razón)
Usamos integración numérica (`odeint` / Runge–Kutta) porque:
1. Necesitábamos **ajustar los parámetros** `r` y `c` a datos reales y ruidosos (el ajuste evalúa el modelo cientos de veces).
2. El **modelo corregido** (con el término `G/(G+h)`) **ya no tiene fórmula elemental**.
3. Permite tratar los 12 escenarios de forma uniforme.

### EL PUNTO CLAVE (lo que impresiona)
> "La EDO **tiene solución matemática perfecta** — existe, es única y se puede escribir. Pero el aporte del proyecto es mostrar que **esa solución no siempre coincide con la realidad**: en el régimen supercrítico la solución predice colapso a cero, y el experimento mostró que **el césped nunca colapsa**. El modelo es correcto matemáticamente; lo que falla es su *supuesto físico*."

---

## 3. EXPLICACIÓN DIAPOSITIVA POR DIAPOSITIVA

> Tiempo objetivo: ~10–12 min. Cada quien puede tomar un bloque de diapositivas.

**Diapo 1 — Portada (menú de Minecraft).**
"Buenas, somos el Grupo 2. Nuestro proyecto es un modelo de crecimiento logístico con extracción, aplicado a la regeneración de césped en Minecraft." Presentarse los que exponen.

**Diapo 2 — La pregunta (gancho).**
Leerla en voz alta y hacer una pausa: *"¿Qué tan rápido se agota el recurso bajo distintos escenarios?"* — "Esa es la pregunta que perseguimos toda la presentación."

**Diapo 3 — Por qué importa.**
"No es solo sobre ovejas: la misma ecuación gobierna el **sobrepastoreo**, la **pesca sostenible**, la **tala de bosques** y el **uso de acuíferos**. Es un modelo de recurso renovable + consumo."

**Diapo 4 — Planteamiento y objetivos.**
"Usamos Minecraft como laboratorio porque da **repetibilidad** y **tiempo acelerado**. Cuatro objetivos: calibrar `r` y `c`, verificar la EDO en 12 escenarios, detectar la bifurcación y comparar obstáculos."

**Diapo 5 — La EDO.**
Aquí va la explicación de la **Sección 1** de esta guía (la balanza / la cuenta bancaria). "La incógnita central es `c`: cuánto come una oveja."

**Diapo 6 — Equilibrios y bifurcación.**
"Buscamos cuándo el césped deja de cambiar (`dG/dt = 0`). Salen dos equilibrios. El discriminante `Δ` decide el destino:
- `Δ > 0` → **subcrítico**, sobrevive.
- `Δ = 0` → **bifurcación silla-nodo** (punto de quiebre).
- `Δ < 0` → **supercrítico**, debería colapsar.
El número de ovejas que cruza ese límite es **N crítico = rK/4c**."
*(Si preguntan qué es bifurcación: "el punto donde dos equilibrios chocan y desaparecen — un cambio cualitativo súbito de comportamiento".)*

**Diapo 7 — El laboratorio.**
"6 corrales (3 regulares de distinto tamaño + 3 con obstáculos). Botones de command blocks (FORMATEAR/INICIAR/DETENER) controlan el experimento; otros bloques **cuentan el césped** automáticamente y mandan los datos por SSH a Python."

**Diapo 8 — Calibración.**
"Medimos `r` sin ovejas (logística pura) y `c` con 5 ovejas. Resultado: **r = 0.005, c = 0.0104**. Primera respuesta a la pregunta: una oveja come ~0.01 bloques por segundo."

**Diapo 9 — Los 12 escenarios.**
"Diseñamos 12 escenarios variando corral y número de ovejas. La teoría predice 3 regímenes y **colapso en los escenarios 3, 6 y 9**."

**Diapo 10 — El giro.**
El momento dramático: "La teoría decía que con 20 ovejas el césped colapsa a cero. **La realidad: nunca colapsó.** Se quedó oscilando en ~60. Y pasó en los tres escenarios supercríticos." Mostrar la gráfica (la línea teórica se desploma, los datos no).

**Diapo 11 — El descubrimiento (autorregulación).**
"¿Por qué? Calculamos el **N efectivo** y en los tres casos es ≈ **N crítico**. Es decir: **cuando metes más ovejas, se estorban entre ellas y no aumentan el consumo real**. El sistema se autorregula justo en la bifurcación."

**Diapo 12 — El obstáculo decide.**
"Comparando los obstáculos a igual condición: las **vallas** bajan más el equilibrio (reducen el área útil), y el **agua** resiste el colapso porque crea **refugios** de césped que las ovejas no alcanzan."

**Diapo 13 — La EDO corregida (resultado central).**
"Arreglamos el modelo: el consumo ya no es constante, **satura cuando hay poco césped por oveja** (respuesta funcional de Holling). Con eso el error (RMS) baja de 24 a 6.6 — **3.6 veces más preciso** — y ajusta los 12 escenarios."

**Diapo 14 — Conclusiones.** (ver Sección 5).

**Diapo 15 — Referencias.** Mencionar Verhulst (logística), Holling (respuesta funcional), Strogatz (sistemas no lineales).

**Diapo 16 — Cierre.** "Gracias por su atención." (Igual que la portada.)

---

## 4. GLOSARIO MATEMÁTICO (para no trabarse)

| Término | Cómo decirlo en simple |
|---|---|
| **EDO** | Ecuación que relaciona una cantidad con su **velocidad de cambio**. |
| **Autónoma** | El tiempo no aparece explícito, solo a través de `G`. |
| **Equilibrio** | Un valor donde el césped **deja de cambiar** (`dG/dt = 0`). |
| **Estable / inestable** | Estable: si te apartas, el sistema **regresa**. Inestable: si te apartas, **te alejas más**. |
| **Capacidad de carga `K`** | El máximo de césped que el corral puede sostener. |
| **Bifurcación silla-nodo** | Punto donde dos equilibrios **chocan y desaparecen** → cambio brusco de comportamiento. |
| **Discriminante `Δ`** | Lo que va dentro de la raíz; decide si hay equilibrios reales o no. |
| **N crítico** | El número de ovejas que separa "sobrevive" de "colapsa": `rK/4c`. |
| **RMS** | "Error promedio" entre el modelo y los datos, en bloques. Bajo = buen ajuste. |
| **Respuesta funcional (Holling II)** | El consumo **se satura**: con poca comida, comer se vuelve lento. |
| **Calibración** | Medir los parámetros (`r`, `c`) con datos reales en vez de inventarlos. |

---

## 5. CONCLUSIONES (lo que NO puede faltar)

1. **Calibramos la EDO con datos reales**: `r = 0.005037 1/s`, `c = 0.010355 bloques/(oveja·s)`. → respondemos la pregunta original.
2. **El modelo clásico funciona en régimen subcrítico**: predice el equilibrio con **error menor a 1 bloque**.
3. **Pero falla en régimen supercrítico**: predice colapso y la realidad muestra **autorregulación** — el consumo efectivo nunca supera el crítico (`N_efectivo ≈ N_crítico`).
4. **El tipo de obstáculo importa**: el agua protege (refugios), las vallas reducen la capacidad efectiva.
5. **Corregimos el modelo** con consumo saturante (ratio-dependiente) → ajusta los 12 escenarios (RMS 24 → 6.6).
6. **Mensaje final**: una EDO simple puede tener solución exacta y aun así **enseñarnos dónde un supuesto se rompe**. Esa brecha entre teoría y experimento es el verdadero hallazgo.

---

## 6. PREGUNTAS PROBABLES DEL PROFESOR + RESPUESTAS

**P: ¿La EDO tiene solución analítica o solo numérica?**
R: Analítica — es separable. En el caso sin ovejas es la logística clásica `K/(1+Ae^{−rt})`; en supercrítico la solución colapsa en tiempo finito. La resolvimos numéricamente para ajustar parámetros y porque el modelo corregido no es elemental.

**P: ¿Por qué Minecraft y no una simulación normal?**
R: Da control total de variables, repetibilidad exacta y tiempo acelerado, y el "consumo" emerge del comportamiento real de las ovejas (no lo programamos a mano), lo que pone a prueba el supuesto del modelo.

**P: ¿Por qué no colapsó si la teoría lo predecía?**
R: Porque el modelo asume que las `N` ovejas siempre consumen a tasa `c·N`, sin importar cuánto césped quede. En la realidad, cuando el césped escasea las ovejas **se estorban y no lo encuentran**, así que el consumo efectivo cae y el sistema se estabiliza en la bifurcación.

**P: ¿Qué es exactamente el RMS?**
R: La raíz del promedio de los errores al cuadrado entre el modelo y los datos. Está en bloques de césped: RMS = 1.5 significa "el modelo se equivoca ~1.5 bloques en promedio".

**P: ¿Cómo midieron `c` si el césped también crece al mismo tiempo?**
R: Con `r` ya conocido, ajustamos la EDO **completa** a la curva real dejando `c` como única incógnita (con `scipy`), en vez de usar solo la pendiente inicial.

**P: ¿Cuál es la diferencia entre agua y vallas?**
R: Las vallas **reducen el área** donde puede crecer/comerse el césped (`K` efectivo menor). El agua **crea refugios**: parcelas inaccesibles donde el césped sobrevive aunque haya muchas ovejas.

**P: Limitaciones / ¿qué mejorarían?**
R: Más réplicas por escenario; un modelo **espacial** explícito (que represente los refugios); y validar el modelo corregido `c·N·G/(G+h)` en los corrales irregulares.

---

### Tip final para exponer
Hablen del **giro** (diapo 10) como una pequeña historia de misterio: *"la teoría predijo una cosa… y la realidad nos sorprendió"*. Eso engancha al público y demuestra que entienden el modelo, no solo que lo aplicaron.
