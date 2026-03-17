import sqlite3
import json
import os
from datetime import datetime
from init_db import get_db_path

DB_PATH = get_db_path()

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def save_user(rol, edad, nivel):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO usuarios (rol, edad, nivel) VALUES (?, ?, ?)", (rol, edad, nivel))
    uid = c.lastrowid
    conn.commit()
    conn.close()
    return uid

def save_survey(uid, respuestas):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO encuestas (usuario_id, respuestas) VALUES (?, ?)", 
              (uid, json.dumps(respuestas, ensure_ascii=False)))
    eid = c.lastrowid
    conn.commit()
    conn.close()
    return eid

def save_result(eid, riesgo, puntaje, detalle):
    conn = get_conn()
    c = conn.cursor()
    detalle_json = json.dumps(detalle, ensure_ascii=False)
    c.execute("INSERT INTO resultados (encuesta_id, riesgo, puntaje, detalle, fecha) VALUES (?, ?, ?, ?, ?)",
              (eid, riesgo, puntaje, detalle_json, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()