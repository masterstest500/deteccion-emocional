import os
import streamlit as st
import sqlite3
import json
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from textblob import TextBlob
import io
import zipfile
import typing as t
import base64
import random
import time
import streamlit.components.v1 as components
import math
import hashlib  # NEW: For password security

from database import save_user, save_survey, save_result

# ================================================================
# CONFIGURACIÓN GENERAL Y RUTAS DINÁMICAS (FASE 1)
# ================================================================

# 1. Configuración de página (Debe ser lo primero)
st.set_page_config(
    page_title="Plataforma de Detección Temprana", 
    page_icon="💡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Rutas dinámicas: Esto permite que el proyecto funcione en cualquier PC
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "images")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Crear carpetas si no existen
for folder in [ASSETS_DIR, DATA_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# 3. Importación de DB (Alineado con tus archivos externos)
from init_db import get_db_path, init_db

DB_PATH = get_db_path()
# LOGO_PATH ahora es relativo, asegúrate de poner tu Logo.png en la carpeta 'assets'
LOGO_PATH = os.path.join(BASE_DIR, "images", "Logo.png") 

LOADER_SECONDS = 5
AUDIO_FILE_PATH = "static/clic.wav"

# Inicializar base de datos
init_db()

# ReportLab (opcional)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

# Scikit-learn (opcional)
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# ================================================================
# UTILIDADES DE SEGURIDAD Y GENERALES (FASE 1)
# ================================================================

def generar_hash(password: str):
    """Convierte texto plano en un código seguro (SHA-256)."""
    return hashlib.sha256(password.encode()).hexdigest()

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def img_to_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""

# [EL RESTO DE TUS UTILIDADES: df_to_csv_bytes, export_all_tables_zip_bytes, etc., SE MANTIENEN IGUAL]
def df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")

def export_all_tables_zip_bytes():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for table in ["usuarios", "encuestas", "resultados"]:
            conn = get_conn()
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                z.writestr(f"{table}.csv", df.to_csv(index=False))
            except Exception:
                z.writestr(f"{table}.csv", "/* Sin datos */")
            finally:
                conn.close()
    buffer.seek(0)
    return buffer.getvalue()

def safe_json_load(s):
    try:
        return json.loads(s)
    except Exception:
        return {}

def safe_float(value, default=0.0):
    try:
        return float(value) 
    except (TypeError, ValueError):
        return default

# ================================================================
# INICIALIZACIÓN DE ESTADOS DE SESIÓN (SIN CAMBIOS)
# ================================================================

if "landing_done" not in st.session_state:
    st.session_state.landing_done = False
if "loader_shown" not in st.session_state:
    st.session_state.loader_shown = False
if "consentimiento" not in st.session_state:
    st.session_state.consentimiento = False
if "nivel_usuario" not in st.session_state:
    st.session_state.nivel_usuario = "Primaria"
if "clave_docente" not in st.session_state:
    st.session_state.clave_docente = ""
if "uid" not in st.session_state:
    st.session_state.uid = None
if "docente_activo" not in st.session_state:
    st.session_state.docente_activo = False
if "menu_estudiante" not in st.session_state:
    st.session_state.menu_estudiante = "Registrar encuesta"
if "menu_docente" not in st.session_state:
    st.session_state.menu_docente = "Panel docente"
if "logo_clicked" not in st.session_state:
    st.session_state.logo_clicked = False

# [AQUÍ SIGUE TU CSS Y EL RESTO DE TU CÓDIGO ORIGINAL...]

# Estados de UI
if "logo_clicked" not in st.session_state:
    st.session_state.logo_clicked = False

# ================================================================
# CSS PARA OCULTAR ELEMENTOS NO DESEADOS DE STREAMLIT
# ================================================================
st.markdown("""
    <style>
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {background: transparent;}
            
    /* SIDEBAR: FORZAR APERTURA Y COLOR OSCURO */
    [data-testid="stSidebar"] {
        transform: none !important;
        visibility: visible !important;
        width: 210px !important;
        margin-left: 0px !important;
        background: #383838 !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        background: #383838 !important;
    }
            
    /* Contenido principal */
    .main {
        padding-left: 210px !important;
        overflow-y: hidden !important;
    }
    
    /* Ocultar botones de colapsar */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }
            
    /* Imágenes */
    .stImage img {
        max-width: 100%;
        height: auto;
        pointer-events: none;
    }
            
    /* Ocultar alertas de rerun */
    .stAlert {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# ================================================================
# UTILIDADES GENERALES
# ================================================================

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def img_to_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return ""

def df_to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")

def export_all_tables_zip_bytes():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for table in ["usuarios", "encuestas", "resultados"]:
            conn = get_conn()
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                z.writestr(f"{table}.csv", df.to_csv(index=False))
            except Exception:
                z.writestr(f"{table}.csv", "/* Sin datos */")
            finally:
                conn.close()
    buffer.seek(0)
    return buffer.getvalue()

def safe_json_load(s):
    try:
        return json.loads(s)
    except Exception:
        return {}

def safe_float(value, default=0.0):
    """Convierte un valor a flotante de forma segura."""
    try:
        return float(value) 
    except (TypeError, ValueError):
        return default

# ================================================================
# ANÁLISIS EMOCIONAL (TextBlob + conteo simple)
# ================================================================

PALABRAS_NEGATIVAS = [
    "triste","mal","cansado","solo","estresado","ansioso","deprimido",
    "agotado","preocupado","paranoia","frustrado","irritable","angustia"
]

def analyze_text_advanced(text: str) -> t.Tuple[float, float, int]:
    """
    Devuelve: (polarity [-1..1], subjectivity [0..1], neg_count)
    """
    if not text or not text.strip():
        return 0.0, 0.0, 0
    blob = TextBlob(text)
    polarity = float(blob.sentiment.polarity)
    subjectivity = float(blob.sentiment.subjectivity)
    text_lower = text.lower()
    neg_count = sum(1 for w in PALABRAS_NEGATIVAS if w in text_lower)
    return polarity, subjectivity, neg_count

# ================================================================
# POMS reducido (Profile of Mood States) — items seleccionados
# ================================================================

POMS_ITEMS = {
    "tension": ["nervioso", "tenso", "estresado"],
    "depression": ["triste", "abatido", "desanimado"],
    "anger": ["irritable", "rabioso", "frustrado"],
    "fatigue": ["cansado", "agotado", "somnoliento"],
    "vigor": ["activo", "energético", "alerta"]
}

def score_poms(answers_block: dict) -> dict:
    """
    answers_block: dict con ítems POMS (palabra: valor 1-5)
    Devuelve dict con puntajes por subescala normalizados (0..1)
    """
    scores = {}
    for sub, items in POMS_ITEMS.items():
        s = 0
        count = 0
        for item in items:
            val = answers_block.get(item)
            if val is None:
                # si faltan valores, asumimos 3 neutro para prevenir NaN
                val = 3
            s += float(val)
            count += 1
        # Normalizamos: cada ítem 1..5 -> subescala promedio 1..5 -> llevamos a 0..1
        avg = s / max(1, count)
        scores[sub] = round((avg - 1) / 4, 3)
    return scores

# ================================================================
# Valence-Arousal (VA) exposición simple
# ================================================================

def normalize_va(valence_raw: int, arousal_raw: int, v_min=1, v_max=9, a_min=1, a_max=9):
    # valence: 1..9 -> -1..1
    valence = ((valence_raw - v_min) / (v_max - v_min)) * 2 - 1
    arousal = (arousal_raw - a_min) / (a_max - a_min)
    return round(valence,3), round(arousal,3)

# ================================================================
# Perfiles emocionales (simple heuristics, NO DIAGNÓSTICO)
# ================================================================

def classify_profile(promedio_encuesta: float, polarity: float, subj: float, poms_scores: dict, neg_words:int):
    """
    Retorna un perfil simple: 'Resiliente', 'Estrés', 'Fatigado', 'Inestable', 'Riesgo neuro-afectivo'
    * Esto es heurístico y orientativo, no diagnóstico clínico.
    """
    # heurísticas simples
    # prioridad a combinaciones más claras
    if promedio_encuesta >= 4.5 and polarity >= 0 and poms_scores.get("vigor",0) >= 0.6:
        return "Resiliente"
    if poms_scores.get("fatigue",0) >= 0.6 and promedio_encuesta >= 4:
        return "Fatigado"
    if promedio_encuesta >= 4 and (poms_scores.get("tension",0) >= 0.5 or neg_words >= 3):
        return "Estrés"
    if subj >= 0.7 and abs(polarity) < 0.15:
        return "Inestable emocional"
    if (poms_scores.get("depression",0) >= 0.5 and polarity < -0.2) or (neg_words >= 4 and promedio_encuesta >= 4.2):
        return "Riesgo neuro-afectivo"
    return "Perfil mixto"

# ================================================================
# FASE 1 — Sistema de encuestas por nivel
# ================================================================

def get_questions_by_level(nivel: str):
    """
    Devuelve la estructura de preguntas según el nivel seleccionado.
    """
    if nivel == "Primaria":
        return [
            {"id": "emocion", "tipo": "carita", "texto": "¿Cómo te sientes hoy?",
             "opciones": ["😀","🙂","😐","🙁","😢"]},

            {"id": "energia", "tipo": "carita", "texto": "¿Cómo está tu energía?",
             "opciones": ["⚡","🙂","😐","🥱","😴"]},

            {"id": "convivencia", "tipo": "likert", "texto": "¿Te fue bien con tus compañeros hoy?"},

            {"id": "seguridad", "tipo": "likert", "texto": "¿Te sentiste seguro en clase o en recreo?"},

            {"id": "texto", "tipo": "texto", "texto": "¿Quieres contarme algo más? (opcional)"}
        ]

    elif nivel == "Secundaria":
        return [
            {"id": "estres", "tipo": "likert", "texto": "¿Cuánto estrés académico sientes?"},
            {"id": "animo", "tipo": "likert", "texto": "¿Cómo describirías tu estado de ánimo?"},
            {"id": "presion", "tipo": "likert", "texto": "¿Sientes presión social o comparaciones?"},
            {"id": "sueno", "tipo": "likert", "texto": "¿Cómo ha sido tu sueño estos días?"},
            {"id": "autoeficacia", "tipo": "likert", "texto": "¿Te sientes capaz de manejar tus tareas?"},
            {"id": "conexion", "tipo": "likert", "texto": "¿Te sientes conectado con otras personas?"},
            {"id": "texto", "tipo": "texto", "texto": "Describe cómo te has sentido (opcional)"}
        ]

    else:  # UNIVERSIDAD
        return [
            {"id": "estres", "tipo": "likert", "texto": "Nivel de estrés académico"},
            {"id": "fatiga", "tipo": "likert", "texto": "Fatiga mental reciente"},
            {"id": "presion", "tipo": "likert", "texto": "Autoexigencia y perfeccionismo"},
            {"id": "burnout", "tipo": "likert", "texto": "Sensación de agotamiento (burnout)"},
            {"id": "suenio", "tipo": "likert", "texto": "Calidad del sueño"},
            {"id": "social", "tipo": "likert", "texto": "Conexión social / apoyo"},
            {"id": "poms_tension", "tipo": "likert", "texto": "Tensión (POMS)"},
            {"id": "poms_depresion", "tipo": "likert", "texto": "Depresión (POMS)"},
            {"id": "poms_fatiga", "tipo": "likert", "texto": "Fatiga (POMS)"},
            {"id": "poms_vigor", "tipo": "likert", "texto": "Vigor (POMS, invertido)"},
            {"id": "texto", "tipo": "texto", "texto": "Describe cómo te sientes (opcional)"}
        ]

def render_questions_by_level(questions):
    respuestas = {}
    for q in questions:
        if q["tipo"] == "likert":
            respuestas[q["id"]] = st.slider(q["texto"], 1, 5, 3)

        elif q["tipo"] == "carita":
            respuestas[q["id"]] = st.select_slider(q["texto"],
                                                   options=q["opciones"],
                                                   value=q["opciones"][2])

        elif q["tipo"] == "texto":
            respuestas[q["id"]] = st.text_area(q["texto"], height=100)

    return respuestas

def process_results_by_level(nivel, respuestas, analisis_texto):
    polarity, subjectivity, neg_count = analisis_texto

    # -------------------------
    # PRIMARIA
    # -------------------------
    if nivel == "Primaria":
        # Convertir caritas a números
        mapa_caritas = {"😀":1,"🙂":2,"😐":3,"🙁":4,"😢":5,
                        "⚡":1,"🙂":2,"😐":3,"🥱":4,"😴":5}

        emoscore = mapa_caritas.get(respuestas["emocion"], 3)
        energiascore = mapa_caritas.get(respuestas["energia"], 3)

        conviv = respuestas["convivencia"]
        segur = respuestas["seguridad"]

        promedio = (emoscore + energiascore + conviv + segur) / 4

        puntaje = promedio * 1.5 + neg_count * 0.5 + (1 - polarity) * 0.3

    # -------------------------
    # SECUNDARIA
    # -------------------------
    elif nivel == "Secundaria":
        q = respuestas
        likerts = (q["estres"] + (6-q["animo"]) + q["presion"] + (6-q["sueno"]) + (6-q["conexion"])) / 5

        puntaje = likerts * 1.2 + (1 - polarity) * 0.4 + neg_count * 0.4

    # -------------------------
    # UNIVERSIDAD
    # -------------------------
    else:
        q = respuestas

        base = (
            q["estres"] + q["fatiga"] + q["presion"] + q["burnout"] +
            (6-q["suenio"]) + (6-q["social"])
        ) / 6

        poms = {
            "tension": q["poms_tension"],
            "depression": q["poms_depresion"],
            "fatigue": q["poms_fatiga"],
            "vigor": (6-q["poms_vigor"])
        }

        poms_score = (poms["tension"] + poms["depression"] + poms["fatigue"] + poms["vigor"]) / 4

        puntaje = base * 0.8 + poms_score * 0.8 + (1 - polarity) * 0.2 + neg_count * 0.2

    # Clasificación final
    if puntaje >= 4.0:
        riesgo = "Alto"
    elif puntaje >= 2.5:
        riesgo = "Medio"
    else:
        riesgo = "Bajo"

    return puntaje, riesgo

# ================================================================
# LANDING PAGE
# ================================================================

def show_landing_page(logo_base64):
    # 1. Carga invisible del audio
    st.audio("static/clic.wav", format='audio/wav', start_time=0) 
    
    # 2. Estilos generales (Ocultar elementos nativos de Streamlit)
    st.markdown("""
    <style>
    /* Ocultar elementos de Streamlit (menú, footer, header) */
    #MainMenu, footer, header { visibility: hidden; }
    .stApp {background: transparent;}
            
    /* --------------------------------------------------------------------- */
    /* SOLUCIÓN 1: OCULTAR REPRODUCTOR DE AUDIO (PERO FUNCIONAL) */
    /* --------------------------------------------------------------------- */
    [data-testid="stAudio"] {
        display: none !important; /* Esto lo oculta de la vista sin quitar la funcionalidad */
    }

    /* --------------------------------------------------------------------- */
    /* SOLUCIÓN 2: SIDEBAR (VISIBILIDAD Y COLOR OSCURO DEFINITIVO) */
    /* --------------------------------------------------------------------- */
    
    /* Contenedor Externo: Fuerza visibilidad, posición, y aplica el color de fondo */
    [data-testid="stSidebar"] {
        /* Reglas de visibilidad y posición forzada */
        transform: none !important; 
        visibility: visible !important; 
        width: 210px !important; 
        margin-left: 0px !important; 
        
        /* 💡 CORRECCIÓN DE COLOR: Aplica color oscuro var(--bg-2) */
        background-color: var(--bg-2) !important;
        background: var(--bg-2) !important;
    } 
            
    /* Contenedor Interno: Sobreescribe el fondo blanco que puede venir de load.css */
    [data-testid="stSidebar"] > div:first-child {
        background: var(--bg-2) !important;
    }
    
    /* Contenido Principal: Crea el espacio para la sidebar y oculta scroll general */
    .main {
        padding-left: 210px !important; 
        overflow-y: hidden !important; 
    }

    /* Oculta todos los botones de colapsar */
    [data-testid="stSidebarCollapseButton"], 
    [data-testid="collapsedControl"] {
        display: none !important;
    }
            
    /* --------------------------------------------------------------------- */
    /* REGLAS ESTÉTICAS ADICIONALES */
    /* --------------------------------------------------------------------- */
    
    /* Ocultar el botón de fullscreen de la imagen y prevenir zoom */
    .stImage img {
        max-width: 100%;
        height: auto;
        pointer-events: none;
    }
            
    /* Ocultar mensajes de st.rerun() */
    .stAlert {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)
    
    # 3. Contenido de la landing page dentro de un IFRAME aislado (Full Screen)
    html_content = f"""
        <html>
        <head>
            <style>
            /* Estilos para la toma de control de pantalla completa (100vw, 100vh) */
            body {{
                margin: 0;
                padding: 0;
                overflow: hidden;
            }}
            .landing-container {{
                position: fixed; 
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: linear-gradient(135deg, #0a2a43 0%, #0e4d92 50%, #1976d2 100%);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                color: white;
                text-align: center;
                z-index: 9999;
                padding: 2rem;
            }}
            .logo-container {{
                margin-bottom: 2rem;
                cursor: pointer;
                transition: all 0.5s ease;
            }}
            .logo-img {{
                width: 230px;  /* CAMBIO 1: De 200px a 230px (15% más grande) */
                height: auto;
                /* Efecto de brillo detrás */
                filter: drop-shadow(0 0 20px rgba(79, 195, 247, 0.8)); 
                margin-bottom: 1.5rem;
                transition: all 0.3s ease;
                animation: logoGlow 3s ease-in-out infinite;
            }}
            .logo-img:hover {{
                transform: scale(1.05);
                filter: drop-shadow(0 0 30px rgba(79, 195, 247, 1));
            }}
            .logo-img:active {{
                transform: scale(0.95);
            }}
            .title {{
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 1rem;
                text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                animation: fadeInUp 1s ease-out;
            }}
            .subtitle {{
                font-size: 1.2rem;
                margin-bottom: 3rem;
                opacity: 0.9;
                max-width: 600px;
                animation: fadeInUp 1s ease-out 0.3s both;
            }}
            /* Partículas y Animaciones (Se mantienen) */
            .particle {{
                position: absolute;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                animation: float 6s ease-in-out infinite;
            }}
            .particle:nth-child(1) {{ width: 8px; height: 8px; top: 20%; left: 10%; animation-delay: 0s; }}
            .particle:nth-child(2) {{ width: 12px; height: 12px; top: 60%; left: 80%; animation-delay: 1s; }}
            .particle:nth-child(3) {{ width: 6px; height: 6px; top: 80%; left: 20%; animation-delay: 2s; }}
            .particle:nth-child(4) {{ width: 10px; height: 10px; top: 30%; left: 70%; animation-delay: 3s; }}
            .particle:nth-child(5) {{ width: 7px; height: 7px; top: 70%; left: 40%; animation-delay: 4s; }}
            
            @keyframes logoGlow {{
                0%, 100% {{ filter: drop-shadow(0 0 20px rgba(79, 195, 247, 0.8)); }}
                50% {{ filter: drop-shadow(0 0 30px rgba(79, 195, 247, 1)) drop-shadow(0 0 40px rgba(79, 195, 247, 0.4)); }}
            }}
            @keyframes fadeInUp {{
                from {{ opacity: 0; transform: translateY(30px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            @keyframes float {{
                0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
                50% {{ transform: translateY(-20px) rotate(180deg); }}
            }}
            @keyframes pulse {{
                0% {{ transform: scale(1); }}
                50% {{ transform: scale(1.1); }}
                100% {{ transform: scale(1); }}
            }}
            @keyframes fadeOut {{
                to {{ opacity: 0; transform: scale(0.95); }}
            }}
            </style>
        </head>
        <body>
            <div class="landing-container">
                <div class="particle"></div>
                <div class="particle"></div>
                <div class="particle"></div>
                <div class="particle"></div>
                <div class="particle"></div>
                
                <div class="logo-container" id="logoClickable">
                    <img class="logo-img" src="data:image/png;base64,{logo_base64}" alt="Logo Plataforma" onclick="handleLogoClick()">
                </div>
                <div class="title">Plataforma de Prevención Cognitiva y Emocional</div>
                <div class="subtitle">Haz clic en el cerebro para iniciar la evaluación</div>
            </div>
            
            <script>
            function handleLogoClick() {{
                // Buscamos el elemento de audio en el documento padre (Streamlit)
                const audioPlayer = window.parent.document.querySelector('audio');
                
                if (audioPlayer) {{
                    audioPlayer.currentTime = 0; 
                    audioPlayer.play().catch(e => console.error('Error reproduciendo audio:', e));
                }}
                
                const logo = document.querySelector('.logo-img');
                const container = document.querySelector('.landing-container');
                
                logo.style.animation = 'pulse 0.5s ease-out';
                container.style.animation = 'fadeOut 0.8s ease-out forwards';
                
                // Enviar evento a Streamlit para pasar a la siguiente pantalla (loading)
                setTimeout(() => {{
                    const invisibleButton = window.parent.document.querySelector('[data-testid="stButton"] button');

                    if (invisibleButton) {{
                        invisibleButton.click();
                    }} else {{
                        console.error("No se encontró el botón de transición invisible.");
                    }}
                }}, 1200);  /* CAMBIO 2: Llave de cierre corregida aquí */
            }}
            </script>
        </body>
        </html>
    """
    
    # 4. Renderizar el IFRAME
    components.html(
    html_content, 
    height=700, 
    scrolling=False 
)

# 5. Botón de Transición Invisible (Activado por JS)
st.button(
    "START_TRANSITION", 
    on_click=lambda: setattr(st.session_state, 'landing_done', True),
    key="transition_btn",
    help="hidden_transition_button"  
)

# 6. Hide Transition Button ONLY (Ultimate Solution)
st.markdown("""
<style>
/* El botón de transición usa key="transition_btn" y title="hidden_transition_button" */
/* Apuntamos al botón dentro de su contenedor de Streamlit (data-testid="stButton") */
div[data-testid="stButton"] button[title="hidden_transition_button"] {
    /* Ocultamiento agresivo */
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
    position: absolute !important;
    top: -9999px !important;
    left: -9999px !important;
    opacity: 0 !important;
    pointer-events: none !important;
    z-index: -9999 !important;
}

/* Aseguramos que los demás botones NO se vean afectados */
.stButton button:not([title="hidden_transition_button"]) {
    visibility: visible !important;
    display: inline-block !important;
}
</style>
""", unsafe_allow_html=True)

# ================================================================
# LOADER MEJORADO
# ================================================================

FRASES_LOADER = [
    "El cerebro no distingue entre imaginación y realidad.",
    "Tu historia no define tu destino.",
    "Conocerse a sí mismo es el principio de toda sabiduría. Aristóteles",
    "La mente es como un paracaídas: solo funciona si se abre.",
    "Todo aprendizaje tiene una base emocional. Platón",
    "La resiliencia es la capacidad de sanar en la adversidad.",
    "Sigue a tu corazón, pero lleva contigo a tu cerebro. Alfred Adler",
    "Lo que niegas te somete; lo que aceptas te transforma. C.G. Jung",
    "El equilibrio es la fuerza de tolerar emociones dolorosas. Melanie Klein",
    "La atención es la llave del cambio.",
]

def show_loading_screen(logo_base64: str, frase: str, seconds: int = 3):
    """Loader mejorado que ocupa toda la pantalla como la landing"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  html,body {{
    height: 100%;
    margin: 0;
    overflow: hidden;
  }}
  .loader-wrap {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    background: linear-gradient(135deg, #2E6FF2 0%, #7B5DFA 100%);
    z-index: 9999;
    animation: fadeIn 0.5s ease-out;
  }}
  .content {{
    max-width: 500px;
    padding: 2rem;
  }}
  .logo-img {{
    width: 150px;
    height: auto;
    margin-bottom: 2rem;
    display: block;
    margin-left: auto;
    margin-right: auto;
    border-radius: 10px;
    animation: logoPulse 2s ease-in-out infinite;
  }}
  .loader-text {{
    font-size: 1.3rem;
    color: white;
    margin-bottom: 2rem;
    font-weight: 500;
    animation: fadeInUp 0.8s ease-out;
  }}
  .progress-container {{
    width: 100%;
    max-width: 400px;
    height: 8px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    margin: 0 auto 1rem auto;
    overflow: hidden;
  }}
  .progress-bar {{
    width: 0%;
    height: 100%;
    background: linear-gradient(90deg, #FFD93D, #FF6B6B);
    border-radius: 10px;
    transition: width 0.3s ease;
  }}
  .loader-subtext {{
    font-size: 0.9rem;
    color: rgba(255, 255, 255, 0.8);
    animation: fadeInUp 1s ease-out;
  }}
  
  @keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
  }}
  
  @keyframes fadeInUp {{
    from {{ 
        opacity: 0; 
        transform: translateY(20px); 
    }}
    to {{ 
        opacity: 1; 
        transform: translateY(0); 
    }}
  }}
  
  @keyframes logoPulse {{
    0%, 100% {{ transform: scale(1); opacity: 0.9; }}
    50% {{ transform: scale(1.05); opacity: 1; }}
  }}
</style>
</head>
<body>
    <div class="loader-wrap">
        <div class="content">
            <img class="logo-img" src="data:image/png;base64,{logo_base64}" />
            <div class="loader-text">{frase}</div>
            <div class="progress-container">
                <div class="progress-bar" id="loader-progress"></div>
            </div>
            <div class="loader-subtext">Inicializando plataforma...</div>
        </div>
    </div>
    
    <script>
        let duration = {seconds};
        let progress = document.getElementById("loader-progress");
        let startTime = Date.now();
        
        function updateProgress() {{
            let elapsed = (Date.now() - startTime) / 1000;
            let percentage = Math.min((elapsed / duration) * 100, 100);
            progress.style.width = percentage + "%";
            
            if (percentage < 100) {{
                requestAnimationFrame(updateProgress);
            }}
        }}
        updateProgress();
    </script>
</body>
</html>
"""
    components.html(html, height=600, scrolling=False)

# ================================================================
# FUNCIÓN DE LOGOUT
# ================================================================

def logout():
    """Función de logout mejorada - Solo limpia estados de docente"""
    # Solo limpiar estados relacionados con docente
    docente_keys = ['docente_activo', 'docente', 'logged_in_user_id']
    for key in docente_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Mantener estados esenciales
    essential_keys = ['landing_done', 'loader_shown', 'consentimiento', 'nivel_usuario', 'uid']
    for key in essential_keys:
        if key not in st.session_state:
            # Restaurar estados esenciales si se perdieron
            if key == 'consentimiento':
                st.session_state[key] = False
            elif key == 'nivel_usuario':
                st.session_state[key] = "Primaria"
    
    # Usar bandera para rerun seguro
    st.session_state.needs_rerun = True

# ================================================================
# FUNCIÓN AUXILIAR DE REPORTE INDIVIDUAL
# ================================================================

def show_single_report(riesgo, perfil, detalle_param =None):
    """Muestra un reporte profesional basado en riesgo, perfil y detalle técnico"""
    st.title("✅ Reporte de Análisis Emocional")
    
    # ================================================================
    # 1. DEFINIR Y VALIDAR LOS DATOS DE UNA VEZ POR TODAS
    # ================================================================
    # Inicializar diccionario vacío como fallback
    datos = {}
    
    # Procesar el parámetro que nos llega (puede ser None, string o dict)
    if detalle_param is not None:
        if isinstance(detalle_param, str):
            # Si es string, intentar convertirlo a JSON
            try:
                datos = json.loads(detalle_param)
            except:
                datos = {}  # Si falla, usar diccionario vacío
        elif isinstance(detalle_param, dict):
            # Si ya es diccionario, usarlo directamente
            datos = detalle_param
        else:
            # Cualquier otro tipo, usar vacío
            datos = {}
    
    # ================================================================
    # 2. EXTRAER TODAS LAS MÉTRICAS CON VALORES POR DEFECTO
    # ================================================================
    # Extraer con .get() para evitar KeyError si alguna clave falta
    valence = datos.get("VA", {}).get("valence", 0.0)
    arousal = datos.get("VA", {}).get("arousal", 0.5)
    polarity = datos.get("Polarity", 0.0)
    subjectivity = datos.get("Subj", 0.0)
    neg_words = datos.get("NegWords", 0)
    poms_tension = datos.get("POMS", {}).get("tension", 0.0)
    poms_fatigue = datos.get("POMS", {}).get("fatigue", 0.0)
    promedio = datos.get("Promedio", 0.0)
    texto_snippet = datos.get('TextoSnippet', '')
    
    # El resto de tu código (200+ líneas) QUEDA EXACTAMENTE IGUAL...
    # Porque ya usa 'riesgo', 'perfil', 'perfil_mapeado', etc.
    
    # ================================================================
    # 3. CONFIGURACIÓN VISUAL PROFESIONAL
    # ================================================================
    # Mapear nombres de perfiles para consistencia
    perfil_mapeado = {
        "Estrés": "Ansioso/Tenso",
        "Resiliente": "Resiliente",
        "Fatigado": "Fatigado", 
        "Inestable emocional": "Inestable emocional",
        "Riesgo neuro-afectivo": "Riesgo neuro-afectivo",
        "Perfil mixto": "Perfil mixto"
    }.get(perfil, perfil)  # Usar el original si no está en el mapa
    
    # Configurar colores y emojis según riesgo
    config_riesgo = {
        "Alto": {"color": "#ff4444", "emoji": "🔴", "color_name": "rojo"},
        "Medio": {"color": "#ffaa44", "emoji": "🟠", "color_name": "naranja"},
        "Bajo": {"color": "#44cc44", "emoji": "🟢", "color_name": "verde"}
    }
    
    riesgo_config = config_riesgo.get(riesgo, {"color": "#666666", "emoji": "⚪", "color_name": "gris"})
    
    # Emojis por perfil emocional
    emojis_perfil = {
        "Resiliente": "🛡️",
        "Ansioso/Tenso": "😰", 
        "Fatigado": "😴",
        "Inestable emocional": "🎭",
        "Riesgo neuro-afectivo": "🧠",
        "Perfil mixto": "🌈"
    }
    
    emoji_perfil = emojis_perfil.get(perfil_mapeado, "📊")
    
    # ================================================================
    # 4. ENCABEZADO DEL REPORTE
    # ================================================================
    st.markdown(f"""
    ### {riesgo_config['emoji']} **Nivel de Riesgo:** <span style='color:{riesgo_config['color']}; font-weight:bold;'>{riesgo.upper()}</span>
    ### {emoji_perfil} **Perfil Emocional:** {perfil_mapeado}
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ================================================================
    # 5. ANÁLISIS PSICOLÓGICO PROFESIONAL
    # ================================================================
    st.subheader("🔬 Análisis Psicológico y Neurocientífico")
    
    # DICCIONARIO COMPLETO DE RECOMENDACIONES (DEFINIDO AQUÍ, NO AFUERA)
    recomendaciones_profesionales = {
        "Resiliente": {
            "alto": {
                "titulo": "🛡️ Resiliencia bajo Presión Extrema",
                "analisis": f"**Análisis Psicológico:** Aunque tu perfil muestra capacidad de adaptación (Resiliente), el nivel de riesgo ALTO ({promedio:.2f}) indica que estás enfrentando desafíos que superan temporalmente tus recursos de afrontamiento habituales.\n\n**Bases Neurocientíficas:** La resiliencia depende de la conectividad prefrontal-ínsula. Bajo estrés crónico, esta conectividad puede verse comprometida, afectando la regulación emocional.",
                "recomendaciones": [
                    "💡 **Intervención Inmediata:** Programa descansos obligatorios cada 90 minutos",
                    "🧠 **Neuroplasticidad Dirigida:** 15 minutos diarios de aprendizaje novedoso",
                    "🫀 **Coherencia Cardíaca:** Técnica 6-6-6 (6 segundos inhalar, 6 exhalar)",
                    "📊 **Monitoreo:** Registra patrones de estrés para identificar triggers"
                ]
            },
            "medio": {
                "titulo": "🛡️ Resiliencia con Desafíos Moderados",
                "analisis": f"**Análisis Psicológico:** Perfil Resiliente con riesgo MEDIO. Mantienes buenas estrategias de afrontamiento, pero algunos factores están desafiando tu equilibrio habitual.\n\n**Bases Neurocientíficas:** La corteza prefrontal (regulación ejecutiva) y la ínsula (conciencia corporal) mantienen buena integración, con signos de sobrecarga temporal.",
                "recomendaciones": [
                    "🧘 **Mindfulness Preventivo:** 10 minutos diarios de atención plena",
                    "🏃 **Ejercicio Aeróbico:** 30 minutos, 3 veces por semana",
                    "🌙 **Higiene de Sueño:** Rutina consistente, sin pantallas 1h antes",
                    "🤝 **Conexión Social:** Mantén contactos de apoyo regularmente"
                ]
            },
            "bajo": {
                "titulo": "🛡️ Resiliencia Óptima Funcional",
                "analisis": f"**Análisis Psicológico:** ¡Excelente! Tu perfil Resiliente muestra capacidad de adaptación y recuperación en niveles óptimos. El sistema de estrés (eje HPA) muestra buena regulación.\n\n**Bases Neurocientíficas:** Actividad prefrontal equilibrada sugiere buena función ejecutiva. Variabilidad de frecuencia cardíaca en rangos saludables.",
                "recomendaciones": [
                    "✅ **Mantenimiento:** Continúa con tus prácticas actuales",
                    "🌟 **Variedad Experiencial:** Incorpora nuevos aprendizajes",
                    "🌐 **Conexión Social Profunda:** Fortalece redes significativas",
                    "📈 **Desarrollo Continuo:** Explora técnicas avanzadas de regulación"
                ]
            }
        },
        
        "Ansioso/Tenso": {
            "alto": {
                "titulo": "😰 Ansiedad Clínicamente Significativa",
                "analisis": f"**Análisis Psicológico:** Niveles elevados de tensión ({poms_tension:.2f}/1.0) y activación ({arousal:.2f}/1.0). El sistema nervioso simpático muestra activación sostenida (lucha/huida).\n\n**Bases Neurocientíficas:** Posible elevación de cortisol afectando hipocampo (memoria) y amígdala (respuesta al miedo). Actividad reducida en corteza prefrontal medial.",
                "recomendaciones": [
                    "🆘 **Intervención Prioritaria:** Consulta profesional de salud mental",
                    "🌬️ **Respiración 4-7-8:** 4s inhalar, 7s retener, 8s exhalar",
                    "🌍 **Grounding 5-4-3-2-1:** 5 cosas que ves, 4 que tocas, 3 que oyes, 2 que hueles, 1 que pruebas",
                    "📵 **Desconexión Digital:** 2 horas sin pantallas antes de dormir"
                ]
            },
            "medio": {
                "titulo": "😰 Ansiedad Moderada Funcional",
                "analisis": f"**Análisis Psicológico:** Tensión psicológica presente pero dentro de rangos manejables. El sistema de alerta está activado pero no abrumado.\n\n**Bases Neurocientíficas:** Variabilidad de frecuencia cardíaca muestra desequilibrio autonómico leve. Actividad amigdalina elevada pero regulable.",
                "recomendaciones": [
                    "🫀 **Coherencia Cardíaca:** 6 respiraciones/minuto durante 5 minutos",
                    "🚶 **Ejercicio Moderado:** Caminata diaria de 30 minutos",
                    "🍃 **Técnicas de Relajación:** Relajación muscular progresiva",
                    "📆 **Estructura Diaria:** Rutinas predecibles reducen incertidumbre"
                ]
            },
            "bajo": {
                "titulo": "😰 Ansiedad Adaptativa Leve",
                "analisis": f"**Análisis Psicológico:** Preocupación y tensión dentro de rangos normales adaptativos. El sistema de alerta funciona adecuadamente como mecanismo protector.\n\n**Bases Neurocientíficas:** Respuesta al estrés apropiada al contexto. Homeostasis autonómica preservada.",
                "recomendaciones": [
                    "🛡️ **Prevención:** Mantén técnicas de relajación como hábito",
                    "👁️ **Atención Plena:** Observa señales corporales tempranas",
                    "⚖️ **Balance:** Respeta ciclos naturales trabajo-descanso",
                    "📚 **Psicoeducación:** Aprende sobre mecanismos de ansiedad"
                ]
            }
        },
        
        "Fatigado": {
            "alto": {
                "titulo": "😴 Fatiga Crónica Severa",
                "analisis": f"**Análisis Psicológico:** Agotamiento significativo (fatiga POMS: {poms_fatigue:.2f}/1.0). Depleción de recursos cognitivos afectando función ejecutiva.\n\n**Bases Neurocientíficas:** Posible acumulación de adenosina cerebral. Reducción de actividad prefrontal dorsolateral. Sueño no reparador.",
                "recomendaciones": [
                    "💤 **Prioridad Absoluta:** 7-9 horas sueño ininterrumpido",
                    "⏰ **Micro-descansos:** 5 minutos cada hora de trabajo",
                    "☀️ **Luz Natural:** Exposición matutina para regular ritmo circadiano",
                    "🥗 **Nutrición Cerebral:** Omega-3, magnesio, vitamina B"
                ]
            },
            "medio": {
                "titulo": "😴 Fatiga Mental Moderada",
                "analisis": f"**Análisis Psicológico:** Cansancio mental presente con recursos cognitivos disminuidos pero recuperables.\n\n**Bases Neurocientíficas:** Glucosa cerebral subóptima para demanda ejecutiva. Actividad reducida en red de modo predeterminado.",
                "recomendaciones": [
                    "😴 **Siestas Estratégicas:** 20-30 minutos máximo",
                    "💧 **Hidratación Cerebral:** 2L agua + electrolitos diarios",
                    "🚴 **Ejercicio Suave:** Yoga, tai chi, caminata ligera",
                    "🎯 **Gestión Energía:** Prioriza tareas en picos energéticos"
                ]
            },
            "bajo": {
                "titulo": "😴 Fatiga Leve Recuperable",
                "analisis": f"**Análisis Psicológico:** Cansancio dentro de lo esperable dada la actividad reciente. Homeostasis energética adecuada.\n\n**Bases Neurocientíficas:** Ritmos circadianos preservados. Recuperación metabólica cerebral funcionando.",
                "recomendaciones": [
                    "⏸️ **Descanso Preventivo:** No esperes al agotamiento total",
                    "🥑 **Combustible Cerebral:** Alimentos ricos en antioxidantes",
                    "🔄 **Rotación Tareas:** Alterna tareas cognitivas y manuales",
                    "🌿 **Técnicas Recarga:** Respiración diafragmática breve"
                ]
            }
        }
    }
    
    # ================================================================
    # 6. MOSTRAR RECOMENDACIÓN CORRESPONDIENTE
    # ================================================================
    
    if perfil_mapeado in recomendaciones_profesionales:
        riesgo_normalizado = riesgo.lower() if isinstance(riesgo, str) else "medio"
        
        # Determinar clave de riesgo (alto, medio, bajo)
        if riesgo_normalizado == "alto":
            riesgo_clave = "alto"
        elif riesgo_normalizado == "medio":
            riesgo_clave = "medio"
        else:
            riesgo_clave = "bajo"
        
        # Obtener recomendación
        if riesgo_clave in recomendaciones_profesionales[perfil_mapeado]:
            rec_data = recomendaciones_profesionales[perfil_mapeado][riesgo_clave]
            
            # Mostrar título
            st.markdown(f"### {rec_data['titulo']}")
            
            # Mostrar análisis según nivel de riesgo
            if riesgo_clave == "alto":
                with st.container():
                    st.markdown("""
                    <div style='
                        background: linear-gradient(135deg, rgba(255,68,68,0.08), rgba(255,68,68,0.03));
                        border-left: 4px solid #ff4444;
                        padding: 20px;
                        border-radius: 10px;
                        margin: 15px 0;
                    '>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"**📋 ANÁLISIS DETALLADO:**\n\n{rec_data['analisis']}")
                    st.markdown("---")
                    st.markdown("**🎯 RECOMENDACIONES ESPECÍFICAS:**")
                    for rec in rec_data['recomendaciones']:
                        st.markdown(f"- {rec}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
            elif riesgo_clave == "medio":
                with st.container():
                    st.markdown("""
                    <div style='
                        background: linear-gradient(135deg, rgba(255,170,68,0.08), rgba(255,170,68,0.03));
                        border-left: 4px solid #ffaa44;
                        padding: 20px;
                        border-radius: 10px;
                        margin: 15px 0;
                    '>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"**📋 ANÁLISIS DETALLADO:**\n\n{rec_data['analisis']}")
                    st.markdown("---")
                    st.markdown("**🎯 RECOMENDACIONES ESPECÍFICAS:**")
                    for rec in rec_data['recomendaciones']:
                        st.markdown(f"- {rec}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
            else:  # bajo
                with st.container():
                    st.markdown("""
                    <div style='
                        background: linear-gradient(135deg, rgba(68,204,68,0.08), rgba(68,204,68,0.03));
                        border-left: 4px solid #44cc44;
                        padding: 20px;
                        border-radius: 10px;
                        margin: 15px 0;
                    '>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"**📋 ANÁLISIS DETALLADO:**\n\n{rec_data['analisis']}")
                    st.markdown("---")
                    st.markdown("**🎯 RECOMENDACIONES ESPECÍFICAS:**")
                    for rec in rec_data['recomendaciones']:
                        st.markdown(f"- {rec}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info(f"**Análisis General:** Perfil '{perfil_mapeado}' con riesgo {riesgo}. Se aplican recomendaciones estándar.")
    else:
        st.warning(f"**Nota:** El perfil '{perfil_mapeado}' requiere configuración adicional.")
    
    st.markdown("---")
    
    # ================================================================
    # 7. PANEL DE MÉTRICAS TÉCNICAS
    # ================================================================
    st.subheader("📊 Panel de Métricas Técnicas")
    
    # Primera fila de métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Puntaje General", 
            value=f"{promedio:.2f}",
            delta="ALTO" if promedio >= 4.0 else "MODERADO" if promedio >= 2.5 else "BAJO",
            delta_color="inverse" if promedio >= 4.0 else "normal"
        )
    
    with col2:
        st.metric(
            label="Valence (Placer)", 
            value=f"{valence:.2f}",
            delta="POSITIVO" if valence > 0.2 else "NEGATIVO" if valence < -0.2 else "NEUTRAL",
            delta_color="normal" if valence > 0.2 else "inverse" if valence < -0.2 else "off"
        )
    
    with col3:
        st.metric(
            label="Arousal (Activación)", 
            value=f"{arousal:.2f}",
            delta="ALTA" if arousal > 0.7 else "BAJA" if arousal < 0.3 else "MODERADA"
        )
    
    # Segunda fila de métricas
    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric(
            label="Palabras Negativas", 
            value=neg_words,
            delta="ELEVADO" if neg_words >= 3 else "MODERADO" if neg_words >= 1 else "BAJO",
            delta_color="inverse" if neg_words >= 3 else "off"
        )
    
    with col5:
        st.metric(
            label="Polaridad Textual", 
            value=f"{polarity:.2f}",
            delta="POSITIVA" if polarity > 0.1 else "NEGATIVA" if polarity < -0.1 else "NEUTRAL"
        )
    
    with col6:
        st.metric(
            label="Subjetividad", 
            value=f"{subjectivity:.2f}",
            delta="ALTA" if subjectivity > 0.7 else "BAJA" if subjectivity < 0.3 else "MEDIA"
        )
    
    # ================================================================
    # 8. TEXTO ANALIZADO (SI EXISTE)
    # ================================================================
    if texto_snippet and texto_snippet.strip() and texto_snippet != "N/A":
        st.markdown("---")
        st.subheader("📝 Contenido Analizado")
        with st.expander("Ver texto proporcionado por el usuario", expanded=False):
            st.markdown(f"""
            <div style='
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #4fc3f7;
                font-style: italic;
                margin: 10px 0;
            '>
            "{texto_snippet}"
            </div>
            """, unsafe_allow_html=True)
            st.caption("*Este texto fue analizado utilizando Procesamiento de Lenguaje Natural (NLP) para extraer indicadores emocionales y cognitivos.*")
    
    # ================================================================
    # 9. DISCLAIMER PROFESIONAL
    # ================================================================
    st.markdown("---")
    st.markdown("""
    <div style='
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 15px;
        margin: 20px 0;
        font-size: 0.9em;
    '>
    <strong>⚠️ DECLARACIÓN DE RESPONSABILIDAD PROFESIONAL</strong><br><br>
    
    Este reporte ha sido generado mediante un sistema automatizado de detección temprana. 
    Tiene un carácter <strong>PREVENTIVO, ORIENTATIVO Y NO DIAGNÓSTICO</strong>.<br><br>
    
    <strong>NO sustituye</strong> la evaluación, diagnóstico o tratamiento por parte de 
    un profesional de la salud mental calificado. Si experimentas malestar significativo, 
    pensamientos de autolesión, o síntomas que interfieran con tu funcionamiento diario, 
    <strong>busca atención profesional inmediata</strong>.<br><br>
    
    <em>Plataforma de Detección Temprana - Versión 2.0 © 2025</em>
    </div>
    """, unsafe_allow_html=True)
# ================================================================
# ALERTA INTELIGENTE 2.0 (Reglas Psicometricas)
# ================================================================

def generate_smart_alerts(user_id):
    """Genera alertas complejas analizando el historial del usuario."""
    conn = get_conn()
    
    # 1. Obtener Historial (últimas 5 sesiones) - CONSULTA CORREGIDA
    df = pd.read_sql_query(
        f"""
        SELECT r.puntaje, r.detalle, r.fecha 
        FROM resultados r
        JOIN encuestas e ON r.encuesta_id = e.id
        WHERE e.usuario_id = '{user_id}' 
        ORDER BY r.fecha DESC 
        LIMIT 5
        """, 
        conn
    )
    conn.close()

    if df.shape[0] < 2:
        return ["🟢 Bajo riesgo: Se necesitan más sesiones para análisis de tendencia."]
    
    # Preprocesar datos
    df["detalle_json"] = df["detalle"].apply(safe_json_load)
    df["puntaje_num"] = df["puntaje"].apply(safe_float)
    df["tension"] = df["detalle_json"].apply(lambda x: safe_float(x.get("POMS", {}).get("tension", 0)))
    df["valence"] = df["detalle_json"].apply(lambda x: safe_float(x.get("VA", {}).get("valence", 0)))
    
    # Lista de alertas
    alerts = []
    
    # --- Regla 1: Caída de Motivación / POMS ---
    avg_valence = df["valence"].mean()
    if avg_valence < 0.4 and df["valence"].iloc[0] < avg_valence:
        alerts.append("🟡 **Caída de Motivación (Valence Bajo):** El estado de ánimo reciente es significativamente bajo.")

    # --- Regla 2: Aumento Sostenido de Tensión (Estrés POMS) ---
    if df.shape[0] >= 3:
        tension_avg_last_3 = df["tension"].head(3).mean()
        if df["tension"].iloc[0] > (tension_avg_last_3 * 1.25) and tension_avg_last_3 > 0.5: 
            alerts.append("🔴 **Aumento de Tensión POMS:** El nivel de estrés actual excede el promedio histórico reciente.")

    # --- Regla 3: Riesgo Lingüístico de Agotamiento (NLP) ---
    neg_words = df["detalle_json"].iloc[0].get("NegWords", 0)
    if neg_words >= 4:
        alerts.append("🔴 **Riesgo Lingüístico:** Uso elevado de lenguaje negativo o crítico en la última sesión.")

    # --- Regla 4: Inestabilidad (Variabilidad en puntaje) ---
    std_puntaje = df["puntaje_num"].std()
    if std_puntaje > 1.5: 
        alerts.append("🟡 **Inestabilidad:** Alta fluctuación en los puntajes globales, indicando inconsistencia emocional.")

    # Alerta por defecto si no hay nada crítico
    riesgo_actual = safe_json_load(df["detalle"].iloc[0]).get("Riesgo", "Bajo")
    
    if not alerts and riesgo_actual in ["Alto", "Medio"]:
        alerts.append(f"🟢 **Revisión General:** Riesgo actual detectado: {riesgo_actual}. No hay tendencias históricas claras.")
    elif not alerts:
        alerts.append("🟢 **Bajo Riesgo Estructural:** Perfil emocional estable y baja incidencia de factores de riesgo.")

    return alerts

# ================================================================
# PANEL DOCENTE - CLUSTERING DE RIESGO
# ================================================================
    
def show_panel_docente():
    
    st.title("🧠 Panel Docente — Análisis de Agrupación (Clustering)")
    st.caption("Identifica grupos de estudiantes con patrones de riesgo emocional similares.")

    if not SKLEARN_AVAILABLE:
        st.error("🚨 La librería Scikit-learn (sklearn) no está instalada. Ejecuta: pip install scikit-learn")
        return
        
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT r.id, r.puntaje, r.detalle, r.fecha, u.id as usuario_id, u.nivel 
        FROM resultados r
        JOIN encuestas e ON r.encuesta_id = e.id
        JOIN usuarios u ON e.usuario_id = u.id
        """, 
        conn
    )
    conn.close()

    if df.empty:
        st.info("No hay datos suficientes para realizar el clustering.")
        return

    # 1. Preparación de datos (usando la encuesta más reciente por usuario)
    df["detalle_json"] = df["detalle"].apply(safe_json_load)
    
    # Extraer variables clave para el clustering
    df["tension"] = df["detalle_json"].apply(lambda x: x.get("POMS", {}).get("tension", 0))
    df["fatigue"] = df["detalle_json"].apply(lambda x: x.get("POMS", {}).get("fatigue", 0))
    df["valence"] = df["detalle_json"].apply(lambda x: x.get("VA", {}).get("valence", 0))
    df["arousal"] = df["detalle_json"].apply(lambda x: x.get("VA", {}).get("arousal", 0.5))
    df["palabras_negativas"] = df["detalle_json"].apply(lambda x: x.get("NegWords", 0))

    # Conservar solo el resultado más reciente de cada usuario para el clustering
    df_latest = df.sort_values(by='fecha', ascending=False).drop_duplicates(subset=['usuario_id'])
    
    if len(df_latest) < 3:
        st.warning("Se necesitan al menos 3 usuarios distintos para realizar un clustering significativo.")
        return

    # Definir features para el clustering (las variables de riesgo)
    features = ['puntaje', 'tension', 'fatigue', 'valence', 'arousal', 'palabras_negativas']
    X = df_latest[features].fillna(0) # Reemplazar NaN, aunque no debería haber

    # 2. Estandarización
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 3. Configuración del Clustering
    st.sidebar.subheader("⚙️ Configuración de Clustering")
    
    # Selector de número de clusters (grupos de riesgo)
    num_clusters = st.sidebar.slider("Número de Grupos (K):", min_value=2, max_value=6, value=3)

    # 4. Aplicar K-Means
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init='auto')
    df_latest['cluster'] = kmeans.fit_predict(X_scaled)

    st.subheader(f"Grupos de Riesgo (K={num_clusters})")

    # 5. Visualización (Reducción de dimensionalidad con PCA para Plotly)
    pca = PCA(n_components=2)
    components = pca.fit_transform(X_scaled)
    pca_df = pd.DataFrame(data = components, columns = ['PCA Componente 1', 'PCA Componente 2'])
    pca_df['cluster'] = df_latest['cluster'].values
    pca_df['usuario_id'] = df_latest['usuario_id'].values
    pca_df['puntaje'] = df_latest['puntaje'].values
    
    # Scatter plot de Clustering (PCA)
    fig_pca = px.scatter(
        pca_df, 
        x='PCA Componente 1', 
        y='PCA Componente 2', 
        color=pca_df['cluster'].astype(str),
        hover_data={'usuario_id': True, 'puntaje': ':.2f', 'cluster': True},
        title="Visualización de Clústeres de Riesgo (Reducción de Dimensionalidad PCA)"
    )
    st.plotly_chart(fig_pca, use_container_width=True)
    
        # 6. Cluster Interpretation (Average Profile Table)
    st.subheader("Perfil Promedio de cada Grupo")
    
    try:
        # 6.1 Calcular estadísticas básicas por cluster (solo features)
        cluster_stats = df_latest.groupby('cluster')[features].agg({
            'puntaje': 'mean',
            'tension': 'mean', 
            'fatigue': 'mean',
            'valence': 'mean',
            'arousal': 'mean',
            'palabras_negativas': 'mean'
        }).reset_index()
        
        # 6.2 Calcular nivel más frecuente por cluster (separadamente)
        nivel_por_cluster = df_latest.groupby('cluster')['nivel'].agg(
            lambda x: x.mode()[0] if not x.mode().empty else 'N/A'
        ).reset_index(name='nivel_mas_frecuente')
        
        # 6.3 Contar miembros por cluster (usando usuario_id correctamente)
        miembros_por_cluster = df_latest.groupby('cluster')['usuario_id'].count().reset_index(name='total_miembros')
        
        # 6.4 Combinar todas las estadísticas
        cluster_summary = pd.merge(cluster_stats, nivel_por_cluster, on='cluster')
        cluster_summary = pd.merge(cluster_summary, miembros_por_cluster, on='cluster')
        
        # 6.5 Formatear números para mejor visualización
        for col in features:
            if col in cluster_summary.columns:
                cluster_summary[col] = cluster_summary[col].round(3)
        
        # 6.6 Mostrar tabla con estilo
        st.dataframe(
            cluster_summary.style.background_gradient(
                cmap='RdYlGn_r',  # Rojo = alto riesgo, Verde = bajo riesgo
                subset=['puntaje', 'tension', 'fatigue']
            ).format({
                'puntaje': '{:.2f}',
                'tension': '{:.3f}',
                'fatigue': '{:.3f}',
                'valence': '{:.3f}',
                'arousal': '{:.3f}',
                'palabras_negativas': '{:.1f}'
            }),
            use_container_width=True
        )
        
        # 6.7 Explicación de las métricas
        with st.expander("📊 ¿Qué significan estas métricas?"):
            st.markdown("""
            **Explicación de las columnas:**
            
            - **cluster**: Grupo identificado por el algoritmo
            - **puntaje**: Puntaje de riesgo combinado (1-5, mayor = más riesgo)
            - **tension**: Subescala de tensión POMS (0-1, mayor = más tensión)
            - **fatigue**: Subescala de fatiga POMS (0-1, mayor = más fatiga)  
            - **valence**: Placer/Displacer (-1 a +1, positivo = placentero)
            - **arousal**: Activación (0 a 1, mayor = más activación)
            - **palabras_negativas**: Conteo de palabras negativas en texto libre
            - **nivel_mas_frecuente**: Nivel educativo más común en el grupo
            - **total_miembros**: Número de usuarios distintos en el grupo
            
            **Interpretación:**
            - Grupos con **puntaje > 4.0** requieren atención prioritaria
            - **tension > 0.6** indica estrés significativo
            - **fatigue > 0.7** sugiere agotamiento importante
            - **valence negativo** indica estado de ánimo displacentero
            """)
            
    except Exception as e:
        st.error(f"❌ Error al calcular estadísticas de clusters: {str(e)}")
        st.info("Para depuración - Columnas disponibles en df_latest:")
        st.write(list(df_latest.columns))
        st.info("Primeras filas de datos:")
        st.write(df_latest.head())

# ================================================================
# DASHBOARD EMOCIONAL HISTÓRICO - EVOLUCIÓN TEMPORAL
# ================================================================

def show_dashboard_historico():
    
    st.title("📈 Dashboard Emocional Histórico")
    st.markdown("Análisis de evolución temporal de los indicadores emocionales.")
    
    # Obtener todos los datos históricos
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT r.id, r.puntaje, r.riesgo, r.detalle, r.fecha, 
               e.usuario_id, -- <--- ¡SE AÑADE ESTO!
               e.respuestas, u.rol, u.edad, u.nivel as usuario_nivel
        FROM resultados r
        JOIN encuestas e ON r.encuesta_id = e.id
        JOIN usuarios u ON e.usuario_id = u.id
        ORDER BY r.fecha ASC
    """, conn)
    conn.close()
    
    if df.empty:
        st.info("No hay datos históricos para mostrar.")
        return
    
    # Procesar datos
    df["detalle_json"] = df["detalle"].apply(safe_json_load)
    df["respuestas_json"] = df["respuestas"].apply(safe_json_load)
    df["fecha_dt"] = pd.to_datetime(df["fecha"])
    
    # Extraer información estructurada
    df["perfil"] = df["detalle_json"].apply(lambda x: x.get("Perfil", "No definido"))
    df["valence"] = df["detalle_json"].apply(lambda x: x.get("VA", {}).get("valence", 0))
    df["arousal"] = df["detalle_json"].apply(lambda x: x.get("VA", {}).get("arousal", 0.5))
    df["poms_tension"] = df["detalle_json"].apply(lambda x: x.get("POMS", {}).get("tension", 0))
    df["poms_fatigue"] = df["detalle_json"].apply(lambda x: x.get("POMS", {}).get("fatigue", 0))
    df["poms_vigor"] = df["detalle_json"].apply(lambda x: x.get("POMS", {}).get("vigor", 0))
    
    # Extraer datos de la encuesta base
    def extract_base_value(respuestas, key):
        try:
            return respuestas.get("base", {}).get(key, 3)
        except:
            return 3
    
    df["base_estres"] = df["respuestas_json"].apply(lambda x: extract_base_value(x, "estres"))
    df["base_motivacion"] = df["respuestas_json"].apply(lambda x: extract_base_value(x, "motivacion"))
    df["base_animo"] = df["respuestas_json"].apply(lambda x: extract_base_value(x, "animo"))
    
    # ===== FILTROS (MODIFICADO) =====
    st.sidebar.subheader("🎛️ Filtros de Análisis")
    
    # Nuevo filtro de Usuario ID y nivel en columnas para mejor UX
    col_u, col_n = st.sidebar.columns(2)
    
    with col_u:
        # Nuevo: Filtro de Usuario ID (clave para la tendencia individual)
        usuarios_ids = ["Todos"] + sorted(df["usuario_id"].unique().tolist())
        usuario_seleccionado = st.selectbox("Filtrar Usuario ID:", usuarios_ids)

    with col_n:
        # Filtro por nivel
        niveles = ["Todos"] + list(df["usuario_nivel"].unique())
        nivel_seleccionado = st.selectbox("Filtrar Nivel:", niveles)
    
    df_filtered = df.copy()

    # Aplicar filtro de Usuario y Nivel
    if usuario_seleccionado != "Todos":
        df_filtered = df_filtered[df_filtered["usuario_id"] == usuario_seleccionado]
        
    if nivel_seleccionado != "Todos":
        df_filtered = df_filtered[df_filtered["usuario_nivel"] == nivel_seleccionado]
        
    # El resto de los filtros usan el df_filtered
    df = df_filtered 
    
    if df.empty:
        st.warning("No hay datos para la combinación de filtros seleccionada.")
        return
        
    # Filtro por fecha (usando el DataFrame ya filtrado)
    fecha_min = df["fecha_dt"].min()
    fecha_max = df["fecha_dt"].max()
    
    if fecha_min is pd.NaT: # Pequeña validación si el filtro de usuario/nivel deja el DF vacío
         st.warning("No hay datos en el rango seleccionado después de aplicar el filtro de usuario/nivel.")
         return
    
    rango_fechas = st.sidebar.date_input(
        "Rango de fechas:",
        value=(fecha_min.date(), fecha_max.date()),
        min_value=fecha_min.date(),
        max_value=fecha_max.date()
    )
    
    if len(rango_fechas) == 2:
        df = df[
            (df["fecha_dt"].dt.date >= rango_fechas[0]) & 
            (df["fecha_dt"].dt.date <= rango_fechas[1])
        ]
    
    if df.empty:
        st.warning("No hay datos en el rango seleccionado.")
        return
    
    # ===== EVOLUCIÓN GENERAL (Se añade el nombre del usuario al título) =====
    st.header("📊 Evolución General del Bienestar")
    
    # Agrupar por fecha para tendencias
    df_diario = df.groupby(df["fecha_dt"].dt.date).agg({
        "puntaje": "mean",
        "base_estres": "mean",
        "base_motivacion": "mean", 
        "base_animo": "mean",
        "poms_tension": "mean",
        "poms_fatigue": "mean",
        "poms_vigor": "mean",
        "valence": "mean",
        "arousal": "mean",
        "id": "count"
    }).reset_index()
    
    df_diario.columns = ["fecha", "puntaje_promedio", "estres_promedio", "motivacion_promedio", 
                         "animo_promedio", "tension_promedio", "fatiga_promedio", "vigor_promedio",
                         "valence_promedio", "arousal_promedio", "num_encuestas"]
    
    # Determinar el título dinámico
    title_suffix = f" (Usuario: {usuario_seleccionado})" if usuario_seleccionado != "Todos" else ""

    # Gráfico de evolución del puntaje
    fig_puntaje = px.line(
        df_diario, x="fecha", y="puntaje_promedio",
        title=f"📈 Evolución del Puntaje de Riesgo Promedio{title_suffix}", # <--- Título dinámico
        labels={"fecha": "Fecha", "puntaje_promedio": "Puntaje Promedio"},
        markers=True
    )
    fig_puntaje.add_hline(y=3.0, line_dash="dash", line_color="red", annotation_text="Límite Riesgo Medio")
    fig_puntaje.add_hline(y=4.2, line_dash="dash", line_color="darkred", annotation_text="Límite Riesgo Alto")
    st.plotly_chart(fig_puntaje, use_container_width=True)
    
    # ===== EVOLUCIÓN DE ESTRÉS Y MOTIVACIÓN =====
    st.header("😌 Evolución de Estrés y Motivación")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_estres = px.line(
            df_diario, x="fecha", y="estres_promedio",
            title="📊 Evolución del Estrés Promedio",
            labels={"fecha": "Fecha", "estres_promedio": "Estrés (1-5)"},
            markers=True,
            color_discrete_sequence=["red"]
        )
        st.plotly_chart(fig_estres, use_container_width=True)
    
    with col2:
        fig_motivacion = px.line(
            df_diario, x="fecha", y="motivacion_promedio",
            title="🚀 Evolución de la Motivación Promedio", 
            labels={"fecha": "Fecha", "motivacion_promedio": "Motivación (1-5)"},
            markers=True,
            color_discrete_sequence=["green"]
        )
        st.plotly_chart(fig_motivacion, use_container_width=True)
    
    # ===== EVOLUCIÓN POMS =====
    st.header("🧠 Evolución de Estados Afectivos (POMS)")
    
    fig_poms = go.Figure()
    
    fig_poms.add_trace(go.Scatter(
        x=df_diario["fecha"], y=df_diario["tension_promedio"],
        name="Tensión", line=dict(color="red", width=3)
    ))
    fig_poms.add_trace(go.Scatter(
        x=df_diario["fecha"], y=df_diario["fatiga_promedio"], 
        name="Fatiga", line=dict(color="orange", width=3)
    ))
    fig_poms.add_trace(go.Scatter(
        x=df_diario["fecha"], y=df_diario["vigor_promedio"],
        name="Vigor", line=dict(color="green", width=3)
    ))
    
    fig_poms.update_layout(
        title="📊 Evolución de Estados Afectivos - POMS",
        xaxis_title="Fecha",
        yaxis_title="Intensidad (0-1)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig_poms, use_container_width=True)
    
    # ===== EVOLUCIÓN VALENCE-AROUSAL =====
    st.header("🎭 Evolución de la Dimensión Emocional (VA)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_valence = px.line(
            df_diario, x="fecha", y="valence_promedio",
            title="😊 Evolución de Valence (Placer)",
            labels={"fecha": "Fecha", "valence_promedio": "Valence (-1 a +1)"},
            markers=True,
            color_discrete_sequence=["blue"]
        )
        fig_valence.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_valence, use_container_width=True)
    
    with col2:
        fig_arousal = px.line(
            df_diario, x="fecha", y="arousal_promedio", 
            title="⚡ Evolución de Arousal (Activación)",
            labels={"fecha": "Fecha", "arousal_promedio": "Arousal (0 a 1)"},
            markers=True,
            color_discrete_sequence=["purple"]
        )
        st.plotly_chart(fig_arousal, use_container_width=True)
    
    # ===== ANÁLISIS DE TENDENCIAS =====
    st.header("📈 Análisis de Tendencias")
    
    if len(df_diario) >= 2:
        # Calcular tendencias
        tendencia_puntaje = (df_diario["puntaje_promedio"].iloc[-1] - df_diario["puntaje_promedio"].iloc[0]) / len(df_diario)
        tendencia_estres = (df_diario["estres_promedio"].iloc[-1] - df_diario["estres_promedio"].iloc[0]) / len(df_diario)
        tendencia_motivacion = (df_diario["motivacion_promedio"].iloc[-1] - df_diario["motivacion_promedio"].iloc[0]) / len(df_diario)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            color_puntaje = "red" if tendencia_puntaje > 0.01 else "green" if tendencia_puntaje < -0.01 else "gray"
            st.metric(
                "Tendencia Riesgo", 
                f"{tendencia_puntaje:+.3f} por día",
                delta=f"{tendencia_puntaje:+.3f}",
                delta_color="inverse"
            )
        
        with col2:
            color_estres = "red" if tendencia_estres > 0.01 else "green" if tendencia_estres < -0.01 else "gray"
            st.metric(
                "Tendencia Estrés",
                f"{tendencia_estres:+.3f} por día", 
                delta=f"{tendencia_estres:+.3f}",
                delta_color="inverse"
            )
        
        with col3:
            color_motivacion = "green" if tendencia_motivacion > 0.01 else "red" if tendencia_motivacion < -0.01 else "gray"
            st.metric(
                "Tendencia Motivación",
                f"{tendencia_motivacion:+.3f} por día",
                delta=f"{tendencia_motivacion:+.3f}"
            )
    
    # ===== RESUMEN ESTADÍSTICO =====
    st.header("📋 Resumen Estadístico")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Encuestas", len(df))
        st.metric("Período Analizado", f"{(df['fecha_dt'].max() - df['fecha_dt'].min()).days} días")
    
    with col2:
        riesgo_actual = df[df["fecha_dt"] == df["fecha_dt"].max()]["riesgo"].value_counts()
        if "Alto" in riesgo_actual:
            st.metric("Riesgo Alto Actual", riesgo_actual["Alto"])
        else:
            st.metric("Riesgo Alto Actual", 0)
    
    with col3:
        st.metric("Puntaje Promedio Actual", f"{df_diario['puntaje_promedio'].iloc[-1]:.2f}")
        st.metric("Encuestas por Día", f"{df_diario['num_encuestas'].mean():.1f}")
    
    st.success("✅ Dashboard histórico cargado correctamente")

# ================================================================
# DASHBOARD PROFESIONAL (Función final con todos los gráficos Plotly)
# ================================================================

def show_dashboard_profesional():
    st.title("👨‍🏫 Dashboard de Bienestar General")
    st.markdown("Vista global y comparativa de los indicadores emocionales por grupo y nivel.")

    conn = get_conn()
    try:
        # CONSULTA CORREGIDA - nombres de columnas consistentes
        df = pd.read_sql_query("""
            SELECT 
                r.id as resultado_id,
                r.puntaje, 
                r.riesgo,
                r.detalle,
                e.usuario_id,
                u.nivel
            FROM resultados r
            JOIN encuestas e ON r.encuesta_id = e.id
            JOIN usuarios u ON e.usuario_id = u.id
        """, conn)
    except pd.io.sql.DatabaseError as e:
        st.error(f"Error al ejecutar consulta SQL para dashboard: {e}")
        st.info("Asegúrate de que las tablas existan y la base de datos esté inicializada.")
        return
    finally:
        conn.close()

    if df.empty:
        st.info("No hay datos cargados para generar el dashboard.")
        return

    # Procesamiento y Extracción
    df["detalle_json"] = df["detalle"].apply(safe_json_load)
    
    # Extraer perfil emocional
    df["perfil"] = df["detalle_json"].apply(lambda x: x.get("Perfil", "No definido"))
    
    # Extracción de métricas
    df["valence"] = df["detalle_json"].apply(lambda x: x.get("VA", {}).get("valence", 0))
    df["arousal"] = df["detalle_json"].apply(lambda x: x.get("VA", {}).get("arousal", 0.5))
    df["tension"] = df["detalle_json"].apply(lambda x: x.get("POMS", {}).get("tension", 0))
    df["fatigue"] = df["detalle_json"].apply(lambda x: x.get("POMS", {}).get("fatigue", 0))
    df["vigor"] = df["detalle_json"].apply(lambda x: x.get("POMS", {}).get("vigor", 0))
    
    # Extraer indicadores de neurodiversidad si existen
    df["atencion"] = df["detalle_json"].apply(lambda x: x.get("Neurodiv", {}).get("atencion", 0.5))
    df["sensibilidad"] = df["detalle_json"].apply(lambda x: x.get("Neurodiv", {}).get("sensibilidad", 0.5))

    # ================================================================
    # FILTROS
    # ================================================================
    st.sidebar.subheader("🎛️ Filtros Globales")
    
    # Filtro por nivel
    niveles_unicos = ["Todos"] + sorted(df["nivel"].unique().tolist())
    nivel_seleccionado = st.sidebar.selectbox("Filtrar por Nivel:", niveles_unicos)

    if nivel_seleccionado != "Todos":
        df = df[df["nivel"] == nivel_seleccionado]
        
    if df.empty:
        st.warning("No hay datos para el nivel seleccionado.")
        return
        
    # ================================================================
    # 1. Indicadores de Riesgo y Perfiles
    # ================================================================
    st.header("1. Distribución de Indicadores Clave")
    col1, col2 = st.columns(2)
    
    # Gráfico de Riesgo (Pie Chart)
    with col1:
        riesgo_counts = df["riesgo"].value_counts().reset_index()
        riesgo_counts.columns = ['riesgo', 'count']
        
        # Mapa de colores para Riesgo
        color_map = {'Alto': 'red', 'Medio': 'gold', 'Bajo': 'green'}
        riesgo_counts['color'] = riesgo_counts['riesgo'].map(color_map).fillna('gray')
        
        fig_riesgo = px.pie(
            riesgo_counts, values='count', names='riesgo',
            title='Distribución de Nivel de Riesgo',
            color='riesgo',
            color_discrete_map=color_map
        )
        fig_riesgo.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
        st.plotly_chart(fig_riesgo, use_container_width=True)

    # Gráfico de Perfiles Emocionales (Barra)
    with col2:
        perfil_counts = df["perfil"].value_counts().reset_index()
        perfil_counts.columns = ['perfil', 'count']
        fig_perfiles = px.bar(
            perfil_counts, x="perfil", y="count",
            title="Frecuencia de Perfiles Emocionales",
            text_auto=True,
            color='perfil',
            color_discrete_sequence=px.colors.qualitative.D3
        )
        st.plotly_chart(fig_perfiles, use_container_width=True)

    # ================================================================
    # 2. Análisis POMS y Dimensión Emocional VA
    # ================================================================
    st.header("2. Métricas Afectivas Avanzadas")
    
    col3, col4 = st.columns(2)
    
    # Gráfico de Dispersión Valence-Arousal (VA)
    with col3:
        fig_va = px.scatter(
            df, x="valence", y="arousal",
            color="riesgo",
            hover_data=["perfil", "usuario_id"],
            title="Distribución Emocional (Valence - Arousal)",
            color_discrete_map=color_map,
            range_x=[-1.1, 1.1],
            range_y=[-0.1, 1.1]
        )
        fig_va.add_shape(type="line", x0=-1, y0=0.5, x1=1, y1=0.5, line=dict(dash="dash", color="gray"))
        fig_va.add_shape(type="line", x0=0, y0=0, x1=0, y1=1, line=dict(dash="dash", color="gray"))
        st.plotly_chart(fig_va, use_container_width=True)
        st.markdown("_Eje X: Placer (-1 a +1), Eje Y: Activación (0 a 1)_")

    # Gráfico de Radar POMS Promedio por Nivel
    with col4:
        # Agrupamos por Nivel para el radar
        poms_group = df.groupby("nivel")[["tension", "fatigue", "vigor"]].mean().reset_index()
        poms_group = poms_group.melt(id_vars='nivel', var_name='Métrica', value_name='Valor')
        
        fig_radar = px.line_polar(
            poms_group, r='Valor', theta='Métrica', color='nivel', 
            line_close=True,
            title="Perfil POMS Promedio por Nivel",
            range_r=[0, poms_group['Valor'].max() * 1.1] # Rango dinámico
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        st.markdown("_Tensión, Fatiga (Negativo) y Vigor (Positivo)_")

    # ================================================================
    # 3. Indicadores Adicionales (Neurodiversidad)
    # ================================================================
    st.header("3. Indicadores de Procesamiento Cognitivo (Promedio)")
    
    neuro_metrics = ["atencion", "sensibilidad"] # Se pueden añadir más si existen en el JSON
    
    if all(m in df.columns for m in neuro_metrics):
        neuro_group = df.groupby("nivel")[neuro_metrics].mean().reset_index()
        fig_neuro = px.bar(
            neuro_group, x="nivel", y=neuro_metrics,
            barmode="group",
            title="Indicadores de Procesamiento Cognitivo por Nivel",
            labels={"value": "Promedio (0 a 1)", "variable": "Indicador"}
        )
        st.plotly_chart(fig_neuro, use_container_width=True)
    else:
        st.info("Los indicadores de procesamiento cognitivo (atención/sensibilidad) no están disponibles en todos los datos.")

    st.markdown("---")
    st.success(f"✅ Dashboard profesional cargado con {len(df)} resultados analizados.")

# ================================================================
# ALERTAS INTELIGENTES
# ================================================================

def show_alertas_inteligentes():
    # Título principal de la sección de Alertas
    st.title("🚨 Alertas de Riesgo Temprano")
    st.write("Análisis focalizado en los casos que presentan mayor puntuación de riesgo combinado (Riesgo Alto).")

    conn = get_conn()
    try:
        # CONSULTA CORREGIDA - nombres de columnas actualizados
        df = pd.read_sql_query("""
            SELECT 
                r.id as resultado_id,
                r.puntaje, 
                r.riesgo,
                r.detalle,
                e.fecha,
                e.respuestas, 
                u.id as usuario_id,
                u.nivel
            FROM resultados r
            JOIN encuestas e ON r.encuesta_id = e.id
            JOIN usuarios u ON e.usuario_id = u.id
            WHERE r.riesgo = 'Alto'
            ORDER BY r.puntaje DESC
        """, conn)
    except pd.io.sql.DatabaseError as e:
        st.error(f"Error al ejecutar consulta SQL para alertas: {e}")
        st.info("Asegúrate de que las tablas existan y la base de datos esté inicializada.")
        return
    finally:
        conn.close()

    if df.empty:
        st.success("No hay casos en riesgo alto. El bienestar general es satisfactorio. 🟢")
        return

    # Procesamiento y Extracción de datos JSON
    df["detalle_json"] = df["detalle"].apply(safe_json_load)
    df["respuestas_json"] = df["respuestas"].apply(safe_json_load)
    
    # Extraer perfil del JSON
    df["perfil"] = df["detalle_json"].apply(lambda x: x.get("Perfil", "No definido"))
    
    # Extraer el texto libre de la encuesta para contextualizar la alerta
    df["texto"] = df["respuestas_json"].apply(lambda x: x.get("texto", ""))
    
    # Lógica de clasificación de la Causa Principal
    causas = []
    for d in df["detalle_json"]:
        prom = d.get("Promedio", 0)
        neg = d.get("NegWords", 0)
        subj = d.get("Subj", 0)

        # Criterios para determinar la causa más probable de la alerta
        if neg >= 3 and prom > 4.2:
            causas.append("🚨 Estrés + Lenguaje Crítico")
        elif prom >= 4.5:
            causas.append("📈 Riesgo por Estrés/Ansiedad General")
        elif neg >= 4:
            causas.append("💬 Lenguaje Crítico Intenso")
        elif subj >= 0.75:
            causas.append("🧠 Alta Subjetividad Emocional")
        else:
            causas.append("📊 Riesgo Alto - Revisar Detalle")

    df["Causa Principal"] = causas
    
    st.markdown("---")
    st.markdown(f"**{len(df)}** casos detectados en **Riesgo Alto** que requieren atención inmediata.")

    # Tabla de resumen de los casos en riesgo alto
    st.dataframe(df[["resultado_id", "usuario_id", "nivel", "puntaje", "Causa Principal", "fecha", "texto"]].rename(
        columns={
            "resultado_id": "ID Resultado", 
            "usuario_id": "Usuario ID", 
            "puntaje": "Puntuación", 
            "fecha": "Fecha"
        }
    ), use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 Detalle del Caso Más Crítico")
    
    # Mostrar el detalle del caso con mayor puntaje de riesgo
    caso = df.iloc[0]
    det = caso["detalle_json"]
    
    # Se usa show_single_report para mostrar la información estructurada
    with st.expander(f"Reporte completo: ID {caso['resultado_id']} | Usuario: {caso['usuario_id']} | Puntaje: {caso['puntaje']:.2f}", expanded=True):
         show_single_report(caso['riesgo'], caso['perfil'], det)
         
    st.markdown("---")
    st.info("El análisis de alertas permite la acción temprana por parte del equipo de acompañamiento.")

# ================================================================
# UTILIDADES PDF (ReportLab) - FUNCIONES EXISTENTES
# ================================================================

def generar_pdf_reporte_general_bytes(data):
    """
    Recibe una lista como:
        [["Alto", 10], ["Medio", 5], ["Bajo", 12]]
    Y devuelve bytes PDF.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("ReportLab no disponible.")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 750, "Reporte General — Niveles de Riesgo")

    y = 720
    c.setFont("Helvetica", 12)
    for riesgo, cantidad in data:
        c.drawString(80, y, f"{riesgo}: {cantidad}")
        y -= 20
        if y < 72:
            c.showPage()
            y = 720

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def generar_pdf_historial_bytes(usuario_label, df_hist):
    """
    Genera un PDF con el historial de un usuario.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("ReportLab no disponible.")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 750, f"Historial — {usuario_label}")

    c.setFont("Helvetica", 10)
    y = 730
    for _, row in df_hist.iterrows():
        fecha = (
            row["Fecha"].strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(row["Fecha"], "strftime")
            else str(row["Fecha"])
        )
        line = f"{fecha} | Puntaje: {row['Puntaje']:.2f} | Riesgo: {row['Riesgo']}"
        c.drawString(72, y, line)
        y -= 14
        if y < 72:
            c.showPage()
            y = 730

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ================================================================
# EXPORTES AVANZADOS - PDF PROFESIONAL
# ================================================================

def generar_pdf_profesional_bytes(usuario_id=None):
    """
    Genera un PDF profesional con:
    - Diagrama VA
    - Barras POMS
    - Perfil emocional
    - Riesgos detectados
    - Comparativa histórica
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("ReportLab no disponible.")

    # Obtener datos
    conn = get_conn()
    if usuario_id:
        # PDF individual
        query = """
            SELECT r.puntaje, r.riesgo, r.detalle, r.fecha, e.respuestas
            FROM resultados r
            JOIN encuestas e ON r.encuesta_id = e.id
            WHERE e.usuario_id = ?
            ORDER BY r.fecha DESC
        """
        df = pd.read_sql_query(query, conn, params=(usuario_id,))
        titulo = f"Reporte Individual - Usuario {usuario_id}"
    else:
        # PDF general
        query = """
            SELECT r.puntaje, r.riesgo, r.detalle, r.fecha, e.respuestas, u.nivel
            FROM resultados r
            JOIN encuestas e ON r.encuesta_id = e.id
            JOIN usuarios u ON e.usuario_id = u.id
        """
        df = pd.read_sql_query(query, conn)
        titulo = "Reporte General - Plataforma de Detección Emocional"
    
    conn.close()

    if df.empty:
        raise ValueError("No hay datos para generar el reporte")

    # Procesar datos
    df["detalle_json"] = df["detalle"].apply(safe_json_load)
    df["respuestas_json"] = df["respuestas"].apply(safe_json_load)
    
    # Extraer información importante
    df["perfil"] = df["detalle_json"].apply(lambda x: x.get("Perfil", "No definido"))
    df["valence"] = df["detalle_json"].apply(lambda x: x.get("VA", {}).get("valence", 0))
    df["arousal"] = df["detalle_json"].apply(lambda x: x.get("VA", {}).get("arousal", 0.5))
    
    # Crear PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # ===== PORTADA =====
    c.setFont("Helvetica-Bold", 18)
    c.drawString(72, 750, titulo)
    c.setFont("Helvetica", 12)
    c.drawString(72, 730, f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(72, 710, f"Total de encuestas: {len(df)}")
    
    # Estadísticas generales
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 680, "Resumen Estadístico")
    c.setFont("Helvetica", 10)
    
    riesgo_counts = df['riesgo'].value_counts()
    y_pos = 660
    for riesgo, count in riesgo_counts.items():
        c.drawString(80, y_pos, f"{riesgo}: {count} encuestas ({count/len(df)*100:.1f}%)")
        y_pos -= 15
    
    # Perfiles emocionales
    y_pos -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y_pos, "Perfiles Emocionales:")
    c.setFont("Helvetica", 10)
    y_pos -= 15
    
    perfil_counts = df['perfil'].value_counts()
    for perfil, count in perfil_counts.head(5).items():
        c.drawString(80, y_pos, f"{perfil}: {count}")
        y_pos -= 12
    
    # Si queda poco espacio, nueva página
    if y_pos < 100:
        c.showPage()
        y_pos = 750
    
    # ===== ANÁLISIS DETALLADO =====
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, y_pos, "Análisis Detallado")
    y_pos -= 20
    
    # Promedios POMS
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y_pos, "Estados Afectivos Promedio (POMS):")
    c.setFont("Helvetica", 10)
    y_pos -= 15
    
    poms_promedios = {}
    for sub in ['tension', 'fatigue', 'vigor']:
        valores = []
        for detalle in df['detalle_json']:
            poms_val = detalle.get('POMS', {}).get(sub, 0)
            if poms_val is not None:
                valores.append(poms_val)
        if valores:
            poms_promedios[sub] = sum(valores) / len(valores)
            c.drawString(80, y_pos, f"{sub.capitalize()}: {poms_promedios[sub]:.3f}")
            y_pos -= 12
    
    # Valence-Arousal promedio
    y_pos -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y_pos, "Dimensión Emocional Promedio (VA):")
    c.setFont("Helvetica", 10)
    y_pos -= 15
    
    valence_prom = df['valence'].mean()
    arousal_prom = df['arousal'].mean()
    c.drawString(80, y_pos, f"Valence: {valence_prom:.3f} ({-1:+} a {1:+})")
    y_pos -= 12
    c.drawString(80, y_pos, f"Arousal: {arousal_prom:.3f} (0 a 1)")
    y_pos -= 15
    
    # ===== RECOMENDACIONES =====
    if y_pos < 150:
        c.showPage()
        y_pos = 750
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, y_pos, "Recomendaciones Generales")
    c.setFont("Helvetica", 10)
    y_pos -= 20
    
    recomendaciones = []
    
    # Análisis de riesgos
    alto_riesgo = riesgo_counts.get('Alto', 0)
    if alto_riesgo > 0:
        recomendaciones.append(f"• {alto_riesgo} casos de alto riesgo requieren atención prioritaria")
    
    if poms_promedios.get('tension', 0) > 0.6:
        recomendaciones.append("• Nivel general de tensión elevado - considerar actividades de relajación")
    
    if valence_prom < -0.2:
        recomendaciones.append("• Valence promedio negativo - fortalecer apoyo emocional")
    
    # Agregar recomendaciones al PDF
    for rec in recomendaciones:
        if y_pos < 100:
            c.showPage()
            y_pos = 750
            c.setFont("Helvetica", 10)
        c.drawString(72, y_pos, rec)
        y_pos -= 15
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ================================================================
# EXPORTES AVANZADOS - EXCEL COMPLETO
# ================================================================

def generar_excel_completo_bytes():
    """
    Genera un archivo Excel completo con múltiples hojas:
    - Resumen general
    - Datos detallados
    - Análisis POMS
    - Valence-Arousal
    - Alertas y riesgos
    """
    # Obtener todos los datos
    conn = get_conn()
    
    # Datos de usuarios
    df_usuarios = pd.read_sql_query("SELECT * FROM usuarios", conn)
    
    # Datos de encuestas con detalles
    df_encuestas = pd.read_sql_query("""
        SELECT e.*, u.rol, u.edad, u.nivel as usuario_nivel
        FROM encuestas e
        JOIN usuarios u ON e.usuario_id = u.id
    """, conn)
    
    # Datos de resultados
    df_resultados = pd.read_sql_query("""
        SELECT r.*, e.respuestas, u.rol, u.edad, u.nivel as usuario_nivel
        FROM resultados r
        JOIN encuestas e ON r.encuesta_id = e.id
        JOIN usuarios u ON e.usuario_id = u.id
    """, conn)
    
    conn.close()
    
    if df_resultados.empty:
        raise ValueError("No hay datos para generar el reporte Excel")
    
    # Procesar datos para análisis
    df_resultados["detalle_json"] = df_resultados["detalle"].apply(safe_json_load)
    df_resultados["respuestas_json"] = df_resultados["respuestas"].apply(safe_json_load)
    
    # Extraer información estructurada
    datos_procesados = []
    for _, row in df_resultados.iterrows():
        detalle = row["detalle_json"]
        respuestas = row["respuestas_json"]
        
        datos_procesados.append({
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "rol": row["rol"],
            "edad": row["edad"],
            "nivel": row["usuario_nivel"],
            "fecha": row["fecha"],
            "puntaje": row["puntaje"],
            "riesgo": row["riesgo"],
            "perfil": detalle.get("Perfil", "No definido"),
            "valence": detalle.get("VA", {}).get("valence", 0),
            "arousal": detalle.get("VA", {}).get("arousal", 0.5),
            "poms_tension": detalle.get("POMS", {}).get("tension", 0),
            "poms_fatigue": detalle.get("POMS", {}).get("fatigue", 0),
            "poms_vigor": detalle.get("POMS", {}).get("vigor", 0),
            "polarity": detalle.get("Polarity", 0),
            "neg_words": detalle.get("NegWords", 0),
            "texto_snippet": detalle.get("TextoSnippet", "")
        })
    
    df_analisis = pd.DataFrame(datos_procesados)
    
    # Crear archivo Excel con múltiples hojas
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Hoja 1: Resumen ejecutivo
        resumen_data = {
            'Métrica': ['Total Usuarios', 'Total Encuestas', 'Total Resultados', 
                       'Riesgo Alto', 'Riesgo Medio', 'Riesgo Bajo',
                       'Fecha de generación'],
            'Valor': [len(df_usuarios), len(df_encuestas), len(df_resultados),
                     len(df_analisis[df_analisis['riesgo'] == 'Alto']),
                     len(df_analisis[df_analisis['riesgo'] == 'Medio']),
                     len(df_analisis[df_analisis['riesgo'] == 'Bajo']),
                     datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        }
        df_resumen = pd.DataFrame(resumen_data)
        df_resumen.to_excel(writer, sheet_name='Resumen Ejecutivo', index=False)
        
        # Hoja 2: Datos detallados
        df_analisis.to_excel(writer, sheet_name='Datos Detallados', index=False)
        
        # Hoja 3: Análisis POMS
        poms_promedio = df_analisis[['poms_tension', 'poms_fatigue', 'poms_vigor']].mean()
        poms_por_nivel = df_analisis.groupby('nivel')[['poms_tension', 'poms_fatigue', 'poms_vigor']].mean()
        
        poms_data = {
            'Subescala': ['Tensión', 'Fatiga', 'Vigor'],
            'Promedio General': poms_promedio.values
        }
        df_poms = pd.DataFrame(poms_data)
        df_poms.to_excel(writer, sheet_name='Análisis POMS', index=False)
        poms_por_nivel.to_excel(writer, sheet_name='POMS por Nivel')
        
        # Hoja 4: Valence-Arousal
        va_stats = df_analisis[['valence', 'arousal']].describe()
        va_por_riesgo = df_analisis.groupby('riesgo')[['valence', 'arousal']].mean()
        
        va_stats.to_excel(writer, sheet_name='Estadísticas VA')
        va_por_riesgo.to_excel(writer, sheet_name='VA por Riesgo')
        
        # Hoja 5: Perfiles emocionales
        perfiles_count = df_analisis['perfil'].value_counts().reset_index()
        perfiles_count.columns = ['Perfil', 'Cantidad']
        perfiles_count.to_excel(writer, sheet_name='Perfiles Emocionales', index=False)
    
    buffer.seek(0)
    return buffer.getvalue()

# ================================================================
# LÓGICA PRINCIPAL DE LA APLICACIÓN
# ================================================================

# Verificar parámetro URL para landing
qs = st.query_params
if qs.get("landing", ["0"])[0] == "1":
    st.session_state.landing_done = True

# Mostrar Landing Page si no se ha completado
if not st.session_state.landing_done:
    _logo_b64 = img_to_base64(LOGO_PATH)
    show_landing_page(_logo_b64)
    st.stop()

# Mostrar Loader si no se ha mostrado
if not st.session_state.loader_shown:
    _logo_b64 = img_to_base64(LOGO_PATH)
    frase = random.choice(FRASES_LOADER)
    show_loading_screen(_logo_b64, frase, seconds=LOADER_SECONDS)
    st.session_state.loader_shown = True
    time.sleep(LOADER_SECONDS)
    st.rerun()

# ================================================================
# BARRA LATERAL (SIDEBAR) - NAVEGACIÓN
# ================================================================

with st.sidebar:
    st.title("🧭 Navegación")
    
    # Mostrar modo de prueba si está activo
    if st.session_state.get('landing_done') and st.session_state.get('loader_shown'):
        st.info("🔧 Modo prueba: Landing deshabilitada")
    
    # Selección de Rol
    rol_seleccionado = st.radio(
        "Selecciona tu rol:",
        ["Estudiante", "Docente"],
        key="rol_seleccionado"
    )
    
    # Navegación para Estudiante
    if rol_seleccionado == "Estudiante":
        st.subheader("👤 Área de Estudiante")
        
        if st.button("📝 Registrar nueva encuesta", use_container_width=True):
            st.session_state.menu_estudiante = "Registrar encuesta"
            st.session_state.consentimiento = False  # Resetear consentimiento
        
        if st.button("📊 Ver mi historial", use_container_width=True):
            st.session_state.menu_estudiante = "Ver historial"
        
        if st.button("ℹ️ Información sobre la plataforma", use_container_width=True):
            st.session_state.menu_estudiante = "Información"
    
    # Navegación para Docente
    else:
        st.subheader("👨‍🏫 Área de Docente")
        
        # Autenticación docente
        if not st.session_state.get('docente_activo'):
            clave = st.text_input("🔑 Clave de acceso docente:", type="password")
            if st.button("🔓 Acceder como docente", use_container_width=True):
                if clave == "admin123":  # Clave por defecto, puedes cambiarla
                    st.session_state.docente_activo = True
                    st.session_state.clave_docente = clave
                    st.success("Acceso concedido")
                    st.rerun()
                else:
                    st.error("Clave incorrecta")
        
        # Si el docente está autenticado, mostrar opciones
        if st.session_state.get('docente_activo'):
            if st.button("📈 Panel docente general", use_container_width=True):
                st.session_state.menu_docente = "Panel docente"
            
            if st.button("🧠 Clustering de riesgo", use_container_width=True):
                st.session_state.menu_docente = "Clustering"
            
            if st.button("📊 Dashboard histórico", use_container_width=True):
                st.session_state.menu_docente = "Dashboard histórico"
            
            if st.button("👨‍🏫 Dashboard profesional", use_container_width=True):
                st.session_state.menu_docente = "Dashboard profesional"
            
            if st.button("🚨 Alertas inteligentes", use_container_width=True):
                st.session_state.menu_docente = "Alertas inteligentes"
            
            if st.button("📁 Exportar datos", use_container_width=True):
                st.session_state.menu_docente = "Exportar datos"
            
            # Botón de logout
            if st.button("🚪 Cerrar sesión docente", use_container_width=True):
                logout()
                st.rerun()

# ================================================================
# CONTENIDO PRINCIPAL SEGÚN SELECCIÓN
# ================================================================

# Área de Estudiante
if rol_seleccionado == "Estudiante":
    if st.session_state.menu_estudiante == "Registrar encuesta":
        # ===== PANTALLA DE CONSENTIMIENTO INFORMADO =====
        if not st.session_state.consentimiento:
            st.title("📝 Consentimiento Informado")
            st.markdown("""
            ### Antes de comenzar, por favor lee atentamente:
            
            **Propósito:** Esta plataforma tiene como objetivo evaluar tu bienestar emocional 
            y cognitivo para detectar posibles riesgos de manera temprana.
            
            **Confidencialidad:** 
            - Tus respuestas son **anónimas** y **confidenciales**.
            - Solo el personal autorizado (docentes/psicólogos) tendrá acceso a los datos 
              agregados, nunca a tu identidad individual.
            - Los datos se almacenan de forma segura en una base de datos local.
            
            **Uso de los datos:**
            - Para análisis estadísticos grupales.
            - Para identificar patrones de riesgo que permitan mejorar los programas de apoyo.
            - Nunca para evaluación académica o personal.
            
            **Tu participación es:**
            - **Voluntaria**: puedes dejar de responder en cualquier momento.
            - **Gratuita**: no hay costo alguno.
            - **Reversible**: puedes solicitar la eliminación de tus datos.
            
            ---
            
            **¿Aceptas participar en esta evaluación?**
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Sí, acepto participar", use_container_width=True):
                    st.session_state.consentimiento = True
                    st.rerun()
            with col2:
                if st.button("❌ No, prefiero no participar", use_container_width=True):
                    st.info("Gracias por tu consideración. Si cambias de opinión, puedes regresar en cualquier momento.")
                    st.stop()
            
            st.markdown("---")
            st.caption("Esta plataforma cumple con los estándares éticos de investigación con seres humanos.")
        
        # ===== FORMULARIO DE REGISTRO =====
        else:
            st.title("📝 Registro de Encuesta")
            
            with st.form("registro_form"):
                st.subheader("Información básica")
                
                col1, col2 = st.columns(2)
                with col1:
                    edad = st.number_input("Edad", min_value=5, max_value=80, value=15, step=1)
                with col2:
                    nivel = st.selectbox(
                        "Nivel educativo",
                        ["Primaria", "Secundaria", "Universidad"],
                        index=0,
                        key="nivel_usuario"
                    )
                
                st.markdown("---")
                st.subheader("Encuesta de bienestar")
                
                # Obtener preguntas según nivel
                questions = get_questions_by_level(nivel)
                respuestas = render_questions_by_level(questions)
                
                submitted = st.form_submit_button("📤 Enviar encuesta", use_container_width=True)
                
                if submitted:
                    with st.spinner("Analizando respuestas..."):
                        # Análisis del texto
                        texto = respuestas.get("texto", "")
                        polarity, subjectivity, neg_count = analyze_text_advanced(texto)
                        
                        # Procesar resultados según nivel
                        puntaje, riesgo = process_results_by_level(nivel, respuestas, (polarity, subjectivity, neg_count))
                        
                        # Calcular POMS si es nivel Universidad
                        poms_scores = {}
                        if nivel == "Universidad":
                            # Extraer respuestas POMS
                            poms_respuestas = {
                                "nervioso": respuestas.get("poms_tension", 3),
                                "tenso": respuestas.get("poms_tension", 3),
                                "estresado": respuestas.get("poms_tension", 3),
                                "triste": respuestas.get("poms_depresion", 3),
                                "abatido": respuestas.get("poms_depresion", 3),
                                "desanimado": respuestas.get("poms_depresion", 3),
                                "cansado": respuestas.get("poms_fatiga", 3),
                                "agotado": respuestas.get("poms_fatiga", 3),
                                "somnoliento": respuestas.get("poms_fatiga", 3),
                                "activo": 6 - respuestas.get("poms_vigor", 3),
                                "energético": 6 - respuestas.get("poms_vigor", 3),
                                "alerta": 6 - respuestas.get("poms_vigor", 3)
                            }
                            poms_scores = score_poms(poms_respuestas)
                        
                        # Clasificar perfil
                        perfil = classify_profile(puntaje, polarity, subjectivity, poms_scores, neg_count)
                        
                        # Crear detalle completo
                        detalle = {
                            "Perfil": perfil,
                            "Polarity": polarity,
                            "Subj": subjectivity,
                            "NegWords": neg_count,
                            "TextoSnippet": texto[:100] + "..." if len(texto) > 100 else texto,
                            "Promedio": puntaje,
                            "Riesgo": riesgo,
                            "POMS": poms_scores,
                            "VA": {"valence": 0.0, "arousal": 0.5}  # Placeholder para VA
                        }
                        
                        # Guardar en base de datos
                        try:
                            # Guardar usuario
                            uid = save_user("estudiante", edad, nivel)
                            
                            # Guardar encuesta
                            eid = save_survey(uid, respuestas)
                            
                            # Guardar resultado
                            save_result(eid, riesgo, puntaje, detalle)
                            
                            # ================================================================
                            # 🎯 REDIRECCIÓN AL BLOQUE DE RESULTADOS (SOLUCIÓN A DUPLICACIÓN)
                            # ================================================================
                            st.session_state.last_report_data = {
                                "riesgo": riesgo, "perfil": perfil, "detalle": detalle, "uid": uid
                            }
                            st.session_state.menu_estudiante = "Resultados"
                            st.success("✅ Encuesta enviada correctamente")
                            st.balloons()
                            st.rerun() # Forzar el cambio de página
                            
                        except Exception as e:
                            st.error(f"Error al guardar los datos: {str(e)}")
        
    
    elif st.session_state.menu_estudiante == "Ver historial":
        st.title("📊 Mi Historial")
        st.info("Feature in development - you'll soon be able to see your survey history")
    
    elif st.session_state.menu_estudiante == "Resultados":
        # Bloque de resultados
        st.title("✨ Reporte de Evaluación")
        
        # Recuperar datos del reporte guardados en la sesión
        data = st.session_state.get('last_report_data', {})
        
        if not data:
            st.warning("No se encontraron datos de la última encuesta. Por favor, realiza una nueva evaluación.")
            if st.button("⬅️ Volver a Encuesta", key="btn_volver_encuesta"):
                st.session_state.menu_estudiante = "Registrar encuesta"
                st.rerun()
            st.stop()
            
        uid = data['uid']
        
        # 1. Mostrar reporte individual
        show_single_report(data['riesgo'], data['perfil'], data['detalle'])
        
        # 2. Generar alertas inteligentes
        alerts = generate_smart_alerts(uid)
        if alerts:
            st.subheader("🚨 Alertas de Seguimiento")
            for alert in alerts:
                st.info(alert)
            
        # 3. Opciones Post-Envío (REUBICADAS AQUÍ)
        st.markdown("---")
        st.subheader("🎯 ¿Qué te gustaría hacer ahora?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Ver mi historial de evaluaciones", use_container_width=True, key="btn_historial_res"):
                st.session_state.menu_estudiante = "Ver historial"
                if 'last_report_data' in st.session_state: del st.session_state.last_report_data
                st.rerun()
        with col2:
            if st.button("📝 Comenzar nueva evaluación", use_container_width=True, key="btn_nueva_res"):
                st.session_state.consentimiento = False
                st.session_state.menu_estudiante = "Registrar encuesta"
                if 'last_report_data' in st.session_state: del st.session_state.last_report_data
                st.rerun()
        
    elif st.session_state.menu_estudiante == "Información":
        st.title("ℹ️ Información sobre la plataforma")
        st.markdown("""
        ## Plataforma de Detección Temprana Emocional
        
        ### ¿Qué es?
        Esta plataforma tiene como objetivo evaluar y monitorear el bienestar emocional 
        y cognitivo de estudiantes de diferentes niveles educativos.
        
        ### ¿Cómo funciona?
        1. **Registro anónimo**: No necesitas proporcionar tu nombre
        2. **Encuesta adaptativa**: Las preguntas se ajustan a tu nivel educativo
        3. **Análisis automático**: El sistema analiza tus respuestas en tiempo real
        4. **Feedback inmediato**: Recibes un reporte personalizado
        
        ### ¿Qué mide?
        - **Estado emocional**: ánimo, motivación, estrés
        - **Factores cognitivos**: atención, fatiga mental
        - **Indicadores de riesgo**: detección temprana de problemas
        
        ### Confidencialidad
        - Tus respuestas son completamente anónimas
        - Los datos se usan solo para análisis estadísticos
        - No afectan tu evaluación académica
        
        ### Equipo responsable
        Esta plataforma ha sido desarrollada por un equipo multidisciplinario 
        de psicólogos, educadores y desarrolladores.
        
        ---
        
        **Para preguntas o soporte:** chirinos.3110444@unir.edu.ve
        """)

# Área de Docente
else:
    if not st.session_state.get('docente_activo'):
        st.title("🔒 Acceso Docente")
        st.info("Por favor, ingresa la clave de acceso en la barra lateral para acceder al panel docente.")
        
    else:
        if st.session_state.menu_docente == "Panel docente":
            st.title("👨‍🏫 Panel Docente")
            st.markdown("Bienvenido al panel de administración docente.")
            
            # Estadísticas rápidas
            conn = get_conn()
            try:
                total_usuarios = pd.read_sql_query("SELECT COUNT(*) as count FROM usuarios", conn).iloc[0]['count']
                total_encuestas = pd.read_sql_query("SELECT COUNT(*) as count FROM encuestas", conn).iloc[0]['count']
                total_resultados = pd.read_sql_query("SELECT COUNT(*) as count FROM resultados", conn).iloc[0]['count']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Usuarios", total_usuarios)
                with col2:
                    st.metric("Total Encuestas", total_encuestas)
                with col3:
                    st.metric("Total Resultados", total_resultados)
                    
            except Exception as e:
                st.error(f"Error al obtener estadísticas: {e}")
            finally:
                conn.close()
            
            st.markdown("---")
            st.subheader("Opciones disponibles")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 Ver Dashboard Profesional", use_container_width=True):
                    st.session_state.menu_docente = "Dashboard profesional"
                    st.rerun()
                if st.button("📈 Ver Dashboard Histórico", use_container_width=True):
                    st.session_state.menu_docente = "Dashboard histórico"
                    st.rerun()
            with col2:
                if st.button("🧠 Análisis de Clustering", use_container_width=True):
                    st.session_state.menu_docente = "Clustering"
                    st.rerun()
                if st.button("🚨 Ver Alertas", use_container_width=True):
                    st.session_state.menu_docente = "Alertas inteligentes"
                    st.rerun()
        
        elif st.session_state.menu_docente == "Clustering":
            show_panel_docente()
        
        elif st.session_state.menu_docente == "Dashboard histórico":
            show_dashboard_historico()
        
        elif st.session_state.menu_docente == "Dashboard profesional":
            show_dashboard_profesional()
        
        elif st.session_state.menu_docente == "Alertas inteligentes":
            show_alertas_inteligentes()
        
        elif st.session_state.menu_docente == "Exportar datos":
            st.title("📁 Exportar Datos")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 Exportar CSV General", use_container_width=True):
                    conn = get_conn()
                    df = pd.read_sql_query("SELECT * FROM resultados", conn)
                    conn.close()
                    
                    csv_bytes = df_to_csv_bytes(df)
                    st.download_button(
                        label="📥 Descargar CSV",
                        data=csv_bytes,
                        file_name="resultados_general.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            with col2:
                if st.button("📦 Exportar ZIP Completo", use_container_width=True):
                    zip_bytes = export_all_tables_zip_bytes()
                    st.download_button(
                        label="📥 Descargar ZIP",
                        data=zip_bytes,
                        file_name="datos_completos.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
            
            with col3:
                if st.button("📄 Exportar PDF Profesional", use_container_width=True):
                    try:
                        pdf_bytes = generar_pdf_profesional_bytes()
                        st.download_button(
                            label="📥 Descargar PDF",
                            data=pdf_bytes,
                            file_name="reporte_profesional.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Error al generar PDF: {e}")
            
            st.markdown("---")
            st.subheader("📈 Exportar Excel Completo")
            
            if st.button("📊 Generar Reporte Excel Completo", use_container_width=True):
                try:
                    excel_bytes = generar_excel_completo_bytes()
                    st.download_button(
                        label="📥 Descargar Excel",
                        data=excel_bytes,
                        file_name="reporte_completo.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error al generar Excel: {e}")

# ================================================================
# PIE DE PÁGINA
# ================================================================
st.markdown("---")
st.caption("Todos los derechos reservados • Versión 2.0 • © 2025")