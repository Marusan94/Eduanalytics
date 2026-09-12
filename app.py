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

# --- Tema: claro / oscuro estilo opencode (negros) ---
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

DARK_CSS = """
<style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px; }

    [data-testid="stAppViewContainer"] { background: #09090b; color: #fafafa; }
    [data-testid="stSidebar"] { background: #0e0e11; border-right: 1px solid #27272a; }
    [data-testid="stHeader"] { background: rgba(9,9,11,0); }
    [data-testid="stSidebar"] hr { border-color: #27272a; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #e4e4e7; }

    .hub-brand { text-align: center; padding: 1rem 0 1.2rem; border-bottom: 1px solid #27272a; margin-bottom: 1rem; }
    .hub-brand h2 { margin: 0; font-size: 1.5rem; font-weight: 700; color: #fafafa; }
    .hub-brand p { margin: 0.5rem 0 0; color: #a1a1aa; font-size: 0.85rem; }

    .sys-card { background: #131316; border: 1px solid #27272a; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; }
    .sys-card-title { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
    .sys-card-title strong { color: #fafafa; font-size: 0.95rem; }
    .sys-card-rows { color: #e4e4e7; font-size: 0.85rem; line-height: 1.7; }
    .sys-card-rows .muted { color: #a1a1aa; }
    .sys-badges { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.6rem; }

    .sidebar-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-right: 6px; margin-bottom: 4px; border: 1px solid transparent; }
    .badge-online { background: rgba(34,197,94,0.12); color: #4ade80; border-color: rgba(34,197,94,0.35); }
    .badge-offline { background: rgba(239,68,68,0.12); color: #f87171; border-color: rgba(239,68,68,0.35); }
    .badge-beta { background: rgba(249,115,22,0.12); color: #fb923c; border-color: rgba(249,115,22,0.35); }
    .badge-new { background: rgba(96,165,250,0.12); color: #60a5fa; border-color: rgba(96,165,250,0.35); }

    .metric-card, .custom-card { background: #131316; border: 1px solid #27272a; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; color: #fafafa; }
    .metric-card:hover { border-color: #3f3f46; }
    .tool-result { background: #131316; border: 1px solid #27272a; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; color: #e4e4e7; }
    [data-testid="metric-container"] { background: #131316; border: 1px solid #27272a; border-radius: 12px; padding: 1rem; }
    [data-testid="metric-container"] label, [data-testid="metric-container"] div { color: #fafafa; }

    .stButton > button { border-radius: 8px; font-weight: 600; padding: 0.5rem 1.5rem; background: #fafafa; color: #09090b; border: 1px solid #fafafa; transition: all 0.2s; }
    .stButton > button:hover { background: #e4e4e7; border-color: #e4e4e7; color: #09090b; transform: translateY(-1px); }

    .stTextArea textarea, .stTextInput input { border-radius: 8px; background: #131316; border: 1px solid #27272a; color: #fafafa; }
    .stTextArea textarea:focus, .stTextInput input:focus { border-color: #fafafa; box-shadow: 0 0 0 3px rgba(250,250,250,0.15); }
    .stSelectbox > div > div { border-radius: 8px; background: #131316; border: 1px solid #27272a; color: #fafafa; }
    div[data-baseweb="select"] div { background: #131316; color: #fafafa; }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: 0.75rem 1.5rem; font-weight: 500; color: #a1a1aa; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background: #fafafa; color: #09090b; }

    .stAlert { border-radius: 8px; background: #131316; border: 1px solid #27272a; color: #e4e4e7; }
    details[data-testid="stExpander"] { background: #131316; border: 1px solid #27272a; border-radius: 12px; }
    details[data-testid="stExpander"] summary { color: #fafafa; }

    [data-testid="stRadio"] label { color: #e4e4e7; }
    h1, h2, h3, h4 { color: #fafafa; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #131316; border-radius: 4px; }
    ::-webkit-scrollbar-thumb { background: #27272a; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #3f3f46; }
</style>
"""

LIGHT_CSS = """
<style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px; }

    [data-testid="stAppViewContainer"] { background: #ffffff; color: #0f172a; }
    [data-testid="stSidebar"] { background: #f8fafc; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #334155; }

    .hub-brand { text-align: center; padding: 1rem 0 1.2rem; border-bottom: 1px solid #e2e8f0; margin-bottom: 1rem; }
    .hub-brand h2 { margin: 0; font-size: 1.5rem; font-weight: 700; color: #0f172a; }
    .hub-brand p { margin: 0.5rem 0 0; color: #64748b; font-size: 0.85rem; }

    .sys-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(15,23,42,0.06); }
    .sys-card-title { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
    .sys-card-title strong { color: #0f172a; font-size: 0.95rem; }
    .sys-card-rows { color: #334155; font-size: 0.85rem; line-height: 1.7; }
    .sys-card-rows .muted { color: #64748b; }
    .sys-badges { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.6rem; }

    .sidebar-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-right: 6px; margin-bottom: 4px; border: 1px solid transparent; }
    .badge-online { background: #e8f5e9; color: #2e7d32; border-color: #c8e6c9; }
    .badge-offline { background: #fdecea; color: #c62828; border-color: #f5c6cb; }
    .badge-beta { background: #fff3e0; color: #ef6c00; border-color: #ffe0b2; }
    .badge-new { background: #e3f2fd; color: #1565c0; border-color: #bbdefb; }

    .metric-card, .custom-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; color: #0f172a; box-shadow: 0 2px 8px rgba(15,23,42,0.05); }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(15,23,42,0.1); }
    .tool-result { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; color: #334155; }
    [data-testid="metric-container"] { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem; box-shadow: 0 2px 8px rgba(15,23,42,0.05); }

    .stButton > button { border-radius: 8px; font-weight: 600; padding: 0.5rem 1.5rem; background: #09090b; color: #fafafa; border: 1px solid #09090b; transition: all 0.2s; }
    .stButton > button:hover { background: #27272a; border-color: #27272a; color: #fafafa; transform: translateY(-1px); }

    .stTextArea textarea, .stTextInput input { border-radius: 8px; border: 1px solid #e2e8f0; }
    .stTextArea textarea:focus, .stTextInput input:focus { border-color: #09090b; box-shadow: 0 0 0 3px rgba(9,9,11,0.12); }
    .stSelectbox > div > div { border-radius: 8px; }

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: 0.75rem 1.5rem; font-weight: 500; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background: #09090b; color: #fafafa; }

    .stAlert, .stSuccess, .stError, .stWarning, .stInfo { border-radius: 8px; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #f1f5f9; border-radius: 4px; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
"""

st.markdown(DARK_CSS if st.session_state.dark_mode else LIGHT_CSS, unsafe_allow_html=True)

# Header del sidebar con logo y versión (colores por clase, hereda del tema)
st.sidebar.markdown("""
<div class="hub-brand">
    <h2>🎓 EduAnalytics HUB</h2>
    <p>v3.3 • 100 registros • 8 campos canónicos</p>
</div>
""", unsafe_allow_html=True)

# Toggle de tema bien visible
st.sidebar.toggle("🌙 Modo oscuro", key="dark_mode", help="Activa los negros estilo opencode")
st.sidebar.divider()

# Estado del sistema (tarjeta adaptativa al tema, sin fondos blancos fijos)
from modules.common import get_client
client = get_client()
api_online = client is not None
api_badge = "badge-online" if api_online else "badge-offline"
api_text = "🟢 API Conectada" if api_online else "🔴 Sin API Key"

st.sidebar.markdown(
    "<div class='sys-card'>"
    "<div class='sys-card-title'><span style='font-size: 1.2rem;'>📊</span><strong>Estado del Sistema</strong></div>"
    "<div class='sys-card-rows'>"
    "📊 Datos: 100 registros · 8 campos canónicos<br>"
    f"🔑 API: <span class='muted'>{api_text}</span><br>"
    "📦 Cache: <span class='muted'>Activo (TTL 1h)</span>"
    "</div>"
    "<div class='sys-badges'>"
    f"<span class='sidebar-badge {api_badge}'>{api_text}</span>"
    "<span class='sidebar-badge badge-online'>📊 100 registros</span>"
    "<span class='sidebar-badge badge-new'>📋 8 campos canónicos</span>"
    "<span class='sidebar-badge badge-beta'>⚡ Cache activo</span>"
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)

st.sidebar.divider()

# Navegación principal
st.sidebar.markdown("### 🧭 Navegación")
mod = st.sidebar.radio(
    "Navegación",
    [
        "📊 Analytics Educativo",
        "⛰️ Dashboard",
        "🤖 Analista IA",
        "🔬 Laboratorio",
        "🧑‍🔬 Asistente de Investigación",
    ],
    index=0,
    key="hub_nav",
    label_visibility="collapsed"
)

st.sidebar.divider()

# Vista rápida si hay datos cargados (sin romper si pandas no está importado)
if "analytics_df_canonical" in st.session_state and st.session_state.analytics_df_canonical is not None:
    _df = st.session_state.analytics_df_canonical
    try:
        _empty = bool(_df.empty) if hasattr(_df, "empty") else (len(_df) == 0)
    except Exception:
        _empty = True
    if not _empty:
        st.sidebar.markdown("### 📈 Vista Rápida")
        try:
            _n_rows = len(_df)
            _n_cols = len(_df.columns) if hasattr(_df, "columns") else 0
        except Exception:
            _n_rows, _n_cols = 0, 0
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Registros", _n_rows)
        with col2:
            st.metric("Campos", _n_cols)
        st.sidebar.divider()

# Info técnica colapsable
with st.sidebar.expander("ℹ️ Info técnica"):
    st.caption("""
    **EduAnalytics HUB v3.3**  
    Python 3.11.9 · Streamlit 1.28+ · Pandas 2.1  
    Modelo: openai/gpt-4o-mini (OpenRouter)  
    Embeddings: LocalHash (fallback) / OpenAI (si hay API)  
    Datos: datos_educativos.csv (100 registros, 8 campos canónicos)
    """)

st.sidebar.divider()
st.sidebar.info("💡 Usa `streamlit run app.py` desde esta carpeta para localhost:8501")

# Router con cache — cada módulo se importa 1 vez y se reutiliza
if mod.startswith("📊"):
    _load_analytics().render()
elif mod.startswith("⛰"):
    _load_dashboard().render()
elif mod.startswith("🤖"):
    _load_chatbot().render()
elif mod.startswith("🔬"):
    _load_laboratory().render()
elif mod.startswith("🧑"):
    _load_research_assistant().render()
else:
    _load_analytics().render()
