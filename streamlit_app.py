import streamlit as st
from pathlib import Path
import pandas as pd

from database import (
    crear_tablas,
    migrar_bd,
    crear_usuarios_iniciales,
    validar_usuario,
    guardar_pregunta,
    listar_preguntas,
    obtener_grados,
    obtener_materias,
    registrar_archivo,
    listar_archivos_subidos,
    eliminar_preguntas_por_ids,
    eliminar_archivos_por_ids
)
from parser_preguntas import extraer_texto, parsear_preguntas
from pdf_generator import generar_pdf_formato
from export_android import exportar_json_android

st.set_page_config(
    page_title="Banco de Preguntas",
    page_icon="📚",
    layout="wide"
)

crear_tablas()
migrar_bd()
crear_usuarios_iniciales()

Path("data/uploads").mkdir(parents=True, exist_ok=True)
Path("data/images").mkdir(parents=True, exist_ok=True)
Path("data/pdf").mkdir(parents=True, exist_ok=True)

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

def vista_profesor():
    st.title("👨‍🏫 Panel del Profesor")
    st.write(f"Usuario: **{st.session_state['usuario']}**")

    profesor_nombre = st.text_input(
        "Nombre completo del profesor",
        placeholder="Ejemplo: Enrique Rhenals Bello"
    )

    st.warning("El nombre completo del profesor es obligatorio para guardar preguntas.")

    with st.expander("Ver formato aceptado"):
        st.code("""GRADO: 8
MATERIA: Ciencias Sociales

TEXTO BASE 1:
Aquí va un texto base si se necesita.
FIN TEXTO BASE

PREGUNTA 1:
Texto de la pregunta.

IMAGEN: pregunta1.png

A. Opción A
B. Opción B
C. Opción C
D. Opción D

PREGUNTA 2:
Texto de otra pregunta.

A. Opción A
B. Opción B
C. Opción C
D. Opción D""", language="text")

    archivo = st.file_uploader(
        "Suba el archivo Word o TXT con las preguntas",
        type=["docx", "txt"]
    )

    imagenes = st.file_uploader(
        "Suba las imágenes de las preguntas, si aplica",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    if st.button("Procesar y guardar preguntas"):
        if not profesor_nombre.strip():
            st.error("Debe ingresar el nombre completo del profesor.")
            return

        if not archivo:
            st.warning("Debe subir un archivo Word o TXT.")
            return

        nombre_doc = archivo.name.lower().replace(" ", "_")
        ruta_archivo = Path("data/uploads") / nombre_doc

        with open(ruta_archivo, "wb") as f:
            f.write(archivo.getbuffer())

        registrar_archivo(
            nombre_archivo=nombre_doc,
            tipo="documento",
            profesor_usuario=st.session_state["usuario"],
            profesor_nombre=profesor_nombre.strip()
        )

        for img in imagenes:
            nombre_img = img.name.lower().replace(" ", "_")
            ruta_img = Path("data/images") / nombre_img
            with open(ruta_img, "wb") as f:
                f.write(img.getbuffer())

            registrar_archivo(
                nombre_archivo=nombre_img,
                tipo="imagen",
                profesor_usuario=st.session_state["usuario"],
                profesor_nombre=profesor_nombre.strip()
            )

        try:
            texto = extraer_texto(ruta_archivo)
            preguntas = parsear_preguntas(texto)

            for p in preguntas:
                if p.get("imagen"):
                    p["imagen"] = p["imagen"].lower().replace(" ", "_")
                p["profesor"] = st.session_state["usuario"]
                p["profesor_nombre"] = profesor_nombre.strip()
                p["archivo_origen"] = nombre_doc
                guardar_pregunta(p)

            st.success(f"Se guardaron {len(preguntas)} preguntas correctamente.")

            with st.expander("Ver preguntas detectadas"):
                for p in preguntas:
                    st.markdown(f"### Pregunta {p['numero']}")
                    if p.get("texto_base"):
                        st.info(p["texto_base"][:800])
                    st.write(p["enunciado"])
                    if p.get("imagen"):
                        st.write(f"Imagen: {p['imagen']}")
                    st.write(p["opciones"])

        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

def vista_admin():
    st.title("🛠️ Panel del Administrador")

    grados = ["Todos"] + obtener_grados()
    materias = ["Todas"] + obtener_materias()

    col1, col2 = st.columns(2)
    with col1:
        grado = st.selectbox("Filtrar por grado", grados)
    with col2:
        materia = st.selectbox("Filtrar por materia", materias)

    preguntas = listar_preguntas(grado, materia)

    st.subheader("Preguntas registradas")

    ids_seleccionados = []

    if preguntas:
        df = pd.DataFrame([
            {
                "Seleccionar": False,
                "ID": p["id"],
                "Grado": p["grado"],
                "Materia": p["materia"],
                "Pregunta": p["numero"],
                "Texto base": "Sí" if p.get("texto_base") else "No",
                "Enunciado": p["enunciado"][:90],
                "Imagen": p["imagen"],
                "Profesor": p["profesor_nombre"] or p["profesor"],
                "Archivo": p["archivo_origen"],
                "Fecha": p["fecha"]
            }
            for p in preguntas
        ])

        editado = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            disabled=["ID", "Grado", "Materia", "Pregunta", "Texto base", "Enunciado", "Imagen", "Profesor", "Archivo", "Fecha"],
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

    st.subheader("📄 Generar PDF normal con formato institucional")

    nombre_pdf_normal = st.text_input(
        "Nombre del PDF normal",
        value="banco_preguntas_formato.pdf"
    )

    if st.button("Generar PDF normal"):
        if not preguntas:
            st.error("No hay preguntas para generar PDF.")
        else:
            ruta_pdf = generar_pdf_formato(
                preguntas=preguntas,
                nombre_pdf=nombre_pdf_normal,
                interactivo=False,
                titulo="EXÁMENES FINALES",
                subtitulo="PRIMER PERIODO",
                institucion="INSTITUCIÓN EDUCATIVA LAS FLORES",
                grado_texto=f"{grado}°" if grado != "Todos" else "GRADO",
                sesion="PRIMERA SESIÓN"
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

    st.subheader("📘 Generar PDF interactivo con formato institucional")

    nombre_pdf_interactivo = st.text_input(
        "Nombre del PDF interactivo",
        value="banco_preguntas_interactivo.pdf"
    )

    if st.button("Generar PDF interactivo"):
        if not preguntas:
            st.error("No hay preguntas para generar PDF interactivo.")
        else:
            ruta_pdf = generar_pdf_formato(
                preguntas=preguntas,
                nombre_pdf=nombre_pdf_interactivo,
                interactivo=True,
                titulo="EXÁMENES FINALES",
                subtitulo="PRIMER PERIODO",
                institucion="INSTITUCIÓN EDUCATIVA LAS FLORES",
                grado_texto=f"{grado}°" if grado != "Todos" else "GRADO",
                sesion="PRIMERA SESIÓN"
            )
            st.success("PDF interactivo generado correctamente.")
            with open(ruta_pdf, "rb") as f:
                st.download_button(
                    "Descargar PDF interactivo",
                    data=f,
                    file_name=nombre_pdf_interactivo,
                    mime="application/pdf"
                )

    st.divider()


    st.subheader("🗂️ Archivos subidos")

    archivos = listar_archivos_subidos()

    if archivos:
        df_archivos = pd.DataFrame([
            {
                "Seleccionar": False,
                "ID": a["id"],
                "Archivo": a["nombre_archivo"],
                "Tipo": a["tipo"],
                "Profesor": a["profesor_nombre"] or a["profesor_usuario"],
                "Fecha": a["fecha"]
            }
            for a in archivos
        ])

        edit_archivos = st.data_editor(
            df_archivos,
            use_container_width=True,
            hide_index=True,
            disabled=["ID", "Archivo", "Tipo", "Profesor", "Fecha"],
            key="tabla_archivos_admin"
        )

        ids_archivos = edit_archivos.loc[edit_archivos["Seleccionar"] == True, "ID"].tolist()

        if st.button("🗑️ Eliminar archivos seleccionados"):
            if ids_archivos:
                eliminar_archivos_por_ids([int(x) for x in ids_archivos])
                st.success("Archivos eliminados correctamente.")
                st.rerun()
            else:
                st.warning("Seleccione al menos un archivo.")
    else:
        st.info("No hay archivos subidos registrados.")

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
