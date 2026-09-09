import streamlit as st
from modules.common import get_client
import json

def render():
    st.title("💬 Chatbot — Analista IA")
    st.caption("Modelo: openai/gpt-4o-mini vía OpenRouter • Streaming • Historial aislado • Pregúntale a tus datos (canónico)")

    client = get_client()
    if client is None:
        st.warning("⚠️ Falta `OPENROUTER_API_KEY` en `.streamlit/secrets.toml` o variable de entorno. El chat no funcionará hasta configurarla.")
        st.code('OPENROUTER_API_KEY="sk-or-v1-..."', language="toml")
        st.info("Copia tu key de https://openrouter.ai/keys y pégala en `.streamlit/secrets.toml` del HUB.")
    else:
        st.success("✅ API Key configurada — listo para chatear", icon="🔑")

    # Contexto de datos canónicos (sesión)
    df = st.session_state.get("analytics_df_canonical")
    has_df = df is not None and not df.empty if hasattr(df, "empty") else False
    if has_df:
        st.info(f"📊 Datos canónicos cargados: {len(df)} filas, {len(df.columns)} columnas — puedes preguntar: '¿nota promedio por materia?', '¿grupo con peor asistencia?', '¿relación asistencia-nota?'")
        with st.expander("Ver muestra (head 3) — no se envía el DataFrame completo al LLM"):
            st.dataframe(df.head(3), use_container_width=True)
            st.caption(f"Columnas canónicas: {list(df.columns)} | Tipos: {df.dtypes.to_dict()}")
    else:
        st.caption("💡 Sube un CSV en Analytics para habilitar preguntas sobre tus datos (modo canónico)")

    # Historial aislado para no colisionar con otros módulos
    if "hub_chatbot_messages" not in st.session_state:
        st.session_state.hub_chatbot_messages = []

    # Mostrar historial
    for message in st.session_state.hub_chatbot_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input del usuario
    if prompt := st.chat_input("Escribe tu mensaje aquí... (ej: ¿nota promedio por materia?)", key="hub_chatbot_input"):
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
                # Construir contexto y tools si hay df
                df_ctx = st.session_state.get("analytics_df_canonical")
                has_ctx = df_ctx is not None and not df_ctx.empty if hasattr(df_ctx, "empty") else False
                if has_ctx:
                    from modules.chatbot_tools import TOOL_SPECS, filter_df, groupby_agg, describe_column
                    # System con esquema y muestra limitada (no df completo)
                    try:
                        head3 = df_ctx.head(3).to_dict(orient="records")
                        # convertir timestamps/NA a string para prompt
                        import pandas as pd
                        for row in head3:
                            for k, v in row.items():
                                if pd.isna(v):
                                    row[k] = None
                                elif hasattr(v, "isoformat"):
                                    try:
                                        row[k] = v.isoformat()
                                    except Exception:
                                        row[k] = str(v)
                        dtypes_str = {c: str(df_ctx[c].dtype) for c in df_ctx.columns}
                    except Exception:
                        head3 = []
                        dtypes_str = {}
                    system_content = (
                        "Eres un analista educativo. Responde en español, de forma concisa y con datos. "
                        "Tienes acceso a un DataFrame canónico (no lo has visto completo, solo esquema y 3 filas de muestra). "
                        "Si la pregunta requiere datos, usa las tools filter_df/groupby_agg/describe_column para obtenerlos y luego responde con tabla y explicación. "
                        f"Esquema canónico: {list(df_ctx.columns)} | Tipos: {dtypes_str} | Filas totales: {len(df_ctx)} | Muestra head(3): {head3}. "
                        "Reglas: solo columnas canónicas, máx 15 filas por tool, no ejecutes Python arbitrario, no uses regex libre."
                    )
                    messages = [{"role": "system", "content": system_content}] + st.session_state.hub_chatbot_messages
                    # Primera llamada con tools (no stream para detectar tool_calls)
                    resp = client.chat.completions.create(
                        model="openai/gpt-4o-mini",
                        messages=messages,
                        tools=TOOL_SPECS,
                        tool_choice="auto",
                        temperature=0.2,
                    )
                    choice = resp.choices[0]
                    tool_calls = getattr(choice.message, "tool_calls", None)
                    if tool_calls:
                        # Ejecutar primer tool (solo uno por turno para simplicidad)
                        tc = tool_calls[0]
                        fname = tc.function.name
                        try:
                            args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                        except Exception:
                            args = {}
                        # Ejecutar localmente
                        if fname == "filter_df":
                            result = filter_df(df_ctx, **args)
                        elif fname == "groupby_agg":
                            result = groupby_agg(df_ctx, **args)
                        elif fname == "describe_column":
                            result = describe_column(df_ctx, **args)
                        else:
                            result = {"error": f"tool {fname} no reconocida"}
                        # Añadir tool result y segunda llamada con streaming
                        messages.append(choice.message)
                        messages.append({"role": "tool", "tool_call_id": tc.id, "name": fname, "content": json.dumps(result, ensure_ascii=False, default=str)})
                        # Mostrar preview de tool si es tabla
                        if "preview" in result and result["preview"]:
                            st.caption(f"🔧 Tool {fname} → {result.get('rows_total', len(result['preview']))} filas")
                            st.dataframe(result["preview"], use_container_width=True)
                        elif "table" in result and result["table"]:
                            st.caption(f"🔧 Tool {fname} → {result.get('rows_total', len(result['table']))} grupos")
                            st.dataframe(result["table"], use_container_width=True)
                        elif "error" in result:
                            st.warning(f"Tool {fname} error: {result['error']}")
                        stream = client.chat.completions.create(
                            model="openai/gpt-4o-mini",
                            messages=messages,
                            stream=True,
                        )
                        for chunk in stream:
                            delta = chunk.choices[0].delta.content if chunk.choices[0].delta.content else ""
                            if delta:
                                full_response += delta
                                placeholder.markdown(full_response)
                    else:
                        # LLM no quiso tool → streaming directo con esa respuesta
                        content = choice.message.content or ""
                        if content:
                            # Si ya hay contenido, mostrarlo directo sin segunda llamada
                            for c in content:
                                full_response += c
                                placeholder.markdown(full_response)
                        else:
                            # Fallback a streaming
                            stream = client.chat.completions.create(
                                model="openai/gpt-4o-mini",
                                messages=messages,
                                stream=True,
                            )
                            for chunk in stream:
                                delta = chunk.choices[0].delta.content if chunk.choices[0].delta.content else ""
                                if delta:
                                    full_response += delta
                                    placeholder.markdown(full_response)
                else:
                    # Sin contexto df → chat normal con streaming
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
                if full_response:
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
