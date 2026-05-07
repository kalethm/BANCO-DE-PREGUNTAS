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
    obtener_preguntas_por_profesor,
    obtener_todos_bancos_profesores,
    obtener_pregunta_por_id,
    actualizar_pregunta,
    actualizar_pregunta_completa,
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
    return Path(f"data/backups/borrador_{usuario}.json")

def guardar_borrador():
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
        "opciones_imagenes": {letra: None for letra in LETRAS},
        "imagen_nombre": None,
    }

def inicializar_banco_temporal():
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
    
    preguntas_form = {}
    for n in range(1, TOTAL_PREGUNTAS + 1):
        preguntas_form[n] = crear_estructura_pregunta()
    
    st.session_state["preguntas_form"] = preguntas_form
    st.session_state["pregunta_actual"] = 1
    st.session_state["profesor_nombre_form"] = st.session_state.get("nombre_completo", "")
    st.session_state["grado_form"] = GRADOS[0]
    st.session_state["materia_form"] = MATERIAS[0]

def guardar_imagen(imagen_file, prefix, usuario):
    if not imagen_file:
        return None
    nombre_limpio = imagen_file.name.lower().replace(" ", "_")
    nombre_final = f"{usuario}_{prefix}_{uuid4().hex}_{nombre_limpio}"
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
        opciones_imagenes = {}
        for i in range(cantidad):
            letra = LETRAS[i]
            opciones[letra] = datos.get("opciones", {}).get(letra, "").strip()
            if datos.get("opciones_imagenes", {}).get(letra):
                opciones_imagenes[letra] = datos["opciones_imagenes"][letra]
        preguntas.append({
            "grado": grado,
            "materia": materia,
            "numero": numero,
            "enunciado": datos.get("enunciado", "").strip(),
            "texto_base": datos.get("texto_base", "").strip() if datos.get("texto_base", "").strip() else None,
            "imagen": datos.get("imagen_nombre"),
            "opciones": opciones,
            "opciones_imagenes": opciones_imagenes,
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

def vista_profesor():
    inicializar_banco_temporal()
    
    st.title("👨‍🏫 Panel del Profesor")
    st.write(f"Bienvenido: **{st.session_state.get('nombre_completo', st.session_state['usuario'])}**")
    st.write(f"Usuario: **{st.session_state['usuario']}**")
    
    # Mostrar bancos de preguntas del profesor
    st.subheader("📚 Mis bancos de preguntas guardados")
    preguntas_guardadas = obtener_preguntas_por_profesor(st.session_state["usuario"])
    
    if preguntas_guardadas:
        # Agrupar por lote
        lotes = {}
        for p in preguntas_guardadas:
            lote_id = p.get("lote_id", "Sin lote")
            if lote_id not in lotes:
                lotes[lote_id] = []
            lotes[lote_id].append(p)
        
        for lote_id, preg_lote in lotes.items():
            with st.expander(f"📦 Banco {lote_id[:8]} - {len(preg_lote)} preguntas - {preg_lote[0]['fecha'][:10] if preg_lote[0].get('fecha') else 'fecha desconocida'}"):
                st.write(f"Materia: {preg_lote[0]['materia']} | Grado: {preg_lote[0]['grado']}")
                if st.button(f"📄 Generar PDF de este banco", key=f"pdf_{lote_id}"):
                    ruta = generar_pdf_normal_compacto(
                        preguntas=preg_lote,
                        grado_texto=preg_lote[0]['grado'],
                        sesion="PRIMERA SESIÓN",
                        periodo="PRIMER PERIODO"
                    )
                    with open(ruta, "rb") as f:
                        st.download_button("Descargar PDF", f, f"banco_{lote_id[:8]}.pdf")
    else:
        st.info("Aún no ha guardado ningún banco de preguntas. Complete el formulario abajo para crear su primer banco.")
    
    st.divider()
    
    col_save1, col_save2 = st.columns([1, 5])
    with col_save1:
        if st.button("💾 Guardar borrador", use_container_width=True):
            if guardar_borrador():
                st.success("Progreso guardado localmente")

    st.subheader("Datos del examen")
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

    for i in range(cantidad_opciones):
        letra = LETRAS[i]
        st.markdown(f"**Opción {letra}**")
        
        col_op1, col_op2 = st.columns([3, 1])
        with col_op1:
            valor = st.text_input(f"Texto", value=datos.get("opciones", {}).get(letra, ""), key=f"opcion_{pregunta_num}_{letra}")
            if "opciones" not in st.session_state["preguntas_form"][pregunta_num]:
                st.session_state["preguntas_form"][pregunta_num]["opciones"] = {}
            st.session_state["preguntas_form"][pregunta_num]["opciones"][letra] = valor
        
        with col_op2:
            imagen_opcion = st.file_uploader(f"Imagen", type=["png", "jpg", "jpeg"], key=f"img_opcion_{pregunta_num}_{letra}")
            if imagen_opcion:
                nombre_img = guardar_imagen(imagen_opcion, f"opcion_{letra}_p{pregunta_num}", st.session_state["usuario"])
                if "opciones_imagenes" not in st.session_state["preguntas_form"][pregunta_num]:
                    st.session_state["preguntas_form"][pregunta_num]["opciones_imagenes"] = {}
                st.session_state["preguntas_form"][pregunta_num]["opciones_imagenes"][letra] = nombre_img
                st.success(f"Imagen cargada para opción {letra}")
        
        st.markdown("---")

    st.markdown("**🖼️ IMAGEN PRINCIPAL (Opcional)**")
    imagen = st.file_uploader("Subir imagen para la pregunta", type=["png", "jpg", "jpeg"], key=f"imagen_{pregunta_num}")
    if imagen:
        nombre_img = guardar_imagen(imagen, f"pregunta_{pregunta_num}", st.session_state["usuario"])
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
    profesores = obtener_profesores()
    
    grados_lista = ["Todos"] + sorted(set(GRADOS + grados_bd), key=lambda x: str(x))
    materias_lista = ["Todas"] + sorted(set(MATERIAS + materias_bd))
    profesores_lista = ["Todos"] + [p[0] for p in profesores]
    profesor_dict = {p[0]: p[1] for p in profesores}
    
    # Mostrar resumen de bancos por profesor
    st.subheader("📊 Bancos de preguntas por profesor")
    bancos_profesores = obtener_todos_bancos_profesores()
    if bancos_profesores:
        df_bancos = pd.DataFrame([
            {
                "Profesor": b["nombre"],
                "Usuario": b["usuario"],
                "Total preguntas": b["total_preguntas"],
                "Grados": ", ".join(b["grados"]) if b["grados"] else "-",
                "Materias": ", ".join(b["materias"]) if b["materias"] else "-"
            }
            for b in bancos_profesores
        ])
        st.dataframe(df_bancos, use_container_width=True, hide_index=True)
    else:
        st.info("No hay preguntas guardadas aún")
    
    st.divider()
    
    # Pestañas para admin
    tab1, tab2, tab3 = st.tabs(["📋 Ver y filtrar preguntas", "✏️ Editar preguntas", "📊 Generar PDFs con filtros múltiples"])
    
    # ==================== TAB 1: Ver y filtrar ====================
    with tab1:
        st.subheader("Filtros de búsqueda")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            grado = st.selectbox("Filtrar por grado", grados_lista, key="filtro_grado")
        with col2:
            materia = st.selectbox("Filtrar por materia", materias_lista, key="filtro_materia")
        with col3:
            profesor_filtro = st.selectbox("Filtrar por profesor", profesores_lista, format_func=lambda x: x if x == "Todos" else f"{profesor_dict.get(x, x)} ({x})", key="filtro_profesor")
        
        profesor_param = None if profesor_filtro == "Todos" else profesor_filtro
        preguntas = listar_preguntas(grado, materia, profesor_param)
        
        st.subheader(f"📋 Preguntas registradas ({len(preguntas)})")
        
        if preguntas:
            # Verificar imágenes
            for p in preguntas:
                if p.get("imagen"):
                    if not Path(f"data/images/{p['imagen']}").exists():
                        p["imagen_valida"] = "❌"
                    else:
                        p["imagen_valida"] = "✅"
                else:
                    p["imagen_valida"] = "—"
            
            df = pd.DataFrame([
                {
                    "Seleccionar": False,
                    "ID": p["id"],
                    "Grado": p["grado"],
                    "Materia": p["materia"],
                    "Número": p["numero"],
                    "Enunciado": p["enunciado"][:60] + "..." if len(p["enunciado"]) > 60 else p["enunciado"],
                    "Imagen": p["imagen_valida"],
                    "Profesor": p["profesor_nombre"],
                    "Fecha": p["fecha"][:10] if p["fecha"] else ""
                }
                for p in preguntas
            ])
            
            editado = st.data_editor(
                df, 
                use_container_width=True, 
                hide_index=True, 
                column_config={"Seleccionar": st.column_config.CheckboxColumn("Seleccionar")}
            )
            
            ids_seleccionados = editado.loc[editado["Seleccionar"] == True, "ID"].tolist()
            
            col_acciones1, col_acciones2 = st.columns(2)
            with col_acciones1:
                if st.button("🗑️ Eliminar seleccionadas", use_container_width=True):
                    if ids_seleccionados:
                        eliminar_preguntas_por_ids([int(x) for x in ids_seleccionados])
                        st.success(f"{len(ids_seleccionados)} preguntas eliminadas")
                        st.rerun()
                    else:
                        st.warning("Seleccione al menos una pregunta")
            
            with col_acciones2:
                if st.button("🔍 Verificar todas las imágenes", use_container_width=True):
                    imagenes_faltantes = []
                    for p in preguntas:
                        if p.get("imagen"):
                            if not Path(f"data/images/{p['imagen']}").exists():
                                imagenes_faltantes.append(f"ID {p['id']}: {p['imagen']}")
                    if imagenes_faltantes:
                        st.warning(f"⚠️ {len(imagenes_faltantes)} imágenes no encontradas:")
                        for img in imagenes_faltantes[:10]:
                            st.write(f"- {img}")
                    else:
                        st.success("✅ Todas las imágenes están disponibles")
        else:
            st.info("No hay preguntas con esos filtros")
    
    # ==================== TAB 2: Editar preguntas ====================
    with tab2:
        st.subheader("✏️ Editar pregunta existente")
        
        pregunta_id_buscar = st.number_input("ID de la pregunta a editar", min_value=1, step=1, key="editar_id")
        
        if pregunta_id_buscar:
            pregunta = obtener_pregunta_por_id(pregunta_id_buscar)
            
            if pregunta:
                st.success(f"Editando pregunta ID {pregunta_id_buscar}")
                st.caption(f"Profesor: {pregunta['profesor_nombre']} | Materia: {pregunta['materia']} | Grado: {pregunta['grado']}")
                
                if pregunta.get("imagen"):
                    img_path = Path(f"data/images/{pregunta['imagen']}")
                    if not img_path.exists():
                        st.error(f"⚠️ IMAGEN NO ENCONTRADA: {pregunta['imagen']}")
                        st.info("Puede subir una nueva imagen para reemplazarla")
                
                nuevo_texto_base = st.text_area("Texto base", value=pregunta.get("texto_base", ""), height=100, key="edit_texto_base")
                nuevo_enunciado = st.text_area("Enunciado", value=pregunta.get("enunciado", ""), height=100, key="edit_enunciado")
                
                opciones_actuales = pregunta.get("opciones", {})
                st.write("Opciones:")
                nuevas_opciones = {}
                cols_op = st.columns(2)
                for i, letra in enumerate(["A", "B", "C", "D"]):
                    with cols_op[i % 2]:
                        nuevas_opciones[letra] = st.text_input(f"Opción {letra}", value=opciones_actuales.get(letra, ""), key=f"edit_opcion_{letra}")
                
                nueva_imagen = st.file_uploader("Nueva imagen principal (opcional)", type=["png", "jpg", "jpeg"], key="edit_imagen")
                
                if st.button("💾 Guardar cambios", type="primary"):
                    nombre_imagen = pregunta.get("imagen")
                    if nueva_imagen:
                        nombre_limpio = nueva_imagen.name.lower().replace(" ", "_")
                        nombre_imagen = f"edit_{pregunta_id_buscar}_{uuid4().hex}_{nombre_limpio}"
                        ruta = Path("data/images") / nombre_imagen
                        with open(ruta, "wb") as f:
                            f.write(nueva_imagen.getbuffer())
                    
                    actualizar_pregunta(
                        pregunta_id_buscar,
                        nuevo_enunciado,
                        nuevo_texto_base,
                        nombre_imagen,
                        nuevas_opciones,
                        json.dumps(nuevas_opciones, ensure_ascii=False)
                    )
                    st.success("Pregunta actualizada correctamente")
                    st.rerun()
            else:
                st.error(f"No se encontró pregunta con ID {pregunta_id_buscar}")
    
    # ==================== TAB 3: Generar PDFs con filtros múltiples ====================
    with tab3:
        st.subheader("📊 Generar PDF con múltiples filtros")
        
        st.info("💡 Puede seleccionar VARIOS grados y VARIAS materias. El PDF incluirá SOLO las preguntas que cumplan TODOS los filtros seleccionados.")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            grados_disponibles = sorted(set(GRADOS + grados_bd))
            grados_seleccionados = st.multiselect(
                "🎯 Grados (seleccione uno o varios)", 
                grados_disponibles,
                help="Ejemplo: seleccione '6' y '7' para incluir preguntas de ambos grados"
            )
            if grados_seleccionados:
                st.success(f"Grados seleccionados: {', '.join(grados_seleccionados)}°")
            else:
                st.warning("⚠️ Seleccione al menos un grado")
        
        with col_f2:
            materias_disponibles = sorted(set(MATERIAS + materias_bd))
            materias_seleccionadas = st.multiselect(
                "📚 Materias (seleccione una o varias)", 
                materias_disponibles,
                help="Ejemplo: seleccione 'Matemáticas' e 'Inglés' para incluir ambas materias"
            )
            if materias_seleccionadas:
                st.success(f"Materias seleccionadas: {', '.join(materias_seleccionadas)}")
            else:
                st.warning("⚠️ Seleccione al menos una materia")
        
        # Filtro opcional por profesor
        profesor_pdf = st.selectbox(
            "👨‍🏫 Profesor (opcional)", 
            ["Todos"] + [p[0] for p in profesores], 
            format_func=lambda x: x if x == "Todos" else f"{profesor_dict.get(x, x)} ({x})"
        )
        
        st.divider()
        st.subheader("⚙️ Configuración de portada")
        
        col_periodo, col_sesion = st.columns(2)
        with col_periodo:
            periodo_pdf = st.selectbox("Período", ["PRIMER PERIODO", "SEGUNDO PERIODO", "TERCER PERIODO", "CUARTO PERIODO"], index=0)
        with col_sesion:
            sesion_pdf = st.selectbox("Sesión", ["PRIMERA SESIÓN", "SEGUNDA SESIÓN"], index=0)
        
        # Obtener preguntas según filtros múltiples
        preguntas_filtradas = []
        if grados_seleccionados and materias_seleccionadas:
            for g in grados_seleccionados:
                for m in materias_seleccionadas:
                    params = listar_preguntas(g, m, profesor_pdf if profesor_pdf != "Todos" else None)
                    preguntas_filtradas.extend(params)
        
        # Eliminar duplicados por ID y ordenar
        preguntas_filtradas = list({p["id"]: p for p in preguntas_filtradas}.values())
        preguntas_filtradas.sort(key=lambda x: (int(x["grado"]) if x["grado"].isdigit() else 99, x["materia"], x["numero"]))
        
        st.info(f"📊 **{len(preguntas_filtradas)} preguntas** encontradas con los filtros seleccionados")
        
        if preguntas_filtradas:
            # Mostrar resumen de lo que se va a generar
            with st.expander("📋 Ver preguntas seleccionadas"):
                for p in preguntas_filtradas[:20]:
                    st.write(f"- [{p['grado']}°] {p['materia']} - P{p['numero']}: {p['enunciado'][:80]}...")
                if len(preguntas_filtradas) > 20:
                    st.write(f"... y {len(preguntas_filtradas) - 20} más")
            
            st.divider()
            
            col_pdf1, col_pdf2 = st.columns(2)
            
            with col_pdf1:
                st.subheader("📄 PDF Normal Compacto")
                nombre_normal = st.text_input("Nombre PDF normal", value=f"examen_{datetime.now().strftime('%Y%m%d')}.pdf")
                if st.button("📄 Generar PDF Normal", key="btn_normal_multi", use_container_width=True):
                    with st.spinner("Generando PDF normal..."):
                        grado_texto = f"{', '.join(grados_seleccionados)}°" if len(grados_seleccionados) <= 3 else f"{len(grados_seleccionados)} grados"
                        ruta = generar_pdf_normal_compacto(
                            preguntas=preguntas_filtradas,
                            nombre_pdf=nombre_normal,
                            grado_texto=grado_texto,
                            sesion=sesion_pdf,
                            periodo=periodo_pdf
                        )
                    with open(ruta, "rb") as f:
                        st.download_button("Descargar PDF Normal", f, nombre_normal, use_container_width=True)
            
            with col_pdf2:
                st.subheader("📘 PDF Interactivo")
                nombre_interactivo = st.text_input("Nombre PDF interactivo", value=f"interactivo_{datetime.now().strftime('%Y%m%d')}.pdf")
                password = st.text_input("Contraseña (opcional)", type="password")
                if st.button("📘 Generar PDF Interactivo", key="btn_interactivo_multi", use_container_width=True):
                    with st.spinner("Generando PDF interactivo..."):
                        grado_texto = f"{', '.join(grados_seleccionados)}°" if len(grados_seleccionados) <= 3 else f"{len(grados_seleccionados)} grados"
                        ruta = generar_pdf_interactivo_una_pregunta(
                            preguntas=preguntas_filtradas,
                            nombre_pdf=nombre_interactivo,
                            grado_texto=grado_texto,
                            sesion=sesion_pdf,
                            periodo=periodo_pdf,
                            password=password if password else None
                        )
                    with open(ruta, "rb") as f:
                        st.download_button("Descargar PDF Interactivo", f, nombre_interactivo, use_container_width=True)
        else:
            st.warning("No hay preguntas con los filtros seleccionados. Ajuste los criterios de búsqueda.")


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
        else:
            st.error("Rol no reconocido")


if __name__ == "__main__":
    main()