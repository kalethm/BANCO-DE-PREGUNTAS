from pathlib import Path
from collections import defaultdict

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.pdfencrypt import StandardEncryption


def _nombre_grado(grado_texto):
    g = str(grado_texto).replace("°", "").strip()
    nombres = {
        "6": "Sexto",
        "7": "Séptimo",
        "8": "Octavo",
        "9": "Noveno",
        "10": "Décimo",
        "11": "Undécimo",
        "GRADO": "Grado",
    }
    return nombres.get(g, str(grado_texto))


def _crear_canvas(ruta_pdf, password=None):
    if password:
        enc = StandardEncryption(
            userPassword=password,
            ownerPassword=password,
            canPrint=1,
            canModify=0,
            canCopy=0,
            canAnnotate=0,
            strength=128,
        )
        return canvas.Canvas(str(ruta_pdf), pagesize=letter, encrypt=enc)

    return canvas.Canvas(str(ruta_pdf), pagesize=letter)


def _wrap_text(text, max_width, font_name="Helvetica", font_size=9):
    text = str(text or "").replace("\r", "")
    lines = []

    for paragraph in text.split("\n"):
        words = paragraph.split()

        if not words:
            lines.append("")
            continue

        line = ""
        for word in words:
            test = f"{line} {word}".strip()

            if stringWidth(test, font_name, font_size) <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word

        if line:
            lines.append(line)

    return lines


def _draw_wrapped(
    c,
    text,
    x,
    y,
    max_width,
    font_name="Helvetica",
    font_size=9,
    leading=11,
    max_lines=None,
):
    c.setFont(font_name, font_size)

    lines = _wrap_text(text, max_width, font_name, font_size)

    if max_lines:
        lines = lines[:max_lines]

    for line in lines:
        c.drawString(x, y, line)
        y -= leading

    return y


def _boton(c, texto, x, y, w, h, destino):
    verde = (0.05, 0.60, 0.12)

    c.setFillColorRGB(*verde)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=0)

    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(x + w / 2, y + h / 2 - 4, texto)

    c.linkRect("", destino, (x, y, x + w, y + h), relative=0)

    c.setFillColorRGB(0, 0, 0)


def _draw_cover(
    c,
    preguntas,
    grado_texto,
    sesion,
    periodo,
    institucion,
    interactivo=False,
):
    ancho, alto = letter
    verde = (0.05, 0.62, 0.12)
    negro = (0, 0, 0)

    # Fondo limpio
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, ancho, alto, fill=1, stroke=0)
    c.setFillColorRGB(*negro)

    # Encabezado institucional
    c.setFont("Helvetica-Bold", 7.8)
    c.drawString(62, alto - 55, institucion.upper())

    c.setFont("Helvetica-Bold", 7)
    c.drawString(62, alto - 68, "Resolución de Reconocimiento Oficial")
    c.drawString(62, alto - 80, "DANE / NIT / Código ICFES")

    # Logos simulados a la derecha
    c.setStrokeColorRGB(0.2, 0.2, 0.2)
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.circle(ancho - 120, alto - 66, 18, stroke=1, fill=1)
    c.circle(ancho - 78, alto - 66, 18, stroke=1, fill=1)

    c.setFillColorRGB(0.1, 0.45, 0.1)
    c.setFont("Helvetica-Bold", 5.5)
    c.drawCentredString(ancho - 120, alto - 68, "ESC")
    c.drawCentredString(ancho - 78, alto - 68, "LOGO")
    c.setFillColorRGB(*negro)

    # Títulos principales
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(ancho / 2, alto - 130, "EXÁMENES FINALES")

    c.setFont("Helvetica-Bold", 25)
    c.drawCentredString(ancho / 2, alto - 168, periodo.upper())

    # Decoraciones superiores sencillas
    c.setFont("Helvetica-Bold", 28)
    c.drawString(88, alto - 270, "✧")
    c.drawString(120, alto - 295, "✦")

    c.setFont("Helvetica-Bold", 24)
    c.drawString(ancho - 115, alto - 250, "✎")
    c.drawString(ancho - 95, alto - 275, "✎")

    # Texto "Mi meta es la excelencia"
    c.setFont("Helvetica-Bold", 42)
    c.drawCentredString(ancho / 2, alto - 250, "MI META")

    c.setFont("Helvetica-Bold", 34)
    c.drawCentredString(ancho / 2, alto - 475, "ES LA EXCELENCIA")

    # Check central
    cx = ancho / 2
    cy = alto - 360

    c.setStrokeColorRGB(*verde)
    c.setLineWidth(10)
    c.circle(cx, cy, 82, stroke=1, fill=0)

    c.setLineWidth(24)
    c.line(cx - 48, cy - 8, cx - 12, cy - 48)
    c.line(cx - 12, cy - 48, cx + 62, cy + 58)

    c.setStrokeColorRGB(*negro)
    c.setLineWidth(1)

    # Globo simple izquierda
    c.setStrokeColorRGB(0.0, 0.55, 0.75)
    c.setFillColorRGB(0.65, 0.90, 1.0)
    c.circle(102, alto - 540, 28, stroke=1, fill=1)
    c.setStrokeColorRGB(0.95, 0.45, 0.0)
    c.setLineWidth(2)
    c.arc(72, alto - 572, 132, alto - 512, 205, 330)
    c.setStrokeColorRGB(*negro)
    c.setLineWidth(1)
    c.line(102, alto - 568, 102, alto - 592)
    c.line(84, alto - 592, 120, alto - 592)
    c.setFillColorRGB(*negro)

    # Grado grande
    c.setFont("Helvetica-Bold", 72)
    c.drawString(ancho - 175, alto - 535, str(grado_texto))

    # Lápices decorativos sencillos
    c.setFont("Helvetica-Bold", 28)
    c.drawString(ancho - 112, alto - 515, "✎")
    c.drawString(ancho - 82, alto - 555, "✎")

    # Sesión
    c.setFont("Helvetica-Bold", 18)
    c.drawString(52, 245, sesion.upper())

    # Materias a la izquierda
    materias = defaultdict(int)
    for p in preguntas:
        materias[p["materia"]] += 1

    y = 212
    for mat, total in materias.items():
        c.setFillColorRGB(*negro)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(52, y, mat.upper())
        y -= 24

        c.setFillColorRGB(*verde)
        c.roundRect(52, y, 220, 25, 7, fill=1, stroke=0)

        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(162, y + 8, f"{total} PREGUNTAS")

        y -= 42
        if y < 70:
            break

    # Recuerda a la derecha
    c.setFillColorRGB(*negro)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(342, 236, "RECUERDA")

    instrucciones = [
        "Lee cada pregunta cuidadosamente y elige UNA opción.",
        "En este cuadernillo encontrarás las preguntas.",
        "Recuerda que tienes una hora para responder.",
        "Por favor, responde TODAS las preguntas.",
        "Si tienes dudas, pide ayuda a tu docente.",
    ]

    if interactivo:
        instrucciones = [
            "Lee cada pregunta cuidadosamente.",
            "Elige UNA sola opción.",
            "Usa los botones para avanzar o regresar.",
            "Puedes volver al inicio cuando lo necesites.",
            "Si tienes dudas, pide ayuda a tu docente.",
        ]

    y2 = 207
    c.setFont("Helvetica", 8.3)
    for item in instrucciones:
        c.drawString(350, y2, f"• {item}")
        y2 -= 16

    # Clip decorativo
    c.setStrokeColorRGB(1.0, 0.55, 0.0)
    c.setLineWidth(2)
    c.ellipse(420, 72, 455, 142, stroke=1, fill=0)
    c.ellipse(438, 72, 473, 142, stroke=1, fill=0)

    c.setStrokeColorRGB(0.0, 0.65, 0.8)
    c.ellipse(465, 75, 500, 145, stroke=1, fill=0)

    c.setStrokeColorRGB(0.0, 0.7, 0.25)
    c.ellipse(495, 78, 530, 148, stroke=1, fill=0)

    c.setStrokeColorRGB(*negro)
    c.setLineWidth(1)


def _draw_header_normal(c, page_num, materia, grado_texto):
    ancho, alto = letter
    margen_x = 36

    c.setFont("Helvetica", 7.5)
    c.drawString(
        margen_x,
        alto - 23,
        f"{_nombre_grado(grado_texto)} - Página {page_num}",
    )
    c.drawRightString(ancho - margen_x, alto - 23, materia.upper())
    c.line(margen_x, alto - 29, ancho - margen_x, alto - 29)


def _draw_header_interactivo(c, i, total, materia, grado_texto):
    ancho, alto = letter
    margen_x = 52

    c.setFont("Helvetica", 8)
    c.drawString(
        margen_x,
        alto - 25,
        f"{_nombre_grado(grado_texto)} - Pregunta {i + 1} de {total}",
    )
    c.drawRightString(ancho - margen_x, alto - 25, materia.upper())
    c.line(margen_x, alto - 32, ancho - margen_x, alto - 32)


def generar_pdf_normal_compacto(
    preguntas,
    nombre_pdf="banco_preguntas_normal.pdf",
    titulo="EXÁMENES FINALES",
    subtitulo="PRIMER PERIODO",
    institucion="INSTITUCIÓN EDUCATIVA",
    grado_texto="GRADO",
    sesion="PRIMERA SESIÓN",
    periodo="PRIMER PERIODO",
):
    output_dir = Path("data/pdf")
    output_dir.mkdir(parents=True, exist_ok=True)

    ruta_pdf = output_dir / nombre_pdf
    c = _crear_canvas(ruta_pdf)

    ancho, alto = letter
    margen_x = 36
    bottom_y = 38
    gap_col = 18
    col_w = (ancho - (2 * margen_x) - gap_col) / 2

    def estimate_height(p):
        h = 12

        if p.get("texto_base"):
            h += min(
                58,
                12 + 7 * len(_wrap_text(p["texto_base"], col_w - 12, "Helvetica", 6.3)),
            )

        h += 8 * len(_wrap_text(p["enunciado"], col_w - 18, "Helvetica", 7.4))

        if p.get("imagen"):
            h += 50

        for letra, opcion in p["opciones"].items():
            h += 8 * len(
                _wrap_text(f"{letra}. {opcion}", col_w - 18, "Helvetica", 7.2)
            ) + 1

        return max(h + 8, 68)

    def draw_question(p, x, y):
        c.setFont("Helvetica-Bold", 8.2)
        c.drawString(x, y, f"{p['numero']}.")
        y -= 10

        if p.get("texto_base"):
            c.setFillColorRGB(0.94, 0.94, 0.94)
            box_h = 45
            c.roundRect(x, y - box_h + 4, col_w, box_h, 4, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 6.4)
            c.drawString(x + 4, y - 6, "TEXTO BASE")

            yy = y - 15
            for line in _wrap_text(p["texto_base"], col_w - 8, "Helvetica", 6.2)[:5]:
                c.setFont("Helvetica", 6.2)
                c.drawString(x + 4, yy, line)
                yy -= 7

            y -= box_h + 4

        y = _draw_wrapped(
            c,
            p["enunciado"],
            x + 15,
            y,
            col_w - 16,
            "Helvetica",
            7.4,
            8,
        )
        y -= 3

        if p.get("imagen"):
            img_path = Path("data/images") / str(p["imagen"])

            if img_path.exists():
                try:
                    img = ImageReader(str(img_path))
                    iw, ih = img.getSize()
                    max_w = col_w - 18
                    max_h = 45
                    scale = min(max_w / iw, max_h / ih)
                    img_w = iw * scale
                    img_h = ih * scale

                    c.drawImage(
                        img,
                        x + 15,
                        y - img_h,
                        width=img_w,
                        height=img_h,
                        preserveAspectRatio=True,
                        mask="auto",
                    )
                    y -= img_h + 5
                except Exception:
                    y = _draw_wrapped(
                        c,
                        "[No se pudo cargar imagen]",
                        x + 15,
                        y,
                        col_w - 18,
                        "Helvetica",
                        6.8,
                        7.4,
                    )

        for letra in sorted(p["opciones"].keys()):
            y = _draw_wrapped(
                c,
                f"{letra}. {p['opciones'][letra]}",
                x + 15,
                y,
                col_w - 18,
                "Helvetica",
                7.2,
                7.8,
            )
            y -= 1

        return y - 6

    # Portada
    _draw_cover(
        c,
        preguntas,
        grado_texto=grado_texto,
        sesion=sesion,
        periodo=periodo,
        institucion=institucion,
        interactivo=False,
    )
    c.showPage()

    # Agrupar por materia conservando orden
    materias_orden = []
    por_materia = defaultdict(list)

    for p in preguntas:
        if p["materia"] not in por_materia:
            materias_orden.append(p["materia"])
        por_materia[p["materia"]].append(p)

    page_num = 2

    for materia in materias_orden:
        _draw_header_normal(c, page_num, materia, grado_texto)

        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(ancho / 2, alto - 45, materia.upper())

        col = 0
        y_positions = [alto - 70, alto - 70]
        x_positions = [margen_x, margen_x + col_w + gap_col]

        for p in por_materia[materia]:
            needed = estimate_height(p)

            if y_positions[col] - needed < bottom_y:
                if col == 0:
                    col = 1
                else:
                    c.showPage()
                    page_num += 1
                    _draw_header_normal(c, page_num, materia, grado_texto)
                    c.setFont("Helvetica-Bold", 12)
                    c.drawCentredString(ancho / 2, alto - 45, materia.upper())
                    col = 0
                    y_positions = [alto - 70, alto - 70]

            if y_positions[col] - needed < bottom_y and col == 1:
                c.showPage()
                page_num += 1
                _draw_header_normal(c, page_num, materia, grado_texto)
                c.setFont("Helvetica-Bold", 12)
                c.drawCentredString(ancho / 2, alto - 45, materia.upper())
                col = 0
                y_positions = [alto - 70, alto - 70]

            y_positions[col] = draw_question(p, x_positions[col], y_positions[col])

        c.showPage()
        page_num += 1

    c.save()
    return str(ruta_pdf)


def generar_pdf_interactivo_una_pregunta(
    preguntas,
    nombre_pdf="banco_preguntas_interactivo.pdf",
    titulo="EXÁMENES FINALES",
    subtitulo="PRIMER PERIODO",
    institucion="INSTITUCIÓN EDUCATIVA",
    grado_texto="GRADO",
    sesion="PRIMERA SESIÓN",
    periodo="PRIMER PERIODO",
    password=None,
):
    output_dir = Path("data/pdf")
    output_dir.mkdir(parents=True, exist_ok=True)

    ruta_pdf = output_dir / nombre_pdf
    c = _crear_canvas(ruta_pdf, password=password)

    ancho, alto = letter
    margen_x = 52

    # Portada
    c.bookmarkPage("inicio")

    _draw_cover(
        c,
        preguntas,
        grado_texto=grado_texto,
        sesion=sesion,
        periodo=periodo,
        institucion=institucion,
        interactivo=True,
    )

    _boton(c, "INICIAR", ancho / 2 - 55, 48, 110, 30, "pregunta_0")
    c.showPage()

    total = len(preguntas)

    for i, p in enumerate(preguntas):
        c.bookmarkPage(f"pregunta_{i}")
        _draw_header_interactivo(c, i, total, p["materia"], grado_texto)

        y = alto - 70

        c.setFont("Helvetica-Bold", 18)
        c.drawString(margen_x, y, f"Pregunta {p['numero']}")
        y -= 34

        if p.get("texto_base"):
            c.setFillColorRGB(0.94, 0.94, 0.94)
            c.roundRect(
                margen_x,
                y - 120,
                ancho - 2 * margen_x,
                112,
                8,
                fill=1,
                stroke=0,
            )
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(margen_x + 10, y - 22, "TEXTO BASE")

            yy = y - 42
            for line in _wrap_text(
                p["texto_base"],
                ancho - 2 * margen_x - 20,
                "Helvetica",
                10,
            )[:8]:
                c.setFont("Helvetica", 10)
                c.drawString(margen_x + 10, yy, line)
                yy -= 13

            y -= 135

        y = _draw_wrapped(
            c,
            p["enunciado"],
            margen_x,
            y,
            ancho - 2 * margen_x,
            "Helvetica",
            14,
            18,
        )
        y -= 12

        if p.get("imagen"):
            img_path = Path("data/images") / str(p["imagen"])

            if img_path.exists():
                try:
                    img = ImageReader(str(img_path))
                    iw, ih = img.getSize()
                    max_w = ancho - 2 * margen_x
                    max_h = 230
                    scale = min(max_w / iw, max_h / ih)
                    img_w = iw * scale
                    img_h = ih * scale

                    c.drawImage(
                        img,
                        margen_x,
                        y - img_h,
                        width=img_w,
                        height=img_h,
                        preserveAspectRatio=True,
                        mask="auto",
                    )
                    y -= img_h + 18
                except Exception:
                    y = _draw_wrapped(
                        c,
                        "[No se pudo cargar la imagen]",
                        margen_x,
                        y,
                        ancho - 2 * margen_x,
                        "Helvetica",
                        11,
                        14,
                    )

        for letra in sorted(p["opciones"].keys()):
            y = _draw_wrapped(
                c,
                f"{letra}. {p['opciones'][letra]}",
                margen_x + 18,
                y,
                ancho - 2 * margen_x - 18,
                "Helvetica",
                13,
                17,
            )
            y -= 5

        _boton(c, "INICIO", 45, 25, 80, 26, "inicio")

        if i > 0:
            _boton(c, "ATRÁS", 145, 25, 85, 26, f"pregunta_{i - 1}")

        if i < total - 1:
            _boton(c, "SIGUIENTE", ancho - 150, 25, 105, 26, f"pregunta_{i + 1}")

        c.showPage()

    c.save()
    return str(ruta_pdf)
