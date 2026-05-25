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
        rol TEXT NOT NULL,
        nombre_completo TEXT,
        documento TEXT
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
        opciones_imagenes_json TEXT,
        profesor_usuario TEXT NOT NULL,
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

    cursor.execute("PRAGMA table_info(usuarios)")
    columnas_usuarios = [c[1] for c in cursor.fetchall()]
    
    if "nombre_completo" not in columnas_usuarios:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN nombre_completo TEXT")
    if "documento" not in columnas_usuarios:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN documento TEXT")

    cursor.execute("PRAGMA table_info(preguntas)")
    columnas = [c[1] for c in cursor.fetchall()]

    nuevas_columnas = {
        "opciones_json": "TEXT",
        "opciones_imagenes_json": "TEXT",
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
        ("admin", "admin123", "admin", "Administrador", "00000000"),
        ("dconeo", "profe123", "profesor", "Coneo Arrieta, Donaida Mercedes", "26006970"),
        ("aflorez", "profe123", "profesor", "FLOREZ AGRESOTT, ANDRES FELIPE", "1003368522"),
        ("gguerra", "profe123", "profesor", "Guerra Diaz, Gusmara Lucia", "25889369"),
        ("yguevara", "profe123", "profesor", "Guevara Bohorquez, Yohn Jairo", "1067845560"),
        ("amestra", "profe123", "profesor", "Mestra Suárez, Armando Rafael", "73578636"),
        ("aordosgoitia", "profe123", "profesor", "Ordosgoitia Doria, Ada Irene", "26006019"),
        ("cortiz", "profe123", "profesor", "ORTIZ POLO, CESAR ANDRES", "1067406604"),
        ("lpacheco", "profe123", "profesor", "Pacheco Nuñez, Ledys Ruth", "30665168"),
        ("rpadilla", "profe123", "profesor", "Padilla Arrazola, Reina Judith", "30660321"),
        ("aracero", "profe123", "profesor", "RACERO FERNANDEZ, ADRIANA ISABEL", "30661106"),
        ("ltanos", "profe123", "profesor", "TANOS ESTRELLA, LIZ SANDRA", "25786141"),
        ("jvergara", "profe123", "profesor", "VERGARA SOTO, JOSÉ RAFAEL", "1065374396"),
    ]

    for usuario, clave, rol, nombre_completo, documento in usuarios:
        try:
            cursor.execute("""
                INSERT INTO usuarios (usuario, clave, rol, nombre_completo, documento) 
                VALUES (?, ?, ?, ?, ?)
            """, (usuario, clave, rol, nombre_completo, documento))
        except sqlite3.IntegrityError:
            cursor.execute("""
                UPDATE usuarios 
                SET nombre_completo = ?, documento = ?
                WHERE usuario = ?
            """, (nombre_completo, documento, usuario))

    conn.commit()
    conn.close()

def validar_usuario(usuario, clave):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT usuario, rol, nombre_completo FROM usuarios WHERE usuario=? AND clave=?",
        (usuario, clave)
    )
    data = cursor.fetchone()
    conn.close()
    return data

def obtener_todos_usuarios():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT usuario, rol, nombre_completo, documento FROM usuarios ORDER BY nombre_completo")
    data = cursor.fetchall()
    conn.close()
    return data

def obtener_profesores():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT usuario, nombre_completo FROM usuarios WHERE rol = 'profesor' ORDER BY nombre_completo")
    data = cursor.fetchall()
    conn.close()
    return data

def guardar_preguntas_lote(preguntas):
    conn = conectar()
    cursor = conn.cursor()

    for p in preguntas:
        cursor.execute("""
        INSERT INTO preguntas (
            grado, materia, numero, enunciado, texto_base, imagen,
            opciones_json, opciones_imagenes_json, profesor_usuario, profesor_nombre, lote_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["grado"],
            p["materia"],
            p["numero"],
            p["enunciado"],
            p.get("texto_base"),
            p.get("imagen"),
            json.dumps(p["opciones"], ensure_ascii=False),
            json.dumps(p.get("opciones_imagenes", {}), ensure_ascii=False),
            p["profesor_usuario"],
            p["profesor_nombre"],
            p.get("lote_id")
        ))

    conn.commit()
    conn.close()

def listar_preguntas(grado=None, materia=None, profesor_usuario=None):
    conn = conectar()
    cursor = conn.cursor()

    query = """
    SELECT id, grado, materia, numero, enunciado, texto_base, imagen,
           opciones_json, opciones_imagenes_json, profesor_usuario, profesor_nombre, lote_id, fecha
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

    if profesor_usuario and profesor_usuario != "Todos":
        query += " AND profesor_usuario=?"
        params.append(profesor_usuario)

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
        try:
            opciones_imagenes = json.loads(r[8]) if r[8] else {}
        except Exception:
            opciones_imagenes = {}

        preguntas.append({
            "id": r[0],
            "grado": r[1],
            "materia": r[2],
            "numero": r[3],
            "enunciado": r[4],
            "texto_base": r[5],
            "imagen": r[6],
            "opciones": opciones,
            "opciones_imagenes": opciones_imagenes,
            "profesor_usuario": r[9],
            "profesor_nombre": r[10],
            "lote_id": r[11],
            "fecha": r[12],
        })
    return preguntas

def obtener_preguntas_por_profesor(profesor_usuario, grado=None, materia=None):
    """Obtiene solo las preguntas de un profesor específico"""
    return listar_preguntas(grado, materia, profesor_usuario)

# ========== FUNCIONES FALTANTES QUE CAUSABAN EL ERROR ==========

def obtener_pregunta_por_id(pregunta_id):
    """Obtiene una pregunta por su ID"""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, grado, materia, numero, enunciado, texto_base, imagen,
               opciones_json, opciones_imagenes_json, profesor_usuario, profesor_nombre, lote_id, fecha
        FROM preguntas WHERE id = ?
    """, (pregunta_id,))
    r = cursor.fetchone()
    conn.close()
    
    if r:
        try:
            opciones = json.loads(r[7]) if r[7] else {}
        except Exception:
            opciones = {}
        try:
            opciones_imagenes = json.loads(r[8]) if r[8] else {}
        except Exception:
            opciones_imagenes = {}
        
        return {
            "id": r[0],
            "grado": r[1],
            "materia": r[2],
            "numero": r[3],
            "enunciado": r[4],
            "texto_base": r[5],
            "imagen": r[6],
            "opciones": opciones,
            "opciones_imagenes": opciones_imagenes,
            "profesor_usuario": r[9],
            "profesor_nombre": r[10],
            "lote_id": r[11],
            "fecha": r[12],
        }
    return None

def actualizar_pregunta(pregunta_id, enunciado, texto_base, imagen, opciones, opciones_imagenes=None):
    """Actualiza una pregunta existente"""
    conn = conectar()
    cursor = conn.cursor()
    if opciones_imagenes:
        cursor.execute("""
            UPDATE preguntas 
            SET enunciado = ?, texto_base = ?, imagen = ?, opciones_json = ?, opciones_imagenes_json = ?
            WHERE id = ?
        """, (enunciado, texto_base, imagen, json.dumps(opciones, ensure_ascii=False), 
              json.dumps(opciones_imagenes, ensure_ascii=False), pregunta_id))
    else:
        cursor.execute("""
            UPDATE preguntas 
            SET enunciado = ?, texto_base = ?, imagen = ?, opciones_json = ?
            WHERE id = ?
        """, (enunciado, texto_base, imagen, json.dumps(opciones, ensure_ascii=False), pregunta_id))
    conn.commit()
    conn.close()

def actualizar_pregunta_completa(pregunta_id, enunciado, texto_base, imagen, opciones, opciones_imagenes):
    """Actualiza una pregunta existente incluyendo las imágenes de opciones"""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE preguntas 
        SET enunciado = ?, texto_base = ?, imagen = ?, opciones_json = ?, opciones_imagenes_json = ?
        WHERE id = ?
    """, (enunciado, texto_base, imagen, json.dumps(opciones, ensure_ascii=False), json.dumps(opciones_imagenes, ensure_ascii=False), pregunta_id))
    conn.commit()
    conn.close()

# ========== FIN FUNCIONES FALTANTES ==========

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

def obtener_todos_bancos_profesores():
    """Obtiene un resumen de cuántas preguntas tiene cada profesor"""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT profesor_usuario, profesor_nombre, COUNT(*) as total, 
               GROUP_CONCAT(DISTINCT grado) as grados,
               GROUP_CONCAT(DISTINCT materia) as materias
        FROM preguntas 
        GROUP BY profesor_usuario, profesor_nombre
        ORDER BY profesor_nombre
    """)
    data = cursor.fetchall()
    conn.close()
    
    resultados = []
    for r in data:
        resultados.append({
            "usuario": r[0],
            "nombre": r[1],
            "total_preguntas": r[2],
            "grados": r[3].split(',') if r[3] else [],
            "materias": r[4].split(',') if r[4] else []
        })
    return resultados


# Agregar esta función al final de database.py

def actualizar_pregunta_con_tipos(pregunta_id, enunciado, texto_base, imagen, 
                                   opciones, opciones_tipos, opciones_imagenes,
                                   opciones_ecuaciones):
    """Actualiza una pregunta incluyendo tipos de opciones y ecuaciones"""
    conn = conectar()
    cursor = conn.cursor()
    
    # Guardar toda la información de opciones en un solo JSON
    opciones_data = {
        "textos": opciones,
        "tipos": opciones_tipos,
        "imagenes": opciones_imagenes,
        "ecuaciones": opciones_ecuaciones
    }
    
    cursor.execute("""
        UPDATE preguntas 
        SET enunciado = ?, texto_base = ?, imagen = ?, 
            opciones_json = ?, opciones_imagenes_json = ?
        WHERE id = ?
    """, (enunciado, texto_base, imagen, 
          json.dumps(opciones_data, ensure_ascii=False), 
          json.dumps(opciones_imagenes, ensure_ascii=False), 
          pregunta_id))
    conn.commit()
    conn.close()