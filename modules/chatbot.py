import streamlit as st
from modules.common import get_client

def render():
    st.title("💬 Chatbot con OpenRouter API")
    st.caption("Modelo: openai/gpt-4o-mini vía OpenRouter • Streaming • Historial aislado por sesión")

    client = get_client()
    if client is None:
        st.warning("⚠️ Falta `OPENROUTER_API_KEY` en `.streamlit/secrets.toml` o variable de entorno. El chat no funcionará hasta configurarla.")
        st.code('OPENROUTER_API_KEY="sk-or-v1-..."', language="toml")
        st.info("Copia tu key de https://openrouter.ai/keys y pégala en `.streamlit/secrets.toml` del HUB.")
    else:
        st.success("✅ API Key configurada — listo para chatear", icon="🔑")

    # Historial aislado para no colisionar con otros módulos
    if "hub_chatbot_messages" not in st.session_state:
        st.session_state.hub_chatbot_messages = []

    # Mostrar historial
    for message in st.session_state.hub_chatbot_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input del usuario
    if prompt := st.chat_input("Escribe tu mensaje aquí...", key="hub_chatbot_input"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.hub_chatbot_messages.append({"role": "user", "content": prompt})

        if client is None:
            st.error("No hay API Key configurada. No se puede enviar el mensaje.")
            return

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            try:
                stream = client.chat.completions.create(
                    model="openai/gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Eres un asistente amable, servicial y útil. Respondes en español."}
                    ] + st.session_state.hub_chatbot_messages,
                    stream=True,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content if chunk.choices[0].delta.content else ""
                    if delta:
                        full_response += delta
                        placeholder.markdown(full_response)
                st.session_state.hub_chatbot_messages.append(
                    {"role": "assistant", "content": full_response}
                )
            except Exception as e:
                err = str(e)
                if "401" in err and "User not found" in err:
                    st.error("🔑 API Key inválida o revocada (401 User not found). Ve a https://openrouter.ai/keys → Create Key → copia la nueva `sk-or-v1-...` y pégala en Render → Environment → OPENROUTER_API_KEY y en `.streamlit/secrets.toml` local, luego redeploy.")
                else:
                    st.error(f"Error al obtener respuesta: {e}")

    # Acciones
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Limpiar chat", key="hub_chatbot_clear"):
            st.session_state.hub_chatbot_messages = []
            st.rerun()
    with col2:
        st.caption(f"Mensajes en historial: {len(st.session_state.get('hub_chatbot_messages', []))}")
