import sqlite3
from pathlib import Path

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
        opcion_a TEXT NOT NULL,
        opcion_b TEXT NOT NULL,
        opcion_c TEXT NOT NULL,
        opcion_d TEXT NOT NULL,
        profesor TEXT,
        profesor_nombre TEXT,
        archivo_origen TEXT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS archivos_subidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_archivo TEXT NOT NULL,
        tipo TEXT NOT NULL,
        profesor_usuario TEXT,
        profesor_nombre TEXT,
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
        "texto_base": "TEXT",
        "profesor_nombre": "TEXT",
        "archivo_origen": "TEXT"
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

def registrar_archivo(nombre_archivo, tipo, profesor_usuario=None, profesor_nombre=None):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO archivos_subidos (nombre_archivo, tipo, profesor_usuario, profesor_nombre)
    VALUES (?, ?, ?, ?)
    """, (nombre_archivo, tipo, profesor_usuario, profesor_nombre))
    conn.commit()
    conn.close()

def guardar_pregunta(p):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO preguntas (
        grado, materia, numero, enunciado, texto_base, imagen,
        opcion_a, opcion_b, opcion_c, opcion_d,
        profesor, profesor_nombre, archivo_origen
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        p["grado"],
        p["materia"],
        p["numero"],
        p["enunciado"],
        p.get("texto_base"),
        p.get("imagen"),
        p["opciones"]["A"],
        p["opciones"]["B"],
        p["opciones"]["C"],
        p["opciones"]["D"],
        p.get("profesor"),
        p.get("profesor_nombre"),
        p.get("archivo_origen")
    ))
    conn.commit()
    conn.close()

def listar_preguntas(grado=None, materia=None):
    conn = conectar()
    cursor = conn.cursor()

    query = """
    SELECT id, grado, materia, numero, enunciado, texto_base, imagen,
           opcion_a, opcion_b, opcion_c, opcion_d,
           profesor, profesor_nombre, archivo_origen, fecha
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
        preguntas.append({
            "id": r[0],
            "grado": r[1],
            "materia": r[2],
            "numero": r[3],
            "enunciado": r[4],
            "texto_base": r[5],
            "imagen": r[6],
            "opciones": {
                "A": r[7],
                "B": r[8],
                "C": r[9],
                "D": r[10],
            },
            "profesor": r[11],
            "profesor_nombre": r[12],
            "archivo_origen": r[13],
            "fecha": r[14],
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

def eliminar_pregunta(id_pregunta):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM preguntas WHERE id=?", (id_pregunta,))
    conn.commit()
    conn.close()

def eliminar_preguntas_por_ids(ids):
    if not ids:
        return
    conn = conectar()
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in ids)
    cursor.execute(f"DELETE FROM preguntas WHERE id IN ({placeholders})", ids)
    conn.commit()
    conn.close()

def listar_archivos_subidos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, nombre_archivo, tipo, profesor_usuario, profesor_nombre, fecha
    FROM archivos_subidos
    ORDER BY fecha DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "nombre_archivo": r[1],
            "tipo": r[2],
            "profesor_usuario": r[3],
            "profesor_nombre": r[4],
            "fecha": r[5],
        }
        for r in rows
    ]

def eliminar_archivo_registro(id_archivo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre_archivo, tipo FROM archivos_subidos WHERE id=?", (id_archivo,))
    row = cursor.fetchone()

    if row:
        nombre_archivo, tipo = row
        if tipo == "documento":
            ruta = Path("data/uploads") / nombre_archivo
        else:
            ruta = Path("data/images") / nombre_archivo

        if ruta.exists():
            ruta.unlink()

        cursor.execute("DELETE FROM archivos_subidos WHERE id=?", (id_archivo,))
        conn.commit()

    conn.close()

def eliminar_archivos_por_ids(ids):
    for id_archivo in ids:
        eliminar_archivo_registro(id_archivo)
