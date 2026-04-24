import sqlite3
from pathlib import Path
import json

DB_PATH = Path("data/banco_preguntas.db")

def conectar():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def crear_tablas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        clave TEXT NOT NULL,
        rol TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS preguntas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grado TEXT NOT NULL,
        materia TEXT NOT NULL,
        numero INTEGER NOT NULL,
        enunciado TEXT NOT NULL,
        texto_base TEXT,
        imagen TEXT,
        opciones_json TEXT NOT NULL,
        profesor_usuario TEXT,
        profesor_nombre TEXT NOT NULL,
        lote_id TEXT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def migrar_bd():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(preguntas)")
    columnas = [c[1] for c in cursor.fetchall()]

    nuevas_columnas = {
        "opciones_json": "TEXT",
        "profesor_usuario": "TEXT",
        "profesor_nombre": "TEXT",
        "texto_base": "TEXT",
        "lote_id": "TEXT",
    }

    for col, tipo in nuevas_columnas.items():
        if col not in columnas:
            cursor.execute(f"ALTER TABLE preguntas ADD COLUMN {col} {tipo}")

    conn.commit()
    conn.close()

def crear_usuarios_iniciales():
    conn = conectar()
    cursor = conn.cursor()

    usuarios = [
        ("admin", "admin123", "admin"),
        ("profesor", "profe123", "profesor")
    ]

    for usuario, clave, rol in usuarios:
        try:
            cursor.execute(
                "INSERT INTO usuarios (usuario, clave, rol) VALUES (?, ?, ?)",
                (usuario, clave, rol)
            )
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()

def validar_usuario(usuario, clave):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT usuario, rol FROM usuarios WHERE usuario=? AND clave=?",
        (usuario, clave)
    )
    data = cursor.fetchone()
    conn.close()
    return data

def guardar_preguntas_lote(preguntas):
    conn = conectar()
    cursor = conn.cursor()

    for p in preguntas:
        cursor.execute("""
        INSERT INTO preguntas (
            grado, materia, numero, enunciado, texto_base, imagen,
            opciones_json, profesor_usuario, profesor_nombre, lote_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["grado"],
            p["materia"],
            p["numero"],
            p["enunciado"],
            p.get("texto_base"),
            p.get("imagen"),
            json.dumps(p["opciones"], ensure_ascii=False),
            p.get("profesor_usuario"),
            p["profesor_nombre"],
            p.get("lote_id")
        ))

    conn.commit()
    conn.close()

def listar_preguntas(grado=None, materia=None):
    conn = conectar()
    cursor = conn.cursor()

    query = """
    SELECT id, grado, materia, numero, enunciado, texto_base, imagen,
           opciones_json, profesor_usuario, profesor_nombre, lote_id, fecha
    FROM preguntas
    WHERE 1=1
    """
    params = []

    if grado and grado != "Todos":
        query += " AND grado=?"
        params.append(grado)

    if materia and materia != "Todas":
        query += " AND materia=?"
        params.append(materia)

    query += " ORDER BY materia, numero, id"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    preguntas = []
    for r in rows:
        try:
            opciones = json.loads(r[7]) if r[7] else {}
        except Exception:
            opciones = {}

        preguntas.append({
            "id": r[0],
            "grado": r[1],
            "materia": r[2],
            "numero": r[3],
            "enunciado": r[4],
            "texto_base": r[5],
            "imagen": r[6],
            "opciones": opciones,
            "profesor_usuario": r[8],
            "profesor_nombre": r[9],
            "lote_id": r[10],
            "fecha": r[11],
        })
    return preguntas

def obtener_grados():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT grado FROM preguntas ORDER BY grado")
    data = [x[0] for x in cursor.fetchall()]
    conn.close()
    return data

def obtener_materias():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT materia FROM preguntas ORDER BY materia")
    data = [x[0] for x in cursor.fetchall()]
    conn.close()
    return data

def eliminar_preguntas_por_ids(ids):
    if not ids:
        return
    conn = conectar()
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in ids)
    cursor.execute(f"DELETE FROM preguntas WHERE id IN ({placeholders})", ids)
    conn.commit()
    conn.close()
