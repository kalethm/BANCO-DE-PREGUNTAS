# equation_editor.py
import streamlit as st
import re
from pathlib import Path

def render_latex(text):
    """Renderiza texto que puede contener ecuaciones LaTeX"""
    if not text:
        return text
    
    # Patrón para detectar ecuaciones: $...$ o $$...$$
    pattern = r'\$\$(.*?)\$\$|\$(.*?)\$'
    
    def replace_math(match):
        if match.group(1):  # $$...$$
            return f"<div style='text-align: center;'>{match.group(1)}</div>"
        elif match.group(2):  # $...$
            return f"<span style='font-family: monospace;'>{match.group(2)}</span>"
        return match.group(0)
    
    return re.sub(pattern, replace_math, text, flags=re.DOTALL)

def equation_editor(key, value="", height=100):
    """Editor de ecuaciones con vista previa LaTeX"""
    col1, col2 = st.columns([2, 1])
    
    with col1:
        text = st.text_area(
            "Contenido (usa $...$ para ecuaciones inline o $$...$$ para ecuaciones centradas)",
            value=value,
            key=f"eq_input_{key}",
            height=height
        )
    
    with col2:
        st.markdown("**Vista previa:**")
        if text:
            # Aquí se mostraría la vista previa renderizada
            # En Streamlit necesitas usar st.latex o componentes externos
            # Por simplicidad, mostramos sugerencias
            st.info("💡 Ejemplos:\n- $E = mc^2$\n- $$\\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}$$\n- $\\vec{F} = m\\vec{a}$")
            
            # Extraer ecuaciones para vista previa
            equations = re.findall(r'\$\$(.*?)\$\$|\$(.*?)\$', text, re.DOTALL)
            if equations:
                st.markdown("**Ecuaciones detectadas:**")
                for eq in equations[:2]:
                    eq_text = eq[0] if eq[0] else eq[1]
                    if eq_text:
                        try:
                            st.latex(eq_text)
                        except:
                            pass
    
    return text

def preview_equation(text):
    """Muestra vista previa de una ecuación"""
    if text and text.strip():
        st.latex(text)