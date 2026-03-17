# generate_dummy_data.py
import sqlite3
import json
import random
from datetime import datetime, timedelta
import os
import sys

# Añadir el directorio actual al path para importar módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from init_db import init_db, get_db_path
    DB_PATH = get_db_path()
except ImportError:
    print("⚠️ Error: No se pudo importar init_db.py")
    print("💡 Asegúrate de que init_db.py esté en el mismo directorio")
    sys.exit(1)

# ===============================================================
# UTILIDADES DE BASE DE DATOS (simplificadas para este script)
# ===============================================================

def get_conn():
    """Establece conexión a la base de datos."""
    return sqlite3.connect(DB_PATH)

def save_user(rol: str, edad: int, nivel: str):
    """Inserta un nuevo usuario y retorna su ID."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO usuarios (rol, edad, nivel) VALUES (?, ?, ?)",
        (rol, edad, nivel)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def save_survey(user_id: int, respuestas: dict, fecha: datetime):
    """Inserta una encuesta y retorna su ID."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO encuestas (usuario_id, respuestas, fecha) VALUES (?, ?, ?)",
        (user_id, json.dumps(respuestas, ensure_ascii=False), fecha.strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    survey_id = cursor.lastrowid
    conn.close()
    return survey_id

def save_result(survey_id: int, riesgo: str, puntaje: float, detalle: dict, fecha: datetime):
    """Inserta el resultado de una encuesta."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO resultados (encuesta_id, puntaje, riesgo, detalle, fecha) VALUES (?, ?, ?, ?, ?)",
        (survey_id, puntaje, riesgo, json.dumps(detalle, ensure_ascii=False), fecha.strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()

# ===============================================================
# FUNCIONES DE ANÁLISIS COMPATIBLES CON app.py
# ===============================================================

def analyze_text_advanced(text: str):
    """Analiza texto con TextBlob y cuenta palabras negativas."""
    if not text:
        return 0.0, 0.0, 0
    
    from textblob import TextBlob
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    
    # Lista de palabras negativas (debe coincidir con app.py)
    negative_words = ["triste", "cansado", "estres", "mal", "ansioso", "pelear", "ignoran", 
                      "solo", "estresado", "ansioso", "deprimido", "agotado", "preocupado", 
                      "paranoia", "frustrado", "irritable", "angustia", "abatido", "desanimado",
                      "rabioso", "somnoliento"]
    
    text_lower = text.lower()
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    return polarity, subjectivity, neg_count

def score_poms(poms_answers: dict):
    """Calcula puntajes POMS (normalizados en 0..1)."""
    scores = {}
    
    # Mapeo de categorías POMS según app.py
    poms_categories = {
        "tension": ["nervioso", "tenso", "estresado"],
        "depression": ["triste", "abatido", "desanimado"],
        "anger": ["irritable", "rabioso", "frustrado"],
        "fatigue": ["cansado", "agotado", "somnoliento"],
        "vigor": ["activo", "energético", "alerta"]
    }
    
    for category, items in poms_categories.items():
        total = 0
        count = 0
        for item in items:
            val = poms_answers.get(item, 3)  # Valor por defecto 3 (neutral)
            total += float(val)
            count += 1
        if count > 0:
            avg = total / count
            scores[category] = round((avg - 1) / 4, 3)  # Normalizar 1-5 a 0-1
    
    return scores

def normalize_va(valence_raw: int, arousal_raw: int, v_min=1, v_max=9, a_min=1, a_max=9):
    """Normaliza Valence (1..9 -> -1..1) y Arousal (1..9 -> 0..1)."""
    valence = ((valence_raw - v_min) / (v_max - v_min)) * 2 - 1
    arousal = (arousal_raw - a_min) / (a_max - a_min)
    return round(valence, 3), round(arousal, 3)

def classify_profile(promedio_encuesta: float, polarity: float, subj: float, poms_scores: dict, neg_words: int):
    """Clasifica el perfil emocional heurístico (compatible con app.py)."""
    # Esta función debe coincidir exactamente con la de app.py
    if promedio_encuesta >= 4.5 and polarity >= 0 and poms_scores.get("vigor", 0) >= 0.6:
        return "Resiliente"
    if poms_scores.get("fatigue", 0) >= 0.6 and promedio_encuesta >= 4:
        return "Fatigado"
    if promedio_encuesta >= 4 and (poms_scores.get("tension", 0) >= 0.5 or neg_words >= 3):
        return "Estrés"
    if subj >= 0.7 and abs(polarity) < 0.15:
        return "Inestable emocional"
    if (poms_scores.get("depression", 0) >= 0.5 and polarity < -0.2) or (neg_words >= 4 and promedio_encuesta >= 4.2):
        return "Riesgo neuro-afectivo"
    return "Perfil mixto"

# ===============================================================
# GENERACIÓN DE DATOS DUMMY (6 ESTUDIANTES REALISTAS)
# ===============================================================

def generate_dummy_data(clean_db=True):
    """
    Genera 6 usuarios estudiantes con encuestas realistas.
    
    Args:
        clean_db (bool): Si True, elimina la base de datos existente antes de crear datos nuevos.
    """
    print("=" * 60)
    print("🧪 GENERADOR DE DATOS DE PRUEBA")
    print("=" * 60)
    
    # 1. Inicializar o limpiar base de datos
    if clean_db and os.path.exists(DB_PATH):
        print("🗑️  Eliminando base de datos existente...")
        os.remove(DB_PATH)
    
    init_db()
    print("✅ Base de datos inicializada")
    
    # Base de tiempo (días atrás)
    today = datetime.now()
    
    # Definición de los 6 estudiantes (actualizados para coincidir con app.py)
    USERS = [
        # USUARIO 1: PRIMARIA - BAJO RIESGO (RESILIENTE)
        {
            "rol": "estudiante", 
            "edad": 7, 
            "nivel": "Primaria", 
            "days_ago": 7,
            "respuestas": {
                "emocion": "😀",
                "energia": "⚡", 
                "convivencia": 1, 
                "seguridad": 1,
                "texto": "Me siento muy feliz en la escuela y juego mucho con mis amigos. Me gusta mi profesora."
            }
        },
        
        # USUARIO 2: PRIMARIA - MEDIO RIESGO (ANSIEDAD INFANTIL)
        {
            "rol": "estudiante", 
            "edad": 8, 
            "nivel": "Primaria", 
            "days_ago": 5,
            "respuestas": {
                "emocion": "🙁",
                "energia": "🥱", 
                "convivencia": 4, 
                "seguridad": 3,
                "texto": "No me gusta la tarea, me estresa mucho. A veces me duele la panza en la escuela y me siento nervioso."
            }
        },
        
        # USUARIO 3: SECUNDARIA - MEDIO RIESGO (FATIGA/DESMOTIVACIÓN)
        {
            "rol": "estudiante", 
            "edad": 15, 
            "nivel": "Secundaria", 
            "days_ago": 3,
            "respuestas": {
                "estres": 3, 
                "animo": 3,
                "presion": 4, 
                "sueno": 5,  # Invertido: 5 = mal sueño
                "autoeficacia": 4, 
                "conexion": 5,  # Invertido: 5 = desconectado
                "texto": "Estoy muy cansado todo el tiempo, paso horas en el celular y no me da tiempo para dormir. No sé qué quiero estudiar."
            }
        },
        
        # USUARIO 4: SECUNDARIA - ALTO RIESGO (DEPRESIÓN LEVE/AISLAMIENTO)
        {
            "rol": "estudiante", 
            "edad": 16, 
            "nivel": "Secundaria", 
            "days_ago": 2,
            "respuestas": {
                "estres": 5, 
                "animo": 2,
                "presion": 5, 
                "sueno": 5,  # Invertido: 5 = mal sueño
                "autoeficacia": 1, 
                "conexion": 5,  # Invertido: 5 = desconectado
                "texto": "Me siento solo. Mis amigos me ignoran y no tengo motivación para ir a clases. Todo es difícil. No quiero salir de casa."
            }
        },
        
        # USUARIO 5: UNIVERSIDAD - ALTO RIESGO (ESTRÉS ACADÉMICO SEVERO)
        {
            "rol": "estudiante", 
            "edad": 21, 
            "nivel": "Universidad", 
            "days_ago": 1,
            "respuestas": {
                "estres": 5, 
                "fatiga": 5,
                "presion": 5, 
                "burnout": 5,
                "suenio": 5,  # Invertido: 5 = mal sueño
                "social": 5,   # Invertido: 5 = poco apoyo social
                "poms_tension": 5, 
                "poms_depresion": 3,
                "poms_fatiga": 5, 
                "poms_vigor": 2,  # Invertido: 2 = bajo vigor
                "texto": "La carga académica es excesiva, me siento atrapado y ansioso todo el tiempo. No puedo dormir más de 4 horas. Necesito ayuda."
            }
        },
        
        # USUARIO 6: UNIVERSIDAD - BAJO RIESGO (ESTABLE)
        {
            "rol": "estudiante", 
            "edad": 22, 
            "nivel": "Universidad", 
            "days_ago": 0,
            "respuestas": {
                "estres": 2, 
                "fatiga": 2,
                "presion": 2, 
                "burnout": 2,
                "suenio": 2,  # Invertido: 2 = buen sueño
                "social": 2,   # Invertido: 2 = buen apoyo social
                "poms_tension": 1, 
                "poms_depresion": 1,
                "poms_fatiga": 2, 
                "poms_vigor": 4,  # Invertido: 4 = alto vigor
                "texto": "Terminando el semestre, me siento bien y listo para las vacaciones. He podido organizar mi tiempo de manera eficiente."
            }
        }
    ]
    
    print(f"\n📋 Creando {len(USERS)} estudiantes de prueba...")
    print("-" * 60)
    
    for i, user_data in enumerate(USERS, 1):
        # 1. Registrar usuario
        user_id = save_user(user_data["rol"], user_data["edad"], user_data["nivel"])
        
        # 2. Preparar datos de la encuesta
        fecha = today - timedelta(days=user_data["days_ago"])
        
        # 3. Guardar encuesta
        survey_id = save_survey(user_id, user_data["respuestas"], fecha)
        
        # 4. Análisis y cálculo de puntaje (simplificado para dummy data)
        texto = user_data["respuestas"].get("texto", "")
        polarity, subjectivity, neg_count = analyze_text_advanced(texto)
        
        # Preparar datos POMS según nivel
        poms_data = {}
        if user_data["nivel"] == "Universidad":
            # Extraer POMS de las respuestas universitarias
            poms_data = {
                "nervioso": user_data["respuestas"].get("poms_tension", 3),
                "tenso": user_data["respuestas"].get("poms_tension", 3),
                "estresado": user_data["respuestas"].get("poms_tension", 3),
                "triste": user_data["respuestas"].get("poms_depresion", 3),
                "abatido": user_data["respuestas"].get("poms_depresion", 3),
                "desanimado": user_data["respuestas"].get("poms_depresion", 3),
                "cansado": user_data["respuestas"].get("poms_fatiga", 3),
                "agotado": user_data["respuestas"].get("poms_fatiga", 3),
                "somnoliento": user_data["respuestas"].get("poms_fatiga", 3),
                "activo": 6 - user_data["respuestas"].get("poms_vigor", 3),  # Invertido
                "energético": 6 - user_data["respuestas"].get("poms_vigor", 3),
                "alerta": 6 - user_data["respuestas"].get("poms_vigor", 3)
            }
        
        poms_scores = score_poms(poms_data)
        
        # Calcular puntaje según nivel (simplificado)
        if user_data["nivel"] == "Primaria":
            # Convertir caritas a números
            mapa_caritas = {"😀":1, "🙂":2, "😐":3, "🙁":4, "😢":5, "⚡":1, "🥱":4, "😴":5}
            emoscore = mapa_caritas.get(user_data["respuestas"].get("emocion", "😐"), 3)
            energiascore = mapa_caritas.get(user_data["respuestas"].get("energia", "😐"), 3)
            conviv = user_data["respuestas"].get("convivencia", 3)
            segur = user_data["respuestas"].get("seguridad", 3)
            
            promedio = (emoscore + energiascore + conviv + segur) / 4
            puntaje = promedio * 1.5 + neg_count * 0.5 + (1 - polarity) * 0.3
            
        elif user_data["nivel"] == "Secundaria":
            q = user_data["respuestas"]
            likerts = (q.get("estres", 3) + (6 - q.get("animo", 3)) + q.get("presion", 3) + 
                      (6 - q.get("sueno", 3)) + (6 - q.get("conexion", 3))) / 5
            puntaje = likerts * 1.2 + (1 - polarity) * 0.4 + neg_count * 0.4
            
        else:  # Universidad
            q = user_data["respuestas"]
            base = (q.get("estres", 3) + q.get("fatiga", 3) + q.get("presion", 3) + 
                   q.get("burnout", 3) + (6 - q.get("suenio", 3)) + (6 - q.get("social", 3))) / 6
            
            poms = {
                "tension": q.get("poms_tension", 3),
                "depression": q.get("poms_depresion", 3),
                "fatigue": q.get("poms_fatiga", 3),
                "vigor": (6 - q.get("poms_vigor", 3))
            }
            
            poms_score = (poms["tension"] + poms["depression"] + poms["fatigue"] + poms["vigor"]) / 4
            puntaje = base * 0.8 + poms_score * 0.8 + (1 - polarity) * 0.2 + neg_count * 0.2
        
        puntaje = round(puntaje, 3)
        
        # Clasificación de riesgo
        if puntaje >= 4.0:
            riesgo = "Alto"
        elif puntaje >= 2.5:
            riesgo = "Medio"
        else:
            riesgo = "Bajo"
        
        # Perfil emocional
        perfil = classify_profile(puntaje, polarity, subjectivity, poms_scores, neg_count)
        
        # Crear detalle compatible con app.py
        detalle = {
            "Perfil": perfil,
            "Polarity": round(polarity, 3),
            "Subj": round(subjectivity, 3),
            "NegWords": neg_count,
            "TextoSnippet": texto[:100] + "..." if len(texto) > 100 else texto,
            "Promedio": round(puntaje, 2),
            "Riesgo": riesgo,
            "POMS": poms_scores,
            "VA": {"valence": 0.0, "arousal": 0.5}  # Placeholder para dummy data
        }
        
        # 5. Guardar resultado
        save_result(survey_id, riesgo, puntaje, detalle, fecha)
        
        print(f"✅ Estudiante {i}: ID {user_id} ({user_data['nivel']})")
        print(f"   📅 Fecha: {fecha.strftime('%Y-%m-%d')}")
        print(f"   📊 Riesgo: {riesgo} | Puntaje: {puntaje:.2f}")
        print(f"   👤 Perfil: {perfil}")
        print(f"   💬 Texto: {texto[:50]}..." if len(texto) > 50 else f"   💬 Texto: {texto}")
        print()
    
    # Mostrar resumen final
    print("=" * 60)
    print("📊 RESUMEN DE DATOS CREADOS")
    print("=" * 60)
    
    conn = get_conn()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    total_usuarios = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM encuestas")
    total_encuestas = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM resultados")
    total_resultados = cursor.fetchone()[0]
    
    print(f"👥 Usuarios creados: {total_usuarios}")
    print(f"📝 Encuestas creadas: {total_encuestas}")
    print(f"📊 Resultados creados: {total_resultados}")
    
    # Distribución de riesgo
    print("\n📈 DISTRIBUCIÓN DE RIESGO:")
    cursor.execute("SELECT riesgo, COUNT(*) FROM resultados GROUP BY riesgo ORDER BY riesgo")
    for riesgo, count in cursor.fetchall():
        print(f"   {riesgo}: {count}")
    
    # Distribución por nivel
    print("\n🏫 DISTRIBUCIÓN POR NIVEL:")
    cursor.execute("""
        SELECT nivel, COUNT(*) 
        FROM usuarios 
        GROUP BY nivel 
        ORDER BY CASE nivel
            WHEN 'Primaria' THEN 1
            WHEN 'Secundaria' THEN 2
            WHEN 'Universidad' THEN 3
            ELSE 4
        END
    """)
    for nivel, count in cursor.fetchall():
        print(f"   {nivel}: {count}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✨ DATOS DE PRUEBA CREADOS EXITOSAMENTE!")
    print("=" * 60)
    print("\n💡 Siguientes pasos:")
    print("1. Ejecuta: streamlit run app.py")
    print("2. Usa la clave docente: 'admin123'")
    print("3. Prueba todas las funcionalidades")
    print("\n🔍 Para ver los datos: python ver_db.py")

if __name__ == "__main__":
    # Preguntar si limpiar la BD existente
    import argparse
    parser = argparse.ArgumentParser(description='Generador de datos de prueba')
    parser.add_argument('--keep', action='store_true', help='Mantener datos existentes (no limpiar BD)')
    parser.add_argument('--clean', action='store_true', help='Limpiar BD antes de generar datos')
    
    args = parser.parse_args()
    
    if args.keep:
        generate_dummy_data(clean_db=False)
    elif args.clean:
        generate_dummy_data(clean_db=True)
    else:
        # Preguntar interactivamente
        if os.path.exists(DB_PATH):
            respuesta = input("¿Deseas limpiar la base de datos existente? (si/no): ").lower()
            if respuesta in ['si', 's', 'yes', 'y']:
                generate_dummy_data(clean_db=True)
            else:
                print("⚠️  Los datos nuevos se añadirán a los existentes.")
                generate_dummy_data(clean_db=False)
        else:
            generate_dummy_data(clean_db=True)