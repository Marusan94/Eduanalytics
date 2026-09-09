import streamlit as st
import pandas as pd
import plotly.express as px
import os
from modules.mapper import to_canonical, IDENTITY_MAPPING

# Cache para no reconstruir el DataFrame en cada cambio de modo
@st.cache_data(ttl=3600, show_spinner=False)
def _get_academic_df():
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos_educativos.csv")
    if not os.path.exists(csv_path):
        csv_path = "datos_educativos.csv"
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    try:
        df_raw = pd.read_csv(csv_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df_raw = pd.read_csv(csv_path, encoding="latin-1")
    except Exception:
        return pd.DataFrame()
    try:
        return to_canonical(df_raw, IDENTITY_MAPPING)
    except Exception:
        # Fallback RAW si validación falla (compatibilidad)
        return df_raw

def _row_risk(nota: float, asistencia: float) -> float:
    """Riesgo determinista y transparente: nota + asistencia -> 0.0 a 1.0."""
    risk = 0.0
    try:
        n = float(nota)
        a = float(asistencia)
    except Exception:
        return 0.0
    if n < 3.0:
        risk += 0.5
    elif n < 3.5:
        risk += 0.3
    elif n < 4.0:
        risk += 0.1
    if a < 70:
        risk += 0.5
    elif a < 80:
        risk += 0.3
    elif a < 90:
        risk += 0.1
    return round(min(risk, 1.0), 2)

def _add_risk(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or not all(c in df.columns for c in ["nota", "asistencia"]):
        return df
    out = df.copy()
    out["riesgo"] = out.apply(lambda r: _row_risk(r["nota"], r["asistencia"]), axis=1)
    def categoria(r):
        if r < 0.3:
            return "Bajo"
        elif r < 0.7:
            return "Medio"
        return "Alto"
    out["Categoria_Riesgo"] = out["riesgo"].apply(categoria)
    return out

def render():
    st.warning(
        "⚠️ **Prototipo académico.** El riesgo se calcula con una regla determinista "
        "(nota + asistencia) sobre `datos_educativos.csv` y **no** es un modelo predictivo validado. "
        "Úsalo solo para priorizar tutorías, no como diagnóstico."
    )

    df = _get_academic_df()
    if df.empty:
        st.error("No se pudo cargar `datos_educativos.csv`. Verifica que el archivo esté en la raíz del proyecto.")
        return

    if not all(c in df.columns for c in ["grupo_id", "materia", "nota", "asistencia"]):
        st.error("El CSV no contiene las columnas requeridas: grupo_id, materia, nota, asistencia.")
        st.dataframe(df.head(), use_container_width=True)
        return

    df = _add_risk(df)

    COLOR_RIESGO = {"Bajo": "#2ecc71", "Medio": "#f39c12", "Alto": "#e74c3c"}

    st.title("Rendimiento Académico – Riesgo de Deserción (prototipo)")
    st.markdown("### Métricas generales")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Promedio Nota", f"{df['nota'].mean():.2f}")
    col2.metric("Asistencia Promedio (%)", f"{df['asistencia'].mean():.1f}")
    col3.metric("Estudiantes", f"{len(df)}")
    col4.metric("Riesgo Promedio", f"{df['riesgo'].mean():.2f}")

    # Filtros en main area (no sidebar)
    st.markdown("#### Filtros")
    colf1, colf2 = st.columns(2)
    with colf1:
        materias = ["Todas"] + sorted(df["materia"].dropna().unique().tolist())
        materia_sel = st.selectbox("Materia:", materias, key="dash_acad_materia")
    with colf2:
        grupos = ["Todos"] + sorted(df["grupo_id"].dropna().unique().tolist(), key=lambda x: str(x))
        grupo_sel = st.selectbox("Grupo:", grupos, key="dash_acad_grupo")

    df_filtrado = df.copy()
    if materia_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["materia"] == materia_sel]
    if grupo_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["grupo_id"] == grupo_sel]

    if df_filtrado.empty:
        st.info("No hay registros para los filtros seleccionados.")
        return

    # Métricas filtradas
    st.caption(f"Registros filtrados: {len(df_filtrado)} / {len(df)}")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Nota (filtrado)", f"{df_filtrado['nota'].mean():.2f}")
    col2.metric("Asistencia (filtrado)", f"{df_filtrado['asistencia'].mean():.1f}")
    col3.metric("Riesgo (filtrado)", f"{df_filtrado['riesgo'].mean():.2f}")
    alto = (df_filtrado["Categoria_Riesgo"] == "Alto").sum()
    col4.metric("Riesgo Alto", f"{alto}")

    # Análisis por grupo
    riesgo_grupo = df_filtrado.groupby("grupo_id")["riesgo"].mean().reset_index()
    riesgo_grupo = riesgo_grupo.sort_values("riesgo", ascending=False)
    fig1 = px.bar(
        riesgo_grupo,
        x="grupo_id",
        y="riesgo",
        color="riesgo",
        color_continuous_scale="Reds",
        template="plotly_dark",
        title="Riesgo Promedio por Grupo",
    )
    fig1.update_layout(yaxis_title="Riesgo (0–1)", yaxis_range=[0, 1], xaxis_title="Grupo")
    st.plotly_chart(fig1, use_container_width=True, key="acad_fig_grupo")

    # Análisis por materia
    riesgo_materia = df_filtrado.groupby("materia")["riesgo"].mean().reset_index()
    riesgo_materia = riesgo_materia.sort_values("riesgo", ascending=False)
    fig2 = px.bar(
        riesgo_materia,
        x="materia",
        y="riesgo",
        color="riesgo",
        color_continuous_scale="Reds",
        title="Riesgo Promedio por Materia",
    )
    fig2.update_layout(yaxis_title="Riesgo (0–1)", yaxis_range=[0, 1])
    st.plotly_chart(fig2, use_container_width=True, key="acad_fig_materia")

    # Riesgo alto por grupo/materia (tabla)
    riesgo_detalle = df_filtrado.groupby(["grupo_id", "materia"])["riesgo"].mean().reset_index()
    riesgo_detalle = riesgo_detalle.sort_values("riesgo", ascending=False)
    st.markdown("### Grupos/Materias con mayor riesgo")
    st.dataframe(riesgo_detalle.head(15), use_container_width=True)

    # Scatter nota vs asistencia coloreado por riesgo
    fig3 = px.scatter(
        df_filtrado,
        x="asistencia",
        y="nota",
        color="riesgo",
        color_continuous_scale="Reds",
        size="riesgo",
        hover_data=["grupo_id", "materia"],
        title="Relación Nota vs Asistencia (color = riesgo)",
        labels={"asistencia": "Asistencia (%)", "nota": "Nota"},
    )
    fig3.update_layout(yaxis_range=[0, 5.5], xaxis_range=[50, 100])
    st.plotly_chart(fig3, use_container_width=True, key="acad_fig_scatter")

    # Tabla datos filtrados
    st.markdown("### Datos filtrados")
    cols_show = [c for c in ["grupo_id", "materia", "nota", "asistencia", "riesgo", "Categoria_Riesgo", "tipo_apoyo"] if c in df_filtrado.columns]
    st.dataframe(df_filtrado[cols_show].sort_values("riesgo", ascending=False).head(50), use_container_width=True)

    with st.expander("ℹ️ Cómo se calcula el riesgo (regla transparente)"):
        st.markdown("""
        **Fórmula determinista (0.0 a 1.0):**
        - Nota: `<3.0 → +0.5`, `<3.5 → +0.3`, `<4.0 → +0.1`
        - Asistencia: `<70% → +0.5`, `<80% → +0.3`, `<90% → +0.1`
        - Suma capada a `1.0`, redondeada a 2 decimales.
        - Categoría: `Bajo <0.3`, `Medio <0.7`, `Alto ≥0.7`
        
        Es una heurística para priorizar, no un modelo ML validado.
        """)
