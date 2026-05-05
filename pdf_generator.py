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


def _draw_wrapped(c, text, x, y, max_width, font_name="Helvetica", font_size=9, leading=11, max_lines=None):
    c.setFont(font_name, font_size)
    lines = _wrap_text(text, max_width, font_name, font_size)
    if max_lines:
        lines = lines[:max_lines]
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y, len(lines)  # Retorna también el número de líneas


def _boton(c, texto, x, y, w, h, destino):
    verde = (0.05, 0.60, 0.12)
    c.setFillColorRGB(*verde)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(x + w / 2, y + h / 2 - 4, texto)
    c.linkRect("", destino, (x, y, x + w, y + h), relative=0)
    c.setFillColorRGB(0, 0, 0)


def _draw_cover(c, preguntas, grado_texto, sesion, periodo, institucion, interactivo=False):
    ancho, alto = letter
    verde = (0.05, 0.62, 0.12)
    negro = (0, 0, 0)
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, ancho, alto, fill=1, stroke=0)
    c.setFillColorRGB(*negro)
    c.setFont("Helvetica-Bold", 7.8)
    c.drawString(62, alto - 55, institucion.upper())
    c.setFont("Helvetica-Bold", 7)
    c.drawString(62, alto - 68, "Resolución De Reconocimiento Oficial No 001271 de 21 de noviembre de 2014")
    c.drawString(62, alto - 80, "DANE No 223586000208 NIT No 900021917-1 Código ICFES No 160333")
    c.setFont("Helvetica-Bold", 25)
    c.drawCentredString(ancho / 2, alto - 130, "EXÁMENES FINALES")
    c.setFont("Helvetica-Bold", 25)
    c.drawCentredString(ancho / 2, alto - 168, periodo.upper())
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(ancho / 2, alto - 250, "MI META")
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(ancho / 2, alto - 475, "ES LA EXCELENCIA")
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
    c.setFont("Helvetica-Bold", 24)
    c.drawString(ancho - 375, alto - 515, "GRADO: "+ str(grado_texto))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(52, 245, sesion.upper())
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
    c.drawString(margen_x, alto - 23, f"{_nombre_grado(grado_texto)} - Página {page_num}")
    c.drawRightString(ancho - margen_x, alto - 23, materia.upper())
    c.line(margen_x, alto - 29, ancho - margen_x, alto - 29)


def _draw_header_interactivo(c, i, total, materia, grado_texto):
    ancho, alto = letter
    margen_x = 52
    c.setFont("Helvetica", 8)
    c.drawString(margen_x, alto - 25, f"{_nombre_grado(grado_texto)} - Pregunta {i + 1} de {total}")
    c.drawRightString(ancho - margen_x, alto - 25, materia.upper())
    c.line(margen_x, alto - 32, ancho - margen_x, alto - 32)


def generar_pdf_normal_compacto(preguntas, nombre_pdf="banco_preguntas_normal.pdf", titulo="EXÁMENES FINALES", subtitulo="PRIMER PERIODO", institucion="INSTITUCIÓN EDUCATIVA", grado_texto="GRADO", sesion="PRIMERA SESIÓN", periodo="PRIMER PERIODO"):
    output_dir = Path("data/pdf")
    output_dir.mkdir(parents=True, exist_ok=True)
    ruta_pdf = output_dir / nombre_pdf
    c = _crear_canvas(ruta_pdf)
    ancho, alto = letter
    margen_x = 36
    bottom_y = 48
    gap_col = 18
    col_w = (ancho - (2 * margen_x) - gap_col) / 2

    # Configuración de texto base
    FONT_SIZE_TB = 8.5
    ALTURA_LINEA_TB = 11
    ALTURA_TITULO_TB = 18
    ESPACIO_DESPUES_TB = 20

    def get_altura_texto_base(texto_base):
        """Calcula la altura necesaria para el texto base según su contenido"""
        if not texto_base:
            return 0, 0
        lineas = _wrap_text(texto_base, col_w - 12, "Helvetica", FONT_SIZE_TB)
        num_lineas = len(lineas)
        altura = ALTURA_TITULO_TB + (num_lineas * ALTURA_LINEA_TB) + 8
        return altura, num_lineas

    def estimate_height(p):
        h = 20  # Número de pregunta
        
        # Texto base (altura dinámica)
        if p.get("texto_base"):
            altura_tb, _ = get_altura_texto_base(p["texto_base"])
            h += altura_tb + ESPACIO_DESPUES_TB
        
        # Enunciado
        h += 12 * len(_wrap_text(p["enunciado"], col_w - 18, "Helvetica", 10))
        
        # Imagen
        if p.get("imagen"):
            h += 100
        
        # Opciones
        for letra, opcion in p["opciones"].items():
            h += 11 * len(_wrap_text(f"{letra}. {opcion}", col_w - 18, "Helvetica", 9)) + 3
        
        return max(h + 10, 130)

    def draw_question(p, x, y):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x, y, f"{p['numero']}.")
        y -= 12
        
        if p.get("texto_base"):
            lineas_tb = _wrap_text(p["texto_base"], col_w - 12, "Helvetica", FONT_SIZE_TB)
            num_lineas = len(lineas_tb)
            altura_tb = ALTURA_TITULO_TB + (num_lineas * ALTURA_LINEA_TB) + 8
            
            # Fondo gris
            c.setFillColorRGB(0.94, 0.94, 0.94)
            c.roundRect(x, y - altura_tb + 6, col_w, altura_tb, 6, fill=1, stroke=0)
            
            # Borde
            c.setStrokeColorRGB(0.6, 0.6, 0.6)
            c.setLineWidth(0.8)
            c.roundRect(x, y - altura_tb + 6, col_w, altura_tb, 6, fill=0, stroke=1)
            c.setStrokeColorRGB(0, 0, 0)
            
            # Título
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x + 6, y - 10, "TEXTO BASE:")
            
            # Texto (todas las líneas)
            yy = y - 25
            c.setFont("Helvetica", FONT_SIZE_TB)
            for line in lineas_tb:
                if yy < y - altura_tb + 6:
                    break
                c.drawString(x + 6, yy, line)
                yy -= ALTURA_LINEA_TB
            
            # Mover la posición Y hacia abajo
            y -= altura_tb + ESPACIO_DESPUES_TB
        
        # Enunciado
        c.setFont("Helvetica-Bold", 11)
        lineas_enc = _wrap_text(p["enunciado"], col_w - 18, "Helvetica", 11)
        for line in lineas_enc[:10]:
            c.drawString(x + 15, y, line)
            y -= 13
        y -= 6
        
        # Imagen
        if p.get("imagen"):
            img_path = Path("data/images") / str(p["imagen"])
            if img_path.exists():
                try:
                    img = ImageReader(str(img_path))
                    iw, ih = img.getSize()
                    max_w = col_w - 20
                    max_h = 90
                    scale = min(max_w / iw, max_h / ih)
                    img_w = iw * scale
                    img_h = ih * scale
                    img_x = x + (col_w - img_w) / 2
                    c.drawImage(img, img_x, y - img_h, width=img_w, height=img_h, preserveAspectRatio=True, mask="auto")
                    y -= img_h + 10
                except Exception:
                    y = _draw_wrapped(c, "[No se pudo cargar imagen]", x + 15, y, col_w - 18, "Helvetica", 8, 10)[0]
        
        # Opciones
        c.setFont("Helvetica", 9)
        for letra in sorted(p["opciones"].keys()):
            if p["opciones"][letra].strip():
                y = _draw_wrapped(c, f"{letra}. {p['opciones'][letra]}", x + 15, y, col_w - 18, "Helvetica", 9, 11)[0]
                y -= 2
        return y - 8

    _draw_cover(c, preguntas, grado_texto=grado_texto, sesion=sesion, periodo=periodo, institucion=institucion, interactivo=False)
    c.showPage()
    materias_orden = []
    por_materia = defaultdict(list)
    for p in preguntas:
        if p["materia"] not in por_materia:
            materias_orden.append(p["materia"])
        por_materia[p["materia"]].append(p)
    page_num = 2
    for materia in materias_orden:
        _draw_header_normal(c, page_num, materia, grado_texto)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(ancho / 2, alto - 45, materia.upper())
        col = 0
        y_positions = [alto - 85, alto - 85]
        x_positions = [margen_x, margen_x + col_w + gap_col]
        for p in por_materia[materia]:
            needed = estimate_height(p) + 15
            if y_positions[col] - needed < bottom_y:
                if col == 0:
                    col = 1
                else:
                    c.showPage()
                    page_num += 1
                    _draw_header_normal(c, page_num, materia, grado_texto)
                    c.setFont("Helvetica-Bold", 14)
                    c.drawCentredString(ancho / 2, alto - 45, materia.upper())
                    col = 0
                    y_positions = [alto - 85, alto - 85]
            if y_positions[col] - needed < bottom_y and col == 1:
                c.showPage()
                page_num += 1
                _draw_header_normal(c, page_num, materia, grado_texto)
                c.setFont("Helvetica-Bold", 14)
                c.drawCentredString(ancho / 2, alto - 45, materia.upper())
                col = 0
                y_positions = [alto - 85, alto - 85]
            y_positions[col] = draw_question(p, x_positions[col], y_positions[col])
            y_positions[col] -= 12
            col = 1 - col
        c.showPage()
        page_num += 1
    c.save()
    return str(ruta_pdf)


def generar_pdf_interactivo_una_pregunta(preguntas, nombre_pdf="banco_preguntas_interactivo.pdf", titulo="EXÁMENES FINALES", subtitulo="PRIMER PERIODO", institucion="INSTITUCIÓN EDUCATIVA", grado_texto="GRADO", sesion="PRIMERA SESIÓN", periodo="PRIMER PERIODO", password=None):
    output_dir = Path("data/pdf")
    output_dir.mkdir(parents=True, exist_ok=True)
    ruta_pdf = output_dir / nombre_pdf
    c = _crear_canvas(ruta_pdf, password=password)
    ancho, alto = letter
    margen_x = 52
    c.bookmarkPage("inicio")
    _draw_cover(c, preguntas, grado_texto=grado_texto, sesion=sesion, periodo=periodo, institucion=institucion, interactivo=True)
    _boton(c, "INICIAR", ancho / 2 - 55, 48, 110, 30, "pregunta_0")
    c.showPage()
    total = len(preguntas)
    
    # Configuración texto base interactivo (dinámico)
    FONT_SIZE_TB_INT = 10.5
    ALTURA_LINEA_TB_INT = 13
    ALTURA_TITULO_TB_INT = 25
    ESPACIO_DESPUES_TB_INT = 30
    
    for i, p in enumerate(preguntas):
        c.bookmarkPage(f"pregunta_{i}")
        _draw_header_interactivo(c, i, total, p["materia"], grado_texto)
        y = alto - 70
        c.setFont("Helvetica-Bold", 18)
        c.drawString(margen_x, y, f"Pregunta {p['numero']}")
        y -= 45
        
        if p.get("texto_base"):
            lineas_tb = _wrap_text(p["texto_base"], ancho - 2 * margen_x - 20, "Helvetica", FONT_SIZE_TB_INT)
            num_lineas = len(lineas_tb)
            altura_tb = ALTURA_TITULO_TB_INT + (num_lineas * ALTURA_LINEA_TB_INT) + 15
            altura_tb = min(altura_tb, alto - 200)  # No puede ocupar toda la página
            
            # Fondo gris
            c.setFillColorRGB(0.94, 0.94, 0.94)
            c.roundRect(margen_x, y - altura_tb, ancho - 2 * margen_x, altura_tb, 10, fill=1, stroke=0)
            
            # Borde
            c.setStrokeColorRGB(0.5, 0.5, 0.5)
            c.setLineWidth(1)
            c.roundRect(margen_x, y - altura_tb, ancho - 2 * margen_x, altura_tb, 10, fill=0, stroke=1)
            c.setStrokeColorRGB(0, 0, 0)
            
            # Título
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margen_x + 12, y - 18, "TEXTO BASE")
            
            # Texto
            yy = y - 38
            c.setFont("Helvetica", FONT_SIZE_TB_INT)
            for line in lineas_tb:
                if yy < y - altura_tb + 12:
                    break
                c.drawString(margen_x + 12, yy, line)
                yy -= ALTURA_LINEA_TB_INT
            
            y -= altura_tb + ESPACIO_DESPUES_TB_INT
        
        # Enunciado
        c.setFont("Helvetica-Bold", 13)
        lineas_enc = _wrap_text(p["enunciado"], ancho - 2 * margen_x, "Helvetica", 13)
        for line in lineas_enc[:15]:
            c.drawString(margen_x, y, line)
            y -= 17
        y -= 15
        
        # Imagen
        if p.get("imagen"):
            img_path = Path("data/images") / str(p["imagen"])
            if img_path.exists():
                try:
                    img = ImageReader(str(img_path))
                    iw, ih = img.getSize()
                    max_w = ancho - 2 * margen_x - 40
                    max_h = 280
                    scale = min(max_w / iw, max_h / ih)
                    img_w = iw * scale
                    img_h = ih * scale
                    img_x = margen_x + (ancho - 2 * margen_x - img_w) / 2
                    c.drawImage(img, img_x, y - img_h, width=img_w, height=img_h, preserveAspectRatio=True, mask="auto")
                    y -= img_h + 25
                except Exception:
                    y = _draw_wrapped(c, "[No se pudo cargar la imagen]", margen_x, y, ancho - 2 * margen_x, "Helvetica", 11, 14)[0]
        
        # Opciones
        c.setFont("Helvetica", 11.5)
        for letra in sorted(p["opciones"].keys()):
            if p["opciones"][letra].strip():
                y = _draw_wrapped(c, f"{letra}. {p['opciones'][letra]}", margen_x + 20, y, ancho - 2 * margen_x - 20, "Helvetica", 11.5, 16)[0]
                y -= 5
        
        _boton(c, "🏠 INICIO", 45, 25, 90, 28, "inicio")
        if i > 0:
            _boton(c, "◀ ATRÁS", 155, 25, 90, 28, f"pregunta_{i - 1}")
        if i < total - 1:
            _boton(c, "SIGUIENTE ▶", ancho - 160, 25, 110, 28, f"pregunta_{i + 1}")
        c.showPage()
    c.save()
    return str(ruta_pdf)