import sqlite3
import pandas as pd
import os
import sys

# Añadir el directorio actual al path para importar init_db
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from init_db import get_db_path
    DB_PATH = get_db_path()
except ImportError:
    # Fallback si no puede importar
    DB_PATH = os.path.join("data", "sistema.db")

print(f"🔍 Conectando a: {DB_PATH}")

if not os.path.exists(DB_PATH):
    print(f"❌ ERROR: La base de datos no existe en {DB_PATH}")
    print("Ejecuta primero la aplicación principal para crear la base de datos.")
    sys.exit(1)

try:
    # Conectar a la base de datos
    conn = sqlite3.connect(DB_PATH)
    
    print("\n" + "="*60)
    print("📊 VISOR DE BASE DE DATOS - PLATAFORMA DE DETECCIÓN")
    print("="*60)
    
    # Verificar tablas existentes
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tablas = cursor.fetchall()
    
    print(f"\n📋 Tablas encontradas ({len(tablas)}):")
    for tabla in tablas:
        print(f"  - {tabla[0]}")
    
    print("\n" + "="*60)
    print("📋 ÚLTIMOS 10 RESULTADOS REGISTRADOS")
    print("="*60)
    
    try:
        # Leemos con pandas para que se vea bonita la tabla
        df = pd.read_sql_query("""
            SELECT 
                r.id,
                r.riesgo,
                r.puntaje,
                r.fecha,
                u.nivel,
                u.edad
            FROM resultados r
            JOIN encuestas e ON r.encuesta_id = e.id
            JOIN usuarios u ON e.usuario_id = u.id
            ORDER BY r.id DESC 
            LIMIT 10
        """, conn)
        
        if not df.empty:
            print(df.to_string(index=False))
        else:
            print("ℹ️ No hay resultados registrados aún.")
            
    except Exception as e:
        print(f"⚠️ Error leyendo resultados: {e}")
        # Intentar versión simple
        df_simple = pd.read_sql_query("SELECT * FROM resultados ORDER BY id DESC LIMIT 5", conn)
        if not df_simple.empty:
            print("\nResultados (vista simple):")
            print(df_simple[['id', 'riesgo', 'puntaje', 'fecha']].to_string(index=False))

    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS GENERALES")
    print("="*60)
    
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    n_usuarios = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM encuestas")
    n_encuestas = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM resultados")
    n_resultados = cursor.fetchone()[0]
    
    print(f"👥 Total Usuarios: {n_usuarios}")
    print(f"📝 Total Encuestas: {n_encuestas}")
    print(f"📊 Total Resultados: {n_resultados}")
    
    if n_encuestas == n_resultados:
        print("✅ Integridad Correcta: Cada encuesta tiene su resultado.")
    else:
        print(f"⚠️ ALERTA: Discrepancia encontrada.")
        print(f"   Encuestas: {n_encuestas}, Resultados: {n_resultados}")
        print(f"   Diferencia: {abs(n_encuestas - n_resultados)}")
    
    # Distribución de riesgo
    print("\n📈 DISTRIBUCIÓN DE RIESGO:")
    cursor.execute("""
        SELECT riesgo, COUNT(*) as cantidad
        FROM resultados 
        GROUP BY riesgo 
        ORDER BY CASE riesgo 
            WHEN 'Alto' THEN 1 
            WHEN 'Medio' THEN 2 
            WHEN 'Bajo' THEN 3 
            ELSE 4 
        END
    """)
    riesgos = cursor.fetchall()
    
    for riesgo, cantidad in riesgos:
        if n_resultados > 0:
            porcentaje = (cantidad / n_resultados) * 100
            print(f"  {riesgo}: {cantidad} ({porcentaje:.1f}%)")
        else:
            print(f"  {riesgo}: {cantidad}")
    
    print("\n" + "="*60)
    print("👥 DISTRIBUCIÓN POR NIVEL EDUCATIVO:")
    print("="*60)
    
    cursor.execute("""
        SELECT nivel, COUNT(*) as cantidad
        FROM usuarios 
        GROUP BY nivel
        ORDER BY CASE nivel
            WHEN 'Primaria' THEN 1
            WHEN 'Secundaria' THEN 2
            WHEN 'Universidad' THEN 3
            ELSE 4
        END
    """)
    niveles = cursor.fetchall()
    
    for nivel, cantidad in niveles:
        print(f"  {nivel}: {cantidad} usuarios")

except sqlite3.Error as e:
    print(f"❌ Error de SQLite: {e}")
except Exception as e:
    print(f"❌ Error inesperado: {e}")
finally:
    if 'conn' in locals():
        conn.close()
    print("\n" + "="*60)
    print("✅ Verificación completada.")
    print("="*60)