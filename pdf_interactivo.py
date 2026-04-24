from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth


def generar_pdf_interactivo(
    preguntas,
    nombre_pdf="pdf_interactivo_formato.pdf",
    titulo="EXÁMENES FINALES",
    subtitulo="PRIMER PERIODO",
    institucion="INSTITUCIÓN EDUCATIVA",
    grado_texto="8°",
    sesion="PRIMERA SESIÓN",
):
    output_dir = Path("data/pdf")
    output_dir.mkdir(parents=True, exist_ok=True)

    ruta_pdf = output_dir / nombre_pdf
    c = canvas.Canvas(str(ruta_pdf), pagesize=letter)

    ancho, alto = letter

    margen_x = 38
    margen_y = 40
    col_gap = 22
    col_width = (ancho - 2 * margen_x - col_gap) / 2

    def draw_header(page_num, total_pages):
        c.setFont("Helvetica", 8)
        c.drawString(margen_x, alto - 22, f"{grado_texto} {sesion} - Página {page_num} de {total_pages}")
        c.line(margen_x, alto - 28, ancho - margen_x, alto - 28)

    def wrap_text(text, max_width, font_name="Helvetica", font_size=9):
        words = str(text).split()
        lines = []
        current = ""

        for word in words:
            test = current + " " + word if current else word
            if stringWidth(test, font_name, font_size) <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines

    def draw_wrapped(text, x, y, max_width, font_name="Helvetica", font_size=9, leading=11):
        c.setFont(font_name, font_size)
        lines = wrap_text(text, max_width, font_name, font_size)
        for line in lines:
            c.drawString(x, y, line)
            y -= leading
        return y

    def boton(texto, x, y, w, h, destino):
        c.setFillColorRGB(0.05, 0.60, 0.12)
        c.roundRect(x, y, w, h, 8, fill=1, stroke=0)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(x + w / 2, y + h / 2 - 3, texto)
        c.linkRect("", destino, (x, y, x + w, y + h), relative=0)
        c.setFillColorRGB(0, 0, 0)

    def crear_portada():
        c.bookmarkPage("inicio")

        c.setFont("Helvetica-Bold", 8)
        c.drawString(70, alto - 55, institucion)
        c.drawString(70, alto - 68, "Resolución de Reconocimiento Oficial")
        c.drawString(70, alto - 81, "DANE / NIT / Código ICFES")

        c.setFont("Helvetica-Bold", 30)
        c.drawCentredString(ancho / 2, alto - 135, titulo)

        c.setFont("Helvetica-Bold", 26)
        c.drawCentredString(ancho / 2, alto - 175, subtitulo)

        c.setFont("Helvetica-Bold", 44)
        c.drawCentredString(ancho / 2, alto - 270, "MI META")
        c.drawCentredString(ancho / 2, alto - 330, "ES LA EXCELENCIA")

        c.setFont("Helvetica-Bold", 72)
        c.drawCentredString(ancho / 2, alto - 430, grado_texto)

        c.setFont("Helvetica-Bold", 18)
        c.drawString(55, 230, sesion)

        materias = {}
        for p in preguntas:
            materias[p["materia"]] = materias.get(p["materia"], 0) + 1

        y = 200
        for mat, total in materias.items():
            c.setFont("Helvetica-Bold", 13)
            c.drawString(55, y, mat.upper())
            y -= 24

            c.setFillColorRGB(0.05, 0.60, 0.12)
            c.roundRect(55, y, 220, 24, 7, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(165, y + 7, f"{total} PREGUNTAS")
            c.setFillColorRGB(0, 0, 0)
            y -= 42

        c.setFont("Helvetica-Bold", 16)
        c.drawString(340, 230, "RECUERDA")

        instrucciones = [
            "Lee cada pregunta cuidadosamente.",
            "Elige una sola opción.",
            "Usa los botones para avanzar o regresar.",
            "Puedes volver al inicio cuando lo necesites.",
        ]

        y2 = 205
        c.setFont("Helvetica", 9)
        for item in instrucciones:
            c.drawString(350, y2, f"• {item}")
            y2 -= 18

        boton("INICIAR", ancho / 2 - 55, 55, 110, 30, "pregunta_0")
        c.showPage()

    def crear_paginas_preguntas():
        total = len(preguntas)
        preguntas_por_pagina = 2
        total_paginas_preguntas = (total + preguntas_por_pagina - 1) // preguntas_por_pagina

        for pagina_idx in range(total_paginas_preguntas):
            inicio = pagina_idx * preguntas_por_pagina
            grupo = preguntas[inicio:inicio + preguntas_por_pagina]

            c.bookmarkPage(f"pagina_{pagina_idx}")
            draw_header(pagina_idx + 2, total_paginas_preguntas + 1)

            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(ancho / 2, alto - 45, grupo[0]["materia"].upper())

            posiciones = [
                (margen_x, alto - 75),
                (margen_x + col_width + col_gap, alto - 75),
            ]

            for idx_local, p in enumerate(grupo):
                i_real = inicio + idx_local
                c.bookmarkPage(f"pregunta_{i_real}")

                x, y = posiciones[idx_local]

                c.setFont("Helvetica-Bold", 10)
                c.drawString(x, y, f"{p['numero']}.")

                y = draw_wrapped(
                    p["enunciado"],
                    x + 18,
                    y,
                    col_width - 18,
                    font_name="Helvetica",
                    font_size=9,
                    leading=11
                )

                y -= 6

                if p.get("imagen"):
                    img_path = Path("data/images") / p["imagen"]
                    if img_path.exists():
                        try:
                            img = ImageReader(str(img_path))
                            iw, ih = img.getSize()

                            max_w = col_width - 10
                            max_h = 110

                            escala = min(max_w / iw, max_h / ih)
                            w = iw * escala
                            h = ih * escala

                            c.drawImage(
                                img,
                                x + 10,
                                y - h,
                                width=w,
                                height=h,
                                preserveAspectRatio=True,
                                mask="auto"
                            )
                            y -= h + 10
                        except Exception:
                            y = draw_wrapped(
                                f"[No se pudo cargar imagen: {p['imagen']}]",
                                x,
                                y,
                                col_width
                            )
                    else:
                        y = draw_wrapped(
                            f"[Imagen no encontrada: {p['imagen']}]",
                            x,
                            y,
                            col_width
                        )

                for letra in ["A", "B", "C", "D"]:
                    opcion = p["opciones"].get(letra, "")
                    y = draw_wrapped(
                        f"{letra}. {opcion}",
                        x + 18,
                        y,
                        col_width - 18,
                        font_name="Helvetica",
                        font_size=9,
                        leading=11
                    )
                    y -= 3

            # Navegación por página
            boton("INICIO", 45, 25, 80, 24, "inicio")

            if pagina_idx > 0:
                boton("ATRÁS", 145, 25, 80, 24, f"pagina_{pagina_idx - 1}")

            if pagina_idx < total_paginas_preguntas - 1:
                boton("SIGUIENTE", ancho - 145, 25, 100, 24, f"pagina_{pagina_idx + 1}")

                c.showPage()

         

    crear_portada()
    crear_paginas_preguntas()
    c.save()

    return str(ruta_pdf)