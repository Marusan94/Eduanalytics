# EduAnalytics HUB Local 🎓

**Hub localhost que integra 3 módulos Streamlit sin tocar repos originales.**

- **Puerto:** `http://localhost:8501`
- **Carpeta:** `DESKTOP/EDUANALYTICS-HUB-LOCAL` (nueva, aislada)
- **Repos originales intactos:** `Documents/eduanalytics` y `Clases CYMETRIA/*` no modificados.

## Módulos

| Módulo | Origen | Archivo Hub | API Key |
|---|---|---|---|
| 📊 Analytics Educativo | `Documents/eduanalytics/app.py:15-478` (14 análisis) | `modules/analytics.py` | No |
| ⛰️ Dashboard Riesgo | `Clases CYMETRIA/Dashboard 2/app.py:1-245` (Folium + Plotly) | `modules/dashboard.py` | No |
| 💬 Chatbot IA | `Clases CYMETRIA/Chatbot2/app.py:1-60` (OpenRouter streaming) | `modules/chatbot.py` | Sí `.streamlit/secrets.toml` |

## Uso local

```bash
cd C:\Users\USUARIO\Desktop\EDUANALYTICS-HUB-LOCAL
py -m pip install -r requirements.txt
py -m streamlit run app.py
# abre http://localhost:8501
```

Usa el **sidebar radio** para cambiar de módulo. El historial del chatbot está aislado en `st.session_state["hub_chatbot_messages"]` y no se borra al navegar.

## Secrets

Copia de `Clases CYMETRIA/Chatbot2/.streamlit/secrets.toml`:
```toml
OPENROUTER_API_KEY="sk-or-v1-..."
```
Ya está copiado en `.streamlit/secrets.toml` del HUB. No commitear.

## Verificación

- `py -m py_compile app.py modules/*.py` → OK (4 archivos)
- `Invoke-WebRequest http://localhost:8501` → 200
- Analytics con `datos_educativos.csv` → 14 secciones idénticas al original
- Dashboard → 6 gráficos + mapa Folium
- Chatbot → streaming `openai/gpt-4o-mini` vía OpenRouter

## Próximos pasos (cuando quieras deploy)

1. Rotar `OPENROUTER_API_KEY` (expuesta en repo local)
2. `git init` en esta carpeta si quieres push a nuevo repo `Eduanalytics-HUB`
3. Render: set env var `OPENROUTER_API_KEY` en dashboard, no `secrets.toml`
4. Integrar `Automatiza Streamlit pro` como 4to módulo `modules/steam_lab.py` (fix bug línea 242)
