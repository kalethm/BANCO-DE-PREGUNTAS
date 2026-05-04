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
    """Inicializa el banco de preguntas con estructura para grupos"""
    if "grupos_preguntas" not in st.session_state:
        # Cada grupo tiene: texto_base_compartido y lista de preguntas
        st.session_state["grupos_preguntas"] = [
            {
                "id": uuid4().hex,
                "texto_base_compartido": "",
                "preguntas": []
            }
        ]
    
    if "profesor_nombre_form" not in st.session_state:
        st.session_state["profesor_nombre_form"] = ""
    
    if "grado_form" not in st.session_state:
        st.session_state["grado_form"] = GRADOS[0]
    
    if "materia_form" not in st.session_state:
        st.session_state["materia_form"] = MATERIAS[0]
    
    if "grupo_actual" not in st.session_state:
        st.session_state["grupo_actual"] = 0
    
    if "pregunta_en_edicion" not in st.session_state:
        st.session_state["pregunta_en_edicion"] = None

def agregar_grupo():
    """Agrega un nuevo grupo de preguntas"""
    nuevo_grupo = {
        "id": uuid4().hex,
        "texto_base_compartido": "",
        "preguntas": []
    }
    st.session_state["grupos_preguntas"].append(nuevo_grupo)
    st.session_state["grupo_actual"] = len(st.session_state["grupos_preguntas"]) - 1

def eliminar_grupo(indice):
    """Elimina un grupo de preguntas"""
    if len(st.session_state["grupos_preguntas"]) > 1:
        st.session_state["grupos_preguntas"].pop(indice)
        if st.session_state["grupo_actual"] >= len(st.session_state["grupos_preguntas"]):
            st.session_state["grupo_actual"] = len(st.session_state["grupos_preguntas"]) - 1

def agregar_pregunta_al_grupo(grupo_idx):
    """Agrega una nueva pregunta al grupo seleccionado"""
    nuevas_preguntas = st.session_state["grupos_preguntas"][grupo_idx]["preguntas"]
    nuevo_numero = len(nuevas_preguntas) + 1
    nuevas_preguntas.append({
        "numero": nuevo_numero,
        "enunciado": "",
        "cantidad_opciones": 4,
        "opciones": {letra: "" for letra in LETRAS},
        "imagen_nombre": None,
    })
    st.session_state["pregunta_en_edicion"] = (grupo_idx, len(nuevas_preguntas) - 1)

def eliminar_pregunta(grupo_idx, pregunta_idx):
    """Elimina una pregunta del grupo"""
    grupo = st.session_state["grupos_preguntas"][grupo_idx]
    grupo["preguntas"].pop(pregunta_idx)
    # Renumerar
    for i, p in enumerate(grupo["preguntas"]):
        p["numero"] = i + 1

def guardar_imagen(imagen_file, grupo_id, pregunta_num):
    """Guarda una imagen y retorna el nombre del archivo"""
    if not imagen_file:
        return None
    
    nombre_limpio = imagen_file.name.lower().replace(" ", "_")
    nombre_final = f"grupo_{grupo_id}_preg_{pregunta_num}_{uuid4().hex}_{nombre_limpio}"
    
    ruta = Path("data/images") / nombre_final
    with open(ruta, "wb") as f:
        f.write(imagen_file.getbuffer())
    
    return nombre_final

def validar_todo():
    """Valida que todas las preguntas de todos los grupos estén completas"""
    errores = []
    total_preguntas = 0
    
    for g_idx, grupo in enumerate(st.session_state["grupos_preguntas"]):
        for p_idx, pregunta in enumerate(grupo["preguntas"]):
            total_preguntas += 1
            
            if not pregunta["enunciado"].strip():
                errores.append(f"Grupo {g_idx+1}, Pregunta {p_idx+1}: falta el enunciado")
            
            cantidad = int(pregunta["cantidad_opciones"])
            for i in range(cantidad):
                letra = LETRAS[i]
                if not pregunta["opciones"].get(letra, "").strip():
                    errores.append(f"Grupo {g_idx+1}, Pregunta {p_idx+1}: falta opción {letra}")
    
    return errores, total_preguntas

def construir_todas_preguntas(profesor_nombre, grado, materia):
    """Construye la lista de todas las preguntas para guardar en BD"""
    lote_id = uuid4().hex
    todas = []
    numero_global = 1
    
    for grupo in st.session_state["grupos_preguntas"]:
        texto_base = grupo["texto_base_compartido"].strip() or None
        
        for pregunta in grupo["preguntas"]:
            cantidad = int(pregunta["cantidad_opciones"])
            opciones = {}
            for i in range(cantidad):
                letra = LETRAS[i]
                opciones[letra] = pregunta["opciones"][letra].strip()
            
            todas.append({
                "grado": grado,
                "materia": materia,
                "numero": numero_global,
                "enunciado": pregunta["enunciado"].strip(),
                "texto_base": texto_base,
                "imagen": pregunta.get("imagen_nombre"),
                "opciones": opciones,
                "profesor_usuario": st.session_state["usuario"],
                "profesor_nombre": profesor_nombre.strip(),
                "lote_id": lote_id,
            })
            numero_global += 1
    
    return todas

def resumen_completo():
    """Muestra resumen de cuántas preguntas hay en total"""
    total = 0
    for grupo in st.session_state["grupos_preguntas"]:
        total += len(grupo["preguntas"])
    return total

def limpiar_banco_temporal():
    """Limpia todo el banco temporal"""
    if "grupos_preguntas" in st.session_state:
        del st.session_state["grupos_preguntas"]
    st.session_state["grupo_actual"] = 0
    inicializar_banco_temporal()

def vista_profesor():
    inicializar_banco_temporal()
    
    st.title("👨‍🏫 Panel del Profesor - Creación de Exámenes")
    st.write(f"Usuario: **{st.session_state['usuario']}**")
    
    # Datos generales
    with st.expander("📋 Datos generales del examen", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state["profesor_nombre_form"] = st.text_input(
                "Nombre completo del profesor",
                value=st.session_state["profesor_nombre_form"],
                placeholder="Ejemplo: Enrique Rhenals Bello"
            )
        with col2:
            st.session_state["grado_form"] = st.selectbox(
                "Grado",
                GRADOS,
                index=GRADOS.index(st.session_state["grado_form"]) if st.session_state["grado_form"] in GRADOS else 0
            )
        with col3:
            st.session_state["materia_form"] = st.selectbox(
                "Materia",
                MATERIAS,
                index=MATERIAS.index(st.session_state["materia_form"]) if st.session_state["materia_form"] in MATERIAS else 0
            )
    
    # Barra de progreso - CORREGIDA
    total_preguntas = resumen_completo()
    errores, _ = validar_todo()
    
    # Calcular preguntas completas correctamente
    preguntas_completas = 0
    for grupo in st.session_state["grupos_preguntas"]:
        for pregunta in grupo["preguntas"]:
            if pregunta["enunciado"].strip():  # Tiene enunciado
                cantidad = int(pregunta["cantidad_opciones"])
                opciones_completas = True
                for i in range(cantidad):
                    letra = LETRAS[i]
                    if not pregunta["opciones"].get(letra, "").strip():
                        opciones_completas = False
                        break
                if opciones_completas:
                    preguntas_completas += 1
    
    col_prog1, col_prog2 = st.columns([3, 1])
    with col_prog1:
        if total_preguntas > 0:
            # Asegurar que el valor esté entre 0 y 1
            valor_progreso = max(0.0, min(1.0, preguntas_completas / total_preguntas))
            st.progress(valor_progreso)
        else:
            st.progress(0.0)
    with col_prog2:
        st.metric("Preguntas", f"{preguntas_completas}/{total_preguntas}")
    
    if errores:
        st.warning(f"⚠️ {len(errores)} campos incompletos")
    
    st.divider()
    
    # Selector de grupos
    col_grupos, col_actions = st.columns([3, 1])
    with col_grupos:
        grupos_tabs = st.tabs([f"Grupo {i+1}" + (f" 📝" if st.session_state["grupos_preguntas"][i]["texto_base_compartido"] else "") for i in range(len(st.session_state["grupos_preguntas"]))])
    
    with col_actions:
        st.write("")
        if st.button("➕ Agregar Grupo", use_container_width=True):
            agregar_grupo()
            st.rerun()
    
    # Mostrar cada grupo en su tab
    for idx, tab in enumerate(grupos_tabs):
        with tab:
            grupo = st.session_state["grupos_preguntas"][idx]
            
            # Botón eliminar grupo
            col_del1, col_del2 = st.columns([6, 1])
            with col_del2:
                if len(st.session_state["grupos_preguntas"]) > 1:
                    if st.button("🗑️", key=f"del_group_{idx}"):
                        eliminar_grupo(idx)
                        st.rerun()
            
            # Texto base compartido del grupo
            nuevo_texto = st.text_area(
                "📄 **Texto base (compartido para todas las preguntas de este grupo)**",
                value=grupo["texto_base_compartido"],
                height=120,
                placeholder="Ejemplo: Lea el siguiente texto y responda las preguntas...",
                key=f"texto_base_{idx}"
            )
            if nuevo_texto != grupo["texto_base_compartido"]:
                grupo["texto_base_compartido"] = nuevo_texto
            
            st.divider()
            
            # Lista de preguntas del grupo
            st.subheader(f"📝 Preguntas del Grupo {idx+1}")
            
            if not grupo["preguntas"]:
                st.info("No hay preguntas en este grupo. Agregue la primera pregunta.")
            else:
                # Mostrar preguntas existentes
                for p_idx, pregunta in enumerate(grupo["preguntas"]):
                    # Determinar si la pregunta está completa
                    pregunta_completa = pregunta["enunciado"].strip()
                    if pregunta_completa:
                        cantidad = int(pregunta["cantidad_opciones"])
                        for i in range(cantidad):
                            letra = LETRAS[i]
                            if not pregunta["opciones"].get(letra, "").strip():
                                pregunta_completa = False
                                break
                    
                    with st.expander(f"Pregunta {pregunta['numero']} - {'✅' if pregunta_completa else '⚠️ Incompleta'}", expanded=False):
                        col_del, col_edit = st.columns([6, 1])
                        with col_del:
                            if st.button(f"Eliminar pregunta", key=f"del_q_{idx}_{p_idx}"):
                                eliminar_pregunta(idx, p_idx)
                                st.rerun()
                        
                        # Editar pregunta
                        nuevo_enunciado = st.text_area(
                            "Enunciado",
                            value=pregunta["enunciado"],
                            height=80,
                            key=f"enunciado_{idx}_{p_idx}"
                        )
                        pregunta["enunciado"] = nuevo_enunciado
                        
                        cantidad = st.number_input(
                            "Cantidad de opciones",
                            min_value=3,
                            max_value=8,
                            value=int(pregunta["cantidad_opciones"]),
                            step=1,
                            key=f"cant_op_{idx}_{p_idx}"
                        )
                        pregunta["cantidad_opciones"] = cantidad
                        
                        cols_op = st.columns(2)
                        for i in range(int(cantidad)):
                            letra = LETRAS[i]
                            with cols_op[i % 2]:
                                pregunta["opciones"][letra] = st.text_input(
                                    f"Opción {letra}",
                                    value=pregunta["opciones"].get(letra, ""),
                                    key=f"opcion_{idx}_{p_idx}_{letra}"
                                )
                        
                        imagen = st.file_uploader(
                            "Imagen (opcional)",
                            type=["png", "jpg", "jpeg"],
                            key=f"img_{idx}_{p_idx}"
                        )
                        if imagen:
                            nombre_img = guardar_imagen(imagen, grupo["id"], pregunta["numero"])
                            pregunta["imagen_nombre"] = nombre_img
                            st.success("Imagen cargada")
                        
                        if pregunta.get("imagen_nombre"):
                            st.caption(f"Imagen: {pregunta['imagen_nombre'][:50]}...")
            
            # Botón para agregar pregunta al grupo
            if st.button(f"➕ Agregar pregunta al Grupo {idx+1}", key=f"add_q_{idx}"):
                agregar_pregunta_al_grupo(idx)
                st.rerun()
    
    # Guardar todo
    st.divider()
    st.subheader("💾 Guardar examen completo")
    
    profesor_nombre = st.session_state["profesor_nombre_form"]
    grado = st.session_state["grado_form"]
    materia = st.session_state["materia_form"]
    
    if not profesor_nombre.strip():
        st.error("Debe ingresar el nombre completo del profesor")
    elif total_preguntas == 0:
        st.error("Debe agregar al menos una pregunta")
    else:
        errores, _ = validar_todo()
        if errores:
            st.warning(f"⚠️ Faltan completar {len(errores)} campos antes de guardar")
            with st.expander("Ver errores"):
                for err in errores[:10]:  # Mostrar máximo 10 errores
                    st.write(f"- {err}")
                if len(errores) > 10:
                    st.write(f"... y {len(errores) - 10} errores más")
        else:
            st.success(f"✅ Todas las {total_preguntas} preguntas están completas")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Guardar examen", type="primary", use_container_width=True):
                    todas = construir_todas_preguntas(profesor_nombre, grado, materia)
                    guardar_preguntas_lote(todas)
                    st.success(f"✅ {len(todas)} preguntas guardadas correctamente")
                    limpiar_banco_temporal()
                    st.rerun()
            with col2:
                if st.button("🔄 Reiniciar formulario", use_container_width=True):
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
    
    st.subheader("📋 Preguntas registradas")
    
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
                "Profesor": p["profesor_nombre"],
                "Fecha": p["fecha"][:10] if p["fecha"] else ""
            }
            for p in preguntas
        ])
        
        editado = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            disabled=["ID", "Grado", "Materia", "Número", "Texto base", "Enunciado", "Opciones", "Profesor", "Fecha"],
            column_config={"Seleccionar": st.column_config.CheckboxColumn("Seleccionar")}
        )
        
        ids_seleccionados = editado.loc[editado["Seleccionar"] == True, "ID"].tolist()
        
        if st.button("🗑️ Eliminar preguntas seleccionadas"):
            if ids_seleccionados:
                eliminar_preguntas_por_ids([int(x) for x in ids_seleccionados])
                st.success("Preguntas eliminadas correctamente")
                st.rerun()
            else:
                st.warning("Seleccione al menos una pregunta")
    else:
        st.warning("No hay preguntas registradas con esos filtros")
    
    st.divider()
    
    st.subheader("⚙️ Configuración de portada y cuadernillo")
    
    col_periodo, col_sesion = st.columns(2)
    with col_periodo:
        periodo_pdf = st.selectbox(
            "Período",
            ["PRIMER PERIODO", "SEGUNDO PERIODO", "TERCER PERIODO", "CUARTO PERIODO"],
            index=0
        )
    with col_sesion:
        sesion_pdf = st.selectbox(
            "Sesión",
            ["PRIMERA SESIÓN", "SEGUNDA SESIÓN"],
            index=0
        )
    
    st.divider()
    
    st.subheader("📄 Generar PDF normal compacto")
    
    nombre_pdf_normal = st.text_input("Nombre del PDF normal", value="banco_preguntas_normal.pdf")
    
    if st.button("Generar PDF normal"):
        if not preguntas:
            st.error("No hay preguntas para generar PDF")
        else:
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
    
    st.subheader("📘 Generar PDF interactivo")
    
    nombre_pdf_interactivo = st.text_input("Nombre del PDF interactivo", value="banco_preguntas_interactivo.pdf")
    password_pdf = st.text_input("Contraseña para el PDF", type="password", placeholder="Opcional")
    
    if st.button("Generar PDF interactivo"):
        if not preguntas:
            st.error("No hay preguntas para generar PDF interactivo")
        else:
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
        cerrar_sesion()
        
        if st.session_state["rol"] == "admin":
            vista_admin()
        elif st.session_state["rol"] == "profesor":
            vista_profesor()
        else:
            st.error("Rol no reconocido")

if __name__ == "__main__":
    main()