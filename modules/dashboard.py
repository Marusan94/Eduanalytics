import streamlit as st

def render():
    modo = st.selectbox(
        "Modo",
        ["Geográfico", "Académico"],
        index=0,
        key="dash_modo"
    )
    if modo == "Geográfico":
        from modules import dashboard_geo as geo
        geo.render()
    else:
        from modules import dashboard_academic as acad
        acad.render()
