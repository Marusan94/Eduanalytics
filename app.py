import os
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
import streamlit as st

st.set_page_config(
    page_title="EduAnalytics HUB",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cache de módulos para que cambiar de pestaña no re-importe todo
@st.cache_resource
def _load_analytics():
    from modules import analytics
    return analytics

@st.cache_resource
def _load_dashboard():
    from modules import dashboard
    return dashboard

@st.cache_resource
def _load_chatbot():
    from modules import chatbot
    return chatbot

@st.cache_resource
def _load_laboratory():
    from modules import laboratory
    return laboratory

@st.cache_resource
def _load_research_assistant():
    from modules import research_assistant
    return research_assistant

# Estilo extra para el HUB
st.markdown("""
<style>
.small-muted {color:#8A8A8A; font-size:13px;}
.sidebar-badge {display:inline-block; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:600; margin-right:6px;}
.badge-online {background:#e8f5e9; color:#2e7d32;}
.badge-offline {background:#fdecea; color:#c62828;}
.badge-beta {background:#fff3e0; color:#ef6c00;}
</style>
""", unsafe_allow_html=True)

# Header del sidebar
st.sidebar.title("🎓 EduAnalytics HUB")
st.sidebar.caption("v3.2 • 100 registros • 8 campos canónicos")
st.sidebar.divider()

# Estado del sistema
from modules.common import get_client
client = get_client()
api_status = "🟢 Conectado" if client else "🔴 Sin API Key"
st.sidebar.markdown(f"""
<div style="padding:8px; background:#f5f5f5; border-radius:8px; margin-bottom:8px;">
    <b>Estado del sistema</b><br>
    📊 Datos: 100 registros · 8 campos canónicos<br>
    🔑 API: {api_status}<br>
    📦 Cache: Activo (TTL 1h)
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()

mod = st.sidebar.radio(
    "Navegación",
    ["📊 Analytics Educativo", "⛰️ Dashboard", "🤖 Analista IA", "🔬 Laboratorio", "🧑‍🔬 Asistente de Investigación"],
    index=0,
    key="hub_nav"
)

st.sidebar.divider()

# Info técnica colapsable
with st.sidebar.expander("ℹ️ Info técnica"):
    st.caption("""
    **EduAnalytics HUB v3.2**  
    Python 3.11.9 · Streamlit 1.28+ · Pandas 2.1  
    Modelo: openai/gpt-4o-mini (OpenRouter)  
    Embeddings: LocalHash (fallback) / OpenAI (si hay API)  
    Datos: datos_educativos.csv (100 registros, 8 campos canónicos)
    """)

st.sidebar.divider()
st.sidebar.info("💡 Usa `streamlit run app.py` para localhost:8501")

# Router con cache — cada módulo se importa 1 vez y se reutiliza
if mod == "📊 Analytics Educativo":
    _load_analytics().render()
elif mod == "⛰️ Dashboard":
    _load_dashboard().render()
elif mod == "🤖 Analista IA":
    _load_chatbot().render()
elif mod == "🔬 Laboratorio":
    _load_laboratory().render()
elif mod == "🧑‍🔬 Asistente de Investigación":
    _load_research_assistant().render()
else:
    _load_steam_lab().render()

st.sidebar.divider()
st.sidebar.info("💡 Tip: Usa `streamlit run app.py` desde esta carpeta para localhost:8501")
