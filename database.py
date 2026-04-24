import sqlite3
from pathlib import Path

DB_PATH = Path("data/banco_preguntas.db")

def conectar():
    DB_PATH.parent.mkdir(exist_ok=True)
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
        imagen TEXT,
        opcion_a TEXT NOT NULL,
        opcion_b TEXT NOT NULL,
        opcion_c TEXT NOT NULL,
        opcion_d TEXT NOT NULL,
        profesor TEXT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

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

def guardar_pregunta(p):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO preguntas (
        grado, materia, numero, enunciado, imagen,
        opcion_a, opcion_b, opcion_c, opcion_d, profesor
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        p["grado"],
        p["materia"],
        p["numero"],
        p["enunciado"],
        p.get("imagen"),
        p["opciones"]["A"],
        p["opciones"]["B"],
        p["opciones"]["C"],
        p["opciones"]["D"],
        p.get("profesor")
    ))
    conn.commit()
    conn.close()

def listar_preguntas(grado=None, materia=None):
    conn = conectar()
    cursor = conn.cursor()

    query = "SELECT id, grado, materia, numero, enunciado, imagen, opcion_a, opcion_b, opcion_c, opcion_d, profesor, fecha FROM preguntas WHERE 1=1"
    params = []

    if grado and grado != "Todos":
        query += " AND grado=?"
        params.append(grado)

    if materia and materia != "Todas":
        query += " AND materia=?"
        params.append(materia)

    query += " ORDER BY grado, materia, numero"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    preguntas = []
    for r in rows:
        preguntas.append({
            "id": r[0],
            "grado": r[1],
            "materia": r[2],
            "numero": r[3],
            "enunciado": r[4],
            "imagen": r[5],
            "opciones": {
                "A": r[6],
                "B": r[7],
                "C": r[8],
                "D": r[9],
            },
            "profesor": r[10],
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
