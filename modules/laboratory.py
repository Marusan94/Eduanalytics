import streamlit as st

def render():
    st.sidebar.caption("🔬 Laboratorio")
    tab = st.tabs(["🧪 Explorar", "💡 Descubrimientos", "📚 Biblioteca"])
    with tab[0]:
        try:
            from modules import lab_explorer
            lab_explorer.render()
        except Exception as e:
            st.error(f"Error en Explorar: {e}")
    with tab[1]:
        st.title("💡 Descubrimientos")
        try:
            from modules.discoveries import load_discoveries
            docs = load_discoveries()
            st.caption(f"{len(docs)} descubrimientos guardados")
            if not docs:
                st.info("Aún no hay descubrimientos. Ve a Explorar y guarda uno.")
            for d in docs[::-1][:20]:
                with st.expander(f"{d.get('title')} — {d.get('date','')[:10]}"):
                    st.markdown(d.get('finding',''))
                    st.caption(f"Variables: {d.get('variables',[])} | Fuente: {d.get('source_csv','')}")
                    st.json(d)
        except Exception as e:
            st.error(str(e))
    with tab[2]:
        try:
            from modules import library
            library.render()
        except Exception as e:
            st.error(f"Error en Biblioteca: {e}")
