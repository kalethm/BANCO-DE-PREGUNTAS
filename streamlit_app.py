import streamlit as st
from pathlib import Path
import pandas as pd
from uuid import uuid4

from database import (
    crear_tablas,
    migrar_bd,
    crear_usuarios_iniciales,
    validar_usuario,
    guardar_preguntas_lote,
    listar_preguntas,
    obtener_grados,
    obtener_materias,
    eliminar_preguntas_por_ids,
)
from pdf_generator import generar_pdf_normal_compacto, generar_pdf_interactivo_una_pregunta

st.set_page_config(
    page_title="Banco de Preguntas",
    page_icon="📚",
    layout="wide"
)

crear_tablas()
migrar_bd()
crear_usuarios_iniciales()

Path("data/images").mkdir(parents=True, exist_ok=True)
Path("data/pdf").mkdir(parents=True, exist_ok=True)

GRADOS = ["6", "7", "8", "9", "10", "11"]

MATERIAS = [
    "Ciencias Sociales",
    "Ciencias Naturales",
    "Lengua Castellana",
    "Matemáticas",
    "Inglés",
    "Tecnología e Informática",
    "Ética y Valores",
    "Educación Religiosa",
    "Educación Artística",
    "Educación Física",
    "Filosofía",
    "Ciencias Económicas",
    "Ciencias Políticas",
]

LETRAS = list("ABCDEFGH")
TOTAL_PREGUNTAS = 20

def login():
    st.title("📚 Banco de Preguntas Institucional")
    st.subheader("Inicio de sesión")

    usuario = st.text_input("Usuario")
    clave = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        data = validar_usuario(usuario, clave)
        if data:
            st.session_state["usuario"] = data[0]
            st.session_state["rol"] = data[1]
            st.success("Ingreso exitoso")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

def cerrar_sesion():
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

def crear_estructura_pregunta():
    return {
        "texto_base": "",
        "enunciado": "",
        "cantidad_opciones": 4,
        "opciones": {letra: "" for letra in LETRAS},
        "imagen_nombre": None,
    }

def inicializar_banco_temporal():
    if "preguntas_form" not in st.session_state:
        st.session_state["preguntas_form"] = {}
        for n in range(1, TOTAL_PREGUNTAS + 1):
            st.session_state["preguntas_form"][n] = crear_estructura_pregunta()

    if "pregunta_actual" not in st.session_state:
        st.session_state["pregunta_actual"] = 1

    if "profesor_nombre_form" not in st.session_state:
        st.session_state["profesor_nombre_form"] = ""

    if "grado_form" not in st.session_state:
        st.session_state["grado_form"] = GRADOS[0]

    if "materia_form" not in st.session_state:
        st.session_state["materia_form"] = MATERIAS[0]

def guardar_imagen(imagen_file, numero):
    if not imagen_file:
        return None

    nombre_limpio = imagen_file.name.lower().replace(" ", "_")
    nombre_final = f"pregunta_{numero}_{uuid4().hex}_{nombre_limpio}"

    ruta = Path("data/images") / nombre_final
    with open(ruta, "wb") as f:
        f.write(imagen_file.getbuffer())

    return nombre_final

def validar_pregunta(datos, numero):
    errores = []

    if not datos["enunciado"].strip():
        errores.append(f"Pregunta {numero}: falta el enunciado.")

    cantidad = int(datos["cantidad_opciones"])
    for i in range(cantidad):
        letra = LETRAS[i]
        if not datos["opciones"].get(letra, "").strip():
            errores.append(f"Pregunta {numero}: falta la opción {letra}.")

    return errores

def construir_preguntas_para_guardar(profesor_nombre, grado, materia):
    lote_id = uuid4().hex
    preguntas = []
    errores = []

    for numero in range(1, TOTAL_PREGUNTAS + 1):
        datos = st.session_state["preguntas_form"][numero]
        errores.extend(validar_pregunta(datos, numero))

        cantidad = int(datos["cantidad_opciones"])
        opciones = {}
        for i in range(cantidad):
            letra = LETRAS[i]
            opciones[letra] = datos["opciones"][letra].strip()

        preguntas.append({
            "grado": grado,
            "materia": materia,
            "numero": numero,
            "enunciado": datos["enunciado"].strip(),
            "texto_base": datos["texto_base"].strip() if datos["texto_base"].strip() else None,
            "imagen": datos.get("imagen_nombre"),
            "opciones": opciones,
            "profesor_usuario": st.session_state["usuario"],
            "profesor_nombre": profesor_nombre.strip(),
            "lote_id": lote_id,
        })

    return preguntas, errores

def resumen_avance():
    completas = 0
    incompletas = []
    for numero in range(1, TOTAL_PREGUNTAS + 1):
        datos = st.session_state["preguntas_form"][numero]
        errs = validar_pregunta(datos, numero)
        if errs:
            incompletas.append(numero)
        else:
            completas += 1
    return completas, incompletas

def cambiar_pregunta(nueva):
    nueva = max(1, min(TOTAL_PREGUNTAS, nueva))
    st.session_state["pregunta_actual"] = nueva

def limpiar_banco_temporal():
    if "preguntas_form" in st.session_state:
        del st.session_state["preguntas_form"]
    st.session_state["pregunta_actual"] = 1
    inicializar_banco_temporal()

def vista_profesor():
    inicializar_banco_temporal()

    st.title("👨‍🏫 Panel del Profesor")
    st.write(f"Usuario: **{st.session_state['usuario']}**")

    st.subheader("Datos obligatorios del banco de preguntas")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state["profesor_nombre_form"] = st.text_input(
            "Nombre completo del profesor",
            value=st.session_state["profesor_nombre_form"],
            placeholder="Ejemplo: Enrique Rhenals Bello",
            key="input_profesor_nombre"
        )

    with col2:
        st.session_state["grado_form"] = st.selectbox(
            "Grado",
            GRADOS,
            index=GRADOS.index(st.session_state["grado_form"]) if st.session_state["grado_form"] in GRADOS else 0,
            key="select_grado_form"
        )

    with col3:
        st.session_state["materia_form"] = st.selectbox(
            "Materia",
            MATERIAS,
            index=MATERIAS.index(st.session_state["materia_form"]) if st.session_state["materia_form"] in MATERIAS else 0,
            key="select_materia_form"
        )

    completas, incompletas = resumen_avance()
    st.progress(completas / TOTAL_PREGUNTAS)
    st.caption(f"Preguntas completas: {completas} de {TOTAL_PREGUNTAS}")

    st.divider()

    st.subheader("Diligenciar las 20 preguntas")

    # Selector rápido y navegación real.
    # Importante: este selector NO usa key fijo para evitar conflicto con Session State.
    col_selector, col_estado = st.columns([2, 1])
    with col_selector:
        seleccion = st.selectbox(
            "Ir a una pregunta",
            list(range(1, TOTAL_PREGUNTAS + 1)),
            index=st.session_state["pregunta_actual"] - 1,
            format_func=lambda n: f"Pregunta {n} {'✅' if n not in incompletas else '⚠️'}"
        )
        if seleccion != st.session_state["pregunta_actual"]:
            st.session_state["pregunta_actual"] = seleccion
            st.rerun()

    with col_estado:
        actual = st.session_state["pregunta_actual"]
        if actual in incompletas:
            st.warning(f"Pregunta {actual} incompleta")
        else:
            st.success(f"Pregunta {actual} completa")

    pregunta_num = st.session_state["pregunta_actual"]
    datos = st.session_state["preguntas_form"][pregunta_num]

    st.markdown(f"### Pregunta {pregunta_num} de {TOTAL_PREGUNTAS}")

    datos["texto_base"] = st.text_area(
        "Texto base, opcional",
        value=datos["texto_base"],
        key=f"texto_base_{pregunta_num}",
        height=120,
        placeholder="Pegue aquí un texto base si esta pregunta lo necesita."
    )

    datos["enunciado"] = st.text_area(
        "Enunciado de la pregunta",
        value=datos["enunciado"],
        key=f"enunciado_{pregunta_num}",
        height=130,
        placeholder="Escriba el enunciado de la pregunta."
    )

    datos["cantidad_opciones"] = st.number_input(
        "Cantidad de opciones",
        min_value=3,
        max_value=8,
        value=int(datos["cantidad_opciones"]),
        step=1,
        key=f"cantidad_opciones_{pregunta_num}"
    )

    cantidad = int(datos["cantidad_opciones"])
    opciones_cols = st.columns(2)
    for i in range(cantidad):
        letra = LETRAS[i]
        with opciones_cols[i % 2]:
            datos["opciones"][letra] = st.text_input(
                f"Opción {letra}",
                value=datos["opciones"].get(letra, ""),
                key=f"opcion_{pregunta_num}_{letra}"
            )

    imagen = st.file_uploader(
        "Imagen de esta pregunta, opcional",
        type=["png", "jpg", "jpeg"],
        key=f"imagen_{pregunta_num}"
    )

    if imagen:
        nombre_img = guardar_imagen(imagen, pregunta_num)
        datos["imagen_nombre"] = nombre_img
        st.success(f"Imagen cargada para la pregunta {pregunta_num}.")

    if datos.get("imagen_nombre"):
        st.caption(f"Imagen vinculada: {datos['imagen_nombre']}")

    errores_p = validar_pregunta(datos, pregunta_num)
    if errores_p:
        for e in errores_p:
            st.warning(e)
    else:
        st.success(f"Pregunta {pregunta_num} completa.")

    st.divider()

    col_prev, col_next, col_clear = st.columns(3)

    with col_prev:
        if st.button("⬅️ Anterior", disabled=pregunta_num == 1, use_container_width=True):
            cambiar_pregunta(pregunta_num - 1)
            st.rerun()

    with col_next:
        if st.button("Siguiente ➡️", disabled=pregunta_num == TOTAL_PREGUNTAS, use_container_width=True):
            cambiar_pregunta(pregunta_num + 1)
            st.rerun()

    with col_clear:
        if st.button("Limpiar esta pregunta", use_container_width=True):
            st.session_state["preguntas_form"][pregunta_num] = crear_estructura_pregunta()
            st.success(f"Pregunta {pregunta_num} limpiada.")
            st.rerun()

    st.divider()

    st.subheader("Guardar banco completo")

    if incompletas:
        st.warning(f"Aún faltan preguntas por completar: {', '.join(map(str, incompletas))}")
    else:
        st.success("Las 20 preguntas están completas y listas para guardar.")

    col_guardar, col_reset = st.columns([2, 1])

    with col_guardar:
        if st.button("💾 Guardar las 20 preguntas", type="primary", use_container_width=True):
            profesor_nombre = st.session_state["profesor_nombre_form"]
            grado = st.session_state["grado_form"]
            materia = st.session_state["materia_form"]

            if not profesor_nombre.strip():
                st.error("Debe ingresar el nombre completo del profesor.")
                return

            if not grado:
                st.error("Debe seleccionar el grado.")
                return

            if not materia:
                st.error("Debe seleccionar la materia.")
                return

            preguntas, errores = construir_preguntas_para_guardar(profesor_nombre, grado, materia)

            if errores:
                st.error("No se puede guardar. Revise las siguientes alertas:")
                for e in errores:
                    st.warning(e)
                return

            guardar_preguntas_lote(preguntas)
            st.success("Las 20 preguntas fueron guardadas correctamente.")

            del st.session_state["preguntas_form"]
            st.session_state["pregunta_actual"] = 1
            st.rerun()

    with col_reset:
        if st.button("Reiniciar formulario", use_container_width=True):
            limpiar_banco_temporal()
            st.rerun()

def vista_admin():
    st.title("🛠️ Panel del Administrador")

    grados_bd = obtener_grados()
    materias_bd = obtener_materias()

    grados = ["Todos"] + sorted(set(GRADOS + grados_bd), key=lambda x: str(x))
    materias = ["Todas"] + sorted(set(MATERIAS + materias_bd))

    col1, col2 = st.columns(2)
    with col1:
        grado = st.selectbox("Filtrar por grado", grados)
    with col2:
        materia = st.selectbox("Filtrar por materia", materias)

    preguntas = listar_preguntas(grado, materia)

    st.subheader("Preguntas registradas")

    if preguntas:
        df = pd.DataFrame([
            {
                "Seleccionar": False,
                "ID": p["id"],
                "Grado": p["grado"],
                "Materia": p["materia"],
                "Número": p["numero"],
                "Texto base": "Sí" if p.get("texto_base") else "No",
                "Enunciado": p["enunciado"][:100],
                "Opciones": ", ".join(p["opciones"].keys()),
                "Imagen": "Sí" if p.get("imagen") else "No",
                "Profesor": p["profesor_nombre"],
                "Lote": p.get("lote_id", "")[:8] if p.get("lote_id") else "",
                "Fecha": p["fecha"]
            }
            for p in preguntas
        ])

        editado = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            disabled=["ID", "Grado", "Materia", "Número", "Texto base", "Enunciado", "Opciones", "Imagen", "Profesor", "Lote", "Fecha"],
            key="tabla_preguntas_admin"
        )

        ids_seleccionados = editado.loc[editado["Seleccionar"] == True, "ID"].tolist()

        if st.button("🗑️ Eliminar preguntas seleccionadas"):
            if ids_seleccionados:
                eliminar_preguntas_por_ids([int(x) for x in ids_seleccionados])
                st.success("Preguntas eliminadas correctamente.")
                st.rerun()
            else:
                st.warning("Seleccione al menos una pregunta.")
    else:
        st.warning("No hay preguntas registradas con esos filtros.")

    st.divider()

    st.subheader("⚙️ Configuración de portada y cuadernillo")

    col_periodo, col_sesion = st.columns(2)
    with col_periodo:
        periodo_pdf = st.selectbox(
            "Seleccione el período",
            ["PRIMER PERIODO", "SEGUNDO PERIODO", "TERCER PERIODO", "CUARTO PERIODO"],
            index=0
        )
    with col_sesion:
        sesion_pdf = st.selectbox(
            "Seleccione la sesión",
            ["PRIMERA SESIÓN", "SEGUNDA SESIÓN"],
            index=0
        )

    st.divider()

    st.subheader("📄 Generar PDF normal compacto")

    nombre_pdf_normal = st.text_input(
        "Nombre del PDF normal",
        value="banco_preguntas_normal.pdf"
    )

    if st.button("Generar PDF normal"):
        if not preguntas:
            st.error("No hay preguntas para generar PDF.")
        else:
            ruta_pdf = generar_pdf_normal_compacto(
                preguntas=preguntas,
                nombre_pdf=nombre_pdf_normal,
                titulo="EXÁMENES FINALES",
                subtitulo=periodo_pdf,
                institucion="INSTITUCIÓN EDUCATIVA LAS FLORES",
                grado_texto=f"{grado}°" if grado != "Todos" else "GRADO",
                sesion=sesion_pdf,
                periodo=periodo_pdf
            )
            st.success("PDF normal generado correctamente.")
            with open(ruta_pdf, "rb") as f:
                st.download_button(
                    "Descargar PDF normal",
                    data=f,
                    file_name=nombre_pdf_normal,
                    mime="application/pdf"
                )

    st.divider()

    st.subheader("📘 Generar PDF interactivo, una pregunta por página")

    nombre_pdf_interactivo = st.text_input(
        "Nombre del PDF interactivo",
        value="banco_preguntas_interactivo.pdf"
    )

    password_pdf = st.text_input(
        "Contraseña para abrir el PDF interactivo",
        type="password",
        placeholder="Escriba la contraseña que usarán en las tablets"
    )

    if st.button("Generar PDF interactivo"):
        if not preguntas:
            st.error("No hay preguntas para generar PDF interactivo.")
        elif not password_pdf.strip():
            st.error("Debe escribir una contraseña para el PDF interactivo.")
        else:
            ruta_pdf = generar_pdf_interactivo_una_pregunta(
                preguntas=preguntas,
                nombre_pdf=nombre_pdf_interactivo,
                titulo="EXÁMENES FINALES",
                subtitulo=periodo_pdf,
                institucion="INSTITUCIÓN EDUCATIVA LAS FLORES",
                grado_texto=f"{grado}°" if grado != "Todos" else "GRADO",
                sesion=sesion_pdf,
                periodo=periodo_pdf,
                password=password_pdf.strip()
            )
            st.success("PDF interactivo generado correctamente con contraseña.")
            with open(ruta_pdf, "rb") as f:
                st.download_button(
                    "Descargar PDF interactivo",
                    data=f,
                    file_name=nombre_pdf_interactivo,
                    mime="application/pdf"
                )

def main():
    if "usuario" not in st.session_state:
        login()
    else:
        st.sidebar.success(f"Usuario: {st.session_state['usuario']}")
        st.sidebar.info(f"Rol: {st.session_state['rol']}")
        cerrar_sesion()

        if st.session_state["rol"] == "admin":
            vista_admin()
        elif st.session_state["rol"] == "profesor":
            vista_profesor()
        else:
            st.error("Rol no reconocido.")

if __name__ == "__main__":
    main()
