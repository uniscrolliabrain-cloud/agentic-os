"""
Agentic-OS · Interfaz de chat (Streamlit)

Arquitectura de dos velocidades:
1. FrontAssistant (Laia) — Responde al instante con KnowledgeBase local (RAG-lite).
2. Orchestrator — Procesa en segundo plano (propone Intents, valida con Policy y audita en EventLog).
"""

import os
import threading
from pathlib import Path
import streamlit as st

from agentic_os.interfaces.llm.chat import FrontAssistant
from agentic_os.interfaces.llm.provider import GeminiProvider
from agentic_os.infrastructure.persistence import get_eventlog_repo
from agentic_os.infrastructure.tenancy.registry import TenantRegistry
from agentic_os.infrastructure.config.settings import settings
from agentic_os.orchestration.orchestrator import Orchestrator

st.set_page_config(page_title="Agentic-OS", page_icon="🧠", layout="wide")

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or settings.gemini_api_key

if not GEMINI_API_KEY:
    st.error("Falta GEMINI_API_KEY. Configúrala en los Secrets o en el archivo .env.")
    st.stop()

# --- Estado global y dependencias ---
if "event_log" not in st.session_state:
    st.session_state.event_log = get_eventlog_repo()

if "tenant_registry" not in st.session_state:
    st.session_state.tenant_registry = TenantRegistry()

if "front_assistant" not in st.session_state:
    st.session_state.front_assistant = FrontAssistant(
        model_name=settings.gemini_chat_model,
        api_key=GEMINI_API_KEY,
        temperature=settings.gemini_temperature,
    )

if "orchestrator" not in st.session_state:
    llm_orch = GeminiProvider(api_key=GEMINI_API_KEY, model=settings.gemini_model)
    st.session_state.orchestrator = Orchestrator(log=st.session_state.event_log, llm=llm_orch)

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar: Selección de Tenant y Estado ---
with st.sidebar:
    st.title("⚙️ Configuración")
    tenants = st.session_state.tenant_registry.list_all()
    tenant_options = {t.config.name: t.id for t in tenants}
    tenant_options["System (Por defecto)"] = "system"

    selected_tenant_name = st.selectbox(
        "Cliente activo (Tenant):",
        options=list(tenant_options.keys()),
        index=0,
    )
    active_tenant_id = tenant_options[selected_tenant_name]

    st.divider()
    events_count = len(st.session_state.event_log.list_for_tenant(active_tenant_id))
    st.metric("Eventos auditados", events_count)
    st.caption(f"Rol activo: {st.session_state.orchestrator.current_role.name}")
    st.caption("Arquitectura: ⚡ FrontAssistant + ⚙️ Back-office Orchestrator")

# --- Chat Principal ---
st.title("🧠 Agentic-OS")
st.caption(f"Tenant: **{selected_tenant_name}** ({active_tenant_id})")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Escribe tu consulta o instrucción...")

if prompt:
    # 1. Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Asistente Frontal (Velocidad 1): respuesta inmediata con Knowledge Base
    assistant_box = st.chat_message("assistant")
    with assistant_box:
        with st.spinner("Laia respondiendo..."):
            tenant_kb_dir = None
            if active_tenant_id != "system":
                data_root = Path(__file__).resolve().parent / "data" / "tenants" / active_tenant_id / "knowledge"
                if data_root.exists():
                    tenant_kb_dir = data_root
            try:
                reply = st.session_state.front_assistant.answer(prompt, tenant_knowledge_dir=tenant_kb_dir)
            except Exception as e:
                reply = f"Error en FrontAssistant: {e}"
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # 3. Orquestador (Velocidad 2): tarea asincrona en segundo plano
    # NOTA: Streamlit NO permite modificar session_state desde hilos secundarios.
    # El orquestador se ejecuta en background con una instancia local (no session_state).
    def _run_background_orchestrator(p: str, tid: str):
        try:
            from agentic_os.orchestration.orchestrator import Orchestrator
            from agentic_os.interfaces.llm.provider import GeminiProvider
            from agentic_os.infrastructure.persistence import get_eventlog_repo
            llm = GeminiProvider(api_key=GEMINI_API_KEY, model=settings.gemini_model)
            local_log = get_eventlog_repo()
            orch = Orchestrator(log=local_log, llm=llm)
            orch.handle_user_message(p, tenant_id=tid)
        except Exception:
            pass

    thread = threading.Thread(
        target=_run_background_orchestrator,
        args=(prompt, active_tenant_id),
        daemon=True,
    )
    thread.start()

    st.toast("⚙️ Orquestador analizando intención en segundo plano...", icon="⚙️")

