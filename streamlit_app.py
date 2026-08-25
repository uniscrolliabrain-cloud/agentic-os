"""
Agentic-OS · Interfaz de chat (Streamlit)

Versión inicial mínima: solo valida que el despliegue funciona
y que la conexión con Gemini está bien configurada.
Todavía NO pasa por el orchestrator/kernel — eso se conecta
en un paso posterior.
"""

import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Agentic-OS", page_icon="🧠")

# --- Configuración desde los Secrets de Streamlit Cloud ---
# (Settings -> Secrets, nunca desde un archivo del repo)
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error(
        "Falta GEMINI_API_KEY en los Secrets de esta app. "
        "Ve a Settings -> Secrets en Streamlit Cloud y añádela."
    )
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

st.title("🧠 Agentic-OS")
st.caption("Fase de validación · sin conexión al kernel todavía")

# --- Historial de chat en memoria de sesión ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Escribe algo para probar la conexión con Gemini...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = model.generate_content(prompt)
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
