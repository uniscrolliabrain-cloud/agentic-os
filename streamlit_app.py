"""
Agentic-OS · Interfaz de chat (Streamlit)

v2: ya no llama a Gemini directo. El mensaje del usuario pasa por el
Orchestrator real -> rol 'director' propone una Intent -> se guarda
como evento auditable. Todavía no hay policy/executor conectados
(el director solo PROPONE, nada se ejecuta aún).
"""

import streamlit as st

from agentic_os.interfaces.llm.provider import GeminiProvider
from agentic_os.kernel.world.events import EventLog
from agentic_os.orchestration.orchestrator import Orchestrator

st.set_page_config(page_title="Agentic-OS", page_icon="🧠")

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("Falta GEMINI_API_KEY en los Secrets de esta app. Ve a Settings -> Secrets en Streamlit Cloud y añádela.")
    st.stop()

if "event_log" not in st.session_state:
    st.session_state.event_log = EventLog()

if "llm" not in st.session_state:
    st.session_state.llm = GeminiProvider(api_key=GEMINI_API_KEY, model="gemini-3.6-flash")

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Orchestrator(log=st.session_state.event_log, llm=st.session_state.llm)

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🧠 Agentic-OS")
st.caption(f"Rol activo: {st.session_state.orchestrator.current_role.name} · eventos en log: {len(st.session_state.event_log)}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Escribe algo...")

if not prompt:
    st.stop()

st.session_state.messages.append({"role": "user", "content": prompt})
with st.chat_message("user"):
    st.markdown(prompt)

chat_box = st.chat_message("assistant")

try:
    intent = st.session_state.orchestrator.handle_user_message(prompt)
    reply = intent.reply_to_user or f"(Propuesta: {intent.kind} sobre {intent.entity_id})"
except Exception as e:
    reply = None
    chat_box.error(f"Error al procesar la propuesta: {e}")

if reply is not None:
    chat_box.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})

if reply is not None:
    chat_box.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
