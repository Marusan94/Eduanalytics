import streamlit as st
from modules.knowledge.vector_store import search, list_library

def render():
    st.title("📚 Biblioteca de Conocimiento")
    st.caption("Explora descubrimientos, informes y recursos. RAG busca semánticamente cuando hay embeddings.")

    col1, col2 = st.columns([3,1])
    with col1:
        query = st.text_input("Buscar", placeholder="asistencia, rendimiento, ciencias...", key="lib_query")
    with col2:
        cat = st.selectbox("Categoría", ["Todos","STEAM","Ciencias","Educación","Analítica","Descubrimientos","Otros"], key="lib_cat")

    # Mostrar lista o búsqueda
    if query:
        results = search(query, k=5)
        st.markdown(f"### Resultados para '{query}' ({len(results)})")
        if not results:
            st.info("Sin resultados. Prueba con otras palabras.")
        for doc in results:
            with st.expander(f"{doc.get('title','Sin título')} — {doc.get('date','')[:10]} · score {doc.get('score',0):.2f}"):
                st.markdown(f"**Fragmento:** {doc.get('fragment','')}")
                st.markdown(f"**Finding:** {doc.get('finding','')}")
                st.caption(f"Variables: {doc.get('variables',[])} | Fuente: {doc.get('source_csv','')}")
                st.json(doc)
    else:
        docs = list_library(category=cat)
        st.markdown(f"### Documentos ({len(docs)}) — filtro: {cat}")
        if not docs:
            st.info("Biblioteca vacía. Guarda descubrimientos en Laboratorio → Explorar.")
        for doc in docs[-20:][::-1]:  # últimos 20
            with st.expander(f"{doc.get('title','Sin título')} — {doc.get('date','')[:10]}"):
                st.markdown(doc.get('finding',''))
                st.caption(f"Variables: {doc.get('variables',[])} | {doc.get('category','')}")
                st.json(doc)
