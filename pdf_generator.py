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
    c.drawString(62, alto - 68, "Resolución De Reconocimiento Oficial No 001271 de 21 de noviembre de 2014")
    c.drawString(62, alto - 80, "DANE No 223586000208 NIT No 900021917-1 Código ICFES No 160333")

    # Títulos principales
    c.setFont("Helvetica-Bold", 25)
    c.drawCentredString(ancho / 2, alto - 130, "EXÁMENES FINALES")

    c.setFont("Helvetica-Bold", 25)
    c.drawCentredString(ancho / 2, alto - 168, periodo.upper())

    # Texto "Mi meta es la excelencia"
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(ancho / 2, alto - 250, "MI META")

    c.setFont("Helvetica-Bold", 22)
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

    # Grado grande
    c.setFont("Helvetica-Bold", 24)
    c.drawString(ancho - 375, alto - 515, "GRADO: "+ str(grado_texto))

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
        y -= 34

        c.setFillColorRGB(*verde)
        c.roundRect(42, y, 220, 25, 7, fill=1, stroke=0)

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

    def dibujar_texto_base_ancho_completo(texto_base, y_actual):
        """Dibuja el texto base ocupando TODO el ancho de la página"""
        if not texto_base:
            return y_actual
        
        ancho_texto = ancho - (2 * margen_x)
        
        # Calcular cuántas líneas tiene el texto base
        lineas = _wrap_text(texto_base, ancho_texto - 20, "Helvetica", 10)
        alto_texto = len(lineas) * 12 + 35
        
        # Limitar altura máxima
        alto_texto = min(alto_texto, 200)
        
        # Fondo gris
        c.setFillColorRGB(0.94, 0.94, 0.94)
        c.roundRect(margen_x, y_actual - alto_texto, ancho_texto, alto_texto, 6, fill=1, stroke=0)
        
        # Título
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margen_x + 8, y_actual - 12, "TEXTO BASE")
        
        # Dibujar líneas de texto
        c.setFont("Helvetica", 10)
        yy = y_actual - 28
        for linea in lineas:
            if yy < y_actual - alto_texto + 8:
                break
            c.drawString(margen_x + 8, yy, linea)
            yy -= 12
        
        return y_actual - alto_texto - 10

    def estimar_altura_pregunta(p):
        """Estima la altura que ocupará UNA pregunta"""
        h = 15
        
        # Enunciado
        h += 12 * len(_wrap_text(p["enunciado"], col_w - 18, "Helvetica", 11))
        
        # Imagen
        if p.get("imagen"):
            h += 115
        
        # Opciones
        for letra, opcion in p["opciones"].items():
            h += 12 * len(_wrap_text(f"{letra}. {opcion}", col_w - 18, "Helvetica", 10)) + 3
        
        return max(h + 12, 140)

    def dibujar_pregunta(p, x, y):
        """Dibuja una pregunta en una columna"""
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, f"{p['numero']}.")
        y -= 14

        # Enunciado
        y = _draw_wrapped(
            c,
            p["enunciado"],
            x + 15,
            y,
            col_w - 16,
            "Helvetica",
            11,
            13,
        )
        y -= 5

        # Imagen
        if p.get("imagen"):
            img_path = Path("data/images") / str(p["imagen"])
            if img_path.exists():
                try:
                    img = ImageReader(str(img_path))
                    iw, ih = img.getSize()
                    max_w = col_w - 20
                    max_h = 115
                    scale = min(max_w / iw, max_h / ih)
                    img_w = iw * scale
                    img_h = ih * scale
                    img_x = x + (col_w - img_w) / 2
                    c.drawImage(
                        img,
                        img_x,
                        y - img_h,
                        width=img_w,
                        height=img_h,
                        preserveAspectRatio=True,
                        mask="auto",
                    )
                    y -= img_h + 12
                except Exception:
                    y = _draw_wrapped(
                        c,
                        "[No se pudo cargar imagen]",
                        x + 15,
                        y,
                        col_w - 18,
                        "Helvetica",
                        9,
                        11,
                    )

        # Opciones
        for letra in sorted(p["opciones"].keys()):
            y = _draw_wrapped(
                c,
                f"{letra}. {p['opciones'][letra]}",
                x + 15,
                y,
                col_w - 18,
                "Helvetica",
                10,
                12,
            )
            y -= 3

        return y - 10

    # ========== PORTADA ==========
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

    # ========== AGRUPAR POR MATERIA Y TEXTO BASE ==========
    # Primero, ordenar preguntas por número
    preguntas_ordenadas = sorted(preguntas, key=lambda x: x["numero"])
    
    # Agrupar por texto base (preguntas consecutivas que comparten texto base)
    grupos = []
    grupo_actual = []
    texto_actual = None
    
    for p in preguntas_ordenadas:
        texto_p = p.get("texto_base", "")
        if texto_p != texto_actual:
            if grupo_actual:
                grupos.append({
                    "texto_base": texto_actual,
                    "preguntas": grupo_actual
                })
            grupo_actual = [p]
            texto_actual = texto_p
        else:
            grupo_actual.append(p)
    
    if grupo_actual:
        grupos.append({
            "texto_base": texto_actual,
            "preguntas": grupo_actual
        })
    
    page_num = 2
    
    for grupo in grupos:
        if not grupo["preguntas"]:
            continue
        
        materia = grupo["preguntas"][0]["materia"]
        
        # Encabezado de página
        _draw_header_normal(c, page_num, materia, grado_texto)
        
        # Título de materia
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(ancho / 2, alto - 45, materia.upper())
        
        y_actual = alto - 90
        
        # Dibujar texto base si existe
        if grupo["texto_base"]:
            y_actual = dibujar_texto_base_ancho_completo(grupo["texto_base"], y_actual)
            y_actual -= 15
        
        # Configurar columnas
        col = 0
        y_positions = [y_actual, y_actual]
        x_positions = [margen_x, margen_x + col_w + gap_col]
        
        # Dibujar preguntas del grupo en columnas
        for p in grupo["preguntas"]:
            altura_necesaria = estimar_altura_pregunta(p)
            
            # Verificar si cabe en la columna actual
            if y_positions[col] - altura_necesaria < bottom_y:
                if col == 0:
                    col = 1
                else:
                    # Nueva página
                    c.showPage()
                    page_num += 1
                    _draw_header_normal(c, page_num, materia, grado_texto)
                    c.setFont("Helvetica-Bold", 16)
                    c.drawCentredString(ancho / 2, alto - 45, materia.upper())
                    
                    # Reiniciar columnas
                    col = 0
                    y_positions = [alto - 90, alto - 90]
                    
                    # Redibujar texto base si es necesario
                    if grupo["texto_base"]:
                        y_positions[0] = dibujar_texto_base_ancho_completo(grupo["texto_base"], y_positions[0])
                        y_positions[0] -= 15
                        y_positions[1] = y_positions[0]
            
            # Dibujar la pregunta
            y_positions[col] = dibujar_pregunta(p, x_positions[col], y_positions[col])
            
            # Alternar columna
            col = 1 - col
        
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

        c.setFont("Helvetica-Bold", 22)
        c.drawString(margen_x, y, f"Pregunta {p['numero']}")
        y -= 40

        if p.get("texto_base"):
            c.setFillColorRGB(0.94, 0.94, 0.94)
            lineas = _wrap_text(p["texto_base"], ancho - 2 * margen_x - 20, "Helvetica", 11)
            alto_texto = min(len(lineas) * 14 + 40, 200)
            
            c.roundRect(
                margen_x,
                y - alto_texto,
                ancho - 2 * margen_x,
                alto_texto,
                8,
                fill=1,
                stroke=0,
            )
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margen_x + 10, y - 25, "TEXTO BASE")

            yy = y - 45
            c.setFont("Helvetica", 11)
            for linea in lineas[:10]:
                if yy < y - alto_texto + 10:
                    break
                c.drawString(margen_x + 10, yy, linea)
                yy -= 14

            y -= alto_texto + 15

        y = _draw_wrapped(
            c,
            p["enunciado"],
            margen_x,
            y,
            ancho - 2 * margen_x,
            "Helvetica",
            15,
            19,
        )
        y -= 15

        if p.get("imagen"):
            img_path = Path("data/images") / str(p["imagen"])

            if img_path.exists():
                try:
                    img = ImageReader(str(img_path))
                    iw, ih = img.getSize()
                    max_w = ancho - 2 * margen_x - 20
                    max_h = 380
                    scale = min(max_w / iw, max_h / ih)
                    img_w = iw * scale
                    img_h = ih * scale

                    img_x = margen_x + (ancho - 2 * margen_x - img_w) / 2
                    
                    c.drawImage(
                        img,
                        img_x,
                        y - img_h,
                        width=img_w,
                        height=img_h,
                        preserveAspectRatio=True,
                        mask="auto",
                    )
                    y -= img_h + 30
                except Exception:
                    y = _draw_wrapped(
                        c,
                        "[No se pudo cargar la imagen]",
                        margen_x,
                        y,
                        ancho - 2 * margen_x,
                        "Helvetica",
                        13,
                        16,
                    )

        for letra in sorted(p["opciones"].keys()):
            y = _draw_wrapped(
                c,
                f"{letra}. {p['opciones'][letra]}",
                margen_x + 18,
                y,
                ancho - 2 * margen_x - 18,
                "Helvetica",
                14,
                18,
            )
            y -= 8

        _boton(c, "INICIO", 45, 25, 80, 26, "inicio")

        if i > 0:
            _boton(c, "ATRÁS", 145, 25, 85, 26, f"pregunta_{i - 1}")

        if i < total - 1:
            _boton(c, "SIGUIENTE", ancho - 150, 25, 105, 26, f"pregunta_{i + 1}")

        c.showPage()

    c.save()
    return str(ruta_pdf)