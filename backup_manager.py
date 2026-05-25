# backup_manager.py
import json
import pandas as pd
from pathlib import Path
import sqlite3
from datetime import datetime
import streamlit as st

def exportar_toda_base_datos(formato="excel"):
    """Exporta toda la base de datos a Excel o JSON"""
    conn = sqlite3.connect("data/banco_preguntas.db")
    
    # Leer todas las tablas
    usuarios_df = pd.read_sql_query("SELECT * FROM usuarios", conn)
    preguntas_df = pd.read_sql_query("SELECT * FROM preguntas", conn)
    
    conn.close()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if formato == "excel":
        # Exportar a Excel (múltiples hojas)
        output_file = Path(f"data/backups/backup_completo_{timestamp}.xlsx")
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            usuarios_df.to_excel(writer, sheet_name='usuarios', index=False)
            preguntas_df.to_excel(writer, sheet_name='preguntas', index=False)
        return str(output_file)
    
    else:  # JSON
        output_file = Path(f"data/backups/backup_completo_{timestamp}.json")
        data = {
            "fecha_backup": timestamp,
            "usuarios": usuarios_df.to_dict(orient='records'),
            "preguntas": preguntas_df.to_dict(orient='records')
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return str(output_file)

def importar_backup(archivo_subido):
    """Importa datos desde un archivo de backup"""
    if archivo_subido is None:
        return False, "No se seleccionó ningún archivo"
    
    try:
        conn = sqlite3.connect("data/banco_preguntas.db")
        cursor = conn.cursor()
        
        # Determinar tipo de archivo
        if archivo_subido.name.endswith('.xlsx'):
            # Leer Excel
            usuarios_df = pd.read_excel(archivo_subido, sheet_name='usuarios')
            preguntas_df = pd.read_excel(archivo_subido, sheet_name='preguntas')
        elif archivo_subido.name.endswith('.json'):
            # Leer JSON
            data = json.load(archivo_subido)
            usuarios_df = pd.DataFrame(data['usuarios'])
            preguntas_df = pd.DataFrame(data['preguntas'])
        else:
            return False, "Formato no soportado. Use .xlsx o .json"
        
        # Preguntar si quiere limpiar datos existentes o fusionar
        limpiar = st.checkbox("⚠️ Eliminar datos existentes antes de importar (recomendado para restauración completa)")
        
        if limpiar:
            cursor.execute("DELETE FROM preguntas")
            cursor.execute("DELETE FROM usuarios")
            conn.commit()
        
        # Insertar usuarios (ignorando duplicados si no se limpió)
        for _, row in usuarios_df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO usuarios 
                    (id, usuario, clave, rol, nombre_completo, documento)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (row.get('id'), row.get('usuario'), row.get('clave'), 
                      row.get('rol'), row.get('nombre_completo'), row.get('documento')))
            except Exception as e:
                st.warning(f"No se pudo insertar usuario {row.get('usuario')}: {e}")
        
        # Insertar preguntas
        for _, row in preguntas_df.iterrows():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO preguntas 
                    (id, grado, materia, numero, enunciado, texto_base, imagen,
                     opciones_json, opciones_imagenes_json, profesor_usuario, 
                     profesor_nombre, lote_id, fecha)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (row.get('id'), row.get('grado'), row.get('materia'), 
                      row.get('numero'), row.get('enunciado'), row.get('texto_base'),
                      row.get('imagen'), row.get('opciones_json'), row.get('opciones_imagenes_json'),
                      row.get('profesor_usuario'), row.get('profesor_nombre'),
                      row.get('lote_id'), row.get('fecha')))
            except Exception as e:
                st.warning(f"No se pudo insertar pregunta {row.get('id')}: {e}")
        
        conn.commit()
        conn.close()
        
        return True, f"Backup importado exitosamente. {len(usuarios_df)} usuarios, {len(preguntas_df)} preguntas."
    
    except Exception as e:
        return False, f"Error al importar: {str(e)}"

def exportar_preguntas_filtradas(preguntas, formato="excel"):
    """Exporta preguntas filtradas a Excel o CSV"""
    if not preguntas:
        return None
    
    df = pd.DataFrame(preguntas)
    
    # Seleccionar columnas relevantes
    columnas = ['id', 'grado', 'materia', 'numero', 'enunciado', 
                'texto_base', 'profesor_nombre', 'fecha']
    df_export = df[[c for c in columnas if c in df.columns]]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if formato == "excel":
        output_file = Path(f"data/backups/preguntas_filtradas_{timestamp}.xlsx")
        df_export.to_excel(output_file, index=False)
    else:  # CSV
        output_file = Path(f"data/backups/preguntas_filtradas_{timestamp}.csv")
        df_export.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    return str(output_file)