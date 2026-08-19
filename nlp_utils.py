# nlp_utils.py — Funciones de NLP y análisis separadas para testing

import re
import typing as t

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# ============================================================
# LÉXICO BÁSICO DE TÉRMINOS NEGATIVOS
# ============================================================

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


# ============================================================
# LÉXICO EMOCIONAL ADAPTADO AL CONTEXTO DEL PROYECTO
# ============================================================

EMOCIONES_VE = {
    "tristeza": [
        "triste",
        "tristeza",
        "llorar",
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


# ============================================================
# ANALIZADOR VADER
# ============================================================

_vader = SentimentIntensityAnalyzer()


# ============================================================
# FUNCIONES INTERNAS
# ============================================================

def _contains_term(text: str, term: str) -> bool:
    """
    Determina si un término aparece como palabra o expresión
    independiente dentro del texto.

    Se utiliza para reducir coincidencias accidentales producidas
    por búsquedas simples de subcadenas.
    """
    pattern = rf"\b{re.escape(term.lower())}\b"
    return bool(re.search(pattern, text))


def _count_terms(text: str, terms: t.Iterable[str]) -> int:
    """
    Cuenta la cantidad de términos distintos encontrados en el texto.
    """
    return sum(1 for term in terms if _contains_term(text, term))


# ============================================================
# ANÁLISIS DE TEXTO
# ============================================================

def analyze_text_advanced(text: str) -> t.Tuple[float, float, int]:
    """
    Analiza una respuesta textual mediante VADER y un léxico
    emocional adaptado al contexto del proyecto.

    Retorna:
        polarity:
            Indicador combinado de orientación emocional del texto
            en un rango de -1 a 1.

        subjectivity:
            Índice heurístico de presencia de contenido emocional
            en el texto, expresado en un rango de 0 a 1.

        neg_count:
            Cantidad de términos negativos identificados.
    """

    if not text or not text.strip():
        return 0.0, 0.0, 0

    text_lower = text.lower()

    # --------------------------------------------------------
    # 1. Detección de términos negativos
    # --------------------------------------------------------

    neg_count = _count_terms(text_lower, PALABRAS_NEGATIVAS)

    # --------------------------------------------------------
    # 2. Identificación de categorías emocionales
    # --------------------------------------------------------

    scores_emociones = {}

    for emocion, palabras in EMOCIONES_VE.items():
        scores_emociones[emocion] = _count_terms(
            text_lower,
            palabras,
        )

    total_emocional = sum(scores_emociones.values())

    # --------------------------------------------------------
    # 3. Análisis de sentimiento mediante VADER
    # --------------------------------------------------------

    vader_scores = _vader.polarity_scores(text)

    vader_compound = vader_scores["compound"]

    # --------------------------------------------------------
    # 4. Ajuste heurístico utilizando el léxico del proyecto
    # --------------------------------------------------------

    polarity = vader_compound

    if neg_count > 0:
        ajuste_negativo = min(
            neg_count * 0.15,
            0.60,
        )

        polarity -= ajuste_negativo

    alegria_count = scores_emociones.get("alegria", 0)

    if alegria_count > 0:
        ajuste_positivo = min(
            alegria_count * 0.10,
            0.40,
        )

        polarity += ajuste_positivo

    # Mantener el resultado dentro del rango de VADER.
    polarity = max(
        -1.0,
        min(1.0, round(polarity, 3)),
    )

    # --------------------------------------------------------
    # 5. Índice heurístico de contenido emocional
    # --------------------------------------------------------

    palabras = text_lower.split()

    if palabras:
        densidad_emocional = total_emocional / len(palabras)

        subjectivity = min(
            densidad_emocional * 3,
            1.0,
        )
    else:
        subjectivity = 0.0

    subjectivity = round(subjectivity, 3)

    return polarity, subjectivity, neg_count


# ============================================================
# NORMALIZACIÓN VALENCE / AROUSAL
# ============================================================

def normalize_va(
    valence_raw: int,
    arousal_raw: int,
    v_min: int = 1,
    v_max: int = 9,
    a_min: int = 1,
    a_max: int = 9,
):
    """
    Normaliza valores de valencia y activación.

    Valencia:
        escala original -> rango [-1, 1]

    Activación:
        escala original -> rango [0, 1]
    """

    valence = (
        (valence_raw - v_min)
        / (v_max - v_min)
    ) * 2 - 1

    arousal = (
        (arousal_raw - a_min)
        / (a_max - a_min)
    )

    return (
        round(valence, 3),
        round(arousal, 3),
    )


# ============================================================
# CLASIFICACIÓN ORIENTATIVA DEL PERFIL
# ============================================================

def classify_profile(
    promedio: float,
    polarity: float,
    subj: float,
    poms_scores: dict,
    neg_words: int,
):
    """
    Genera una clasificación orientativa a partir de los
    indicadores disponibles.

    Estas categorías no representan diagnósticos clínicos.
    Su finalidad es facilitar la interpretación y el seguimiento
    de los indicadores producidos por la plataforma.
    """

    vigor = poms_scores.get("vigor", 0.5)
    fatigue = poms_scores.get("fatigue", 0.5)
    tension = poms_scores.get("tension", 0.5)
    depression = poms_scores.get("depression", 0.5)

    # Perfil favorable
    if (
        promedio <= 0.40
        and polarity >= 0
        and vigor >= 0.5
    ):
        return "Perfil favorable"

    # Indicadores relacionados con fatiga
    if (
        fatigue >= 0.55
        and promedio >= 0.40
    ):
        return "Indicadores de fatiga"

    # Indicadores relacionados con estrés
    if (
        tension >= 0.45
        or neg_words >= 2
    ):
        return "Indicadores de estrés"

    # Alta presencia de contenido emocional
    if (
        subj >= 0.60
        and abs(polarity) < 0.20
    ):
        return "Expresión emocional elevada"

    # Indicadores que requieren seguimiento
    if (
        depression >= 0.45
        and polarity < -0.15
    ):
        return "Indicadores emocionales de atención"

    if (
        neg_words >= 3
        and promedio >= 0.55
    ):
        return "Indicadores emocionales de atención"

    return "Perfil mixto"