# generate_dummy_data.py
# ================================================================
# Generador de datos de prueba para el TEG
# SOLO ESTUDIANTES UNIVERSITARIOS
# ================================================================

import argparse
import os
import random
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DB_PATH
from database import init_db
from db_queries import get_conn, save_result, save_survey, save_user


# ================================================================
# ANÁLISIS NLP VENEZOLANO
# Compatible con la lógica utilizada por app.py
# ================================================================

PALABRAS_NEGATIVAS = [
    "triste",
    "mal",
    "cansado",
    "solo",
    "estresado",
    "ansioso",
    "deprimido",
    "agotado",
    "preocupado",
    "paranoia",
    "frustrado",
    "irritable",
    "angustia",
    "arrecho",
    "arrechera",
    "harto",
    "desesperado",
    "rendido",
    "quemado",
    "vacío",
    "inútil",
    "fracasado",
    "odio",
    "rabia",
    "miedo",
    "pánico",
]

EMOCIONES_VE = {
    "tristeza": [
        "triste",
        "tristeza",
        "deprimido",
        "abatido",
        "desanimado",
        "solo",
        "vacío",
    ],
    "ansiedad": [
        "ansioso",
        "ansiedad",
        "nervioso",
        "estresado",
        "angustia",
        "preocupado",
        "pánico",
    ],
    "agotamiento": [
        "cansado",
        "agotado",
        "fatiga",
        "exhausto",
        "rendido",
        "quemado",
        "burnout",
    ],
    "frustracion": [
        "frustrado",
        "rabia",
        "enojado",
        "arrecho",
        "harto",
        "odio",
    ],
    "alegria": [
        "feliz",
        "alegre",
        "bien",
        "chévere",
        "motivado",
        "positivo",
        "tranquilo",
    ],
}


def analyze_text_simple(text):
    """
    Análisis NLP simple basado en palabras clave.

    Retorna:
        polarity:       -1.0 a 1.0
        subjectivity:    0.0 a 1.0
        neg_count:       cantidad de palabras negativas detectadas
    """
    if not text or not text.strip():
        return 0.0, 0.0, 0

    text_lower = text.lower()

    neg_count = sum(
        1 for palabra in PALABRAS_NEGATIVAS
        if palabra in text_lower
    )

    scores = {
        emocion: sum(
            1 for palabra in palabras
            if palabra in text_lower
        )
        for emocion, palabras in EMOCIONES_VE.items()
    }

    total_emocional = sum(scores.values())

    alegria = scores.get("alegria", 0)
    negativo_total = sum(
        valor
        for emocion, valor in scores.items()
        if emocion != "alegria"
    )

    if total_emocional == 0:
        polarity = 0.0
    else:
        polarity = (
            alegria - negativo_total
        ) / max(total_emocional, 1)

    polarity = max(
        -1.0,
        min(1.0, round(polarity, 3))
    )

    words = len(text.split())

    subjectivity = (
        min(
            total_emocional / max(words, 1) * 3,
            1.0,
        )
        if words > 0
        else 0.0
    )

    return polarity, round(subjectivity, 3), neg_count


# ================================================================
# NORMALIZACIÓN VALENCE / AROUSAL
# ================================================================

def normalize_va(valence_raw, arousal_raw):
    """
    Convierte escalas 1-9 a:

        valence -> -1 a 1
        arousal -> 0 a 1
    """
    valence = ((valence_raw - 1) / 8) * 2 - 1
    arousal = (arousal_raw - 1) / 8

    return round(valence, 3), round(arousal, 3)


# ================================================================
# POMS
# ================================================================

def score_poms(answers):
    """
    Normaliza las cuatro dimensiones POMS utilizadas por el proyecto.

    Dimensiones:
        tension
        depression
        fatigue
        vigor

    Las tres primeras representan estados negativos:
        1 = mínimo
        5 = máximo

    Vigor representa un estado positivo:
        1 = mínimo vigor
        5 = máximo vigor

    Por eso 'vigor' se mantiene en su dirección natural aquí.
    La inversión de vigor para calcular riesgo se realiza
    posteriormente en calcular_puntaje().
    """

    cats = {
        "tension": ["nervioso", "tenso", "estresado"],
        "depression": ["triste", "abatido", "desanimado"],
        "fatigue": ["cansado", "agotado", "somnoliento"],
        "vigor": ["activo", "energético", "alerta"],
    }

    scores = {}

    for sub, items in cats.items():
        vals = [
            float(answers.get(item, 3))
            for item in items
        ]

        avg = sum(vals) / len(vals)

        scores[sub] = round(
            (avg - 1) / 4,
            3,
        )

    return scores


# ================================================================
# CÁLCULO PRINCIPAL
# SOLO UNIVERSIDAD
# ================================================================

def calcular_puntaje(
    respuestas,
    polarity,
    neg_count,
):
    """
    Calcula el puntaje global exclusivamente para estudiantes
    universitarios.

    Componentes:

        70% -> indicadores generales
        30% -> POMS
        NLP -> pequeña penalización adicional

    Retorna:

        puntaje
        riesgo
        valence
        arousal
        nd_score
    """

    q = respuestas

    # ------------------------------------------------------------
    # Indicadores generales
    # ------------------------------------------------------------

    estres_n = (
        (q.get("estres", 3) - 1) / 4
    )

    fatiga_n = (
        (q.get("fatiga", 3) - 1) / 4
    )

    presion_n = (
        (q.get("presion", 3) - 1) / 4
    )

    burnout_n = (
        (q.get("burnout", 3) - 1) / 4
    )

    suenio_n = (
        (5 - q.get("suenio", 3)) / 4
    )

    social_n = (
        (q.get("social", 3) - 1) / 4
    )

    base_norm = (
        estres_n
        + fatiga_n
        + presion_n
        + burnout_n
        + suenio_n
        + social_n
    ) / 6

    # ------------------------------------------------------------
    # POMS
    # ------------------------------------------------------------

    poms_answers = {
        "nervioso": q.get("poms_tension", 3),
        "tenso": q.get("poms_tension", 3),
        "estresado": q.get("poms_tension", 3),

        "triste": q.get("poms_depresion", 3),
        "abatido": q.get("poms_depresion", 3),
        "desanimado": q.get("poms_depresion", 3),

        "cansado": q.get("poms_fatiga", 3),
        "agotado": q.get("poms_fatiga", 3),
        "somnoliento": q.get("poms_fatiga", 3),

        # POMS vigor es positivo.
        # Se mantiene en dirección positiva dentro de score_poms.
        "activo": q.get("poms_vigor", 3),
        "energético": q.get("poms_vigor", 3),
        "alerta": q.get("poms_vigor", 3),
    }

    poms_scores = score_poms(poms_answers)

    # Para riesgo, vigor debe invertirse:
    # mucho vigor -> menos riesgo
    vigor_risk_n = 1 - poms_scores["vigor"]

    poms_norm = (
        poms_scores["tension"]
        + poms_scores["depression"]
        + poms_scores["fatigue"]
        + vigor_risk_n
    ) / 4

    # ------------------------------------------------------------
    # Penalización NLP
    # ------------------------------------------------------------

    texto_pen = (
        neg_count * 0.03
        + (1 - polarity) * 0.03
    )

    # ------------------------------------------------------------
    # Puntaje final
    # ------------------------------------------------------------

    puntaje = (
        base_norm * 0.70
        + poms_norm * 0.30
        + texto_pen
    )

    puntaje = min(
        round(puntaje, 3),
        1.0,
    )

    # ------------------------------------------------------------
    # Clasificación de riesgo
    # ------------------------------------------------------------

    if puntaje >= 0.65:
        riesgo = "Alto"
    elif puntaje >= 0.40:
        riesgo = "Medio"
    else:
        riesgo = "Bajo"

    # ------------------------------------------------------------
    # Valence / Arousal
    # ------------------------------------------------------------

    vr = q.get("valence_raw", 5)
    ar = q.get("arousal_raw", 5)

    valence_calc, arousal_calc = normalize_va(
        vr,
        ar,
    )

    # ------------------------------------------------------------
    # Neurodiversidad
    # ------------------------------------------------------------

    nd_items = [
        q.get("nd_atencion", 3),
        q.get("nd_sensorial", 3),
        q.get("nd_inicio", 3),
        q.get("nd_olvidos", 3),
        q.get("nd_rutinas", 3),
        q.get("nd_social", 3),
    ]

    nd_score = round(
        (sum(nd_items) / len(nd_items) - 1) / 4,
        3,
    )

    return (
        puntaje,
        riesgo,
        valence_calc,
        arousal_calc,
        nd_score,
    )


# ================================================================
# CLASIFICACIÓN DE PERFIL
# ================================================================

def classify_profile(
    puntaje,
    polarity,
    subj,
    poms_scores,
    neg_words,
):
    """
    Clasifica el perfil general del estudiante.

    Nota:
    'vigor' aquí está en dirección positiva:
        alto vigor = mayor resiliencia
    """

    vigor = poms_scores.get("vigor", 0.5)
    fatigue = poms_scores.get("fatigue", 0.5)
    tension = poms_scores.get("tension", 0.5)
    depression = poms_scores.get("depression", 0.5)

    if (
        puntaje <= 0.40
        and polarity >= 0
        and vigor >= 0.50
    ):
        return "Resiliente"

    if (
        fatigue >= 0.55
        and puntaje >= 0.40
    ):
        return "Fatigado"

    if (
        tension >= 0.45
        or neg_words >= 2
    ):
        return "Estrés"

    if (
        subj >= 0.60
        and abs(polarity) < 0.20
    ):
        return "Inestable emocional"

    if (
        depression >= 0.45
        and polarity < -0.15
    ):
        return "Riesgo neuro-afectivo"

    if (
        neg_words >= 3
        and puntaje >= 0.55
    ):
        return "Riesgo neuro-afectivo"

    return "Perfil mixto"


# ================================================================
# DATOS DEMO
# SOLO UNIVERSIDAD
# ================================================================

USUARIOS_DEMO = [

    # ------------------------------------------------------------
    # UNIVERSIDAD — BAJO RIESGO
    # ------------------------------------------------------------

    {
        "rol": "estudiante",
        "edad": 19,
        "nivel": "Universidad",
        "days_ago": 7,
        "respuestas": {
            "estres": 2,
            "fatiga": 1,
            "presion": 2,
            "burnout": 1,
            "suenio": 2,
            "social": 2,

            "poms_tension": 1,
            "poms_depresion": 1,
            "poms_fatiga": 2,
            "poms_vigor": 4,

            "valence_raw": 7,
            "arousal_raw": 6,

            "nd_atencion": 1,
            "nd_sensorial": 1,
            "nd_inicio": 2,
            "nd_olvidos": 1,
            "nd_rutinas": 1,
            "nd_social": 2,

            "texto": (
                "Terminando el semestre, me siento bien y organizado. "
                "Tengo buen apoyo de mi familia."
            ),
        },
    },

    {
        "rol": "estudiante",
        "edad": 20,
        "nivel": "Universidad",
        "days_ago": 5,
        "respuestas": {
            "estres": 2,
            "fatiga": 2,
            "presion": 2,
            "burnout": 1,
            "suenio": 2,
            "social": 2,

            "poms_tension": 2,
            "poms_depresion": 1,
            "poms_fatiga": 2,
            "poms_vigor": 4,

            "valence_raw": 6,
            "arousal_raw": 5,

            "nd_atencion": 2,
            "nd_sensorial": 1,
            "nd_inicio": 2,
            "nd_olvidos": 2,
            "nd_rutinas": 2,
            "nd_social": 2,

            "texto": (
                "Me siento tranquilo, estoy avanzando bien "
                "en mis proyectos."
            ),
        },
    },

    # ------------------------------------------------------------
    # UNIVERSIDAD — MEDIO RIESGO
    # ------------------------------------------------------------

    {
        "rol": "estudiante",
        "edad": 20,
        "nivel": "Universidad",
        "days_ago": 4,
        "respuestas": {
            "estres": 3,
            "fatiga": 3,
            "presion": 3,
            "burnout": 3,
            "suenio": 3,
            "social": 3,

            "poms_tension": 3,
            "poms_depresion": 3,
            "poms_fatiga": 3,
            "poms_vigor": 3,

            "valence_raw": 5,
            "arousal_raw": 5,

            "nd_atencion": 3,
            "nd_sensorial": 2,
            "nd_inicio": 3,
            "nd_olvidos": 3,
            "nd_rutinas": 2,
            "nd_social": 3,

            "texto": (
                "Más o menos, hay días buenos y días malos. "
                "Trato de mantenerme."
            ),
        },
    },

    {
        "rol": "estudiante",
        "edad": 21,
        "nivel": "Universidad",
        "days_ago": 3,
        "respuestas": {
            "estres": 4,
            "fatiga": 3,
            "presion": 3,
            "burnout": 3,
            "suenio": 4,
            "social": 3,

            "poms_tension": 3,
            "poms_depresion": 2,
            "poms_fatiga": 3,
            "poms_vigor": 3,

            "valence_raw": 4,
            "arousal_raw": 4,

            "nd_atencion": 3,
            "nd_sensorial": 3,
            "nd_inicio": 3,
            "nd_olvidos": 3,
            "nd_rutinas": 3,
            "nd_social": 3,

            "texto": (
                "La universidad es exigente, a veces me siento "
                "abrumado pero lo manejo."
            ),
        },
    },

    {
        "rol": "estudiante",
        "edad": 22,
        "nivel": "Universidad",
        "days_ago": 2,
        "respuestas": {
            "estres": 4,
            "fatiga": 4,
            "presion": 4,
            "burnout": 3,
            "suenio": 4,
            "social": 3,

            "poms_tension": 4,
            "poms_depresion": 3,
            "poms_fatiga": 4,
            "poms_vigor": 2,

            "valence_raw": 3,
            "arousal_raw": 4,

            "nd_atencion": 4,
            "nd_sensorial": 3,
            "nd_inicio": 4,
            "nd_olvidos": 3,
            "nd_rutinas": 3,
            "nd_social": 3,

            "texto": (
                "Estoy cansado y preocupado por los exámenes. "
                "Me cuesta concentrarme."
            ),
        },
    },

    # ------------------------------------------------------------
    # UNIVERSIDAD — ALTO RIESGO
    # ------------------------------------------------------------

    {
        "rol": "estudiante",
        "edad": 21,
        "nivel": "Universidad",
        "days_ago": 2,
        "respuestas": {
            "estres": 5,
            "fatiga": 5,
            "presion": 5,
            "burnout": 5,
            "suenio": 5,
            "social": 5,

            "poms_tension": 5,
            "poms_depresion": 4,
            "poms_fatiga": 5,
            "poms_vigor": 1,

            "valence_raw": 2,
            "arousal_raw": 7,

            "nd_atencion": 5,
            "nd_sensorial": 4,
            "nd_inicio": 5,
            "nd_olvidos": 4,
            "nd_rutinas": 4,
            "nd_social": 5,

            "texto": (
                "La carga académica es excesiva, me siento atrapado "
                "y ansioso. No puedo dormir más de 4 horas. "
                "Necesito ayuda."
            ),
        },
    },

    {
        "rol": "estudiante",
        "edad": 23,
        "nivel": "Universidad",
        "days_ago": 1,
        "respuestas": {
            "estres": 5,
            "fatiga": 5,
            "presion": 4,
            "burnout": 5,
            "suenio": 5,
            "social": 4,

            "poms_tension": 5,
            "poms_depresion": 5,
            "poms_fatiga": 5,
            "poms_vigor": 1,

            "valence_raw": 1,
            "arousal_raw": 6,

            "nd_atencion": 5,
            "nd_sensorial": 5,
            "nd_inicio": 5,
            "nd_olvidos": 5,
            "nd_rutinas": 4,
            "nd_social": 5,

            "texto": (
                "Estoy agotado y deprimido. No encuentro sentido "
                "a seguir estudiando. Me siento frustrado y desesperado."
            ),
        },
    },

    {
        "rol": "estudiante",
        "edad": 20,
        "nivel": "Universidad",
        "days_ago": 1,
        "respuestas": {
            "estres": 5,
            "fatiga": 4,
            "presion": 5,
            "burnout": 4,
            "suenio": 5,
            "social": 5,

            "poms_tension": 4,
            "poms_depresion": 4,
            "poms_fatiga": 4,
            "poms_vigor": 2,

            "valence_raw": 2,
            "arousal_raw": 5,

            "nd_atencion": 4,
            "nd_sensorial": 4,
            "nd_inicio": 4,
            "nd_olvidos": 4,
            "nd_rutinas": 4,
            "nd_social": 4,

            "texto": (
                "Todo está mal. Estoy solo, ansioso y no puedo "
                "concentrarme en nada."
            ),
        },
    },

    {
        "rol": "estudiante",
        "edad": 22,
        "nivel": "Universidad",
        "days_ago": 0,
        "respuestas": {
            "estres": 4,
            "fatiga": 5,
            "presion": 4,
            "burnout": 5,
            "suenio": 4,
            "social": 4,

            "poms_tension": 4,
            "poms_depresion": 3,
            "poms_fatiga": 5,
            "poms_vigor": 2,

            "valence_raw": 3,
            "arousal_raw": 3,

            "nd_atencion": 3,
            "nd_sensorial": 3,
            "nd_inicio": 4,
            "nd_olvidos": 4,
            "nd_rutinas": 3,
            "nd_social": 3,

            "texto": (
                "Me siento quemado. Demasiadas responsabilidades "
                "y poco descanso."
            ),
        },
    },

    # ------------------------------------------------------------
    # UNIVERSIDAD — PERFIL NORMAL / CONTROL
    # ------------------------------------------------------------

    {
        "rol": "estudiante",
        "edad": 19,
        "nivel": "Universidad",
        "days_ago": 0,
        "respuestas": {
            "estres": 3,
            "fatiga": 3,
            "presion": 3,
            "burnout": 3,
            "suenio": 3,
            "social": 3,

            "poms_tension": 3,
            "poms_depresion": 3,
            "poms_fatiga": 3,
            "poms_vigor": 3,

            "valence_raw": 5,
            "arousal_raw": 5,

            "nd_atencion": 2,
            "nd_sensorial": 2,
            "nd_inicio": 2,
            "nd_olvidos": 2,
            "nd_rutinas": 2,
            "nd_social": 2,

            "texto": (
                "Un día normal, sin nada especial que reportar."
            ),
        },
    },
]


# ================================================================
# LIMPIEZA CONTROLADA DE LA BASE DE DATOS
# ================================================================

def clean_database():
    """
    Limpia las tablas de la base de datos sin eliminar el esquema.

    Se desactivan temporalmente las foreign keys para evitar problemas
    de orden de borrado.

    Se conservan las tablas y su estructura.
    Solo se eliminan los registros.
    """

    if not os.path.exists(DB_PATH):
        print("  ℹ️ No existe una base de datos previa.")
        return

    print("\n🧹 Limpiando base de datos...")

    conn = get_conn()

    try:
        conn.execute("PRAGMA foreign_keys = OFF")

        tables = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            """
        ).fetchall()

        for (table_name,) in tables:
            try:
                conn.execute(
                    f'DELETE FROM "{table_name}"'
                )
                print(f"  ✓ Tabla limpiada: {table_name}")
            except Exception as exc:
                print(
                    f"  ⚠️ No se pudo limpiar "
                    f"{table_name}: {exc}"
                )

        conn.commit()

    finally:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()

    print("  ✅ Base de datos limpiada.")


# ================================================================
# PROCESAMIENTO DE UNA EVALUACIÓN
# ================================================================

def process_evaluation(
    uid,
    respuestas,
    fecha,
    verbose=True,
):
    """
    Procesa una encuesta universitaria y guarda el resultado.
    """

    eid = save_survey(
        uid,
        respuestas,
        fecha,
    )

    texto = respuestas.get("texto", "")

    polarity, subjectivity, neg_count = (
        analyze_text_simple(texto)
    )

    (
        puntaje,
        riesgo,
        valence_calc,
        arousal_calc,
        nd_score,
    ) = calcular_puntaje(
        respuestas,
        polarity,
        neg_count,
    )

    poms_answers = {
        "nervioso": respuestas.get("poms_tension", 3),
        "tenso": respuestas.get("poms_tension", 3),
        "estresado": respuestas.get("poms_tension", 3),

        "triste": respuestas.get("poms_depresion", 3),
        "abatido": respuestas.get("poms_depresion", 3),
        "desanimado": respuestas.get("poms_depresion", 3),

        "cansado": respuestas.get("poms_fatiga", 3),
        "agotado": respuestas.get("poms_fatiga", 3),
        "somnoliento": respuestas.get("poms_fatiga", 3),

        "activo": respuestas.get("poms_vigor", 3),
        "energético": respuestas.get("poms_vigor", 3),
        "alerta": respuestas.get("poms_vigor", 3),
    }

    poms_scores = score_poms(
        poms_answers
    )

    perfil = classify_profile(
        puntaje,
        polarity,
        subjectivity,
        poms_scores,
        neg_count,
    )

    detalle = {
        "resultado": {
            "puntaje": puntaje,
            "riesgo": riesgo,
            "perfil": perfil,
        },

        "emocional": {
            "polarity": polarity,
            "subjectivity": subjectivity,
            "neg_words": neg_count,
        },

        "va": {
            "valence": valence_calc,
            "arousal": arousal_calc,
        },

        "poms": poms_scores,

        "neurodiv": {
            "nd_score": nd_score,
        },

        "texto": texto,
    }

    save_result(
        eid,
        riesgo,
        puntaje,
        detalle,
        fecha,
    )

    if verbose:
        emoji = {
            "Alto": "🔴",
            "Medio": "🟠",
            "Bajo": "🟢",
        }.get(riesgo, "⚪")

        print(
            f"  {emoji} "
            f"{fecha.strftime('%Y-%m-%d')} | "
            f"{riesgo:5} | "
            f"{puntaje:.3f} | "
            f"{perfil}"
        )

    return {
        "eid": eid,
        "puntaje": puntaje,
        "riesgo": riesgo,
        "perfil": perfil,
    }


# ================================================================
# GENERAR DATASET DEMO
# ================================================================

def generate_dummy_data(clean_db=True):
    """
    Genera el dataset principal de demostración.

    IMPORTANTE:
    Este proyecto trabaja exclusivamente con estudiantes
    universitarios. No se generan datos de Primaria ni Secundaria.
    """

    print("\n" + "=" * 64)
    print("🎓 GENERADOR DE DATOS DEMO — UNIVERSIDAD")
    print("=" * 64)

    init_db()

    if clean_db:
        clean_database()

    print(
        f"\n📊 Generando {len(USUARIOS_DEMO)} "
        "estudiantes universitarios..."
    )

    today = datetime.now()

    resultados = []

    for index, usuario in enumerate(
        USUARIOS_DEMO,
        start=1,
    ):
        uid = save_user(
            usuario["rol"],
            usuario["edad"],
            usuario["nivel"],
        )

        fecha = (
            today
            - timedelta(
                days=usuario["days_ago"]
            )
        )

        resultado = process_evaluation(
            uid,
            usuario["respuestas"],
            fecha,
        )

        resultados.append(
            {
                "uid": uid,
                **resultado,
            }
        )

        print(
            f"  👤 Estudiante #{index:02d} "
            f"| ID {uid} "
            f"| edad {usuario['edad']}"
        )

    print("\n" + "-" * 64)
    print("📈 RESUMEN DEL DATASET")
    print("-" * 64)

    conteo = {
        "Bajo": 0,
        "Medio": 0,
        "Alto": 0,
    }

    for resultado in resultados:
        conteo[resultado["riesgo"]] += 1

    print(f"  🟢 Bajo:  {conteo['Bajo']}")
    print(f"  🟠 Medio: {conteo['Medio']}")
    print(f"  🔴 Alto:  {conteo['Alto']}")

    print(
        "\n✅ Dataset universitario generado correctamente."
    )

    return resultados


# ================================================================
# HISTORIA DE CRISIS PROGRESIVA
# ================================================================

def generate_historia_crisis(uid=None):
    """
    Genera un estudiante universitario con tres evaluaciones
    que muestran deterioro progresivo:

        Bajo → Medio → Alto

    Ideal para probar:
        - historial
        - gráficas
        - evolución temporal
        - alertas
        - detección de deterioro
    """

    print(
        "\n📖 Generando historia de crisis progresiva..."
    )

    today = datetime.now()

    # ------------------------------------------------------------
    # Crear estudiante
    # ------------------------------------------------------------

    if uid is None:
        uid = save_user(
            "estudiante",
            21,
            "Universidad",
        )

    evaluaciones = [

        # --------------------------------------------------------
        # Evaluación 1 — BAJO
        # --------------------------------------------------------

        {
            "days_ago": 14,
            "respuestas": {
                "estres": 2,
                "fatiga": 2,
                "presion": 2,
                "burnout": 1,
                "suenio": 2,
                "social": 2,

                "poms_tension": 1,
                "poms_depresion": 1,
                "poms_fatiga": 2,
                "poms_vigor": 4,

                "valence_raw": 7,
                "arousal_raw": 5,

                "nd_atencion": 2,
                "nd_sensorial": 1,
                "nd_inicio": 2,
                "nd_olvidos": 1,
                "nd_rutinas": 2,
                "nd_social": 2,

                "texto": (
                    "Me siento bien, el semestre arrancó "
                    "tranquilo. Tengo energía y apoyo de mi familia."
                ),
            },
        },

        # --------------------------------------------------------
        # Evaluación 2 — MEDIO
        # --------------------------------------------------------

        {
            "days_ago": 7,
            "respuestas": {
                "estres": 4,
                "fatiga": 3,
                "presion": 4,
                "burnout": 3,
                "suenio": 4,
                "social": 3,

                "poms_tension": 3,
                "poms_depresion": 3,
                "poms_fatiga": 3,
                "poms_vigor": 3,

                "valence_raw": 4,
                "arousal_raw": 5,

                "nd_atencion": 3,
                "nd_sensorial": 2,
                "nd_inicio": 3,
                "nd_olvidos": 3,
                "nd_rutinas": 3,
                "nd_social": 3,

                "texto": (
                    "La carga aumentó bastante. Me cuesta dormir "
                    "y siento que no me alcanza el tiempo. "
                    "Trato de mantenerme pero está difícil."
                ),
            },
        },

        # --------------------------------------------------------
        # Evaluación 3 — ALTO
        # --------------------------------------------------------

        {
            "days_ago": 0,
            "respuestas": {
                "estres": 5,
                "fatiga": 5,
                "presion": 5,
                "burnout": 5,
                "suenio": 5,
                "social": 5,

                "poms_tension": 5,
                "poms_depresion": 4,
                "poms_fatiga": 5,
                "poms_vigor": 1,

                "valence_raw": 2,
                "arousal_raw": 7,

                "nd_atencion": 5,
                "nd_sensorial": 4,
                "nd_inicio": 5,
                "nd_olvidos": 4,
                "nd_rutinas": 4,
                "nd_social": 5,

                "texto": (
                    "Ya no puedo más. Estoy agotado, ansioso y "
                    "deprimido. No encuentro sentido a seguir. "
                    "Me siento completamente solo y desesperado. "
                    "Necesito ayuda urgente."
                ),
            },
        },
    ]

    resultados = []

    for evaluacion in evaluaciones:
        fecha = (
            today
            - timedelta(
                days=evaluacion["days_ago"]
            )
        )

        resultado = process_evaluation(
            uid,
            evaluacion["respuestas"],
            fecha,
        )

        resultados.append(resultado)

    print(
        f"\n  👤 Estudiante ID {uid} "
        "— historia de crisis lista"
    )

    return uid, resultados


# ================================================================
# GENERAR UNIVERSITARIOS
# ================================================================

def generate_universitarios(
    total=20,
    clean_db=True,
):
    """
    Genera estudiantes universitarios de prueba.

    El dataset base contiene 10 perfiles definidos manualmente.
    Si se solicitan más estudiantes, se generan copias con pequeñas
    variaciones para ampliar el conjunto de pruebas.
    """

    if total <= 0:
        raise ValueError(
            "El número de estudiantes debe ser mayor que 0."
        )

    print(
        "\n🎓 Generando dataset universitario..."
    )

    init_db()

    if clean_db:
        clean_database()

    today = datetime.now()

    resultados = []

    for index in range(total):

        base = random.choice(
            USUARIOS_DEMO
        )

        respuestas = dict(
            base["respuestas"]
        )

        # Pequeñas variaciones para evitar que todos
        # los registros adicionales sean idénticos.
        for campo in [
            "estres",
            "fatiga",
            "presion",
            "burnout",
            "suenio",
            "social",
            "poms_tension",
            "poms_depresion",
            "poms_fatiga",
            "poms_vigor",
            "nd_atencion",
            "nd_sensorial",
            "nd_inicio",
            "nd_olvidos",
            "nd_rutinas",
            "nd_social",
        ]:
            if campo in respuestas:
                variacion = random.choice(
                    [-1, 0, 0, 0, 1]
                )

                respuestas[campo] = max(
                    1,
                    min(
                        5,
                        respuestas[campo]
                        + variacion,
                    ),
                )

        edad = random.randint(18, 25)

        uid = save_user(
            "estudiante",
            edad,
            "Universidad",
        )

        fecha = (
            today
            - timedelta(
                days=random.randint(0, 14)
            )
        )

        resultado = process_evaluation(
            uid,
            respuestas,
            fecha,
        )

        resultados.append(
            {
                "uid": uid,
                **resultado,
            }
        )

        print(
            f"  👤 #{index + 1:02d} "
            f"| ID {uid} "
            f"| edad {edad} "
            f"| {resultado['riesgo']:5} "
            f"| {resultado['puntaje']:.3f}"
        )

    print(
        f"\n✅ {total} estudiantes universitarios generados."
    )

    return resultados


# ================================================================
# MAIN
# ================================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generador de datos de prueba "
            "para el TEG — exclusivamente Universidad."
        )
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Limpiar la BD y generar el dataset demo.",
    )

    parser.add_argument(
        "--keep",
        action="store_true",
        help=(
            "Agregar el dataset demo sin limpiar "
            "los datos existentes."
        ),
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help=(
            "Generar dataset demo universitario "
            "más historia de crisis."
        ),
    )

    parser.add_argument(
        "--universitarios",
        action="store_true",
        help=(
            "Generar estudiantes universitarios "
            "de prueba."
        ),
    )

    args = parser.parse_args()

    # ------------------------------------------------------------
    # DEMO 360
    # ------------------------------------------------------------

    if args.demo:
        generate_dummy_data(
            clean_db=True
        )

        generate_historia_crisis()

        print(
            "\n" + "=" * 64
        )
        print(
            "✅ DATOS DE DEMO 360 LISTOS"
        )
        print(
            "=" * 64
        )

    # ------------------------------------------------------------
    # UNIVERSITARIOS
    # ------------------------------------------------------------

    elif args.universitarios:
        generate_universitarios(
            total=20,
            clean_db=True,
        )

    # ------------------------------------------------------------
    # CLEAN
    # ------------------------------------------------------------

    elif args.clean:
        generate_dummy_data(
            clean_db=True
        )

    # ------------------------------------------------------------
    # KEEP
    # ------------------------------------------------------------

    elif args.keep:
        generate_dummy_data(
            clean_db=False
        )

    # ------------------------------------------------------------
    # SIN ARGUMENTOS
    # ------------------------------------------------------------

    else:
        if os.path.exists(DB_PATH):
            respuesta = input(
                "¿Limpiar base de datos existente? (si/no): "
            ).strip().lower()

            generate_dummy_data(
                clean_db=respuesta in [
                    "si",
                    "s",
                    "yes",
                    "y",
                ]
            )

        else:
            generate_dummy_data(
                clean_db=True
            )


if __name__ == "__main__":
    main()