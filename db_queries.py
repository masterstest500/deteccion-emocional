"""Consultas SQLite centralizadas. Usa DB_PATH desde config."""
import json
import sqlite3
from datetime import datetime
from typing import Any, Optional, Union

import pandas as pd

from config import DB_PATH


def get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def save_user(rol: str, edad: Any, nivel: str) -> int:
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO usuarios (rol, edad, nivel) VALUES (?, ?, ?)",
            (rol, edad, nivel),
        )
        uid = c.lastrowid
        conn.commit()
        return int(uid)
    finally:
        conn.close()


def save_survey(
    uid: int,
    respuestas: dict,
    fecha: Optional[Union[datetime, str]] = None,
) -> int:
    """Inserta encuesta. Si se pasa fecha, se usa en lugar del DEFAULT."""
    conn = get_conn()
    try:
        c = conn.cursor()
        payload = json.dumps(respuestas, ensure_ascii=False)
        if fecha is None:
            c.execute(
                "INSERT INTO encuestas (usuario_id, respuestas) VALUES (?, ?)",
                (uid, payload),
            )
        else:
            fecha_str = (
                fecha.strftime("%Y-%m-%d %H:%M:%S")
                if hasattr(fecha, "strftime")
                else str(fecha)
            )
            c.execute(
                "INSERT INTO encuestas (usuario_id, respuestas, fecha) VALUES (?, ?, ?)",
                (uid, payload, fecha_str),
            )
        eid = c.lastrowid
        conn.commit()
        return int(eid)
    finally:
        conn.close()


def save_result(
    eid: int,
    riesgo: str,
    puntaje: float,
    detalle: dict,
    fecha: Optional[Union[datetime, str]] = None,
) -> None:
    """Inserta resultado. Si no se pasa fecha, usa la hora actual."""
    conn = get_conn()
    try:
        c = conn.cursor()
        detalle_json = json.dumps(detalle, ensure_ascii=False)
        if fecha is None:
            fecha_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            fecha_str = (
                fecha.strftime("%Y-%m-%d %H:%M:%S")
                if hasattr(fecha, "strftime")
                else str(fecha)
            )
        c.execute(
            "INSERT INTO resultados (encuesta_id, riesgo, puntaje, detalle, fecha) VALUES (?, ?, ?, ?, ?)",
            (eid, riesgo, puntaje, detalle_json, fecha_str),
        )
        conn.commit()
    finally:
        conn.close()


def fetch_table_all(table: str) -> pd.DataFrame:
    """SELECT * FROM una tabla (usuarios, encuestas, resultados, etc.)."""
    conn = get_conn()
    try:
        return pd.read_sql_query(f"SELECT * FROM {table}", conn)
    finally:
        conn.close()


def fetch_resultados_all() -> pd.DataFrame:
    return fetch_table_all("resultados")


def fetch_usuarios_ids_ordered() -> pd.DataFrame:
    conn = get_conn()
    try:
        return pd.read_sql_query(
            "SELECT DISTINCT id FROM usuarios ORDER BY id", conn
        )
    finally:
        conn.close()


def fetch_counts_resumen() -> tuple:
    """Totales para panel docente: usuarios, encuestas, resultados."""
    conn = get_conn()
    try:
        total_usuarios = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM usuarios", conn
        ).iloc[0]["count"]
        total_encuestas = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM encuestas", conn
        ).iloc[0]["count"]
        total_resultados = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM resultados", conn
        ).iloc[0]["count"]
        return total_usuarios, total_encuestas, total_resultados
    finally:
        conn.close()


def fetch_riesgo_counts_por_resultado() -> pd.DataFrame:
    """Agrupa cantidad de resultados por nivel de riesgo (semáforo docente)."""
    conn = get_conn()
    try:
        return pd.read_sql_query(
            """
            SELECT r.riesgo, COUNT(*) as cantidad
            FROM resultados r
            JOIN encuestas e ON r.encuesta_id = e.id
            GROUP BY r.riesgo
            """,
            conn,
        )
    finally:
        conn.close()


def fetch_historial_usuario(
    usuario_id: int, *, include_respuestas_y_nivel: bool = False
) -> pd.DataFrame:
    """
    Evaluaciones de un usuario ordenadas por fecha descendente.

    - include_respuestas_y_nivel=False: columnas mínimas (historial estudiante).
    - include_respuestas_y_nivel=True: añade respuestas, edad y nivel (psicólogo).
    """
    conn = get_conn()
    try:
        if include_respuestas_y_nivel:
            sql = """
                SELECT
                    r.fecha,
                    r.puntaje,
                    r.riesgo,
                    r.detalle,
                    e.respuestas,
                    u.edad,
                    u.nivel
                FROM resultados r
                JOIN encuestas e ON r.encuesta_id = e.id
                JOIN usuarios u ON e.usuario_id = u.id
                WHERE e.usuario_id = ?
                ORDER BY r.fecha DESC
            """
        else:
            sql = """
                SELECT
                    r.fecha,
                    r.puntaje,
                    r.riesgo,
                    r.detalle
                FROM resultados r
                JOIN encuestas e ON r.encuesta_id = e.id
                WHERE e.usuario_id = ?
                ORDER BY r.fecha DESC
            """
        return pd.read_sql_query(sql, conn, params=(usuario_id,))
    finally:
        conn.close()


def fetch_ultimas_sesiones_usuario_para_alertas(usuario_id, limit: int = 5) -> pd.DataFrame:
    """Historial reciente para generate_smart_alerts (parametrizado)."""
    conn = get_conn()
    try:
        return pd.read_sql_query(
            """
            SELECT r.puntaje, r.detalle, r.fecha
            FROM resultados r
            JOIN encuestas e ON r.encuesta_id = e.id
            WHERE e.usuario_id = ?
            ORDER BY r.fecha DESC
            LIMIT ?
            """,
            conn,
            params=(usuario_id, limit),
        )
    finally:
        conn.close()


def fetch_resultados_clustering() -> pd.DataFrame:
    """Datos para panel docente — clustering."""
    conn = get_conn()
    try:
        return pd.read_sql_query(
            """
            SELECT r.id, r.puntaje, r.detalle, r.fecha, u.id as usuario_id, u.nivel
            FROM resultados r
            JOIN encuestas e ON r.encuesta_id = e.id
            JOIN usuarios u ON e.usuario_id = u.id
            """,
            conn,
        )
    finally:
        conn.close()


def fetch_dashboard_historico() -> pd.DataFrame:
    """Serie temporal completa para dashboard histórico (docente y psicólogo)."""
    conn = get_conn()
    try:
        return pd.read_sql_query(
            """
            SELECT r.id, r.puntaje, r.riesgo, r.detalle, r.fecha,
                   e.usuario_id,
                   e.respuestas, u.rol, u.edad, u.nivel as usuario_nivel
            FROM resultados r
            JOIN encuestas e ON r.encuesta_id = e.id
            JOIN usuarios u ON e.usuario_id = u.id
            ORDER BY r.fecha ASC
            """,
            conn,
        )
    finally:
        conn.close()


def fetch_dashboard_profesional() -> pd.DataFrame:
    conn = get_conn()
    try:
        return pd.read_sql_query(
            """
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
            """,
            conn,
        )
    finally:
        conn.close()


def fetch_alertas_riesgo_alto() -> pd.DataFrame:
    """Casos en riesgo alto — vista alertas inteligentes (fecha desde encuesta)."""
    conn = get_conn()
    try:
        return pd.read_sql_query(
            """
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
            """,
            conn,
        )
    finally:
        conn.close()


def fetch_casos_prioritarios() -> pd.DataFrame:
    """Riesgo alto — vista casos prioritarios (fecha del resultado)."""
    conn = get_conn()
    try:
        return pd.read_sql_query(
            """
            SELECT
                u.id as usuario_id,
                u.nivel,
                u.edad,
                r.puntaje,
                r.riesgo,
                r.detalle,
                r.fecha,
                e.respuestas
            FROM resultados r
            JOIN encuestas e ON r.encuesta_id = e.id
            JOIN usuarios u ON e.usuario_id = u.id
            WHERE r.riesgo = 'Alto'
            ORDER BY r.puntaje DESC
            """,
            conn,
        )
    finally:
        conn.close()


def fetch_pdf_resultados_por_usuario(usuario_id: Optional[int] = None) -> pd.DataFrame:
    """Datos para generar_pdf_profesional_bytes (individual o general)."""
    conn = get_conn()
    try:
        if usuario_id is not None:
            return pd.read_sql_query(
                """
                SELECT r.puntaje, r.riesgo, r.detalle, r.fecha, e.respuestas
                FROM resultados r
                JOIN encuestas e ON r.encuesta_id = e.id
                WHERE e.usuario_id = ?
                ORDER BY r.fecha DESC
                """,
                conn,
                params=(usuario_id,),
            )
        return pd.read_sql_query(
            """
            SELECT r.puntaje, r.riesgo, r.detalle, r.fecha, e.respuestas, u.nivel
            FROM resultados r
            JOIN encuestas e ON r.encuesta_id = e.id
            JOIN usuarios u ON e.usuario_id = u.id
            """,
            conn,
        )
    finally:
        conn.close()


def fetch_excel_export_bundle() -> tuple:
    """Tupla (df_usuarios, df_encuestas, df_resultados) para Excel completo."""
    conn = get_conn()
    try:
        df_usuarios = pd.read_sql_query("SELECT * FROM usuarios", conn)
        df_encuestas = pd.read_sql_query(
            """
            SELECT e.*, u.rol, u.edad, u.nivel as usuario_nivel
            FROM encuestas e
            JOIN usuarios u ON e.usuario_id = u.id
            """,
            conn,
        )
        df_resultados = pd.read_sql_query(
            """
            SELECT r.*, e.respuestas, u.rol, u.edad, u.nivel as usuario_nivel
            FROM resultados r
            JOIN encuestas e ON r.encuesta_id = e.id
            JOIN usuarios u ON e.usuario_id = u.id
            """,
            conn,
        )
        return df_usuarios, df_encuestas, df_resultados
    finally:
        conn.close()
