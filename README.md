# App Banco de Preguntas - Streamlit v9

## Cambios v8

- El profesor diligencia exactamente 20 preguntas.
- Navegación con botones Anterior y Siguiente.
- También conserva selector rápido de pregunta.
- Todo lo escrito se mantiene en memoria hasta guardar las 20 preguntas.
- Imagen opcional por pregunta.
- Texto base opcional por pregunta.
- Opciones desde A, B, C hasta máximo H.
- Se eliminó la exportación JSON.

## Usuarios iniciales

Administrador:

usuario: admin
clave: admin123

Profesor:

usuario: profesor
clave: profe123

## Ejecutar

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```


## Ajustes v9

- Se corrigió el conflicto de Streamlit con el selector de preguntas y `session_state`.
- Los botones Anterior y Siguiente ahora navegan sin generar advertencias.

## Ajustes v9

- Portada rediseñada para parecerse más al formato de referencia.
- El administrador puede seleccionar período.
- El administrador puede seleccionar primera o segunda sesión.
- El PDF interactivo exige contraseña definida por el administrador al generarlo.
