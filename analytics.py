"""
analytics.py
----------------------------------------
Motor analítico de la plataforma.

Este módulo concentra toda la lógica relacionada con:

- Tendencias históricas
- Detección temprana
- Priorización de casos
- Recomendaciones automáticas

No contiene código de Streamlit ni consultas SQL.
"""

from statistics import mean


# ==========================================================
# TENDENCIAS
# ==========================================================

def analyze_risk_trend(history):
    """
    Analiza la evolución del riesgo.

    Parameters
    ----------
    history : list[float]

        Historial cronológico de riesgos.

        Ejemplo:
        [0.21,0.35,0.47,0.59]

    Returns
    -------
    dict
    """

    if history is None or len(history) < 2:
        return {
            "trend": "Sin datos",
            "delta": 0,
            "severity": "N/A"
        }

    delta = history[-1] - history[0]

    if delta >= 0.20:
        trend = "Ascendente"

    elif delta <= -0.20:
        trend = "Descendente"

    else:
        trend = "Estable"

    magnitude = abs(delta)

    if magnitude < 0.10:
        severity = "Leve"

    elif magnitude < 0.30:
        severity = "Moderada"

    else:
        severity = "Alta"

    return {
        "trend": trend,
        "delta": round(delta,3),
        "severity": severity
    }


# ==========================================================
# DETERIORO PROGRESIVO
# ==========================================================

def detect_progressive_deterioration(history):
    """
    Detecta si el riesgo aumenta de forma continua.

    Ejemplo:

    0.21
    0.35
    0.46
    0.62

    devuelve True
    """

    if history is None:
        return False

    if len(history) < 3:
        return False

    return all(
        history[i] < history[i+1]
        for i in range(len(history)-1)
    )


# ==========================================================
# CAMBIO BRUSCO
# ==========================================================

def detect_abrupt_change(history, threshold=0.30):
    """
    Detecta incrementos repentinos entre
    dos evaluaciones consecutivas.
    """

    if history is None:
        return {
            "abrupt": False,
            "difference": 0
        }

    if len(history) < 2:
        return {
            "abrupt": False,
            "difference": 0
        }

    diff = history[-1] - history[-2]

    return {
        "abrupt": diff >= threshold,
        "difference": round(diff,3)
    }


# ==========================================================
# PRIORIDAD
# ==========================================================

def calculate_priority_score(current_risk, history):
    """
    Calcula un puntaje institucional de prioridad.

    Se considera:

    - Riesgo actual
    - Tendencia
    - Deterioro progresivo
    """

    score = current_risk * 100

    trend = analyze_risk_trend(history)

    if trend["trend"] == "Ascendente":
        score += 15

    if detect_progressive_deterioration(history):
        score += 10

    abrupt = detect_abrupt_change(history)

    if abrupt["abrupt"]:
        score += 15

    return round(min(score,100),1)


# ==========================================================
# ESTABILIDAD
# ==========================================================

def calculate_stability_index(history):
    """
    Calcula un índice de estabilidad.

    100 = completamente estable

    0 = extremadamente variable
    """

    if history is None:
        return 100

    if len(history) < 2:
        return 100

    variations = []

    for i in range(len(history)-1):

        variations.append(
            abs(history[i+1]-history[i])
        )

    instability = mean(variations)

    stability = max(0,100-(instability*200))

    return round(stability,1)


# ==========================================================
# RECOMENDACIONES
# ==========================================================

def generate_recommendations(risk_level, cognitive_score=0, trend_data=None):
    recommendations = []

    # 1. Recomendaciones por riesgo emocional
    if risk_level == "Alto":
        recommendations.append("Programar entrevista prioritaria con el Departamento de Bienestar Estudiantil.")
    elif risk_level == "Medio":
        recommendations.append("Realizar seguimiento preventivo en el lapso de 2 semanas.")

    # 2. Recomendaciones por deterioro o tendencia (si aplica)
    if trend_data and trend_data.get("deterioration"):
        recommendations.append("Atención: Se detecta un incremento progresivo en los niveles de riesgo.")

    # 3. 🔥 RECOMENDACIÓN POR EVALUACIÓN COGNITIVA / NEURODIVERGENCIA
    # Ajusta el umbral (ej. > 40 o > 50) según la escala de tu nd_score
    if cognitive_score >= 40:
        recommendations.append(
            "Sugerir evaluación especializada de aspectos cognitivos y neurodivergencia "
            "(atención, sobrecarga académica o rutinas de estudio)."
        )

    return recommendations

# ==========================================================
# EXPLICACIÓN DEL RIESGO
# ==========================================================

def explain_risk(
        stress=None,
        fatigue=None,
        polarity=None,
        trend=None):
    """
    Explica por qué la plataforma
    clasificó un determinado riesgo.
    """

    reasons = []

    if stress is not None:

        if stress >= 4:
            reasons.append("Estrés elevado.")

    if fatigue is not None:

        if fatigue >= 4:
            reasons.append("Fatiga elevada.")

    if polarity is not None:

        if polarity < -0.20:
            reasons.append("Predominio de lenguaje negativo.")

    if trend == "Ascendente":

        reasons.append(
            "El historial muestra un aumento progresivo del riesgo."
        )

    return reasons
