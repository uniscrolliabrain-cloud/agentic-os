"""Bug 16 - Streamlit Threading Race: streamlit_app.py modifica st.session_state desde hilo secundario"""

import pytest


def test_streamlit_does_not_modify_session_state_from_thread():
    """Streamlit NO debe modificar st.session_state desde un hilo secundario."""
    import inspect
    # Leer el archivo streamlit_app.py
    from pathlib import Path
    app_path = Path(__file__).resolve().parent.parent.parent / "streamlit_app.py"
    if not app_path.exists():
        pytest.skip("streamlit_app.py no encontrado")
    source = app_path.read_text(encoding='utf-8')

    # No debe haber st.session_state.*= dentro de un hilo secundario
    # El bug: modificar session_state desde threading.Thread
    lines = source.split('\n')
    in_thread = False
    for i, line in enumerate(lines):
        if 'threading.Thread' in line or 'def _run_background' in line:
            in_thread = True
        if in_thread and 'st.session_state' in line and '=' in line:
            # Es una asignación a session_state desde un hilo
            assert False, f"Línea {i+1}: modifica st.session_state desde hilo secundario: {line.strip()}"


def test_streamlit_uses_safe_thread_communication():
    """Streamlit debe usar mecanismos seguros para comunicar hilos (Queue, callbacks)."""
    from pathlib import Path
    app_path = Path(__file__).resolve().parent.parent.parent / "streamlit_app.py"
    if not app_path.exists():
        pytest.skip("streamlit_app.py no encontrado")
    source = app_path.read_text(encoding='utf-8')

    # Si usa hilos, debe haber mecanismo seguro
    if 'threading.Thread' in source:
        # No debe modificar directamente session_state
        assert 'st.session_state.orchestrator.handle_user_message' not in source, \
            "Modifica orchestrator en session_state desde hilo sin mecanismo seguro"
