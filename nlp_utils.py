# nlp_utils.py — Funciones de NLP y análisis separadas para testing
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import typing as t

PALABRAS_NEGATIVAS = [
    "triste", "mal", "cansado", "solo", "estresado", "ansioso", "deprimido",
    "agotado", "preocupado", "paranoia", "frustrado", "irritable", "angustia",
    "arrecho", "arrechera", "harto", "desesperado", "rendido", "quemado",
    "vacío", "inútil", "fracasado", "odio", "rabia", "miedo", "pánico"
]

EMOCIONES_VE = {
    "tristeza": ["triste", "tristeza", "llorar", "deprimido", "abatido", "desanimado", "solo", "vacío"],
    "ansiedad": ["ansioso", "ansiedad", "nervioso", "estresado", "angustia", "preocupado", "pánico"],
    "agotamiento": ["cansado", "agotado", "fatiga", "exhausto", "rendido", "quemado", "burnout"],
    "frustracion": ["frustrado", "rabia", "enojado", "arrecho", "harto", "odio"],
    "alegria": ["feliz", "alegre", "bien", "chévere", "motivado", "positivo", "tranquilo"]
}

_vader = SentimentIntensityAnalyzer()

def analyze_text_advanced(text: str) -> t.Tuple[float, float, int]:
    if not text or not text.strip():
        return 0.0, 0.0, 0
    text_lower = text.lower()
    neg_count = sum(1 for w in PALABRAS_NEGATIVAS if w in text_lower)
    scores_emociones = {}
    for emocion, palabras in EMOCIONES_VE.items():
        scores_emociones[emocion] = sum(1 for p in palabras if p in text_lower)
    total_emocional = sum(scores_emociones.values())
    vader_scores = _vader.polarity_scores(text)
    vader_compound = vader_scores["compound"]
    if neg_count > 0:
        ajuste_negativo = min(neg_count * 0.15, 0.6)
        polarity = vader_compound - ajuste_negativo
    else:
        polarity = vader_compound
    if scores_emociones.get("alegria", 0) > 0:
        polarity = min(polarity + scores_emociones["alegria"] * 0.1, 1.0)
    polarity = max(-1.0, min(1.0, round(polarity, 3)))
    if len(text.split()) > 0:
        densidad = total_emocional / len(text.split())
        subjectivity = min(densidad * 3, 1.0)
    else:
        subjectivity = 0.0
    return polarity, round(subjectivity, 3), neg_count

def normalize_va(valence_raw: int, arousal_raw: int, v_min=1, v_max=9, a_min=1, a_max=9):
    valence = ((valence_raw - v_min) / (v_max - v_min)) * 2 - 1
    arousal = (arousal_raw - a_min) / (a_max - a_min)
    return round(valence, 3), round(arousal, 3)

def classify_profile(promedio: float, polarity: float, subj: float, poms_scores: dict, neg_words: int):
    vigor      = poms_scores.get("vigor", 0.5)
    fatigue    = poms_scores.get("fatigue", 0.5)
    tension    = poms_scores.get("tension", 0.5)
    depression = poms_scores.get("depression", 0.5)
    if promedio <= 0.40 and polarity >= 0 and vigor >= 0.5:
        return "Resiliente"
    if fatigue >= 0.55 and promedio >= 0.40:
        return "Fatigado"
    if tension >= 0.45 or neg_words >= 2:
        return "Estrés"
    if subj >= 0.60 and abs(polarity) < 0.20:
        return "Inestable emocional"
    if depression >= 0.45 and polarity < -0.15:
        return "Riesgo neuro-afectivo"
    if neg_words >= 3 and promedio >= 0.55:
        return "Riesgo neuro-afectivo"
    return "Perfil mixto"