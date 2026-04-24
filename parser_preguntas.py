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
    return Path(ruta).read_text(encoding="utf-8")

def extraer_texto(ruta):
    ruta = Path(ruta)
    if ruta.suffix.lower() == ".docx":
        return leer_docx(ruta)
    elif ruta.suffix.lower() == ".txt":
        return leer_txt(ruta)
    else:
        raise ValueError("Solo se permiten archivos .docx o .txt")

def parsear_preguntas(texto):
    grado_match = re.search(r"GRADO:\s*(.+)", texto, re.IGNORECASE)
    materia_match = re.search(r"MATERIA:\s*(.+)", texto, re.IGNORECASE)

    if not grado_match:
        raise ValueError("No se encontró el campo GRADO.")
    if not materia_match:
        raise ValueError("No se encontró el campo MATERIA.")

    grado = grado_match.group(1).strip()
    materia = materia_match.group(1).strip()

    bloques = re.split(r"\n\s*PREGUNTA\s+(\d+)\s*:\s*", texto, flags=re.IGNORECASE)

    preguntas = []

    # bloques[0] contiene encabezado, luego vienen pares: numero, contenido
    for i in range(1, len(bloques), 2):
        numero = int(bloques[i])
        contenido = bloques[i + 1].strip()

        imagen = None
        imagen_match = re.search(r"IMAGEN:\s*(.+)", contenido, re.IGNORECASE)
        if imagen_match:
            imagen = imagen_match.group(1).strip()

        opcion_a = re.search(r"\n?A\.\s*(.+)", contenido, re.IGNORECASE)
        opcion_b = re.search(r"\n?B\.\s*(.+)", contenido, re.IGNORECASE)
        opcion_c = re.search(r"\n?C\.\s*(.+)", contenido, re.IGNORECASE)
        opcion_d = re.search(r"\n?D\.\s*(.+)", contenido, re.IGNORECASE)

        if not all([opcion_a, opcion_b, opcion_c, opcion_d]):
            raise ValueError(f"La pregunta {numero} no tiene las opciones A, B, C y D completas.")

        # El enunciado es lo que está antes de IMAGEN o antes de la opción A
        corte = None
        posiciones = []

        img_pos = re.search(r"\n?IMAGEN:", contenido, re.IGNORECASE)
        a_pos = re.search(r"\n?A\.", contenido, re.IGNORECASE)

        if img_pos:
            posiciones.append(img_pos.start())
        if a_pos:
            posiciones.append(a_pos.start())

        if posiciones:
            corte = min(posiciones)
            enunciado = contenido[:corte].strip()
        else:
            enunciado = contenido.strip()

        preguntas.append({
            "grado": grado,
            "materia": materia,
            "numero": numero,
            "enunciado": enunciado,
            "imagen": imagen,
            "opciones": {
                "A": opcion_a.group(1).strip(),
                "B": opcion_b.group(1).strip(),
                "C": opcion_c.group(1).strip(),
                "D": opcion_d.group(1).strip(),
            }
        })

    if not preguntas:
        raise ValueError("No se encontraron preguntas. Revise que usen PREGUNTA 1:, PREGUNTA 2:, etc.")

    return preguntas
