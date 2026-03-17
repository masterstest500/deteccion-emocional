# init_db.py 

import os
import sqlite3

# 🚨 CORRECCIÓN: Definir DB_PATH en UN solo lugar
# Mejor hacerlo relativo o usar variable de entorno
DB_PATH = os.path.join("data", "sistema.db")


def init_db():
    """Crea la estructura de la BD si no existe (idempotente)."""
    
    # 1. Asegurar la existencia de la carpeta 'data'
    basedir = os.path.dirname(DB_PATH)
    if basedir and not os.path.exists(basedir):
        os.makedirs(basedir)
        
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 2. CREAR TABLAS (USANDO IF NOT EXISTS)
        
        # Tabla USUARIOS
        c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rol TEXT NOT NULL,
            edad INTEGER,
            nivel TEXT NOT NULL
        );
        """)

        # Tabla ENCUESTAS (Sintaxis y campos corregidos)
        c.execute("""
        CREATE TABLE IF NOT EXISTS encuestas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            respuestas TEXT,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP, 
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        );
        """)

        # Tabla RESULTADOS (Campos clave definidos como NOT NULL)
        c.execute("""
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            encuesta_id INTEGER NOT NULL,
            puntaje REAL NOT NULL, 
            riesgo TEXT NOT NULL, 
            detalle TEXT,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP, 
            FOREIGN KEY(encuesta_id) REFERENCES encuestas(id)
        );
        """)

        conn.commit()
        print("✅ Base de datos inicializada o verificada correctamente.")
        
    except sqlite3.Error as e:
        print(f"❌ Error al inicializar la base de datos: {e}") 
    finally:
        if conn:
            conn.close()


def get_db_path():
    """Devuelve la ruta de la base de datos para usar en otros módulos."""
    return DB_PATH


# Permite ejecutar el script directamente para forzar un reinicio (reset)
if __name__ == "__main__":
    confirm = input("¿Estás seguro de que quieres reiniciar la base de datos? (si/no): ")
    if confirm.lower() == "si":
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH) 
            print("🗑️ Base de datos anterior eliminada.")
        init_db()
        print("✅ Base de datos reiniciada y creada exitosamente.")
    else:
        print("❌ Operación cancelada.")