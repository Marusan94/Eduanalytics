"""
Asistente de Investigación - EduAnalytics HUB
Humanizer + CAJAL Article Generator + Quick Tools
OpenRouter first, local fallback
"""

import streamlit as st
from modules.common import get_client
from modules.humanizer import humanize_text
from modules.cajal import generate_cajal_article

def render():
    st.title("🧑‍🔬 Asistente de Investigación")
    st.caption("OpenRouter first • Local fallback • Sin ejecución de código • Citas reales arXiv")
    
    # Verificar API key
    client = get_client()
    if not client:
        st.warning("⚠️ Configura OPENROUTER_API_KEY en .streamlit/secrets.toml para usar las herramientas IA")
        st.info("Las herramientas funcionarán en modo local limitado (sin citas reales arXiv)")
    
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["🎯 Humanizer", "📄 Generador CAJAL", "⚡ Herramientas Rápidas"])
    
    with tab1:
        render_humanizer()
    
    with tab2:
        render_cajal_generator()
    
    with tab3:
        render_quick_tools()


def render_humanizer():
    st.subheader("🎯 Humanizer - Texto IA → Texto Humano")
    st.caption("OpenRouter primero • Fallback local • Descarga Word")
    
    # Input
    text_input = st.text_area(
        "Texto a humanizar",
        placeholder="Pega aquí el texto generado por IA...",
        height=200,
        key="humanizer_input"
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        tone = st.selectbox(
            "Tono",
            ["Académico", "Cercano", "Formal", "Divulgativo", "Técnico"],
            index=0,
            key="humanizer_tone"
        )
    with col2:
        intensity = st.slider(
            "Intensidad",
            1, 5, 3,
            help="1 = cambios sutiles, 5 = reescritura profunda",
            key="humanizer_intensity"
        )
    with col3:
        language = st.selectbox(
            "Idioma",
            ["Español", "Inglés", "Portugués"],
            index=0,
            key="humanizer_lang"
        )
    
    if st.button("🎯 Humanizar", type="primary", use_container_width=True, key="humanizer_btn"):
        if not st.session_state.get("humanizer_input", "").strip():
            st.warning("Ingresa un texto para humanizar")
            return
        
        with st.spinner("Humanizando con OpenRouter..."):
            try:
                result = humanize_text(
                    text=st.session_state.humanizer_input,
                    tone=tone,
                    intensity=st.session_state.humanizer_intensity,
                    language=st.session_state.humanizer_lang
                )
                st.session_state.humanizer_result = result
                st.success("✅ Texto humanizado")
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.humanizer_result = None
    
    # Mostrar resultado
    if "humanizer_result" in st.session_state and st.session_state.humanizer_result:
        st.divider()
        st.subheader("Resultado")
        st.markdown(st.session_state.humanizer_result)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Descargar Word",
                data=create_word_doc(st.session_state.humanizer_result),
                file_name="texto_humanizado.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        with col2:
            if st.button("🔄 Rehumanizar", use_container_width=True):
                st.rerun()


def render_cajal_generator():
    st.subheader("📄 Generador de Artículos CAJAL")
    st.caption("OpenRouter • IMRaD + Citas arXiv reales • Puntuación tribunal • Word")
    
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input(
            "Tema del artículo",
            placeholder="Ej: Impacto de la IA en la educación superior",
            key="cajal_topic"
        )
        level = st.selectbox(
            "Nivel",
            ["Pregrado", "Maestría", "Doctorado", "Publicación"],
            index=1,
            key="cajal_level"
        )
    with col2:
        format_style = st.selectbox(
            "Formato",
            ["CAJAL (IMRaD + Puntuación Tribunal)", "APA 7ma", "IEEE", "Vancouver"],
            index=0,
            key="cajal_format"
        )
        length = st.selectbox(
            "Extensión",
            ["800-1200 palabras", "1500-2500 palabras", "3000+ palabras"],
            index=0,
            key="cajal_length"
        )
    
    # Opciones avanzadas
    with st.expander("⚙️ Opciones avanzadas"):
        col1, col2 = st.columns(2)
        with col1:
            include_citations = st.checkbox("Citas reales arXiv", value=True, key="cajal_citations")
            include_methodology = st.checkbox("Metodología detallada", value=True)
        with col2:
            include_stats = st.checkbox("Análisis estadístico simulado", value=False)
            peer_review_score = st.checkbox("Puntuación tribunal simulada", value=True)
    
    if st.button("📄 Generar Artículo CAJAL", type="primary", use_container_width=True, key="cajal_btn"):
        if not st.session_state.get("cajal_topic", "").strip():
            st.warning("Ingresa un tema para el artículo")
            return
        
        with st.spinner("Generando artículo CAJAL con citas arXiv..."):
            try:
                result = generate_cajal_article(
                    topic=st.session_state.cajal_topic,
                    level=st.session_state.cajal_level,
                    format_style=st.session_state.cajal_format,
                    length=st.session_state.cajal_length,
                    include_citations=st.session_state.cajal_citations,
                    include_methodology=st.session_state.cajal_methodology,
                    include_stats=st.session_state.cajal_stats,
                    peer_review=st.session_state.cajal_peer_review
                )
                st.session_state.cajal_result = result
                st.success("✅ Artículo CAJAL generado")
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.cajal_result = None
    
    if "cajal_result" in st.session_state and st.session_state.cajal_result:
        st.divider()
        st.subheader("📄 Artículo Generado")
        st.markdown(st.session_state.cajal_result)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Descargar Word",
                data=create_word_doc(st.session_state.cajal_result),
                file_name="articulo_cajal.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        with col2:
            if st.button("🔄 Regenerar", use_container_width=True):
                st.session_state.cajal_result = None
                st.rerun()


def render_quick_tools():
    st.subheader("⚡ Herramientas Rápidas")
    st.caption("Una acción • Un resultado • Descarga inmediata")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📝 Resumir")
        text_to_summarize = st.text_area("Texto a resumir", height=120, key="summarize_input")
        length = st.selectbox("Longitud", ["Muy breve (50 palabras)", "Breve (100 palabras)", "Medio (200 palabras)", "Detallado (400+)"], key="summarize_len")
        if st.button("📝 Resumir", use_container_width=True, key="summarize_btn"):
            if st.session_state.get("summarize_input", "").strip():
                with st.spinner("Resumiendo..."):
                    try:
                        from modules.humanizer import summarize_text
                        result = summarize_text(
                            st.session_state.summarize_input,
                            st.session_state.summarize_len
                        )
                        st.session_state.summarize_result = result
                        st.success("✅ Resumen generado")
                    except Exception as e:
                        st.error(f"Error: {e}")
            if "summarize_result" in st.session_state and st.session_state.summarize_result:
                st.markdown(st.session_state.summarize_result)
                st.download_button("📥 Word", data=create_word_doc(st.session_state.summarize_result), 
                                 file_name="resumen.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    
    with col2:
        st.markdown("#### 🔄 Parafrasear")
        text_to_paraphrase = st.text_area("Texto a parafrasear", height=120, key="paraphrase_input")
        style = st.selectbox("Estilo", ["Académico", "Simple", "Formal", "Creativo"], key="paraphrase_style")
        if st.button("🔄 Parafrasear", use_container_width=True, key="paraphrase_btn"):
            if st.session_state.get("paraphrase_input", "").strip():
                with st.spinner("Parafraseando..."):
                    try:
                        from modules.humanizer import paraphrase_text
                        result = paraphrase_text(st.session_state.paraphrase_input, st.session_state.paraphrase_style)
                        st.session_state.paraphrase_result = result
                        st.success("✅ Parafraseado")
                    except Exception as e:
                        st.error(f"Error: {e}")
            if "paraphrase_result" in st.session_state and st.session_state.paraphrase_result:
                st.markdown(st.session_state.paraphrase_result)
                st.download_button("📥 Word", data=create_word_doc(st.session_state.paraphrase_result),
                                 file_name="parafraseo.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    
    with col3:
        st.markdown("#### ✍️ Corregir Estilo")
        text_to_correct = st.text_area("Texto a corregir", height=120, key="correct_input")
        target = st.selectbox("Objetivo", ["Corregir gramática", "Mejorar fluidez", "Formalizar", "Simplificar"], key="correct_target")
        if st.button("✍️ Corregir", use_container_width=True, key="correct_btn"):
            if st.session_state.get("correct_input", "").strip():
                with st.spinner("Corrigiendo..."):
                    try:
                        from modules.humanizer import correct_style
                        result = correct_style(st.session_state.correct_input, st.session_state.correct_target)
                        st.session_state.correct_result = result
                        st.success("✅ Corregido")
                    except Exception as e:
                        st.error(f"Error: {e}")
            if "correct_result" in st.session_state and st.session_state.correct_result:
                st.markdown(st.session_state.correct_result)
                st.download_button("📥 Word", data=create_word_doc(st.session_state.correct_result),
                                 file_name="corregido.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)


def create_word_doc(content: str):
    """Crear documento Word con el contenido"""
    from docx import Document
    from io import BytesIO
    
    doc = Document()
    doc.add_heading("Documento Generado", level=0)
    
    for line in content.split("\n"):
        if line.startswith("# "):
            doc.add_heading(line[2:], level=1)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=2)
        elif line.startswith("### "):
            doc.add_heading(line[4:], level=3)
        else:
            doc.add_paragraph(line)
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer