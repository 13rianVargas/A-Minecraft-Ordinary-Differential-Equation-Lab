#!/usr/bin/env python3
"""
generar_plantilla_pf.py — Build PF-G2-...docx and BEPF-G2-...docx with the
exact format required by the assignment (Arial 12, doble espacio, justificado,
una sola columna, sin hoja de presentación).

Sections 1-7 come from ANTE-PROYECTO.md (with verbs in past tense where
appropriate, per the instructions: "Desde Título hasta Justificación, estas
secciones son en principio las mismas que en el anteproyecto, salvo por algunos
cambios menores que se deban realizar para complementar lo hecho en el
anteproyecto.").

Sections 8-10 (Resultados, Mejoras, Conclusiones) are placeholders the team
will fill in.

Section 11 (Referencias APA) reproduces the 6 references from the anteproyecto.

Output:
  templates/PF-G2-Bello Ballen, Cristancho Niño, Gordillo Meneses, Vargas Clavijo.docx
  templates/BEPF-G2-Bello Ballen, Cristancho Niño, Gordillo Meneses, Vargas Clavijo.docx
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

TITLE = (
    "MODELO DE CRECIMIENTO LOGÍSTICO CON EXTRACCIÓN APLICADO A LA "
    "DINÁMICA DE REGENERACIÓN DE CÉSPED EN MINECRAFT"
)

AUTHORS = (
    "Bello Ballen Lina Andrea, Cristancho Niño Julián David, "
    "Gordillo Meneses Mariana Alejandra, Vargas Clavijo Brian Steven"
)

INTRO = (
    "El presente proyecto aplica el modelo matemático de crecimiento logístico "
    "con extracción para analizar la dinámica de regeneración de bloques de "
    "césped frente al consumo de ovejas en el videojuego Minecraft. Este "
    "entorno virtual opera bajo reglas algorítmicas fijas: el motor procesa 20 "
    "ticks por segundo (Minecraft Wiki, s.f.), y cada oveja tiene una "
    "probabilidad constante de consumir bloques de césped y transformarlos en "
    "tierra (Sportskeeda, 2024). A su vez, el césped puede regenerarse mediante "
    "propagación hacia bloques de tierra cercanos dentro de un rango limitado, "
    "siempre que exista un nivel mínimo de luz (Minecraft Wiki, 2024)."
)

GLOSSARY_PREFIX = "Notación: "
GLOSSARY_TEXT = (
    "G(t) = bloques de césped en el corral; r = tasa de regeneración (1/s); "
    "K = capacidad máxima del corral (bloques); c = tasa de consumo por oveja "
    "(bloques/oveja·s); N = número de ovejas; G*₊ = equilibrio estable "
    "(bloques); N_crit = ovejas en el punto de bifurcación silla-nodo."
)

# Estado del arte ahora se construye con bloques: cada bloque es un párrafo
# de texto o una ecuación. Esto permite intercalar las ecuaciones (1) y (2)
# centradas y numeradas, como pidió el docente.
ESTADO_BLOCKS = [
    ("text",
     "En el presente proyecto se modeló, mediante EDOs, la rapidez con la "
     "que las ovejas consumen el césped dentro de un corral en Minecraft, "
     "considerando la regeneración del césped y el consumo proporcional al "
     "número de ovejas. Para sustentar matemáticamente el modelo, se "
     "seleccionaron los artículos Harvesting Policies with Stepwise Effort "
     "and Logistic Growth in a Random Environment (Brites & Braumann, 2020) "
     "y Trimming to Coexistence (Braverman & Lawson, 2025), ya que ambos "
     "utilizan modelos de dinámica de poblaciones descritos mediante EDOs "
     "que pueden adaptarse al problema planteado."),
    ("text",
     "El artículo Harvesting Policies with Stepwise Effort and Logistic "
     "Growth in a Random Environment (Brites & Braumann, 2020) presenta un "
     "modelo basado en la ecuación logística con extracción, utilizada para "
     "describir poblaciones que crecen con límite y al mismo tiempo son "
     "reducidas por un proceso de consumo. La ecuación general es:"),
    ("eq", "dX/dt = rX(1 − X/K) − H(t)", 1),
    ("text",
     "donde X(t) representa la población, r la tasa de crecimiento, K la "
     "capacidad máxima del entorno y H(t) la tasa de extracción. Este modelo "
     "se relaciona directamente con el proyecto, ya que el césped puede "
     "interpretarse como un recurso que se regenera con límite, mientras que "
     "las ovejas representan el proceso de consumo. En Minecraft, la "
     "regeneración del césped depende de bloques cercanos y el consumo "
     "depende del número de ovejas, por lo que el término de extracción "
     "puede considerarse proporcional a la cantidad de ovejas dentro del "
     "corral."),
    ("text",
     "Por otra parte, el artículo Trimming to Coexistence (Braverman & "
     "Lawson, 2025) estudia sistemas dinámicos donde dos poblaciones "
     "interactúan y pueden coexistir bajo ciertas condiciones. Estos modelos "
     "también se describen mediante EDOs y permiten analizar estabilidad y "
     "equilibrio en sistemas recurso-consumidor. Este enfoque es útil para "
     "el proyecto porque permite determinar si la regeneración del césped "
     "es suficiente para sostener a las ovejas o si el sistema termina sin "
     "recurso."),
    ("text",
     "Aplicando estas ideas al problema, se definió G(t) como la cantidad "
     "de césped disponible y N como el número de ovejas, obteniendo el "
     "modelo:"),
    ("eq", "dG/dt = rG(1 − G/K) − cN", 2),
    ("text",
     "donde r es la tasa de regeneración, K el máximo de bloques con "
     "césped y c la tasa de consumo por oveja. Esta ecuación diferencial "
     "permite analizar distintos escenarios variando el número de ovejas, "
     "el tamaño del corral y el tipo de obstáculo presente, y estudiar "
     "cuándo el sistema alcanza equilibrio o cuándo el césped se agota. "
     "En conclusión, ambos artículos resultaron adecuados, pero el modelo "
     "logístico con extracción fue el más apropiado para describir el "
     "comportamiento esperado en el sistema de Minecraft. El modelo (2) "
     "será objeto de calibración experimental y análisis sistemático en "
     "las siguientes secciones."),
]

PROPUESTA = (
    "El proyecto modeló el ecosistema de un corral en Minecraft como un "
    "sistema de recurso renovable sometido a consumo constante. Aunque los "
    "modelos logísticos con extracción se utilizan comúnmente para describir "
    "poblaciones biológicas o recursos naturales, su aplicación a sistemas "
    "virtuales gobernados por reglas algorítmicas ha sido menos explorada. En "
    "este contexto, el césped se interpretó como una población que se "
    "regenera con crecimiento logístico, mientras que las ovejas actuaron "
    "como agentes que consumen el recurso. El sistema se describió mediante "
    "una ecuación diferencial que incorpora la regeneración limitada por la "
    "capacidad del entorno y el consumo proporcional al número de ovejas. Con "
    "base en la teoría de modelos logísticos con cosecha (Alharbi, 2020), se "
    "analizó si el sistema alcanza un equilibrio sostenible o si el césped se "
    "agota cuando la extracción supera la capacidad de regeneración."
)

OBJETIVO_GENERAL = (
    "Desarrollar un modelo matemático basado en EDOs que permita analizar la "
    "dinámica entre el consumo y la regeneración del césped dentro de un "
    "corral en Minecraft, con el fin de determinar qué tan rápido se agota el "
    "recurso bajo distintos escenarios, variando el número de ovejas, el "
    "tamaño y el tipo de obstáculos del área cercada, evaluando así las "
    "condiciones en las que el sistema alcanza equilibrio o en las que el "
    "césped desaparece."
)

OBJETIVOS_ESPEC = [
    # 1 — consolidado: formulación + calibración (atiende comentario 4)
    "Formular un modelo basado en una EDO que describa la regeneración del "
    "césped y su consumo por las ovejas, y determinar experimentalmente los "
    "parámetros de regeneración r y consumo c mediante un protocolo de "
    "calibración controlada en un corral de referencia.",
    # 2 — consolida los antiguos 2, 3, 4, 5
    "Analizar el comportamiento del sistema bajo distintos escenarios — "
    "variando el número de ovejas, el tamaño del corral y el tipo de "
    "obstáculo presente (agua, hojas, vallas) — para identificar las "
    "condiciones bajo las cuales el sistema alcanza equilibrio sostenible y "
    "aquellas en las que el césped se agota.",
]

# Metodología también con bloques para intercalar la ecuación (3).
METODOLOGIA_BLOCKS = [
    ("step",
     "Definición del sistema de estudio. Se diseñaron 12 configuraciones "
     "experimentales distribuidas en 6 corrales construidos en Minecraft (3 "
     "regulares de 5×5, 10×10 y 15×15, y 3 con obstáculos de 12×12 con agua, "
     "hojas y vallas), especificando para cada una el tamaño del área "
     "cercada, el número de ovejas N y el tipo de obstáculo presente."),
    ("step",
     "Formulación del modelo matemático. Las variables del sistema se "
     "parametrizaron como variables continuas para construir el modelo "
     "basado en la EDO logística con extracción, ecuación (2)."),
    ("step",
     "Definición de condiciones iniciales. Cada experimento inició con el "
     "terreno completamente cubierto de césped (G₀ = K) y con las ovejas "
     "distribuidas uniformemente dentro del corral mediante el comando "
     "spreadplayers."),
    ("step",
     "Calibración de parámetros. Los parámetros r (tasa de regeneración) y "
     "c (tasa de consumo por oveja) se determinaron experimentalmente en el "
     "corral regular C2 (10×10, K=100) mediante cinco réplicas controladas: "
     "para r se observó la saturación G(t) → K partiendo de G₀ = 1 sin "
     "ovejas, y se ajustó la solución logística analítica "
     "G(t) = K/(1 + A·e^(−rt)) con curve_fit de SciPy; para c se ajustó la "
     "EDO completa (ecuación 2) usando r ya calibrado como parámetro fijo y "
     "N = 5 ovejas, dejando c como único parámetro libre. Estos valores se "
     "asumieron constantes para los 12 escenarios, asunción que se discute "
     "en la sección de limitaciones."),
    ("step",
     "Captura automatizada de datos. La trayectoria G(t) se midió cada 100 "
     "ticks de juego mediante una cadena de command blocks que ejecuta "
     "store result score G estado run clone … filtered grass_block, "
     "capturando el conteo exacto de bloques de césped. El registro queda "
     "almacenado en el archivo latest.log del servidor Minecraft, alojado "
     "en un VPS remoto. Una skill personalizada de Claude Code conectada "
     "por SSH al VPS extrae los logs, los renombra según el escenario y la "
     "réplica, los procesa con un parser Python para producir un CSV "
     "unificado, y ejecuta el script de análisis."),
    ("step",
     "Registro audiovisual. Se realizaron grabaciones de las sesiones de "
     "juego para llevar un registro preciso de los tiempos de evolución del "
     "sistema y permitir verificación posterior de los eventos clave "
     "(transiciones a G = 0, alcance del equilibrio G*₊, comportamiento de "
     "las ovejas frente a obstáculos)."),
    ("step",
     "Simulación de distintos escenarios. Se variaron el número de ovejas N "
     "(de 1 a 40) y el tamaño/tipo de obstáculo del corral para analizar "
     "cómo estos parámetros afectan la regeneración y el consumo del "
     "césped. Cada escenario se replicó cinco veces para promediar la "
     "estocasticidad intrínseca de los random ticks y reducir la varianza "
     "muestral."),
    ("step",
     "Análisis del comportamiento del sistema. Para cada escenario se "
     "comparó la trayectoria experimental promedio (con desviación "
     "estándar) contra la solución numérica de la EDO obtenida con "
     "scipy.integrate.odeint y contra el equilibrio analítico, ecuación (3), "
     "cuando el discriminante es no negativo. El error se cuantificó con la "
     "raíz cuadrática media (RMS)."),
    ("eq", "G*₊ = (K/2)(1 + √(1 − 4cN/(rK)))", 3),
    ("step",
     "Comparación de resultados. Finalmente, se compararon los escenarios "
     "para identificar las condiciones bajo las cuales el sistema mantiene "
     "un equilibrio entre regeneración y consumo, y se aisló el efecto del "
     "obstáculo comparando los escenarios C2/C4/C5/C6 con K = 100 y N = 10 "
     "idénticos."),
]

JUSTIFICACION_PARRAFOS = [
    "Este proyecto surgió del interés por aplicar herramientas matemáticas "
    "concretas, específicamente las EDOs, a un sistema virtual con reglas "
    "precisas y medibles. Minecraft ofrece un entorno controlado donde los "
    "parámetros son fijos y reproducibles, lo que lo convierte en un "
    "laboratorio ideal para observar, registrar y modelar el comportamiento "
    "de un recurso renovable bajo consumo constante.",
    "El aporte principal está en la modelación: se tomó un fenómeno que "
    "ocurre dentro del juego y se tradujo al lenguaje matemático del modelo "
    "logístico con extracción, permitiendo predecir cuándo el sistema es "
    "sostenible y cuándo colapsa. Esto no solo refuerza la comprensión del "
    "modelo de EDO, sino que hace visible su utilidad en un contexto "
    "tangible y familiar.",
    "Adicionalmente, este proyecto integró técnicas de ingeniería de "
    "sistemas: la simulación se ejecutó en un servidor Minecraft alojado en "
    "un VPS, la captura de datos se automatizó mediante una skill de Claude "
    "Code que orquesta conexiones SSH, extracción de logs, parseo con "
    "expresiones regulares y análisis numérico con Python (scipy, "
    "matplotlib). Esta integración demostró cómo una herramienta matemática "
    "puede convertirse en un pipeline reproducible cuando se combina con "
    "infraestructura computacional moderna.",
]

# Referencias: cada entry es lista de runs (text, italic_bool) para que el
# nombre del journal y el volumen queden en cursiva (norma APA 7).
REFERENCIAS = [
    [("Alharbi, F. M. (2020). Analysis of logistic model with constant "
      "harvesting in a view of non-integer derivative. ", False),
     ("Journal of Mathematics and System Science, 10", True),
     ("(2). https://doi.org/10.17265/2159-5291/2020.02.004", False)],
    [("Braverman, E., & Lawson, J. (2025). Trimming to coexistence: How "
      "dispersal strategies should be accounted for in resource management. ",
      False),
     ("Journal of Mathematical Biology, 92", True),
     ("(1), 8. https://doi.org/10.1007/s00285-025-02324-8", False)],
    [("Brites, N. M., & Braumann, C. A. (2020). Harvesting policies with "
      "stepwise effort and logistic growth in a random environment. ", False),
     ("Applied Stochastic Models in Business and Industry, 36", True),
     ("(5), 825–835. https://doi.org/10.1002/asmb.2532", False)],
    [("Minecraft Wiki. (2024, 25 de octubre). Grass block. "
      "https://minecraft.wiki/w/Grass_Block", False)],
    [("Minecraft Wiki. (s. f.). Tick. https://es.minecraft.wiki/w/Tick", False)],
    [("Sportskeeda. (2024, 24 de mayo). Sheep Minecraft. "
      "https://wiki.sportskeeda.com/minecraft/sheep", False)],
]


def setup_styles(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(12)
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        from docx.oxml import OxmlElement
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), "Arial")
    rfonts.set(qn("w:hAnsi"), "Arial")
    rfonts.set(qn("w:cs"), "Arial")
    rfonts.set(qn("w:eastAsia"), "Arial")
    pf = style.paragraph_format
    pf.line_spacing = 2.0
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def add_body(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 2.0


def add_heading(doc: Document, text: str, level: int = 1) -> None:
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = "Arial"
        rpr = run._r.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            from docx.oxml import OxmlElement
            rfonts = OxmlElement("w:rFonts")
            rpr.append(rfonts)
        rfonts.set(qn("w:ascii"), "Arial")
        rfonts.set(qn("w:hAnsi"), "Arial")
        rfonts.set(qn("w:cs"), "Arial")
    h.paragraph_format.line_spacing = 2.0


def add_placeholder(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.italic = True
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 2.0


def add_equation(doc: Document, formula: str, num: int) -> None:
    """Insert a centered equation paragraph with right-aligned number `(num)`.

    Implementation: paragraph centered with the formula, then a tab stop at
    the right margin (15.24 cm for letter size), then `(N)` after a tab.
    Mariana can convert these to Word Equation Editor objects manually if
    she wants LaTeX-rendered visuals — the structure is preserved.
    """
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = 2.0
    p.paragraph_format.tab_stops.add_tab_stop(
        Cm(15.24), WD_TAB_ALIGNMENT.RIGHT
    )
    p.add_run(formula)
    p.add_run(f"\t({num})")


def add_glossary(doc: Document) -> None:
    """Pre-poblar el glosario de variables como párrafo justificado al final
    de la Introducción. Prefix 'Notación:' en negrita. Mariana puede
    convertirlo a footnote real en Word si quiere — python-docx no soporta
    footnotes nativamente."""
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 2.0
    bold_run = p.add_run(GLOSSARY_PREFIX)
    bold_run.bold = True
    p.add_run(GLOSSARY_TEXT)


def build_pf(out: Path) -> None:
    doc = Document()
    setup_styles(doc)

    # Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.line_spacing = 2.0
    run = title_p.add_run(TITLE)
    run.bold = True
    run.font.size = Pt(14)

    authors_p = doc.add_paragraph()
    authors_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    authors_p.paragraph_format.line_spacing = 2.0
    authors_p.add_run(AUTHORS).italic = True

    # 1. Introducción
    add_heading(doc, "Introducción", level=1)
    add_body(doc, INTRO)
    add_glossary(doc)

    # 2. Estado del arte
    add_heading(doc, "Estado del arte", level=1)
    for block in ESTADO_BLOCKS:
        if block[0] == "text":
            add_body(doc, block[1])
        elif block[0] == "eq":
            add_equation(doc, block[1], block[2])

    # 3. Planteamiento de la propuesta
    add_heading(doc, "Planteamiento de la propuesta", level=1)
    add_body(doc, PROPUESTA)

    # 4. Objetivos
    add_heading(doc, "Objetivos", level=1)
    add_heading(doc, "Objetivo general", level=2)
    add_body(doc, OBJETIVO_GENERAL)
    add_heading(doc, "Objetivos específicos", level=2)
    for i, obj in enumerate(OBJETIVOS_ESPEC, 1):
        p = doc.add_paragraph(f"{i}. {obj}")
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 2.0

    # 5. Metodología
    add_heading(doc, "Metodología", level=1)
    step_idx = 0
    for block in METODOLOGIA_BLOCKS:
        if block[0] == "step":
            step_idx += 1
            p = doc.add_paragraph(f"{step_idx}. {block[1]}")
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.line_spacing = 2.0
        elif block[0] == "eq":
            add_equation(doc, block[1], block[2])

    # 6. Justificación
    add_heading(doc, "Justificación", level=1)
    for p in JUSTIFICACION_PARRAFOS:
        add_body(doc, p)

    # 7. Resultados (PLACEHOLDER, Lina A + Julián B)
    add_heading(doc, "Resultados", level=1)
    add_placeholder(
        doc,
        "[LINA — Resultados parte A | Escenarios 1-6, corrales regulares "
        "C1/C2/C3 con K creciente]\n\n"
        "(0) Abrir Resultados con una tabla compacta de calibración con los "
        "valores de cal.json: columnas Corral | K | N_crit | r_cal | c_cal. "
        "Esta tabla ancla los siguientes análisis y debe etiquetarse como "
        "Tabla 1.\n\n"
        "(1) Reportar la ecuación calibrada como ecuación (4):\n"
        "    dG/dt = 0.005037·G·(1 − G/K) − 0.010355·N    (4)\n"
        "Esta es la respuesta cuantitativa al objetivo del proyecto. "
        "Insertarla con la helper add_equation o con el equation editor de "
        "Word.\n\n"
        "(2) Describir cómo cambia el equilibrio G*₊ al variar K manteniendo "
        "la proporción N/K. Insertar la gráfica grupo_A_K_creciente.png como "
        "Figura 1.\n\n"
        "(3) Comparar el tiempo a colapso entre C1 (5×5, K=25), C2 (10×10, "
        "K=100) y C3 (15×15, K=225). Discutir explícitamente el caso de "
        "bifurcación silla-nodo en el escenario 2 (C1 con N=3 ≈ N_crit=3.04), "
        "que es el ejemplo más limpio del proyecto.\n\n"
        "(4) Etiquetar la tabla RMS de los escenarios 1-6 como Tabla 2."
    )
    add_placeholder(
        doc,
        "[JULIÁN — Resultados parte B | Escenarios 7-12, comparación de "
        "obstáculos]\n\n"
        "(1) Analizar el bloque C3 grande (esc 7-9), destacando que esc 8 "
        "(N=25 vs N_crit=27.36) cae cerca del crítico — bifurcación visible.\n\n"
        "(2) Enfocar la comparación directa entre C2 esc 5, C4 esc 10 (agua), "
        "C5 esc 11 (hojas), C6 esc 12 (vallas) — todos con K=100 y N=10. "
        "Aislar el efecto del obstáculo. Discutir si las ovejas pueden cruzar "
        "(agua → sí nadando, hojas → sí saltando, vallas → solo rodear). "
        "Cuantificar K efectivo y RMS por obstáculo.\n\n"
        "(3) Insertar grupo_B_obstaculos.png como Figura 2 y "
        "grupo_C_bifurcacion.png como Figura 3.\n\n"
        "(4) Etiquetar la tabla RMS de los escenarios 7-12 como Tabla 3 (o "
        "Mariana puede unificar en una sola Tabla 2 al integrar)."
    )

    # 8. Posibles mejoras y trabajo futuro (PLACEHOLDER, Julián)
    add_heading(doc, "Posibles mejoras y trabajo futuro", level=1)
    add_placeholder(
        doc,
        "[JULIÁN — Mejoras] "
        "Enumerar y justificar (basados en lo aprendido): "
        "(a) calibración por corral en lugar de asumir r/c constantes; "
        "(b) modelo asimétrico donde K_efectivo_consumo difiere de K_geométrico "
        "en C6 (vallas no saltables); "
        "(c) acoplamiento explícito del movimiento de ovejas (modelo agente-"
        "basado para los irregulares); "
        "(d) variar el random_tick_speed para estudiar la sensibilidad de r; "
        "(e) repetir con versiones futuras de Minecraft para verificar "
        "estabilidad de la calibración; "
        "(f) automatizar la creación de los corrales via datapack para "
        "facilitar reproducibilidad por otros estudiantes."
    )

    # 9. Conclusiones (PLACEHOLDER, Mariana)
    add_heading(doc, "Conclusiones", level=1)
    add_placeholder(
        doc,
        "[MARIANA — Conclusiones] "
        "Verificar el cumplimiento de los 2 objetivos específicos enumerados "
        "arriba. Para cada uno, indicar: (i) si se cumplió, (ii) con qué "
        "evidencia (escenario / gráfica), (iii) qué tan acertado fue el "
        "modelo (citar RMS por escenario). Cerrar con una valoración global: "
        "¿el modelo logístico con extracción es adecuado para describir el "
        "sistema Minecraft? ¿En qué régimen falla? ¿La asunción r/c "
        "constantes sostuvo en los corrales con obstáculos?"
    )

    # 10. Referencias
    add_heading(doc, "Referencias", level=1)
    for runs in REFERENCIAS:
        p = doc.add_paragraph()
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 2.0
        pf = p.paragraph_format
        pf.first_line_indent = Pt(-18)
        pf.left_indent = Pt(18)
        for text, italic in runs:
            r = p.add_run(text)
            r.italic = italic

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    print(f"Saved {out}")


def build_bepf(out: Path) -> None:
    doc = Document()
    setup_styles(doc)

    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.line_spacing = 2.0
    run = title_p.add_run(
        "BITÁCORA-EXPOSICIÓN PROYECTO FINAL — VIDEO"
    )
    run.bold = True
    run.font.size = Pt(14)

    authors_p = doc.add_paragraph()
    authors_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    authors_p.paragraph_format.line_spacing = 2.0
    authors_p.add_run(AUTHORS).italic = True

    spacer = doc.add_paragraph("")
    spacer.paragraph_format.line_spacing = 2.0

    label = doc.add_paragraph()
    label.alignment = WD_ALIGN_PARAGRAPH.CENTER
    label.paragraph_format.line_spacing = 2.0
    label.add_run("Enlace al video:").bold = True

    link_p = doc.add_paragraph()
    link_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    link_p.paragraph_format.line_spacing = 2.0
    run = link_p.add_run("[REEMPLAZAR_CON_URL_DEL_VIDEO]")
    run.font.size = Pt(12)
    run.italic = True

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    print(f"Saved {out}")


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    templates = root / "templates"
    build_pf(
        templates
        / "PF-G2-Bello Ballen, Cristancho Niño, Gordillo Meneses, Vargas Clavijo.docx"
    )
    build_bepf(
        templates
        / "BEPF-G2-Bello Ballen, Cristancho Niño, Gordillo Meneses, Vargas Clavijo.docx"
    )


if __name__ == "__main__":
    main()
