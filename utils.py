from config import RISK_LABELS
import pandas as pd


def apply_riesgo_labels(df):
    """
    Unifica el sistema de riesgo visual en todo el proyecto.
    Genera riesgo_label consistente para dashboards y gráficos.
    """
    df = df.copy()

    # normalización robusta (evita errores silenciosos)
    df["riesgo"] = (
        df["riesgo"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # mapping seguro
    df["riesgo_label"] = df["riesgo"].map(RISK_LABELS)

    # fallback por seguridad (evita NaN en dashboards)
    df["riesgo_label"] = df["riesgo_label"].fillna("⚪ Sin clasificar")

    return df


def ensure_numeric(df, cols):
    """
    Fuerza columnas a numéricas sin romper el pipeline.
    """
    df = df.copy()

    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    return df