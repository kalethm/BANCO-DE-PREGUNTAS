# App Banco de Preguntas - Streamlit v4

## Instalación

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Usuarios iniciales

Administrador:

```txt
usuario: admin
clave: admin123
```

Profesor:

```txt
usuario: profesor
clave: profe123
```

## Formato base

```txt
GRADO: 8
MATERIA: Ciencias Sociales

PREGUNTA 1:
Texto de la pregunta.

IMAGEN: pregunta1.png

A. Opción A
B. Opción B
C. Opción C
D. Opción D
```

La imagen es opcional.

## Formato con texto base opcional

```txt
GRADO: 8
MATERIA: Lengua Castellana

TEXTO BASE 1:
Aquí va la lectura, fragmento o información base.
Puede tener varias líneas.
FIN TEXTO BASE

PREGUNTA 1:
Pregunta relacionada con el texto base.

A. Opción A
B. Opción B
C. Opción C
D. Opción D

PREGUNTA 2:
Otra pregunta relacionada con el mismo texto base.

A. Opción A
B. Opción B
C. Opción C
D. Opción D
```

Reglas:

- GRADO, MATERIA, PREGUNTA y opciones A, B, C, D son obligatorios.
- IMAGEN es opcional.
- TEXTO BASE es opcional.
- Si se usa TEXTO BASE, debe cerrarse con FIN TEXTO BASE.
- Las preguntas posteriores quedan asociadas al último texto base encontrado.
- Si aparece otro TEXTO BASE, las siguientes preguntas se asocian al nuevo texto.
