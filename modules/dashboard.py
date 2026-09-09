import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium

def render():
    st.warning(
        "⚠️ **Datos de demostración.** Los valores de este panel (índice de "
        "vulnerabilidad, población afectada, pendiente) son simulados con "
        "fines de prototipo técnico y **no** representan evaluaciones "
        "oficiales de riesgo geológico. Revisa las fuentes oficiales al "
        "final de la página antes de usar esta información para cualquier "
        "decisión real."
    )

    data = {
        "Barrio": ["La América", "Robledo", "Belén", "Comuna 13 (San Javier)", "Manrique", "Popular"],
        "Indice_Vulnerabilidad": [0.3, 0.7, 0.5, 0.8, 0.75, 0.6],
        "Poblacion_Afectada": [1200, 4500, 3000, 5000, 4800, 3500],
        "Pendiente_Laderas": [15, 40, 25, 45, 38, 35],
        "lat": [6.2600, 6.2760, 6.2320, 6.2460, 6.2830, 6.2960],
        "lon": [-75.5950, -75.5920, -75.6050, -75.6130, -75.5540, -75.5550],
    }
    df = pd.DataFrame(data)

    def categoria_vulnerabilidad(valor: float) -> str:
        if valor < 0.5:
            return "Bajo"
        elif valor < 0.8:
            return "Medio"
        return "Alto"

    df["Categoria_Vulnerabilidad"] = df["Indice_Vulnerabilidad"].apply(categoria_vulnerabilidad)
    COLOR_CATEGORIA = {"Bajo": "#2ecc71", "Medio": "#f39c12", "Alto": "#e74c3c"}

    # Filtro en main area (no sidebar para no colisionar con hub nav)
    st.markdown("#### Filtro de Vulnerabilidad")
    categoria_seleccionada = st.selectbox(
        "Selecciona categoría de vulnerabilidad:",
        options=["Todas"] + sorted(df["Categoria_Vulnerabilidad"].unique().tolist()),
        key="dashboard_filtro_categoria"
    )

    if categoria_seleccionada == "Todas":
        df_filtrado = df.copy()
    else:
        df_filtrado = df[df["Categoria_Vulnerabilidad"] == categoria_seleccionada]

    if df_filtrado.empty:
        st.info("No hay barrios en esta categoría con los datos actuales.")
        return

    st.title("Vulnerabilidad de Barrios Medellín – Riesgo Geológico (prototipo)")
    st.markdown("### Análisis múltiple de variables clave")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Promedio Vulnerabilidad", f"{df_filtrado['Indice_Vulnerabilidad'].mean():.2f}")
    col2.metric("Población en Riesgo Total", f"{df_filtrado['Poblacion_Afectada'].sum():,}")
    col3.metric("Pendiente Promedio (°)", f"{df_filtrado['Pendiente_Laderas'].mean():.1f}")
    col4.metric("Barrio Más Vulnerable", df_filtrado.loc[df_filtrado["Indice_Vulnerabilidad"].idxmax(), "Barrio"])

    df_orden_vuln = df_filtrado.sort_values("Indice_Vulnerabilidad", ascending=False)
    fig1 = px.bar(
        df_orden_vuln,
        x="Barrio",
        y="Indice_Vulnerabilidad",
        color="Categoria_Vulnerabilidad",
        color_discrete_map=COLOR_CATEGORIA,
        template="plotly_dark",
        title="Índice de Vulnerabilidad por Barrio",
    )
    fig1.update_layout(yaxis_title="Índice de Vulnerabilidad (0–1)", yaxis_range=[0, 1])
    st.plotly_chart(fig1, use_container_width=True, key="dash_fig1")

    fig2 = px.bar(
        df_filtrado,
        x="Barrio",
        y="Poblacion_Afectada",
        color="Poblacion_Afectada",
        color_continuous_scale="Blues",
        title="Población Afectada por Barrio",
    )
    fig2.update_layout(yaxis_title="Población Afectada")
    st.plotly_chart(fig2, use_container_width=True, key="dash_fig2")

    fig3 = px.scatter(
        df_filtrado,
        x="Pendiente_Laderas",
        y="Poblacion_Afectada",
        size="Poblacion_Afectada",
        color="Indice_Vulnerabilidad",
        color_continuous_scale="Reds",
        title="Relación Pendiente y Población Afectada",
        labels={"Pendiente_Laderas": "Pendiente (°)", "Poblacion_Afectada": "Población Afectada"},
    )
    st.plotly_chart(fig3, use_container_width=True, key="dash_fig3")

    fig4 = make_subplots(specs=[[{"secondary_y": True}]])
    fig4.add_trace(
        go.Bar(
            x=df_filtrado["Barrio"],
            y=df_filtrado["Poblacion_Afectada"],
            name="Población Afectada",
            marker=dict(color=df_filtrado["Poblacion_Afectada"], colorscale="Blues", showscale=False),
            opacity=0.6,
        ),
        secondary_y=False,
    )
    fig4.add_trace(
        go.Scatter(
            x=df_filtrado["Barrio"],
            y=df_filtrado["Indice_Vulnerabilidad"],
            name="Índice de Vulnerabilidad",
            mode="lines+markers",
            line=dict(color="red", width=3),
        ),
        secondary_y=True,
    )
    fig4.update_yaxes(title_text="Población Afectada", secondary_y=False)
    fig4.update_yaxes(title_text="Índice de Vulnerabilidad (0–1)", range=[0, 1], secondary_y=True)
    fig4.update_layout(title_text="Población y Vulnerabilidad por Barrio")
    st.plotly_chart(fig4, use_container_width=True, key="dash_fig4")

    df_orden_pop = df_filtrado.sort_values("Poblacion_Afectada", ascending=True)
    fig5 = px.bar(
        df_orden_pop,
        x="Poblacion_Afectada",
        y="Barrio",
        orientation="h",
        template="plotly_dark",
        color="Poblacion_Afectada",
        color_continuous_scale="Blues",
        title="Distribución de Población Afectada por Barrio",
    )
    fig5.update_layout(xaxis_title="Población Afectada")
    st.plotly_chart(fig5, use_container_width=True, key="dash_fig5")

    st.markdown("### 🗺️ Mapa de referencia")
    st.caption(
        "Las coordenadas usadas aquí son aproximadas y solo sirven para ubicar "
        "visualmente los barrios en este prototipo — no son límites oficiales. "
        "Para un mapa con polígonos reales de comunas/barrios, descarga el "
        "GeoJSON oficial desde GeoMedellín: "
        "https://geomedellin-m-medellin.opendata.arcgis.com/ "
        "(buscar 'Comunas' o 'Barrio Vereda') y cárgalo con geopandas."
    )

    mapa = folium.Map(location=[6.2530, -75.5900], zoom_start=12, tiles="CartoDB positron")
    for _, row in df_filtrado.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8 + row["Indice_Vulnerabilidad"] * 12,
            popup=folium.Popup(
                f"<b>{row['Barrio']}</b><br>"
                f"Índice de vulnerabilidad: {row['Indice_Vulnerabilidad']:.2f}<br>"
                f"Población afectada (simulada): {row['Poblacion_Afectada']:,}<br>"
                f"Pendiente promedio: {row['Pendiente_Laderas']}°",
                max_width=250,
            ),
            color=COLOR_CATEGORIA.get(row["Categoria_Vulnerabilidad"], "gray"),
            fill=True,
            fill_color=COLOR_CATEGORIA.get(row["Categoria_Vulnerabilidad"], "gray"),
            fill_opacity=0.7,
        ).add_to(mapa)
    st_folium(mapa, use_container_width=True, height=450, key="dash_map")

    st.markdown("### Datos Filtrados de Barrios")
    st.dataframe(df_filtrado.drop(columns=["lat", "lon"]), use_container_width=True)

    with st.expander("📚 Fuentes oficiales para reemplazar los datos simulados"):
        st.markdown("""
        - **DAGRD Medellín** — Mapas de amenaza por movimiento en masa: https://www.medellin.gov.co/es/dagrd/
        - **GeoMedellín** — Límites oficiales de comunas/barrios y cartografía base: https://geomedellin-m-medellin.opendata.arcgis.com/
        - **SIATA** — Datos de precipitación y sensores que alimentan alertas tempranas: https://siata.gov.co/
        - **DANE** — Censo y proyecciones de población por comuna.
        """)
