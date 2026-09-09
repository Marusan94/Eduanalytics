import streamlit as st

st.set_page_config(
    page_title="EduAnalytics HUB Local",
    page_icon="🎓",
    layout="wide"
)

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

# Router lazy para no cargar todo si no se usa
if mod == "📊 Analytics Educativo":
    from modules import analytics
    analytics.render()
elif mod == "⛰️ Dashboard Riesgo":
    from modules import dashboard
    dashboard.render()
elif mod == "💬 Chatbot IA":
    from modules import chatbot
    chatbot.render()
else:
    from modules import steam_lab
    steam_lab.render()

st.sidebar.divider()
st.sidebar.info("💡 Tip: Usa `streamlit run app.py` desde esta carpeta para localhost:8501")
