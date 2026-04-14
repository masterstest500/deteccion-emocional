"""Configuración global, rutas y constantes de la aplicación."""
import os

import streamlit as st

PAGE_CONFIG = {
    "page_title": "Plataforma de Detección Temprana",
    "page_icon": "💡",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "images")
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "sistema.db")
LOGO_PATH = os.path.join(BASE_DIR, "images", "Logo.png")

LOADER_SECONDS = 5
AUDIO_FILE_PATH = "static/clic.wav"


def configure_page() -> None:
    """Aplica la configuración global de Streamlit."""
    st.set_page_config(**PAGE_CONFIG)


def ensure_directories() -> None:
    """Crea carpetas necesarias si no existen."""
    for folder in (ASSETS_DIR, DATA_DIR):
        if not os.path.exists(folder):
            os.makedirs(folder)


def initialize_database() -> None:
    """Inicializa la base de datos local."""
    from database import init_db

    ensure_directories()
    init_db()

# ================================================================
# RIESGO (UNIFICACIÓN VISUAL GLOBAL)
# ================================================================

RISK_LABELS = {
    "bajo": "🟢 Bajo",
    "medio": "🟡 Medio",
    "alto": "🔴 Alto"
}

RISK_COLORS = {
    "🟢 Bajo": "#2ecc71",
    "🟡 Medio": "#f1c40f",
    "🔴 Alto": "#e74c3c"
}