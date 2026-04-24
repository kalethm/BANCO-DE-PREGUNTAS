import streamlit as st
from pathlib import Path
import shutil
import pandas as pd

from database import (
    crear_tablas,
    crear_usuarios_iniciales,
    validar_usuario,
    guardar_pregunta,
    listar_preguntas,
    obtener_grados,
    obtener_materias
)
from parser_preguntas import extraer_texto, parsear_preguntas
from pdf_generator import generar_pdf
from export_android import exportar_json_android

st.set_page_config(
    page_title="Banco de Preguntas",
    page_icon="📚",
    layout="wide"
)

crear_tablas()
crear_usuarios_iniciales()

Path("data/uploads").mkdir(parents=True, exist_ok=True)
Path("data/images").mkdir(parents=True, exist_ok=True)

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
    st.write(f"Bienvenido, **{st.session_state['usuario']}**")

    st.info("""
    Formato esperado:

    GRADO: 6  
    MATERIA: Ciencias Sociales  

    PREGUNTA 1:  
    Texto de la pregunta...  

    IMAGEN: pregunta1.png  

    A. Opción A  
    B. Opción B  
    C. Opción C  
    D. Opción D
    """)

    archivo = st.file_uploader("Suba el archivo Word o TXT con las preguntas", type=["docx", "txt"])

    imagenes = st.file_uploader(
        "Suba las imágenes de las preguntas, si aplica",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    if st.button("Procesar y guardar preguntas"):
        if not archivo:
            st.warning("Debe subir un archivo Word o TXT.")
            return

        ruta_archivo = Path("data/uploads") / archivo.name
        with open(ruta_archivo, "wb") as f:
            f.write(archivo.getbuffer())

        for img in imagenes:
            ruta_img = Path("data/images") / img.name.lower()
            with open(ruta_img, "wb") as f:
                f.write(img.getbuffer())

        try:
            texto = extraer_texto(ruta_archivo)
            preguntas = parsear_preguntas(texto)

            for p in preguntas:
                if p.get("imagen"):
                    p["imagen"] = p["imagen"].lower()
                p["profesor"] = st.session_state["usuario"]
                guardar_pregunta(p)

            st.success(f"Se guardaron {len(preguntas)} preguntas correctamente.")

            with st.expander("Ver preguntas detectadas"):
                for p in preguntas:
                    st.markdown(f"### Pregunta {p['numero']}")
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

    if preguntas:
        df = pd.DataFrame([
            {
                "ID": p["id"],
                "Grado": p["grado"],
                "Materia": p["materia"],
                "Pregunta": p["numero"],
                "Enunciado": p["enunciado"][:80],
                "Imagen": p["imagen"],
                "Profesor": p["profesor"],
                "Fecha": p["fecha"]
            }
            for p in preguntas
        ])
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No hay preguntas registradas con esos filtros.")

    st.divider()

    st.subheader("📄 Generar PDF")

    nombre_pdf = st.text_input("Nombre del PDF", value="banco_preguntas.pdf")

    if st.button("Generar PDF"):
        if not preguntas:
            st.error("No hay preguntas para generar PDF.")
        else:
            ruta_pdf = generar_pdf(preguntas, nombre_pdf)
            st.success("PDF generado correctamente.")
            with open(ruta_pdf, "rb") as f:
                st.download_button(
                    "Descargar PDF",
                    data=f,
                    file_name=nombre_pdf,
                    mime="application/pdf"
                )

    st.divider()

    st.subheader("📱 Exportar preguntas para Android")

    nombre_json = st.text_input("Nombre del archivo JSON para Android", value="preguntas_android.json")

    if st.button("Exportar JSON para APK"):
        if not preguntas:
            st.error("No hay preguntas para exportar.")
        else:
            ruta_json = exportar_json_android(preguntas, nombre_json)
            st.success("Archivo JSON exportado correctamente.")
            with open(ruta_json, "rb") as f:
                st.download_button(
                    "Descargar JSON",
                    data=f,
                    file_name=nombre_json,
                    mime="application/json"
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
