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
