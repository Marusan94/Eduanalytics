import streamlit as st
import pandas as pd
import plotly.express as px
import os

def _get_df():
    df = st.session_state.get("analytics_df_canonical")
    if df is not None and not df.empty:
        return df
    # fallback a datos_educativos.csv
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datos_educativos.csv")
    if not os.path.exists(csv_path):
        csv_path = "datos_educativos.csv"
    if os.path.exists(csv_path):
        try:
            from modules.mapper import to_canonical, IDENTITY_MAPPING
            df_raw = pd.read_csv(csv_path, encoding="utf-8-sig")
            return to_canonical(df_raw, IDENTITY_MAPPING)
        except Exception:
            try:
                return pd.read_csv(csv_path)
            except Exception:
                return pd.DataFrame()
    return pd.DataFrame()

def render():
    st.title("🔬 Laboratorio — Explorar")
    st.caption("Explora relaciones entre variables del modelo canónico. Guarda descubrimientos para la Biblioteca.")

    df = _get_df()
    if df.empty:
        st.warning("No hay datos canónicos. Sube un CSV en Analytics primero.")
        return

    # Solo columnas canónicas compatibles
    num_cols = [c for c in ["nota", "asistencia"] if c in df.columns]
    cat_cols = [c for c in ["grupo_id", "materia", "tipo_apoyo", "tipo_usuario"] if c in df.columns]
    all_cols = list(df.columns)

    st.markdown("### Configurar exploración")
    col1, col2 = st.columns(2)
    with col1:
        x = st.selectbox("Variable X", all_cols, index=all_cols.index("asistencia") if "asistencia" in all_cols else 0, key="lab_x")
    with col2:
        y = st.selectbox("Variable Y", all_cols, index=all_cols.index("nota") if "nota" in all_cols else 0, key="lab_y")

    if x not in df.columns or y not in df.columns:
        st.error("Variables no válidas")
        return

    # Visualización según tipos
    is_x_num = pd.api.types.is_numeric_dtype(df[x])
    is_y_num = pd.api.types.is_numeric_dtype(df[y])

    if is_x_num and is_y_num:
        fig = px.scatter(df, x=x, y=y, color="materia" if "materia" in df.columns else None, hover_data=["grupo_id"] if "grupo_id" in df.columns else None, title=f"{y} vs {x}")
        st.plotly_chart(fig, use_container_width=True, key="lab_scatter")
        # correlación si ambas numéricas
        try:
            corr = df[[x, y]].corr().iloc[0, 1]
            st.metric("Correlación", f"{corr:.2f}")
        except Exception:
            pass
    elif not is_x_num and is_y_num:
        fig = px.box(df, x=x, y=y, title=f"Distribución de {y} por {x}")
        st.plotly_chart(fig, use_container_width=True, key="lab_box")
    elif is_x_num and not is_y_num:
        fig = px.box(df, x=y, y=x, title=f"Distribución de {x} por {y}")
        st.plotly_chart(fig, use_container_width=True, key="lab_box2")
    else:
        # ambas categóricas → conteo
        ct = df.groupby([x, y]).size().reset_index(name="count")
        fig = px.bar(ct, x=x, y="count", color=y, barmode="group", title=f"Conteo {x} vs {y}")
        st.plotly_chart(fig, use_container_width=True, key="lab_bar")

    st.markdown("### Estadísticas")
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(df[[x, y]].describe(include="all"), use_container_width=True)
    with col2:
        if "grupo_id" in df.columns:
            st.markdown("**Por grupo**")
            st.dataframe(df.groupby("grupo_id")[[c for c in [x, y] if pd.api.types.is_numeric_dtype(df[c])]].mean().round(2), use_container_width=True)

    st.markdown("### Interpretación asistida")
    if st.button("💡 Generar interpretación", key="lab_interpret"):
        df_ctx = st.session_state.get("analytics_df_canonical")
        has_key = False
        try:
            from modules.common import get_client
            c = get_client()
            has_key = c is not None
        except Exception:
            has_key = False
        if not has_key:
            st.warning("Sin API key, interpretación básica:")
            try:
                corr = df[[x, y]].corr().iloc[0, 1] if is_x_num and is_y_num else None
                if corr is not None:
                    if abs(corr) > 0.5:
                        st.info(f"Correlación {corr:.2f} sugiere relación moderada/fuerte entre {x} e {y}. Investiga causalidad por grupo/materia.")
                    else:
                        st.info(f"Correlación {corr:.2f} débil. Explora por grupo/materia para patrones ocultos.")
                else:
                    st.info(f"Distribución de {y} varía por {x}. Revisa tabla por grupo.")
            except Exception as e:
                st.error(str(e))
        else:
            try:
                from modules.common import get_client
                client = get_client()
                # enviar solo stats, no df completo
                stats = df[[x, y]].describe().to_dict()
                prompt = f"Interpreta la relación entre {x} (X) e {y} (Y) en datos educativos. Stats: {stats}. Da 3 bullets y 1 hipótesis investigable, en español, 80 palabras."
                resp = client.chat.completions.create(model="openai/gpt-4o-mini", messages=[{"role":"system","content":"Eres analista educativo, interpretas exploraciones."},{"role":"user","content": prompt}], temperature=0.3, max_tokens=300)
                txt = resp.choices[0].message.content
                st.markdown(txt)
                st.session_state["lab_last_interpretation"] = txt
            except Exception as e:
                st.error(f"Error IA: {e}")

    st.divider()
    st.markdown("### Guardar descubrimiento")
    with st.form("save_discovery_form"):
        title = st.text_input("Título", placeholder="Relación asistencia-nota en Ciencias")
        finding = st.text_area("Hallazgo", value=st.session_state.get("lab_last_interpretation",""), placeholder="Grupos con asistencia <80% tienen nota promedio 0.5 menor...")
        variables = st.text_input("Variables", value=f"{x}, {y}")
        submitted = st.form_submit_button("📌 Guardar descubrimiento")
        if submitted:
            if not title or not finding:
                st.warning("Título y hallazgo requeridos")
            else:
                try:
                    from modules.discoveries import save_discovery
                    did = save_discovery(title=title, finding=finding, variables=[v.strip() for v in variables.split(",")], source_csv="datos_educativos.csv", context={"x": x, "y": y})
                    st.success(f"Descubrimiento guardado: {did}")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
