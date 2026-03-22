# generate_dummy_data.py — Versión actualizada con lógica calibrada 0-1
import sqlite3
import json
import random
from datetime import datetime, timedelta
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from init_db import init_db, get_db_path
    DB_PATH = get_db_path()
except ImportError:
    print("Error: No se pudo importar init_db.py")
    sys.exit(1)

# ================================================================
# UTILIDADES DE BASE DE DATOS
# ================================================================

def get_conn():
    return sqlite3.connect(DB_PATH)

def save_user(rol, edad, nivel):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO usuarios (rol, edad, nivel) VALUES (?, ?, ?)", (rol, edad, nivel))
    conn.commit()
    uid = c.lastrowid
    conn.close()
    return uid

def save_survey(uid, respuestas, fecha):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO encuestas (usuario_id, respuestas, fecha) VALUES (?, ?, ?)",
              (uid, json.dumps(respuestas, ensure_ascii=False), fecha.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    eid = c.lastrowid
    conn.close()
    return eid

def save_result(eid, riesgo, puntaje, detalle, fecha):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO resultados (encuesta_id, puntaje, riesgo, detalle, fecha) VALUES (?, ?, ?, ?, ?)",
              (eid, puntaje, riesgo, json.dumps(detalle, ensure_ascii=False), fecha.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

# ================================================================
# ANÁLISIS NLP VENEZOLANO (compatible con app.py)
# ================================================================

PALABRAS_NEGATIVAS = [
    "triste", "mal", "cansado", "solo", "estresado", "ansioso", "deprimido",
    "agotado", "preocupado", "paranoia", "frustrado", "irritable", "angustia",
    "arrecho", "arrechera", "harto", "desesperado", "rendido", "quemado",
    "vacío", "inútil", "fracasado", "odio", "rabia", "miedo", "pánico"
]

EMOCIONES_VE = {
    "tristeza": ["triste", "tristeza", "deprimido", "abatido", "desanimado", "solo", "vacío"],
    "ansiedad": ["ansioso", "ansiedad", "nervioso", "estresado", "angustia", "preocupado", "pánico"],
    "agotamiento": ["cansado", "agotado", "fatiga", "exhausto", "rendido", "quemado", "burnout"],
    "frustracion": ["frustrado", "rabia", "enojado", "arrecho", "harto", "odio"],
    "alegria": ["feliz", "alegre", "bien", "chévere", "motivado", "positivo", "tranquilo"]
}

def analyze_text_simple(text):
    if not text or not text.strip():
        return 0.0, 0.0, 0
    text_lower = text.lower()
    neg_count = sum(1 for w in PALABRAS_NEGATIVAS if w in text_lower)
    scores = {e: sum(1 for p in palabras if p in text_lower)
              for e, palabras in EMOCIONES_VE.items()}
    total_emocional = sum(scores.values())
    alegria = scores.get("alegria", 0)
    negativo_total = sum(v for k, v in scores.items() if k != "alegria")
    if total_emocional == 0:
        polarity = 0.0
    else:
        polarity = (alegria - negativo_total) / max(total_emocional, 1)
    polarity = max(-1.0, min(1.0, round(polarity, 3)))
    words = len(text.split())
    subjectivity = min(total_emocional / max(words, 1) * 3, 1.0) if words > 0 else 0.0
    return polarity, round(subjectivity, 3), neg_count

# ================================================================
# LÓGICA DE CÁLCULO CALIBRADA 0-1 (idéntica a app.py)
# ================================================================

def normalize_va(valence_raw, arousal_raw):
    valence = ((valence_raw - 1) / 8) * 2 - 1
    arousal = (arousal_raw - 1) / 8
    return round(valence, 3), round(arousal, 3)

def score_poms(answers):
    cats = {
        "tension":    ["nervioso", "tenso", "estresado"],
        "depression": ["triste", "abatido", "desanimado"],
        "fatigue":    ["cansado", "agotado", "somnoliento"],
        "vigor":      ["activo", "energético", "alerta"]
    }
    scores = {}
    for sub, items in cats.items():
        vals = [float(answers.get(i, 3)) for i in items]
        avg = sum(vals) / len(vals)
        scores[sub] = round((avg - 1) / 4, 3)
    return scores

def calcular_puntaje(nivel, respuestas, polarity, neg_count):
    nd_score = 0.5
    valence_calc = round((polarity + 1) / 2 * 2 - 1, 3)
    arousal_calc = 0.5

    if nivel == "Primaria":
        mapa = {"😀":1,"🙂":2,"😐":3,"🙁":4,"😢":5,
                "⚡":1,"🥱":4,"😴":5}
        emo = mapa.get(respuestas.get("emocion","😐"), 3)
        ene = mapa.get(respuestas.get("energia","😐"), 3)
        conv = respuestas.get("convivencia", 3)
        seg  = respuestas.get("seguridad", 3)
        prom_raw = (emo + ene + conv + seg) / 4
        prom_norm = (prom_raw - 1) / 4
        texto_pen = neg_count * 0.05 + (1 - polarity) * 0.05
        puntaje = prom_norm + texto_pen

        nd_a = mapa.get(respuestas.get("nd_atencion","😐"), 3)
        nd_s = mapa.get(respuestas.get("nd_sensorial","😐"), 3)
        nd_o = mapa.get(respuestas.get("nd_olvidos","😐"), 3)
        nd_score = ((nd_a + nd_s + nd_o) / 3 - 1) / 4

    elif nivel == "Secundaria":
        q = respuestas
        estres_n  = (q.get("estres",3) - 1) / 4
        animo_n   = (5 - q.get("animo",3)) / 4
        presion_n = (q.get("presion",3) - 1) / 4
        sueno_n   = (5 - q.get("sueno",3)) / 4
        conexion_n= (5 - q.get("conexion",3)) / 4
        prom_norm = (estres_n + animo_n + presion_n + sueno_n + conexion_n) / 5
        texto_pen = neg_count * 0.05 + (1 - polarity) * 0.05
        puntaje = prom_norm + texto_pen

        nd_items = [q.get("nd_atencion",3), q.get("nd_sensorial",3),
                    q.get("nd_inicio",3), q.get("nd_olvidos",3), q.get("nd_social",3)]
        nd_score = (sum(nd_items) / len(nd_items) - 1) / 4

    else:  # Universidad
        q = respuestas
        estres_n  = (q.get("estres",3) - 1) / 4
        fatiga_n  = (q.get("fatiga",3) - 1) / 4
        presion_n = (q.get("presion",3) - 1) / 4
        burnout_n = (q.get("burnout",3) - 1) / 4
        suenio_n  = (5 - q.get("suenio",3)) / 4
        social_n  = (5 - q.get("social",3)) / 4
        base_norm = (estres_n + fatiga_n + presion_n + burnout_n + suenio_n + social_n) / 6

        tension_n   = (q.get("poms_tension",3) - 1) / 4
        depresion_n = (q.get("poms_depresion",3) - 1) / 4
        fatiga_p_n  = (q.get("poms_fatiga",3) - 1) / 4
        vigor_n     = (5 - q.get("poms_vigor",3)) / 4
        poms_norm = (tension_n + depresion_n + fatiga_p_n + vigor_n) / 4

        texto_pen = neg_count * 0.03 + (1 - polarity) * 0.03
        puntaje = base_norm * 0.70 + poms_norm * 0.30 + texto_pen

        vr = q.get("valence_raw", 5)
        ar = q.get("arousal_raw", 5)
        valence_calc, arousal_calc = normalize_va(vr, ar)

        nd_items = [q.get("nd_atencion",3), q.get("nd_sensorial",3), q.get("nd_inicio",3),
                    q.get("nd_olvidos",3), q.get("nd_rutinas",3), q.get("nd_social",3)]
        nd_score = (sum(nd_items) / len(nd_items) - 1) / 4

    # Asegurar que el puntaje no supere 1.0
    puntaje = min(round(puntaje, 3), 1.0)

    if puntaje >= 0.65:
        riesgo = "Alto"
    elif puntaje >= 0.40:
        riesgo = "Medio"
    else:
        riesgo = "Bajo"

    return round(puntaje, 3), riesgo, valence_calc, arousal_calc, nd_score

def classify_profile(puntaje, polarity, subj, poms_scores, neg_words):
    vigor      = poms_scores.get("vigor", 0.5)
    fatigue    = poms_scores.get("fatigue", 0.5)
    tension    = poms_scores.get("tension", 0.5)
    depression = poms_scores.get("depression", 0.5)
    if puntaje <= 0.40 and polarity >= 0 and vigor >= 0.5:
        return "Resiliente"
    if fatigue >= 0.55 and puntaje >= 0.40:
        return "Fatigado"
    if tension >= 0.45 or neg_words >= 2:
        return "Estrés"
    if subj >= 0.60 and abs(polarity) < 0.20:
        return "Inestable emocional"
    if depression >= 0.45 and polarity < -0.15:
        return "Riesgo neuro-afectivo"
    if neg_words >= 3 and puntaje >= 0.55:
        return "Riesgo neuro-afectivo"
    return "Perfil mixto"

# ================================================================
# DATOS DE PRUEBA — 20 ESTUDIANTES REALISTAS
# ================================================================

USUARIOS_DEMO = [
    # PRIMARIA — BAJO RIESGO
    {"rol":"estudiante","edad":7,"nivel":"Primaria","days_ago":7,"respuestas":{
        "emocion":"😀","energia":"⚡","convivencia":1,"seguridad":1,
        "nd_atencion":"😀","nd_sensorial":"😀","nd_olvidos":"🙂",
        "texto":"Me siento muy feliz en la escuela y juego mucho con mis amigos."
    }},
    {"rol":"estudiante","edad":8,"nivel":"Primaria","days_ago":5,"respuestas":{
        "emocion":"🙂","energia":"😐","convivencia":2,"seguridad":2,
        "nd_atencion":"🙂","nd_sensorial":"😐","nd_olvidos":"🙂",
        "texto":"Hoy estuve bien, me gusta la clase de matemáticas."
    }},
    # PRIMARIA — MEDIO RIESGO
    {"rol":"estudiante","edad":9,"nivel":"Primaria","days_ago":3,"respuestas":{
        "emocion":"🙁","energia":"🥱","convivencia":4,"seguridad":3,
        "nd_atencion":"🙁","nd_sensorial":"😐","nd_olvidos":"🙁",
        "texto":"No me gusta la tarea, me estresa mucho. Me siento nervioso a veces."
    }},
    # PRIMARIA — ALTO RIESGO
    {"rol":"estudiante","edad":10,"nivel":"Primaria","days_ago":1,"respuestas":{
        "emocion":"😢","energia":"😴","convivencia":5,"seguridad":5,
        "nd_atencion":"😢","nd_sensorial":"🙁","nd_olvidos":"😢",
        "texto":"Estoy triste y cansado. No quiero ir a la escuela, me siento solo."
    }},
    # SECUNDARIA — BAJO RIESGO
    {"rol":"estudiante","edad":13,"nivel":"Secundaria","days_ago":6,"respuestas":{
        "estres":2,"animo":2,"presion":2,"sueno":2,"autoeficacia":2,"conexion":2,
        "nd_atencion":1,"nd_sensorial":1,"nd_inicio":2,"nd_olvidos":1,"nd_social":2,
        "texto":"Me siento bien, organicé mis materias y tengo tiempo libre."
    }},
    {"rol":"estudiante","edad":14,"nivel":"Secundaria","days_ago":4,"respuestas":{
        "estres":2,"animo":2,"presion":3,"sueno":2,"autoeficacia":2,"conexion":2,
        "nd_atencion":2,"nd_sensorial":2,"nd_inicio":2,"nd_olvidos":2,"nd_social":2,
        "texto":"Todo está tranquilo, me llevo bien con mis compañeros."
    }},
    # SECUNDARIA — MEDIO RIESGO
    {"rol":"estudiante","edad":15,"nivel":"Secundaria","days_ago":3,"respuestas":{
        "estres":3,"animo":3,"presion":4,"sueno":4,"autoeficacia":3,"conexion":4,
        "nd_atencion":3,"nd_sensorial":2,"nd_inicio":3,"nd_olvidos":3,"nd_social":3,
        "texto":"Estoy cansado todo el tiempo, paso horas en el celular y no duermo bien."
    }},
    {"rol":"estudiante","edad":15,"nivel":"Secundaria","days_ago":2,"respuestas":{
        "estres":4,"animo":3,"presion":3,"sueno":4,"autoeficacia":3,"conexion":3,
        "nd_atencion":4,"nd_sensorial":3,"nd_inicio":4,"nd_olvidos":3,"nd_social":3,
        "texto":"Me cuesta concentrarme en clases, me distraigo mucho."
    }},
    # SECUNDARIA — ALTO RIESGO
    {"rol":"estudiante","edad":16,"nivel":"Secundaria","days_ago":1,"respuestas":{
        "estres":5,"animo":2,"presion":5,"sueno":5,"autoeficacia":1,"conexion":5,
        "nd_atencion":4,"nd_sensorial":3,"nd_inicio":5,"nd_olvidos":4,"nd_social":5,
        "texto":"Me siento solo. Mis amigos me ignoran y no tengo motivación para ir a clases. Estoy agotado y frustrado."
    }},
    {"rol":"estudiante","edad":17,"nivel":"Secundaria","days_ago":0,"respuestas":{
        "estres":5,"animo":1,"presion":4,"sueno":5,"autoeficacia":2,"conexion":5,
        "nd_atencion":5,"nd_sensorial":4,"nd_inicio":5,"nd_olvidos":4,"nd_social":4,
        "texto":"Estoy muy estresado y ansioso. No puedo dormir, me siento deprimido y sin energía."
    }},
    # UNIVERSIDAD — BAJO RIESGO
    {"rol":"estudiante","edad":19,"nivel":"Universidad","days_ago":7,"respuestas":{
        "estres":2,"fatiga":1,"presion":2,"burnout":1,"suenio":2,"social":2,
        "poms_tension":1,"poms_depresion":1,"poms_fatiga":2,"poms_vigor":4,
        "valence_raw":7,"arousal_raw":6,
        "nd_atencion":1,"nd_sensorial":1,"nd_inicio":2,"nd_olvidos":1,"nd_rutinas":1,"nd_social":2,
        "texto":"Terminando el semestre, me siento bien y organizado. Tengo buen apoyo de mi familia."
    }},
    {"rol":"estudiante","edad":20,"nivel":"Universidad","days_ago":5,"respuestas":{
        "estres":2,"fatiga":2,"presion":2,"burnout":1,"suenio":2,"social":2,
        "poms_tension":2,"poms_depresion":1,"poms_fatiga":2,"poms_vigor":4,
        "valence_raw":6,"arousal_raw":5,
        "nd_atencion":2,"nd_sensorial":1,"nd_inicio":2,"nd_olvidos":2,"nd_rutinas":2,"nd_social":2,
        "texto":"Me siento tranquilo, estoy avanzando bien en mis proyectos."
    }},
    # UNIVERSIDAD — MEDIO RIESGO
    {"rol":"estudiante","edad":20,"nivel":"Universidad","days_ago":4,"respuestas":{
        "estres":3,"fatiga":3,"presion":3,"burnout":3,"suenio":3,"social":3,
        "poms_tension":3,"poms_depresion":3,"poms_fatiga":3,"poms_vigor":3,
        "valence_raw":5,"arousal_raw":5,
        "nd_atencion":3,"nd_sensorial":2,"nd_inicio":3,"nd_olvidos":3,"nd_rutinas":2,"nd_social":3,
        "texto":"Más o menos, hay días buenos y días malos. Trato de mantenerme."
    }},
    {"rol":"estudiante","edad":21,"nivel":"Universidad","days_ago":3,"respuestas":{
        "estres":4,"fatiga":3,"presion":3,"burnout":3,"suenio":4,"social":3,
        "poms_tension":3,"poms_depresion":2,"poms_fatiga":3,"poms_vigor":3,
        "valence_raw":4,"arousal_raw":4,
        "nd_atencion":3,"nd_sensorial":3,"nd_inicio":3,"nd_olvidos":3,"nd_rutinas":3,"nd_social":3,
        "texto":"La universidad es exigente, a veces me siento abrumado pero lo manejo."
    }},
    {"rol":"estudiante","edad":22,"nivel":"Universidad","days_ago":2,"respuestas":{
        "estres":4,"fatiga":4,"presion":4,"burnout":3,"suenio":4,"social":3,
        "poms_tension":4,"poms_depresion":3,"poms_fatiga":4,"poms_vigor":2,
        "valence_raw":3,"arousal_raw":4,
        "nd_atencion":4,"nd_sensorial":3,"nd_inicio":4,"nd_olvidos":3,"nd_rutinas":3,"nd_social":3,
        "texto":"Estoy cansado y preocupado por los exámenes. Me cuesta concentrarme."
    }},
    # UNIVERSIDAD — ALTO RIESGO
    {"rol":"estudiante","edad":21,"nivel":"Universidad","days_ago":2,"respuestas":{
        "estres":5,"fatiga":5,"presion":5,"burnout":5,"suenio":5,"social":5,
        "poms_tension":5,"poms_depresion":4,"poms_fatiga":5,"poms_vigor":1,
        "valence_raw":2,"arousal_raw":7,
        "nd_atencion":5,"nd_sensorial":4,"nd_inicio":5,"nd_olvidos":4,"nd_rutinas":4,"nd_social":5,
        "texto":"La carga académica es excesiva, me siento atrapado y ansioso. No puedo dormir más de 4 horas. Necesito ayuda."
    }},
    {"rol":"estudiante","edad":23,"nivel":"Universidad","days_ago":1,"respuestas":{
        "estres":5,"fatiga":5,"presion":4,"burnout":5,"suenio":5,"social":4,
        "poms_tension":5,"poms_depresion":5,"poms_fatiga":5,"poms_vigor":1,
        "valence_raw":1,"arousal_raw":6,
        "nd_atencion":5,"nd_sensorial":5,"nd_inicio":5,"nd_olvidos":5,"nd_rutinas":4,"nd_social":5,
        "texto":"Estoy agotado y deprimido. No encuentro sentido a seguir estudiando. Me siento frustrado y desesperado."
    }},
    {"rol":"estudiante","edad":20,"nivel":"Universidad","days_ago":1,"respuestas":{
        "estres":5,"fatiga":4,"presion":5,"burnout":4,"suenio":5,"social":5,
        "poms_tension":4,"poms_depresion":4,"poms_fatiga":4,"poms_vigor":2,
        "valence_raw":2,"arousal_raw":5,
        "nd_atencion":4,"nd_sensorial":4,"nd_inicio":4,"nd_olvidos":4,"nd_rutinas":4,"nd_social":4,
        "texto":"Todo está mal. Estoy solo, ansioso y no puedo concentrarme en nada."
    }},
    {"rol":"estudiante","edad":22,"nivel":"Universidad","days_ago":0,"respuestas":{
        "estres":4,"fatiga":5,"presion":4,"burnout":5,"suenio":4,"social":4,
        "poms_tension":4,"poms_depresion":3,"poms_fatiga":5,"poms_vigor":2,
        "valence_raw":3,"arousal_raw":3,
        "nd_atencion":3,"nd_sensorial":3,"nd_inicio":4,"nd_olvidos":4,"nd_rutinas":3,"nd_social":3,
        "texto":"Me siento quemado. Demasiadas responsabilidades y poco descanso."
    }},
    {"rol":"estudiante","edad":19,"nivel":"Universidad","days_ago":0,"respuestas":{
        "estres":3,"fatiga":3,"presion":3,"burnout":3,"suenio":3,"social":3,
        "poms_tension":3,"poms_depresion":3,"poms_fatiga":3,"poms_vigor":3,
        "valence_raw":5,"arousal_raw":5,
        "nd_atencion":2,"nd_sensorial":2,"nd_inicio":2,"nd_olvidos":2,"nd_rutinas":2,"nd_social":2,
        "texto":"Un día normal, sin nada especial que reportar."
    }},
]

# ================================================================
# FUNCIÓN PRINCIPAL
# ================================================================

def generate_dummy_data(clean_db=False):
    print("=" * 60)
    print("🧪 GENERADOR DE DATOS DE PRUEBA — v2.0")
    print("=" * 60)

    if clean_db and os.path.exists(DB_PATH):
        print("🗑️  Eliminando base de datos existente...")
        os.remove(DB_PATH)

    init_db()
    print("✅ Base de datos inicializada\n")

    today = datetime.now()
    creados = 0

    for i, u in enumerate(USUARIOS_DEMO, 1):
        uid  = save_user(u["rol"], u["edad"], u["nivel"])
        fecha = today - timedelta(days=u["days_ago"])
        eid  = save_survey(uid, u["respuestas"], fecha)

        texto = u["respuestas"].get("texto", "")
        polarity, subjectivity, neg_count = analyze_text_simple(texto)

        puntaje, riesgo, valence_calc, arousal_calc, nd_score = calcular_puntaje(
            u["nivel"], u["respuestas"], polarity, neg_count)

        # POMS para perfil
        poms_scores = {}
        if u["nivel"] == "Universidad":
            q = u["respuestas"]
            poms_answers = {
                "nervioso": q.get("poms_tension",3), "tenso": q.get("poms_tension",3),
                "estresado": q.get("poms_tension",3), "triste": q.get("poms_depresion",3),
                "abatido": q.get("poms_depresion",3), "desanimado": q.get("poms_depresion",3),
                "cansado": q.get("poms_fatiga",3), "agotado": q.get("poms_fatiga",3),
                "somnoliento": q.get("poms_fatiga",3),
                "activo": 6-q.get("poms_vigor",3), "energético": 6-q.get("poms_vigor",3),
                "alerta": 6-q.get("poms_vigor",3)
            }
            poms_scores = score_poms(poms_answers)

        perfil = classify_profile(puntaje, polarity, subjectivity, poms_scores, neg_count)

        detalle = {
            "Perfil": perfil,
            "Polarity": polarity,
            "Subj": subjectivity,
            "NegWords": neg_count,
            "TextoSnippet": texto[:100] + "..." if len(texto) > 100 else texto,
            "Promedio": puntaje,
            "Riesgo": riesgo,
            "POMS": poms_scores,
            "VA": {"valence": valence_calc, "arousal": arousal_calc},
            "Neurodiv": {
                "atencion": round(u["respuestas"].get("nd_atencion", 3) / 5
                    if isinstance(u["respuestas"].get("nd_atencion",3), int) else 0.5, 3),
                "sensibilidad": round(u["respuestas"].get("nd_sensorial", 3) / 5
                    if isinstance(u["respuestas"].get("nd_sensorial",3), int) else 0.5, 3),
                "nd_score": round(nd_score, 3)
            }
        }

        save_result(eid, riesgo, puntaje, detalle, fecha)
        creados += 1

        emoji = {"Alto":"🔴","Medio":"🟠","Bajo":"🟢"}.get(riesgo,"⚪")
        print(f"{emoji} [{u['nivel']:12}] ID {uid:2} | {riesgo:5} | {puntaje:.3f} | {perfil}")

    print(f"\n✅ {creados} estudiantes creados correctamente")
    print("=" * 60)

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT riesgo, COUNT(*) FROM resultados GROUP BY riesgo")
    dist = dict(c.fetchall())
    c.execute("SELECT nivel, COUNT(*) FROM usuarios GROUP BY nivel")
    niveles = dict(c.fetchall())
    conn.close()

    print("📈 DISTRIBUCIÓN DE RIESGO:")
    for r, n in dist.items():
        print(f"   {r}: {n}")
    print("🏫 POR NIVEL:")
    for nv, n in niveles.items():
        print(f"   {nv}: {n}")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--clean', action='store_true', help='Limpiar BD antes de generar')
    parser.add_argument('--keep', action='store_true', help='Agregar a datos existentes')
    args = parser.parse_args()

    if args.clean:
        generate_dummy_data(clean_db=True)
    elif args.keep:
        generate_dummy_data(clean_db=False)
    else:
        if os.path.exists(DB_PATH):
            r = input("¿Limpiar base de datos existente? (si/no): ").lower()
            generate_dummy_data(clean_db=r in ['si','s','yes','y'])
        else:
            generate_dummy_data(clean_db=True)