"""
Punto de entrada para arrancar el backend API de Agentic OS en local.

Uso:
    uvicorn run_api:app --reload --port 8000
"""
from agentic_os.interfaces.api.rest import app

__all__ = ["app"]