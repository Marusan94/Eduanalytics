import streamlit as st
from openai import OpenAI

def get_client():
    api_key = None
    try:
        api_key = st.secrets.get("OPENROUTER_API_KEY")
    except Exception:
        api_key = None
    if not api_key:
        import os
        api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

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
                st.error(f"Error al obtener respuesta: {e}")

    # Acciones
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Limpiar chat", key="hub_chatbot_clear"):
            st.session_state.hub_chatbot_messages = []
            st.rerun()
    with col2:
        st.caption(f"Mensajes en historial: {len(st.session_state.get('hub_chatbot_messages', []))}")
