"""Esquema SQLite: creación de tablas. Conexión vía db_queries.get_conn."""
import os
import sqlite3

from config import DATA_DIR
from db_queries import get_conn


def init_db() -> None:
    """Crea la estructura de la BD si no existe (idempotente)."""
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = None
    try:
        conn = get_conn()
        c = conn.cursor()

        c.execute(
            """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rol TEXT NOT NULL,
            edad INTEGER,
            nivel TEXT NOT NULL
        );
        """
        )

        c.execute(
            """
        CREATE TABLE IF NOT EXISTS encuestas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            respuestas TEXT,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        );
        """
        )

        c.execute(
            """
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            encuesta_id INTEGER NOT NULL,
            puntaje REAL NOT NULL,
            riesgo TEXT NOT NULL,
            detalle TEXT,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(encuesta_id) REFERENCES encuestas(id)
        );
        """
        )

        conn.commit()
        print("✅ Base de datos inicializada o verificada correctamente.")

    except sqlite3.Error as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    from config import DB_PATH

    confirm = input(
        "¿Estás seguro de que quieres reiniciar la base de datos? (si/no): "
    )
    if confirm.lower() == "si":
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print("🗑️ Base de datos anterior eliminada.")
        init_db()
        print("✅ Base de datos reiniciada y creada exitosamente.")
    else:
        print("❌ Operación cancelada.")
