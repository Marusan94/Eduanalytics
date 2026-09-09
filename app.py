import os
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
import streamlit as st

st.set_page_config(
    page_title="EduAnalytics HUB Local",
    page_icon="🎓",
    layout="wide"
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
def _load_steam_lab():
    from modules import steam_lab
    return steam_lab

# Estilo extra para distinguir el HUB local
st.markdown("""
<style>
.small-muted {color:#8A8A8A; font-size:13px;}
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🎓 EduAnalytics HUB")
st.sidebar.caption("LOCALHOST • 4 módulos integrados • sin tocar repos originales")
st.sidebar.divider()

mod = st.sidebar.radio(
    "Navegación",
    ["📊 Analytics Educativo", "⛰️ Dashboard Riesgo", "💬 Chatbot IA", "🧪 STEAM Lab"],
    index=0,
    key="hub_nav"
)

st.sidebar.divider()
st.sidebar.markdown(
    """
    <span class="small-muted">
    Repo nuevo: <code>DESKTOP/EDUANALYTICS-HUB-LOCAL</code><br/>
    Orígenes:<br/>
    • Analytics → Documents/eduanalytics/app.py<br/>
    • Dashboard → Clases CYMETRIA/Dashboard 2/app.py<br/>
    • Chatbot → Clases CYMETRIA/Chatbot2/app.py<br/>
    • STEAM Lab → Clases CYMETRIA/Automatiza Streamlit pro/app.py<br/>
    </span>
    """,
    unsafe_allow_html=True
)
st.sidebar.caption("API Key: .streamlit/secrets.toml (copia de Chatbot2)")

# Router con cache — cada módulo se importa 1 vez y se reutiliza
if mod == "📊 Analytics Educativo":
    _load_analytics().render()
elif mod == "⛰️ Dashboard Riesgo":
    _load_dashboard().render()
elif mod == "💬 Chatbot IA":
    _load_chatbot().render()
else:
    _load_steam_lab().render()

st.sidebar.divider()
st.sidebar.info("💡 Tip: Usa `streamlit run app.py` desde esta carpeta para localhost:8501")
