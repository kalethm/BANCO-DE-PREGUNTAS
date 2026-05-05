import streamlit as st
from pathlib import Path
import pandas as pd
from uuid import uuid4
import json
from datetime import datetime

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
    obtener_profesores,
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
Path("data/backups").mkdir(parents=True, exist_ok=True)

GRADOS = ["6", "7", "8", "9", "10", "11"]

MATERIAS = [
    "CIENCIAS NATURALES",
    "CIENCIAS SOCIALES",
    "MATEMATICAS",
    "INGLES",
    "LENGUA CASTELLANA",
    "CIENCIAS NATURALES - BIOLOGÍA",
    "CIENCIAS NATURALES - QUÍMICA",
    "CIENCIAS NATURALES - FISICA",
]

LETRAS = list("ABCDEFGH")
TOTAL_PREGUNTAS = 20

def get_backup_file(usuario):
    """Obtiene la ruta del archivo de borrador para un usuario específico"""
    return Path(f"data/backups/borrador_{usuario}.json")

def guardar_borrador():
    """Guarda el progreso actual del usuario en un archivo local"""
    if "preguntas_form" in st.session_state and st.session_state["preguntas_form"]:
        if "usuario" not in st.session_state:
            return False
        try:
            preguntas_form_serializable = {}
            for k, v in st.session_state["preguntas_form"].items():
                preguntas_form_serializable[str(k)] = v
            
            borrador = {
                "preguntas_form": preguntas_form_serializable,
                "profesor_nombre_form": st.session_state.get("profesor_nombre_form", ""),
                "grado_form": st.session_state.get("grado_form", GRADOS[0]),
                "materia_form": st.session_state.get("materia_form", MATERIAS[0]),
                "pregunta_actual": st.session_state.get("pregunta_actual", 1),
                "fecha_guardado": datetime.now().isoformat()
            }
            backup_file = get_backup_file(st.session_state["usuario"])
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(borrador, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error guardando borrador: {e}")
    return False

def cargar_borrador():
    """Carga el progreso guardado del usuario actual"""
    if "usuario" not in st.session_state:
        return None
    backup_file = get_backup_file(st.session_state["usuario"])
    if backup_file.exists():
        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                borrador = json.load(f)
            if "preguntas_form" in borrador:
                preguntas_form = {}
                for k, v in borrador["preguntas_form"].items():
                    preguntas_form[int(k)] = v
                borrador["preguntas_form"] = preguntas_form
            return borrador
        except Exception as e:
            print(f"Error cargando borrador: {e}")
    return None

def eliminar_borrador():
    """Elimina el archivo de borrador del usuario actual"""
    if "usuario" in st.session_state:
        backup_file = get_backup_file(st.session_state["usuario"])
        if backup_file.exists():
            backup_file.unlink()

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
            st.session_state["nombre_completo"] = data[2] if data[2] else data[0]
            st.success(f"Bienvenido {st.session_state['nombre_completo']}")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

def cerrar_sesion():
    if st.sidebar.button("Cerrar sesión"):
        guardar_borrador()
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
    """Inicializa el banco de preguntas para el usuario actual"""
    if "preguntas_form" in st.session_state and st.session_state["preguntas_form"]:
        if len(st.session_state["preguntas_form"]) == TOTAL_PREGUNTAS:
            return
    
    borrador = cargar_borrador()
    
    if borrador and "preguntas_form" in borrador:
        if len(borrador["preguntas_form"]) == TOTAL_PREGUNTAS:
            st.session_state["preguntas_form"] = borrador["preguntas_form"]
            st.session_state["profesor_nombre_form"] = borrador.get("profesor_nombre_form", st.session_state.get("nombre_completo", ""))
            st.session_state["grado_form"] = borrador.get("grado_form", GRADOS[0])
            st.session_state["materia_form"] = borrador.get("materia_form", MATERIAS[0])
            st.session_state["pregunta_actual"] = borrador.get("pregunta_actual", 1)
            st.info("📀 Se recuperó su progreso guardado")
            return
    
    # Crear nuevo banco
    preguntas_form = {}
    for n in range(1, TOTAL_PREGUNTAS + 1):
        preguntas_form[n] = crear_estructura_pregunta()
    
    st.session_state["preguntas_form"] = preguntas_form
    if "pregunta_actual" not in st.session_state:
        st.session_state["pregunta_actual"] = 1
    # El nombre del profesor se carga automáticamente desde la sesión
    st.session_state["profesor_nombre_form"] = st.session_state.get("nombre_completo", "")
    if "grado_form" not in st.session_state:
        st.session_state["grado_form"] = GRADOS[0]
    if "materia_form" not in st.session_state:
        st.session_state["materia_form"] = MATERIAS[0]

def guardar_imagen(imagen_file, numero, usuario):
    if not imagen_file:
        return None
    nombre_limpio = imagen_file.name.lower().replace(" ", "_")
    nombre_final = f"{usuario}_pregunta_{numero}_{uuid4().hex}_{nombre_limpio}"
    ruta = Path("data/images") / nombre_final
    with open(ruta, "wb") as f:
        f.write(imagen_file.getbuffer())
    return nombre_final

def validar_pregunta(datos, numero):
    errores = []
    if not datos.get("enunciado", "").strip():
        errores.append(f"Pregunta {numero}: falta el enunciado.")
    cantidad = int(datos.get("cantidad_opciones", 4))
    for i in range(cantidad):
        letra = LETRAS[i]
        if not datos.get("opciones", {}).get(letra, "").strip():
            errores.append(f"Pregunta {numero}: falta la opción {letra}.")
    return errores

def construir_preguntas_para_guardar(profesor_nombre, grado, materia, usuario):
    lote_id = uuid4().hex
    preguntas = []
    errores = []
    for numero in range(1, TOTAL_PREGUNTAS + 1):
        datos = st.session_state["preguntas_form"].get(numero, crear_estructura_pregunta())
        errores.extend(validar_pregunta(datos, numero))
        cantidad = int(datos.get("cantidad_opciones", 4))
        opciones = {}
        for i in range(cantidad):
            letra = LETRAS[i]
            opciones[letra] = datos.get("opciones", {}).get(letra, "").strip()
        preguntas.append({
            "grado": grado,
            "materia": materia,
            "numero": numero,
            "enunciado": datos.get("enunciado", "").strip(),
            "texto_base": datos.get("texto_base", "").strip() if datos.get("texto_base", "").strip() else None,
            "imagen": datos.get("imagen_nombre"),
            "opciones": opciones,
            "profesor_usuario": usuario,
            "profesor_nombre": profesor_nombre.strip(),
            "lote_id": lote_id,
        })
    return preguntas, errores

def resumen_avance():
    completas = 0
    incompletas = []
    preguntas_form = st.session_state.get("preguntas_form", {})
    for numero in range(1, TOTAL_PREGUNTAS + 1):
        datos = preguntas_form.get(numero)
        if datos is None:
            incompletas.append(numero)
        else:
            errs = validar_pregunta(datos, numero)
            if errs:
                incompletas.append(numero)
            else:
                completas += 1
    return completas, incompletas

def cambiar_pregunta(nueva):
    nueva = max(1, min(TOTAL_PREGUNTAS, nueva))
    guardar_borrador()
    st.session_state["pregunta_actual"] = nueva

def limpiar_banco_temporal():
    if "preguntas_form" in st.session_state:
        del st.session_state["preguntas_form"]
    st.session_state["pregunta_actual"] = 1
    eliminar_borrador()
    preguntas_form = {}
    for n in range(1, TOTAL_PREGUNTAS + 1):
        preguntas_form[n] = crear_estructura_pregunta()
    st.session_state["preguntas_form"] = preguntas_form
    st.session_state["profesor_nombre_form"] = st.session_state.get("nombre_completo", "")

def vista_profesor():
    inicializar_banco_temporal()
    
    st.title("👨‍🏫 Panel del Profesor")
    st.write(f"Bienvenido: **{st.session_state.get('nombre_completo', st.session_state['usuario'])}**")
    st.write(f"Usuario: **{st.session_state['usuario']}**")
    
    col_save1, col_save2 = st.columns([1, 5])
    with col_save1:
        if st.button("💾 Guardar borrador", use_container_width=True):
            if guardar_borrador():
                st.success("Progreso guardado localmente")

    st.subheader("Datos del examen")
    
    # El nombre del profesor ya está cargado automáticamente
    st.info(f"👤 Profesor: {st.session_state.get('nombre_completo', st.session_state['usuario'])}")
    
    col1, col2 = st.columns(2)
    with col1:
        grado = st.selectbox("Grado", GRADOS, index=GRADOS.index(st.session_state.get("grado_form", GRADOS[0])) if st.session_state.get("grado_form", GRADOS[0]) in GRADOS else 0)
        st.session_state["grado_form"] = grado
    with col2:
        materia = st.selectbox("Materia", MATERIAS, index=MATERIAS.index(st.session_state.get("materia_form", MATERIAS[0])) if st.session_state.get("materia_form", MATERIAS[0]) in MATERIAS else 0)
        st.session_state["materia_form"] = materia

    completas, incompletas = resumen_avance()
    if TOTAL_PREGUNTAS > 0:
        st.progress(completas / TOTAL_PREGUNTAS)
    st.caption(f"Preguntas completas: {completas} de {TOTAL_PREGUNTAS}")
    st.divider()
    st.subheader("Diligenciar las 20 preguntas")

    col_selector, col_estado = st.columns([2, 1])
    with col_selector:
        seleccion = st.selectbox("Ir a una pregunta", list(range(1, TOTAL_PREGUNTAS + 1)), index=st.session_state.get("pregunta_actual", 1) - 1, format_func=lambda n: f"Pregunta {n} {'✅' if n not in incompletas else '⚠️'}")
        if seleccion != st.session_state.get("pregunta_actual", 1):
            st.session_state["pregunta_actual"] = seleccion
            st.rerun()
    with col_estado:
        actual = st.session_state.get("pregunta_actual", 1)
        if actual in incompletas:
            st.warning(f"Pregunta {actual} incompleta")
        else:
            st.success(f"Pregunta {actual} completa")

    pregunta_num = st.session_state.get("pregunta_actual", 1)
    datos = st.session_state["preguntas_form"][pregunta_num]

    st.markdown(f"### Pregunta {pregunta_num} de {TOTAL_PREGUNTAS}")
    
    st.markdown("---")
    st.markdown("**📄 TEXTO BASE (Opcional)**")
    texto_base = st.text_area("", value=datos.get("texto_base", ""), key=f"texto_base_{pregunta_num}", height=100)
    st.session_state["preguntas_form"][pregunta_num]["texto_base"] = texto_base
    
    st.markdown("---")
    st.markdown("**❓ ENUNCIADO DE LA PREGUNTA (Obligatorio)**")
    enunciado = st.text_area("", value=datos.get("enunciado", ""), key=f"enunciado_{pregunta_num}", height=100)
    st.session_state["preguntas_form"][pregunta_num]["enunciado"] = enunciado

    st.markdown("---")
    st.markdown("**🔘 OPCIONES DE RESPUESTA**")
    cantidad_opciones = st.number_input("Cantidad de opciones", min_value=3, max_value=8, value=int(datos.get("cantidad_opciones", 4)), step=1, key=f"cantidad_opciones_{pregunta_num}")
    st.session_state["preguntas_form"][pregunta_num]["cantidad_opciones"] = cantidad_opciones

    opciones_cols = st.columns(2)
    for i in range(cantidad_opciones):
        letra = LETRAS[i]
        with opciones_cols[i % 2]:
            valor = st.text_input(f"Opción {letra}", value=datos.get("opciones", {}).get(letra, ""), key=f"opcion_{pregunta_num}_{letra}")
            if "opciones" not in st.session_state["preguntas_form"][pregunta_num]:
                st.session_state["preguntas_form"][pregunta_num]["opciones"] = {}
            st.session_state["preguntas_form"][pregunta_num]["opciones"][letra] = valor

    st.markdown("---")
    st.markdown("**🖼️ IMAGEN (Opcional)**")
    imagen = st.file_uploader("Subir imagen", type=["png", "jpg", "jpeg"], key=f"imagen_{pregunta_num}")
    if imagen:
        nombre_img = guardar_imagen(imagen, pregunta_num, st.session_state["usuario"])
        st.session_state["preguntas_form"][pregunta_num]["imagen_nombre"] = nombre_img
        st.success("Imagen cargada")
    if st.session_state["preguntas_form"][pregunta_num].get("imagen_nombre"):
        st.caption(f"Imagen: {st.session_state['preguntas_form'][pregunta_num]['imagen_nombre']}")

    errores_p = validar_pregunta(st.session_state["preguntas_form"][pregunta_num], pregunta_num)
    if errores_p:
        for e in errores_p:
            st.warning(e)
    else:
        st.success(f"Pregunta {pregunta_num} completa.")
    st.divider()

    col_prev, col_next, col_clear, col_top = st.columns(4)
    with col_prev:
        if st.button("⬅️ Anterior", disabled=pregunta_num == 1, use_container_width=True):
            guardar_borrador()
            st.session_state["pregunta_actual"] = pregunta_num - 1
            st.rerun()
    with col_next:
        if st.button("Siguiente ➡️", disabled=pregunta_num == TOTAL_PREGUNTAS, use_container_width=True):
            guardar_borrador()
            st.session_state["pregunta_actual"] = pregunta_num + 1
            st.rerun()
    with col_clear:
        if st.button("🗑️ Limpiar", use_container_width=True):
            st.session_state["preguntas_form"][pregunta_num] = crear_estructura_pregunta()
            guardar_borrador()
            st.success(f"Pregunta {pregunta_num} limpiada.")
            st.rerun()
    with col_top:
        if st.button("🔝 Ir al inicio", use_container_width=True):
            guardar_borrador()
            st.session_state["pregunta_actual"] = 1
            st.rerun()

    st.divider()
    st.subheader("Guardar banco completo")
    if incompletas:
        st.warning(f"Faltan preguntas: {', '.join(map(str, incompletas))}")
    else:
        st.success("¡Todas las 20 preguntas están completas!")
    col_guardar, col_reset = st.columns(2)
    with col_guardar:
        if st.button("💾 Guardar en base de datos", type="primary", use_container_width=True):
            profesor_nombre = st.session_state.get("nombre_completo", st.session_state["usuario"])
            grado = st.session_state.get("grado_form", GRADOS[0])
            materia = st.session_state.get("materia_form", MATERIAS[0])
            usuario = st.session_state["usuario"]
            
            preguntas, errores = construir_preguntas_para_guardar(profesor_nombre, grado, materia, usuario)
            if errores:
                st.error("Revise los errores:")
                for e in errores:
                    st.warning(e)
                return
            guardar_preguntas_lote(preguntas)
            eliminar_borrador()
            st.success(f"¡{len(preguntas)} preguntas guardadas exitosamente!")
            del st.session_state["preguntas_form"]
            st.session_state["pregunta_actual"] = 1
            st.rerun()
    with col_reset:
        if st.button("🔄 Reiniciar todo", use_container_width=True):
            limpiar_banco_temporal()
            st.rerun()

def vista_admin():
    st.title("🛠️ Panel del Administrador")
    
    grados_bd = obtener_grados()
    materias_bd = obtener_materias()
    profesores = obtener_profesores()  # Lista de tuplas (usuario, nombre_completo)
    
    grados = ["Todos"] + sorted(set(GRADOS + grados_bd), key=lambda x: str(x))
    materias = ["Todas"] + sorted(set(MATERIAS + materias_bd))
    
    # Crear lista de opciones para el selectbox de profesores
    profesores_opciones = ["Todos"]
    profesor_dict = {}  # Diccionario para mapear usuario -> nombre
    for usuario, nombre in profesores:
        profesores_opciones.append(usuario)
        profesor_dict[usuario] = nombre
    
    col1, col2, col3 = st.columns(3)
    with col1:
        grado = st.selectbox("Filtrar por grado", grados)
    with col2:
        materia = st.selectbox("Filtrar por materia", materias)
    with col3:
        profesor_seleccionado = st.selectbox(
            "Filtrar por profesor", 
            profesores_opciones,
            format_func=lambda x: x if x == "Todos" else f"{profesor_dict.get(x, x)} ({x})"
        )

    # Obtener preguntas según filtros
    profesor_filtro = None if profesor_seleccionado == "Todos" else profesor_seleccionado
    preguntas = listar_preguntas(grado, materia, profesor_filtro)
    
    st.subheader("📋 Preguntas registradas")
    st.caption(f"Total: {len(preguntas)} preguntas")

    if preguntas:
        df = pd.DataFrame([
            {
                "Seleccionar": False,
                "ID": p["id"],
                "Grado": p["grado"],
                "Materia": p["materia"],
                "Número": p["numero"],
                "Texto base": "Sí" if p.get("texto_base") else "No",
                "Enunciado": p["enunciado"][:80] + "..." if len(p["enunciado"]) > 80 else p["enunciado"],
                "Opciones": ", ".join(p["opciones"].keys()),
                "Imagen": "Sí" if p.get("imagen") else "No",
                "Profesor": p["profesor_nombre"],
                "Usuario": p["profesor_usuario"],
                "Fecha": p["fecha"][:10] if p["fecha"] else ""
            }
            for p in preguntas
        ])
        editado = st.data_editor(
            df, 
            use_container_width=True, 
            hide_index=True, 
            disabled=["ID", "Grado", "Materia", "Número", "Texto base", "Enunciado", "Opciones", "Imagen", "Profesor", "Usuario", "Fecha"], 
            column_config={"Seleccionar": st.column_config.CheckboxColumn("Seleccionar")}
        )
        ids_seleccionados = editado.loc[editado["Seleccionar"] == True, "ID"].tolist()
        if st.button("🗑️ Eliminar seleccionadas"):
            if ids_seleccionados:
                eliminar_preguntas_por_ids([int(x) for x in ids_seleccionados])
                st.success(f"{len(ids_seleccionados)} preguntas eliminadas")
                st.rerun()
            else:
                st.warning("Seleccione al menos una pregunta")
    else:
        st.warning("No hay preguntas registradas con esos filtros")

    st.divider()
    st.subheader("⚙️ Configuración de portada y cuadernillo")
    col_periodo, col_sesion = st.columns(2)
    with col_periodo:
        periodo_pdf = st.selectbox("Período", ["PRIMER PERIODO", "SEGUNDO PERIODO", "TERCER PERIODO", "CUARTO PERIODO"], index=0)
    with col_sesion:
        sesion_pdf = st.selectbox("Sesión", ["PRIMERA SESIÓN", "SEGUNDA SESIÓN"], index=0)

    st.divider()
    st.subheader("📄 Generar PDF normal compacto")
    nombre_pdf_normal = st.text_input("Nombre del PDF normal", value="banco_preguntas_normal.pdf")
    if st.button("Generar PDF normal", key="btn_normal"):
        if not preguntas:
            st.error("No hay preguntas para generar PDF")
        else:
            with st.spinner("Generando PDF normal..."):
                ruta_pdf = generar_pdf_normal_compacto(
                    preguntas=preguntas, 
                    nombre_pdf=nombre_pdf_normal, 
                    institucion="INSTITUCIÓN EDUCATIVA LAS FLORES", 
                    grado_texto=f"{grado}°" if grado != "Todos" else "GRADO", 
                    sesion=sesion_pdf, 
                    periodo=periodo_pdf
                )
            st.success("PDF normal generado correctamente")
            with open(ruta_pdf, "rb") as f:
                st.download_button("Descargar PDF normal", data=f, file_name=nombre_pdf_normal, mime="application/pdf")

    st.divider()
    st.subheader("📘 Generar PDF interactivo (una pregunta por página)")
    nombre_pdf_interactivo = st.text_input("Nombre del PDF interactivo", value="banco_preguntas_interactivo.pdf")
    password_pdf = st.text_input("Contraseña para abrir el PDF interactivo", type="password", placeholder="Opcional - dejar vacío si no quiere contraseña")
    
    if st.button("📘 Generar PDF interactivo", key="btn_interactivo", use_container_width=True):
        if not preguntas:
            st.error("No hay preguntas para generar PDF interactivo")
        else:
            with st.spinner("Generando PDF interactivo..."):
                ruta_pdf = generar_pdf_interactivo_una_pregunta(
                    preguntas=preguntas, 
                    nombre_pdf=nombre_pdf_interactivo, 
                    institucion="INSTITUCIÓN EDUCATIVA LAS FLORES", 
                    grado_texto=f"{grado}°" if grado != "Todos" else "GRADO", 
                    sesion=sesion_pdf, 
                    periodo=periodo_pdf, 
                    password=password_pdf.strip() if password_pdf else None
                )
            st.success("PDF interactivo generado correctamente")
            with open(ruta_pdf, "rb") as f:
                st.download_button("Descargar PDF interactivo", data=f, file_name=nombre_pdf_interactivo, mime="application/pdf")

def main():
    if "usuario" not in st.session_state:
        login()
    else:
        st.sidebar.success(f"Usuario: {st.session_state['usuario']}")
        st.sidebar.info(f"Rol: {st.session_state['rol']}")
        if st.sidebar.button("💾 Guardar progreso"):
            guardar_borrador()
            st.sidebar.success("Guardado")
        cerrar_sesion()
        if st.session_state["rol"] == "admin":
            vista_admin()
        elif st.session_state["rol"] == "profesor":
            vista_profesor()

if __name__ == "__main__":
    main()