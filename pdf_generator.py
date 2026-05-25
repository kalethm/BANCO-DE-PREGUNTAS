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

        return canvas.Canvas(
            str(ruta_pdf),
            pagesize=letter,
            encrypt=enc,
        )

    return canvas.Canvas(str(ruta_pdf), pagesize=letter)


def _texto_base_valido(texto):

    if texto is None:
        return False

    texto = str(texto or "")

    texto = texto.replace("\r", "")
    texto = texto.replace("\n", "")
    texto = texto.strip()

    if texto.lower() in ["", "none", "null"]:
        return False

    return len(texto) > 0


def _wrap_text(
    text,
    max_width,
    font_name="Helvetica",
    font_size=9,
):

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

            if (
                stringWidth(
                    test,
                    font_name,
                    font_size,
                )
                <= max_width
            ):
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

    lines = _wrap_text(
        text,
        max_width,
        font_name,
        font_size,
    )

    if max_lines:
        lines = lines[:max_lines]

    for line in lines:
        c.drawString(x, y, line)
        y -= leading

    return y, len(lines)


def _boton(
    c,
    texto,
    x,
    y,
    w,
    h,
    destino,
):

    verde = (0.05, 0.60, 0.12)

    c.setFillColorRGB(*verde)

    c.roundRect(
        x,
        y,
        w,
        h,
        8,
        fill=1,
        stroke=0,
    )

    c.setFillColorRGB(1, 1, 1)

    c.setFont(
        "Helvetica-Bold",
        10,
    )

    c.drawCentredString(
        x + w / 2,
        y + h / 2 - 4,
        texto,
    )

    c.linkRect(
        "",
        destino,
        (
            x,
            y,
            x + w,
            y + h,
        ),
        relative=0,
    )

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

    negro = (0, 0, 0)

    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, ancho, alto, fill=1, stroke=0)

    c.setFillColorRGB(*negro)

    c.setFont("Helvetica-Bold", 7.8)
    c.drawString(62, alto - 55, institucion.upper())

    c.setFont("Helvetica-Bold", 25)
    c.drawCentredString(
        ancho / 2,
        alto - 130,
        "EXÁMENES FINALES",
    )

    c.setFont("Helvetica-Bold", 25)
    c.drawCentredString(
        ancho / 2,
        alto - 168,
        periodo.upper(),
    )

    c.setFont("Helvetica-Bold", 24)
    c.drawString(
        ancho - 375,
        alto - 515,
        "GRADO: " + str(grado_texto),
    )


def _draw_header_normal(
    c,
    page_num,
    materia,
    grado_texto,
):

    ancho, alto = letter

    margen_x = 36

    c.setFont("Helvetica", 7.5)

    c.drawString(
        margen_x,
        alto - 23,
        f"{_nombre_grado(grado_texto)} - Página {page_num}",
    )

    c.drawRightString(
        ancho - margen_x,
        alto - 23,
        materia.upper(),
    )

    c.line(
        margen_x,
        alto - 29,
        ancho - margen_x,
        alto - 29,
    )


def _draw_header_interactivo(
    c,
    i,
    total,
    materia,
    grado_texto,
):

    ancho, alto = letter

    margen_x = 52

    c.setFont("Helvetica", 8)

    c.drawString(
        margen_x,
        alto - 25,
        f"{_nombre_grado(grado_texto)} - Pregunta {i + 1} de {total}",
    )

    c.drawRightString(
        ancho - margen_x,
        alto - 25,
        materia.upper(),
    )

    c.line(
        margen_x,
        alto - 32,
        ancho - margen_x,
        alto - 32,
    )


# =========================================================
# PDF NORMAL - UNA SOLA COLUMNA (MODIFICADO)
# =========================================================

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

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta_pdf = output_dir / nombre_pdf

    c = _crear_canvas(ruta_pdf)

    ancho, alto = letter

    margen_x = 48  # Margen izquierdo y derecho (más espacio para una columna)
    margen_y = 65  # Margen superior después del encabezado
    bottom_y = 48  # Margen inferior
    
    # Ancho de la columna (una sola columna ocupa casi todo el ancho)
    col_w = ancho - (2 * margen_x)

    FONT_SIZE_TB = 9
    ALTURA_LINEA_TB = 12
    ESPACIO_DESPUES_TB = 15
    PADDING_TB = 12

    def estimate_height(p):
        """Estima la altura que ocupará una pregunta"""
        h = 45  # Altura base (número de pregunta + espacio)

        texto_base = p.get("texto_base")

        if _texto_base_valido(texto_base):

            lineas_tb = _wrap_text(
                texto_base,
                col_w - 20,
                "Helvetica",
                FONT_SIZE_TB,
            )

            h += (
                PADDING_TB
                + (len(lineas_tb) * ALTURA_LINEA_TB)
                + 20
            )

        lineas_enc = _wrap_text(
            f"{p['numero']}. {p['enunciado']}",
            col_w - 15,
            "Helvetica",
            11,
        )

        h += len(lineas_enc) * 14

        if p.get("imagen"):
            h += 110

        opciones_imagenes = p.get("opciones_imagenes", {})
        opciones_ecuaciones = p.get("opciones_ecuaciones", {})

        for letra in sorted(p["opciones"].keys()):

            if opciones_imagenes.get(letra):
                h += 130
            elif opciones_ecuaciones.get(letra):
                # Para ecuaciones, estimar líneas
                ecuacion = opciones_ecuaciones.get(letra, "")
                lineas_eq = _wrap_text(
                    f"{letra}. {ecuacion}",
                    col_w - 20,
                    "Helvetica-Oblique",
                    9,
                )
                h += (len(lineas_eq) * 12) + 10
            else:
                opcion_texto = str(
                    p["opciones"].get(letra) or ""
                ).strip()
                
                # Si la opción comienza con $, es una ecuación
                if opcion_texto.startswith('$') and opcion_texto.endswith('$'):
                    lineas_op = _wrap_text(
                        f"{letra}. {opcion_texto}",
                        col_w - 20,
                        "Helvetica-Oblique",
                        9,
                    )
                else:
                    lineas_op = _wrap_text(
                        f"{letra}. {opcion_texto}",
                        col_w - 20,
                        "Helvetica",
                        9,
                    )
                h += (len(lineas_op) * 11) + 6

        return h + 20

    def draw_question(p, x, y):
        """Dibuja una pregunta en la posición dada"""
        texto_base = p.get("texto_base")

        texto_base = str(texto_base or "")
        texto_base = texto_base.replace("\r", "")
        texto_base = texto_base.strip()

        tiene_texto_base = (
            texto_base
            and texto_base.replace("\n", "").strip()
        )

        if tiene_texto_base:

            lineas_tb = _wrap_text(
                texto_base,
                col_w - 20,
                "Helvetica",
                FONT_SIZE_TB,
            )

            altura_tb = (
                PADDING_TB
                + (len(lineas_tb) * ALTURA_LINEA_TB)
                + 8
            )

            c.saveState()

            c.setFillColorRGB(0.94, 0.94, 0.94)

            c.roundRect(
                x,
                y - altura_tb + 6,
                col_w,
                altura_tb,
                6,
                fill=1,
                stroke=0,
            )

            c.setStrokeColorRGB(0.75, 0.75, 0.75)

            c.roundRect(
                x,
                y - altura_tb + 6,
                col_w,
                altura_tb,
                6,
                fill=0,
                stroke=1,
            )

            c.restoreState()

            yy = y - 12

            c.setFont(
                "Helvetica",
                FONT_SIZE_TB,
            )

            c.setFillColorRGB(0, 0, 0)

            for line in lineas_tb:

                c.drawString(
                    x + 8,
                    yy,
                    line,
                )

                yy -= ALTURA_LINEA_TB

            y -= altura_tb + ESPACIO_DESPUES_TB

        # Dibujar el número y enunciado de la pregunta
        c.setFont("Helvetica-Bold", 11)
        
        # Procesar el enunciado (podría contener ecuaciones)
        enunciado = p['enunciado']
        
        # Dividir el enunciado en líneas
        lineas_enc = _wrap_text(
            f"{p['numero']}. {enunciado}",
            col_w - 15,
            "Helvetica",
            11,
        )

        for line in lineas_enc:
            c.drawString(x, y, line)
            y -= 14

        y -= 6

        # Dibujar imagen de la pregunta si existe
        if p.get("imagen"):

            img_path = Path("data/images") / str(p["imagen"])

            if img_path.exists():

                try:

                    img = ImageReader(str(img_path))

                    iw, ih = img.getSize()

                    max_w = col_w - 40
                    max_h = 200

                    scale = min(
                        max_w / iw,
                        max_h / ih,
                    )

                    img_w = iw * scale
                    img_h = ih * scale

                    img_x = x + ((col_w - img_w) / 2)

                    c.drawImage(
                        img,
                        img_x,
                        y - img_h,
                        width=img_w,
                        height=img_h,
                        preserveAspectRatio=True,
                        mask="auto",
                    )

                    y -= img_h + 15

                except Exception:
                    pass

        # Dibujar opciones
        c.setFont("Helvetica", 9)
        
        opciones_imagenes = p.get("opciones_imagenes", {})
        opciones_ecuaciones = p.get("opciones_ecuaciones", {})
        opciones_tipos = p.get("opciones_tipos", {})

        for letra in sorted(p["opciones"].keys()):
            
            tiene_imagen = opciones_imagenes.get(letra)
            tiene_ecuacion = opciones_ecuaciones.get(letra)
            opcion_texto = str(p["opciones"].get(letra) or "").strip()

            if tiene_imagen:
                # Mostrar la letra de la opción
                c.setFont("Helvetica-Bold", 9)
                c.drawString(x + 5, y, f"{letra}.")
                
                # Cargar y mostrar la imagen
                img_path = Path("data/images") / str(tiene_imagen)

                if img_path.exists():
                    try:
                        img = ImageReader(str(img_path))
                        iw, ih = img.getSize()
                        max_w = col_w - 60
                        max_h = 120
                        scale = min(max_w / iw, max_h / ih)
                        img_w = iw * scale
                        img_h = ih * scale
                        img_x = x + 25

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

                        # Si también hay texto, mostrarlo debajo
                        if opcion_texto and opcion_texto != "[IMAGEN]":
                            c.setFont("Helvetica", 9)
                            lineas_op_img = _wrap_text(
                                opcion_texto,
                                col_w - 40,
                                "Helvetica",
                                9,
                            )
                            for line in lineas_op_img:
                                y -= 11
                                c.drawString(x + 25, y, line)
                            y -= 6
                    except Exception:
                        # Si falla la imagen, mostrar texto
                        c.setFont("Helvetica", 9)
                        y = _draw_wrapped(
                            c,
                            f"{letra}. {opcion_texto}",
                            x + 15,
                            y,
                            col_w - 25,
                            "Helvetica",
                            9,
                            11,
                        )[0]
                        y -= 2
                else:
                    # Imagen no encontrada, mostrar texto
                    c.setFont("Helvetica", 9)
                    y = _draw_wrapped(
                        c,
                        f"{letra}. {opcion_texto}",
                        x + 15,
                        y,
                        col_w - 25,
                        "Helvetica",
                        9,
                        11,
                    )[0]
                    y -= 2
                    
            elif tiene_ecuacion:
                # Mostrar opción como ecuación
                c.setFont("Helvetica-Bold", 9)
                c.drawString(x + 5, y, f"{letra}.")
                
                # Mostrar la ecuación en cursiva
                c.setFont("Helvetica-Oblique", 9)
                ecuacion_texto = tiene_ecuacion
                lineas_eq = _wrap_text(
                    ecuacion_texto,
                    col_w - 30,
                    "Helvetica-Oblique",
                    9,
                )
                for line in lineas_eq:
                    y -= 11
                    c.drawString(x + 20, y, line)
                y -= 6
                
                # Restaurar fuente normal
                c.setFont("Helvetica", 9)
                
            else:
                # Opción de texto normal
                # Verificar si el texto es una ecuación (empieza con $)
                if opcion_texto.startswith('$') and opcion_texto.endswith('$'):
                    c.setFont("Helvetica-Oblique", 9)
                else:
                    c.setFont("Helvetica", 9)
                    
                y = _draw_wrapped(
                    c,
                    f"{letra}. {opcion_texto}",
                    x + 15,
                    y,
                    col_w - 25,
                    "Helvetica" if not (opcion_texto.startswith('$') and opcion_texto.endswith('$')) else "Helvetica-Oblique",
                    9,
                    11,
                )[0]
                y -= 2

        return y - 8

    # Portada
    _draw_cover(
        c,
        preguntas,
        grado_texto,
        sesion,
        periodo,
        institucion,
        False,
    )

    c.showPage()

    # Agrupar preguntas por materia
    materias_orden = []
    por_materia = defaultdict(list)

    for p in preguntas:
        if p["materia"] not in por_materia:
            materias_orden.append(p["materia"])
        por_materia[p["materia"]].append(p)

    page_num = 2

    # Procesar cada materia
    for materia in materias_orden:

        _draw_header_normal(
            c,
            page_num,
            materia,
            grado_texto,
        )

        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(
            ancho / 2,
            alto - 45,
            materia.upper(),
        )

        # Posición Y inicial para la primera pregunta (después del título)
        y_position = alto - 95
        
        # Iterar sobre las preguntas de esta materia (una columna)
        for p in por_materia[materia]:

            needed = estimate_height(p)

            # Si no cabe en la página actual, crear nueva página
            if y_position - needed < bottom_y:
                c.showPage()
                page_num += 1

                # Dibujar encabezado en la nueva página
                _draw_header_normal(
                    c,
                    page_num,
                    materia,
                    grado_texto,
                )

                c.setFont("Helvetica-Bold", 14)
                c.drawCentredString(
                    ancho / 2,
                    alto - 45,
                    materia.upper(),
                )

                y_position = alto - 95

            # Dibujar la pregunta
            y_position = draw_question(
                p,
                margen_x,
                y_position,
            )

            # Espacio entre preguntas
            y_position -= 15

        c.showPage()
        page_num += 1

    c.save()

    return str(ruta_pdf)


# =========================================================
# PDF INTERACTIVO (sin cambios, una pregunta por página)
# =========================================================

def generar_pdf_interactivo_una_pregunta(
    preguntas,
    nombre_pdf="banco_preguntas_interactivo.pdf",
    institucion="INSTITUCIÓN EDUCATIVA",
    grado_texto="GRADO",
    sesion="PRIMERA SESIÓN",
    periodo="PRIMER PERIODO",
    password=None,
):

    output_dir = Path("data/pdf")

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta_pdf = output_dir / nombre_pdf

    c = _crear_canvas(
        ruta_pdf,
        password=password,
    )

    ancho, alto = letter

    margen_x = 52

    # PORTADA
    _draw_cover(
        c,
        preguntas,
        grado_texto,
        sesion,
        periodo,
        institucion,
        True,
    )

    c.bookmarkPage("home")

    _boton(
        c,
        "INICIAR",
        ancho / 2 - 55,
        48,
        110,
        30,
        "pregunta_0",
    )

    c.showPage()

    total = len(preguntas)

    for i, p in enumerate(preguntas):

        page_name = f"pregunta_{i}"

        c.bookmarkPage(page_name)

        _draw_header_interactivo(
            c,
            i,
            total,
            p["materia"],
            grado_texto,
        )

        y = alto - 70

        c.setFont("Helvetica-Bold", 18)

        c.drawString(
            margen_x,
            y,
            f"Pregunta {p['numero']}",
        )

        y -= 45

        texto_base = p.get("texto_base")

        texto_base = str(texto_base or "")
        texto_base = texto_base.replace("\r", "")
        texto_base = texto_base.strip()

        tiene_texto_base = (
            texto_base
            and texto_base.replace("\n", "").strip()
        )

        if tiene_texto_base:

            lineas_tb = _wrap_text(
                texto_base,
                ancho - 2 * margen_x - 20,
                "Helvetica",
                10,
            )

            altura_tb = 20 + (len(lineas_tb) * 13)

            c.saveState()

            c.setFillColorRGB(0.94, 0.94, 0.94)

            c.roundRect(
                margen_x,
                y - altura_tb,
                ancho - 2 * margen_x,
                altura_tb,
                10,
                fill=1,
                stroke=0,
            )

            c.restoreState()

            yy = y - 18

            c.setFont("Helvetica", 10)

            for line in lineas_tb:

                c.drawString(
                    margen_x + 10,
                    yy,
                    line,
                )

                yy -= 13

            y -= altura_tb + 20

        c.setFont("Helvetica-Bold", 13)

        lineas_enc = _wrap_text(
            p["enunciado"],
            ancho - 2 * margen_x,
            "Helvetica",
            13,
        )

        for line in lineas_enc:

            c.drawString(
                margen_x,
                y,
                line,
            )

            y -= 17

        y -= 20

        if p.get("imagen"):

            img_path = Path("data/images") / str(p["imagen"])

            if img_path.exists():

                try:

                    img = ImageReader(str(img_path))

                    iw, ih = img.getSize()

                    max_w = ancho - 120
                    max_h = 220

                    scale = min(
                        max_w / iw,
                        max_h / ih,
                    )

                    img_w = iw * scale
                    img_h = ih * scale

                    img_x = (ancho - img_w) / 2

                    c.drawImage(
                        img,
                        img_x,
                        y - img_h,
                        width=img_w,
                        height=img_h,
                        preserveAspectRatio=True,
                        mask="auto",
                    )

                    y -= img_h + 20

                except Exception:
                    pass

        c.setFont("Helvetica", 11)
        
        opciones_ecuaciones = p.get("opciones_ecuaciones", {})
        opciones_imagenes = p.get("opciones_imagenes", {})

        for letra in sorted(p["opciones"].keys()):

            opcion_texto = str(
                p["opciones"].get(letra) or ""
            ).strip()
            
            # Verificar si es ecuación
            if opciones_ecuaciones.get(letra):
                c.setFont("Helvetica-Oblique", 11)
                y = _draw_wrapped(
                    c,
                    f"{letra}. {opciones_ecuaciones[letra]}",
                    margen_x + 20,
                    y,
                    ancho - 2 * margen_x - 20,
                    "Helvetica-Oblique",
                    11,
                    16,
                )[0]
                c.setFont("Helvetica", 11)
            else:
                y = _draw_wrapped(
                    c,
                    f"{letra}. {opcion_texto}",
                    margen_x + 20,
                    y,
                    ancho - 2 * margen_x - 20,
                    "Helvetica",
                    11,
                    16,
                )[0]
                
            y -= 5

            opcion_imagen = p.get(
                "opciones_imagenes",
                {},
            ).get(letra)

            if opcion_imagen:

                img_path = (
                    Path("data/images")
                    / str(opcion_imagen)
                )

                if img_path.exists():

                    try:

                        img = ImageReader(str(img_path))

                        iw, ih = img.getSize()

                        max_w = 220
                        max_h = 120

                        scale = min(
                            max_w / iw,
                            max_h / ih,
                        )

                        img_w = iw * scale
                        img_h = ih * scale

                        c.drawImage(
                            img,
                            margen_x + 40,
                            y - img_h,
                            width=img_w,
                            height=img_h,
                            preserveAspectRatio=True,
                            mask="auto",
                        )

                        y -= img_h + 12

                    except Exception:
                        pass

        btn_y = 28

        _boton(
            c,
            "HOME",
            55,
            btn_y,
            80,
            28,
            "home",
        )

        if i > 0:

            _boton(
                c,
                "ATRÁS",
                170,
                btn_y,
                90,
                28,
                f"pregunta_{i - 1}",
            )

        if i < total - 1:

            _boton(
                c,
                "SIGUIENTE",
                ancho - 170,
                btn_y,
                110,
                28,
                f"pregunta_{i + 1}",
            )

        c.showPage()

    c.save()

    return str(ruta_pdf)