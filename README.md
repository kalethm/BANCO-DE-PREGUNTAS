# App Banco de Preguntas - Streamlit

## Instalación

1. Crear entorno virtual:

```bash
python -m venv venv
```

2. Activar entorno:

En Windows:

```bash
venv\Scripts\activate
```

En Linux/Mac:

```bash
source venv/bin/activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Ejecutar la app:

```bash
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

## Formato del archivo Word o TXT

```txt
GRADO: 6
MATERIA: Ciencias Sociales

PREGUNTA 1:
Texto de la pregunta...

IMAGEN: pregunta1.png

A. Opción A
B. Opción B
C. Opción C
D. Opción D
```

La imagen es opcional. Si la pregunta no tiene imagen, no escriba la línea IMAGEN.
