from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from math import ceil
from collections import defaultdict

def generar_pdf_formato(
    preguntas,
    nombre_pdf="banco_preguntas.pdf",
    interactivo=False,
    titulo="EXÁMENES FINALES",
    subtitulo="PRIMER PERIODO",
    institucion="INSTITUCIÓN EDUCATIVA",
    grado_texto="GRADO",
    sesion="PRIMERA SESIÓN",
):
    output_dir = Path("data/pdf")
    output_dir.mkdir(parents=True, exist_ok=True)

    ruta_pdf = output_dir / nombre_pdf
    c = canvas.Canvas(str(ruta_pdf), pagesize=letter)

    ancho, alto = letter
    margen_x = 34
    margen_top = 66
    margen_bottom = 58
    gap_col = 16
    gap_row = 12

    usable_w = ancho - 2 * margen_x
    col_w = (usable_w - gap_col) / 2
    usable_h = alto - margen_top - margen_bottom
    card_h = (usable_h - gap_row) / 2

    verde = (0.05, 0.60, 0.12)

    def wrap_text(text, max_width, font_name="Helvetica", font_size=8):
        text = str(text or "").replace("\r", "")
        final_lines = []
        for paragraph in text.split("\n"):
            words = paragraph.split()
            if not words:
                final_lines.append("")
                continue
            line = ""
            for word in words:
                test = f"{line} {word}".strip()
                if stringWidth(test, font_name, font_size) <= max_width:
                    line = test
                else:
                    if line:
                        final_lines.append(line)
                    line = word
            if line:
                final_lines.append(line)
        return final_lines

    def draw_wrapped(text, x, y, max_width, font_name="Helvetica", font_size=8, leading=9.5, max_y_bottom=0):
        c.setFont(font_name, font_size)
        lines = wrap_text(text, max_width, font_name, font_size)
        for line in lines:
            if y < max_y_bottom:
                break
            c.drawString(x, y, line)
            y -= leading
        return y

    def draw_header(page_num, total_pages, materia=""):
        c.setFont("Helvetica", 7.5)
        c.drawString(margen_x, alto - 23, f"{grado_texto} {sesion} - Página {page_num} de {total_pages}")
        c.drawRightString(ancho - margen_x, alto - 23, materia.upper())
        c.line(margen_x, alto - 29, ancho - margen_x, alto - 29)

    def boton(texto, x, y, w, h, destino):
        if not interactivo:
            return
        c.setFillColorRGB(*verde)
        c.roundRect(x, y, w, h, 7, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x + w / 2, y + h / 2 - 3, texto)
        c.linkRect("", destino, (x, y, x + w, y + h), relative=0)
        c.setFillColorRGB(0, 0, 0)

    def crear_portada(total_pages):
        if interactivo:
            c.bookmarkPage("inicio")

        c.setFont("Helvetica-Bold", 8)
        c.drawString(62, alto - 55, institucion.upper())
        c.drawString(62, alto - 68, "Resolución de Reconocimiento Oficial")
        c.drawString(62, alto - 81, "DANE / NIT / Código ICFES")

        c.setFont("Helvetica-Bold", 29)
        c.drawCentredString(ancho / 2, alto - 135, titulo)

        c.setFont("Helvetica-Bold", 25)
        c.drawCentredString(ancho / 2, alto - 172, subtitulo)

        c.setFont("Helvetica-Bold", 42)
        c.drawCentredString(ancho / 2, alto - 270, "MI META")
        c.drawCentredString(ancho / 2, alto - 326, "ES LA EXCELENCIA")

        c.setFillColorRGB(*verde)
        c.circle(ancho / 2, alto - 303, 78, stroke=1, fill=0)
        c.setFillColorRGB(0, 0, 0)

        c.setFont("Helvetica-Bold", 70)
        c.drawCentredString(ancho / 2 + 165, alto - 420, grado_texto)

        c.setFont("Helvetica-Bold", 18)
        c.drawString(52, 234, sesion)

        materias = defaultdict(int)
        for p in preguntas:
            materias[p["materia"]] += 1

        y = 205
        for mat, total in materias.items():
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(52, y, mat.upper())
            y -= 24

            c.setFillColorRGB(*verde)
            c.roundRect(52, y, 220, 24, 7, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(162, y + 7, f"{total} PREGUNTAS")
            y -= 42
            if y < 78:
                break

        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(340, 230, "RECUERDA")

        instrucciones = [
            "Lee cada pregunta cuidadosamente.",
            "Elige una sola opción.",
            "En este cuadernillo encontrarás las preguntas.",
            "Si tienes dudas, pide orientación al docente.",
        ]

        if interactivo:
            instrucciones.insert(2, "Usa los botones para avanzar o regresar.")

        y2 = 205
        c.setFont("Helvetica", 9)
        for item in instrucciones:
            c.drawString(350, y2, f"• {item}")
            y2 -= 18

        if interactivo:
            boton("INICIAR", ancho / 2 - 55, 48, 110, 30, "pagina_0")

        c.showPage()

    def dibujar_card(p, x, y_top, w, h):
        y = y_top
        bottom = y_top - h + 6

        c.setLineWidth(0.4)
        c.roundRect(x - 4, y_top - h, w + 8, h, 5, stroke=1, fill=0)

        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, y - 12, f"{p['numero']}.")
        y -= 12

        # Texto base, opcional. Se imprime compacto dentro del cuadro de la pregunta.
        if p.get("texto_base"):
            c.setFillColorRGB(0.94, 0.94, 0.94)
            c.roundRect(x, y - 50, w, 48, 4, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica-Bold", 7.2)
            c.drawString(x + 4, y - 10, "TEXTO BASE")
            y_text = y - 21
            y_text = draw_wrapped(
                p["texto_base"],
                x + 4,
                y_text,
                w - 8,
                font_name="Helvetica",
                font_size=6.6,
                leading=7.5,
                max_y_bottom=y - 47
            )
            y -= 56

        y = draw_wrapped(
            p["enunciado"],
            x + 17,
            y,
            w - 18,
            font_name="Helvetica",
            font_size=7.6,
            leading=8.6,
            max_y_bottom=bottom + 84
        )

        y -= 3

        if p.get("imagen"):
            img_path = Path("data/images") / str(p["imagen"])
            if img_path.exists() and y > bottom + 96:
                try:
                    img = ImageReader(str(img_path))
                    iw, ih = img.getSize()
                    max_w = w - 16
                    max_h = 58
                    escala = min(max_w / iw, max_h / ih)
                    img_w = iw * escala
                    img_h = ih * escala
                    c.drawImage(
                        img,
                        x + 8,
                        y - img_h,
                        width=img_w,
                        height=img_h,
                        preserveAspectRatio=True,
                        mask="auto"
                    )
                    y -= img_h + 4
                except Exception:
                    y = draw_wrapped("[No se pudo cargar la imagen]", x + 17, y, w - 18, font_size=6.8, leading=7.5, max_y_bottom=bottom + 80)
            elif y > bottom + 84:
                y = draw_wrapped(f"[Imagen no encontrada: {p['imagen']}]", x + 17, y, w - 18, font_size=6.8, leading=7.5, max_y_bottom=bottom + 80)

        for letra in ["A", "B", "C", "D"]:
            opcion = p["opciones"].get(letra, "")
            y = draw_wrapped(
                f"{letra}. {opcion}",
                x + 17,
                y,
                w - 18,
                font_name="Helvetica",
                font_size=7.4,
                leading=8.3,
                max_y_bottom=bottom
            )
            y -= 1.5

    # Agrupar por materia, preservando orden original
    materias_orden = []
    por_materia = defaultdict(list)
    for p in preguntas:
        if p["materia"] not in por_materia:
            materias_orden.append(p["materia"])
        por_materia[p["materia"]].append(p)

    total_paginas_preguntas = sum(ceil(len(por_materia[m]) / 4) for m in materias_orden)
    total_pages = 1 + total_paginas_preguntas

    crear_portada(total_pages)

    pagina_global = 0
    page_num = 2

    for materia in materias_orden:
        lista = por_materia[materia]

        for idx in range(0, len(lista), 4):
            grupo = lista[idx:idx + 4]

            if interactivo:
                c.bookmarkPage(f"pagina_{pagina_global}")

            draw_header(page_num, total_pages, materia=materia)

            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(ancho / 2, alto - 47, materia.upper())

            positions = [
                (margen_x, alto - margen_top),
                (margen_x + col_w + gap_col, alto - margen_top),
                (margen_x, alto - margen_top - card_h - gap_row),
                (margen_x + col_w + gap_col, alto - margen_top - card_h - gap_row),
            ]

            for pos, p in zip(positions, grupo):
                dibujar_card(p, pos[0], pos[1], col_w, card_h)

            if interactivo:
                boton("INICIO", 44, 25, 72, 24, "inicio")
                if pagina_global > 0:
                    boton("ATRÁS", 132, 25, 72, 24, f"pagina_{pagina_global - 1}")
                if pagina_global < total_paginas_preguntas - 1:
                    boton("SIGUIENTE", ancho - 132, 25, 88, 24, f"pagina_{pagina_global + 1}")

            c.showPage()
            pagina_global += 1
            page_num += 1

    c.save()
    return str(ruta_pdf)
