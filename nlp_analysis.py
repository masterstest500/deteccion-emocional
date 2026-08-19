"""
nlp_analysis.py
----------------------------------------
Módulo de Procesamiento de Lenguaje Natural (NLP)
y procesamiento de variables emocionales de la plataforma.

Responsabilidades:

- Diccionario emocional adaptado al español venezolano.
- Análisis de sentimiento mediante VADER.
- Ajuste léxico contextual.
- Obtención de indicadores de polaridad y subjetividad.
- Conteo de expresiones negativas.
- Procesamiento de POMS reducido.
- Normalización de Valence-Arousal.
- Clasificación de perfil emocional orientativa.

Este módulo no contiene código de Streamlit ni consultas SQL.
Las funciones reciben valores simples y devuelven estructuras
de datos que pueden ser utilizadas desde app.py, analytics.py
y pruebas automatizadas.

Los resultados son de carácter orientativo y preventivo.
No constituyen diagnóstico clínico ni sustituyen la evaluación
de profesionales especializados.
"""

import typing as t

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# ================================================================
# DICCIONARIO EMOCIONAL ADAPTADO
# ================================================================

EMOCIONES_VE = {
    "tristeza": [
        "triste", "tristeza", "llorar", "lloro", "llorando",
        "deprimido", "depresión", "melancolía", "melancólico",
        "abatido", "desanimado", "sin ganas", "desmotivado",
        "vacío", "soledad", "solo", "sola", "abandono",
        "perdido", "perdida", "infeliz", "sufriendo", "sufro"
    ],

    "ansiedad": [
        "ansioso", "ansiosa", "ansiedad", "nervioso", "nerviosa",
        "nervios", "estresado", "estresada", "estrés",
        "angustia", "angustiado", "preocupado", "preocupada",
        "preocupación", "miedo", "temor", "asustado", "pánico",
        "agitado", "inquieto", "intranquilo", "desesperado",
        "desesperación", "paranoia"
    ],

    "agotamiento": [
        "cansado", "cansada", "cansancio", "agotado", "agotada",
        "agotamiento", "sin energía", "fatigado", "fatiga",
        "exhausto", "rendido", "rendida", "no puedo más",
        "no aguanto", "sobrecargado", "sobrecargada",
        "quemado", "burnout", "dormido", "somnoliento"
    ],

    "frustracion": [
        "frustrado", "frustrada", "frustración", "molesto",
        "molesta", "irritado", "irritada", "rabia", "rabioso",
        "enojado", "enojada", "bravo", "brava", "arrecho",
        "arrechera", "fastidiado", "harto", "harta",
        "no soporto", "odio", "detesto", "indignado"
    ],

    "desesperanza": [
        "sin esperanza", "desesperanzado", "no vale",
        "no sirve", "para qué", "para que", "no tiene sentido",
        "inútil", "inutil", "fracasado", "fracasada",
        "no puedo", "imposible", "nunca", "siempre mal",
        "todo mal", "nada funciona", "rendirse"
    ],

    "alegria": [
        "feliz", "felicidad", "alegre", "alegría", "contento",
        "contenta", "bien", "excelente", "genial", "chévere",
        "chevere", "bacano", "emocionado", "emocionada",
        "motivado", "motivada", "energético", "positivo",
        "positiva", "tranquilo", "tranquila", "estable"
    ],

    "confusion": [
        "confundido", "confundida", "confusión", "no entiendo",
        "perdido", "perdida", "desorientado", "bloqueado",
        "bloqueada", "no sé", "no se", "dudas",
        "inseguro", "insegura"
    ]
}


PALABRAS_NEGATIVAS = [
    "triste", "mal", "cansado", "solo", "estresado",
    "ansioso", "deprimido", "agotado", "preocupado",
    "paranoia", "frustrado", "irritable", "angustia",
    "arrecho", "arrechera", "harto", "desesperado",
    "rendido", "quemado", "vacío", "inútil", "fracasado",
    "odio", "rabia", "miedo", "pánico"
]


# ================================================================
# ANALIZADOR VADER
# ================================================================

_vader = SentimentIntensityAnalyzer()


# ================================================================
# ANÁLISIS DE TEXTO
# ================================================================

def analyze_text_advanced(
    text: str
) -> t.Tuple[float, float, int]:
    """
    Analiza un texto mediante VADER y un ajuste léxico
    adaptado al contexto del español venezolano.

    Retorna:

    polarity:
        Valor entre -1 y 1.

    subjectivity:
        Valor estimado entre 0 y 1 a partir de la densidad
        de expresiones emocionales detectadas.

    neg_count:
        Cantidad de expresiones negativas detectadas.
    """

    if not text or not text.strip():
        return 0.0, 0.0, 0

    text_lower = text.lower()

    # ------------------------------------------------------------
    # 1. Conteo de expresiones negativas
    # ------------------------------------------------------------

    neg_count = sum(
        1
        for palabra in PALABRAS_NEGATIVAS
        if palabra in text_lower
    )

    # ------------------------------------------------------------
    # 2. Conteo de categorías emocionales
    # ------------------------------------------------------------

    scores_emociones = {}

    for emocion, palabras in EMOCIONES_VE.items():
        scores_emociones[emocion] = sum(
            1
            for palabra in palabras
            if palabra in text_lower
        )

    total_emocional = sum(scores_emociones.values())

    # ------------------------------------------------------------
    # 3. Polaridad base mediante VADER
    # ------------------------------------------------------------

    vader_scores = _vader.polarity_scores(text)

    vader_compound = vader_scores["compound"]

    # ------------------------------------------------------------
    # 4. Ajuste léxico contextual
    # ------------------------------------------------------------

    polarity = vader_compound

    if neg_count > 0:
        ajuste_negativo = min(
            neg_count * 0.15,
            0.60
        )

        polarity -= ajuste_negativo

    alegria_count = scores_emociones.get("alegria", 0)

    if alegria_count > 0:
        polarity += alegria_count * 0.10

    polarity = max(
        -1.0,
        min(1.0, polarity)
    )

    polarity = round(polarity, 3)

    # ------------------------------------------------------------
    # 5. Estimación de subjetividad
    # ------------------------------------------------------------

    cantidad_palabras = len(text.split())

    if cantidad_palabras > 0:
        densidad_emocional = (
            total_emocional / cantidad_palabras
        )

        subjectivity = min(
            densidad_emocional * 3,
            1.0
        )
    else:
        subjectivity = 0.0

    subjectivity = round(subjectivity, 3)

    return polarity, subjectivity, neg_count


# ================================================================
# PERFIL EMOCIONAL DEL TEXTO
# ================================================================

def get_emociones_texto(text: str) -> dict:
    """
    Obtiene la cantidad de expresiones asociadas a cada
    categoría emocional detectada en el texto.
    """

    if not text or not text.strip():
        return {
            emocion: 0
            for emocion in EMOCIONES_VE
        }

    text_lower = text.lower()

    resultado = {}

    for emocion, palabras in EMOCIONES_VE.items():
        resultado[emocion] = sum(
            1
            for palabra in palabras
            if palabra in text_lower
        )

    return resultado


# ================================================================
# POMS REDUCIDO
# ================================================================

def score_poms(answers_block: dict) -> dict:
    """
    Calcula los puntajes normalizados del POMS reducido utilizado
    por la plataforma.

    Las respuestas recibidas utilizan una escala de 1 a 5.
    Cada dimensión se normaliza a un rango de 0..1.

    Las claves de salida se mantienen en español para conservar
    un contrato de datos coherente con el resto de la plataforma.
    """

    dimensiones = {
        "tension": "tension",
        "depresion": "depresion",
        "fatiga": "fatiga",
        "vigor": "vigor",
    }

    scores = {}

    for salida, entrada in dimensiones.items():
        valor = answers_block.get(entrada, 3)

        try:
            valor = float(valor)
        except (TypeError, ValueError):
            valor = 3.0

        # Garantizar que el valor permanezca dentro de la escala POMS 1..5.
        valor = max(1.0, min(5.0, valor))

        scores[salida] = round(
            (valor - 1.0) / 4.0,
            3
        )

    return scores


# ================================================================
# VALENCE - AROUSAL
# ================================================================

def normalize_va(
    valence_raw: int,
    arousal_raw: int,
    v_min: int = 1,
    v_max: int = 9,
    a_min: int = 1,
    a_max: int = 9
):
    """
    Normaliza las escalas Valence-Arousal.

    Valence:
        1..9 -> -1..1

    Arousal:
        1..9 -> 0..1
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
        round(arousal, 3)
    )


# ================================================================
# CLASIFICACIÓN DE PERFIL
# ================================================================

def classify_profile(
    promedio_encuesta: float,
    polarity: float,
    subj: float,
    poms_scores: dict,
    neg_words: int
):
    """
    Clasifica de forma orientativa el perfil emocional
    a partir de los indicadores disponibles.

    Esta función:

    - no realiza diagnóstico clínico;
    - no sustituye evaluación profesional;
    - utiliza reglas heurísticas definidas para la propuesta.
    """

    vigor = poms_scores.get(
        "vigor",
        0.5
    )

    fatigue = poms_scores.get(
        "fatigue",
        0.5
    )

    tension = poms_scores.get(
        "tension",
        0.5
    )

    depression = poms_scores.get(
        "depression",
        0.5
    )

    # ------------------------------------------------------------
    # Perfil resiliente
    # ------------------------------------------------------------

    if (
        promedio_encuesta <= 0.40
        and polarity >= 0
        and vigor >= 0.50
    ):
        return "Resiliente"

    # ------------------------------------------------------------
    # Perfil fatigado
    # ------------------------------------------------------------

    if (
        fatigue >= 0.55
        and promedio_encuesta >= 0.40
    ):
        return "Fatigado"

    # ------------------------------------------------------------
    # Perfil de estrés
    # ------------------------------------------------------------

    if (
        tension >= 0.45
        or neg_words >= 2
    ):
        return "Estrés"

    # ------------------------------------------------------------
    # Perfil emocional inestable
    # ------------------------------------------------------------

    if (
        subj >= 0.60
        and abs(polarity) < 0.20
    ):
        return "Inestable emocional"

    # ------------------------------------------------------------
    # Perfil de riesgo neuro-afectivo
    # ------------------------------------------------------------

    if (
        depression >= 0.45
        and polarity < -0.15
    ):
        return "Riesgo neuro-afectivo"

    if (
        neg_words >= 3
        and promedio_encuesta >= 0.55
    ):
        return "Riesgo neuro-afectivo"

    # ------------------------------------------------------------
    # Perfil mixto
    # ------------------------------------------------------------

    return "Perfil mixto"