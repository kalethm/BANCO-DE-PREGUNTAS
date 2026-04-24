from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generar_pdf(preguntas, nombre_pdf):
    output_dir = Path("data/pdf")
    output_dir.mkdir(parents=True, exist_ok=True)

    ruta_pdf = output_dir / nombre_pdf

    doc = SimpleDocTemplate(
        str(ruta_pdf),
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "Titulo",
        parent=styles["Title"],
        fontSize=16,
        spaceAfter=14
    )
    normal = styles["Normal"]
    normal.fontSize = 11
    normal.leading = 15

    elements = []

    if preguntas:
        grado = preguntas[0]["grado"]
        materia = preguntas[0]["materia"]
        elements.append(Paragraph(f"Banco de Preguntas - Grado {grado} - {materia}", titulo))
        elements.append(Spacer(1, 12))

    for p in preguntas:
        elements.append(Paragraph(f"<b>Pregunta {p['numero']}.</b> {p['enunciado']}", normal))
        elements.append(Spacer(1, 8))

        if p.get("imagen"):
            img_path = Path("data/images") / p["imagen"]
            if img_path.exists():
                try:
                    elements.append(Image(str(img_path), width=4.8*inch, height=2.8*inch, kind="proportional"))
                    elements.append(Spacer(1, 8))
                except Exception:
                    elements.append(Paragraph(f"[No se pudo cargar la imagen: {p['imagen']}]", normal))
            else:
                elements.append(Paragraph(f"[Imagen no encontrada: {p['imagen']}]", normal))

        elements.append(Paragraph(f"A. {p['opciones']['A']}", normal))
        elements.append(Paragraph(f"B. {p['opciones']['B']}", normal))
        elements.append(Paragraph(f"C. {p['opciones']['C']}", normal))
        elements.append(Paragraph(f"D. {p['opciones']['D']}", normal))
        elements.append(Spacer(1, 16))

    doc.build(elements)
    return str(ruta_pdf)
