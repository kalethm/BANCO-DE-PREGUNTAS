import re
from pathlib import Path
from docx import Document

def leer_docx(ruta):
    doc = Document(ruta)
    textos = []
    for p in doc.paragraphs:
        if p.text.strip():
            textos.append(p.text.strip())
    return "\n".join(textos)

def leer_txt(ruta):
    try:
        return Path(ruta).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Path(ruta).read_text(encoding="latin-1")

def extraer_texto(ruta):
    ruta = Path(ruta)
    if ruta.suffix.lower() == ".docx":
        return leer_docx(ruta)
    elif ruta.suffix.lower() == ".txt":
        return leer_txt(ruta)
    else:
        raise ValueError("Solo se permiten archivos .docx o .txt")

def limpiar_opcion(texto):
    return texto.strip().replace("\n", " ")

def parsear_preguntas(texto):
    grado_match = re.search(r"GRADO:\s*(.+)", texto, re.IGNORECASE)
    materia_match = re.search(r"MATERIA:\s*(.+)", texto, re.IGNORECASE)

    if not grado_match:
        raise ValueError("No se encontró el campo GRADO.")
    if not materia_match:
        raise ValueError("No se encontró el campo MATERIA.")

    grado = grado_match.group(1).strip()
    materia = materia_match.group(1).strip()

    cuerpo_inicio = max(grado_match.end(), materia_match.end())
    cuerpo = texto[cuerpo_inicio:].strip()

    patron = re.compile(
        r"(TEXTO\s+BASE\s+\d+\s*:|PREGUNTA\s+\d+\s*:)",
        re.IGNORECASE
    )

    matches = list(patron.finditer(cuerpo))

    if not matches:
        raise ValueError("No se encontraron preguntas. Revise que usen PREGUNTA 1:, PREGUNTA 2:, etc.")

    preguntas = []
    texto_base_actual = None

    for idx, match in enumerate(matches):
        etiqueta = match.group(1)
        inicio_contenido = match.end()
        fin_contenido = matches[idx + 1].start() if idx + 1 < len(matches) else len(cuerpo)
        contenido = cuerpo[inicio_contenido:fin_contenido].strip()

        if re.match(r"TEXTO\s+BASE\s+\d+\s*:", etiqueta, re.IGNORECASE):
            fin_match = re.search(r"FIN\s+TEXTO\s+BASE", contenido, re.IGNORECASE)
            if not fin_match:
                raise ValueError("Encontré TEXTO BASE, pero falta cerrar con FIN TEXTO BASE.")
            texto_base_actual = contenido[:fin_match.start()].strip()
            continue

        pregunta_num_match = re.search(r"PREGUNTA\s+(\d+)", etiqueta, re.IGNORECASE)
        numero = int(pregunta_num_match.group(1))

        imagen = None
        imagen_match = re.search(r"IMAGEN:\s*(.+)", contenido, re.IGNORECASE)
        if imagen_match:
            imagen = imagen_match.group(1).strip()

        opciones_match = re.search(
            r"A\.\s*(.*?)\s*B\.\s*(.*?)\s*C\.\s*(.*?)\s*D\.\s*(.*)",
            contenido,
            re.IGNORECASE | re.DOTALL
        )

        if not opciones_match:
            raise ValueError(f"La pregunta {numero} no tiene las opciones A, B, C y D completas o en orden.")

        opcion_a = limpiar_opcion(opciones_match.group(1))
        opcion_b = limpiar_opcion(opciones_match.group(2))
        opcion_c = limpiar_opcion(opciones_match.group(3))
        opcion_d = limpiar_opcion(opciones_match.group(4))

        corte_opciones = opciones_match.start()

        contenido_antes_opciones = contenido[:corte_opciones].strip()

        img_pos = re.search(r"IMAGEN:", contenido_antes_opciones, re.IGNORECASE)
        if img_pos:
            enunciado = contenido_antes_opciones[:img_pos.start()].strip()
        else:
            enunciado = contenido_antes_opciones.strip()

        if not enunciado:
            raise ValueError(f"La pregunta {numero} no tiene enunciado.")

        preguntas.append({
            "grado": grado,
            "materia": materia,
            "numero": numero,
            "enunciado": enunciado,
            "texto_base": texto_base_actual,
            "imagen": imagen,
            "opciones": {
                "A": opcion_a,
                "B": opcion_b,
                "C": opcion_c,
                "D": opcion_d,
            }
        })

    if not preguntas:
        raise ValueError("No se encontraron preguntas válidas.")

    return preguntas
