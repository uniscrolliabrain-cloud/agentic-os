"""
Punto de entrada para arrancar el backend API de Agentic OS en local.

Uso:
    python run_api.py            # uvicorn en http://localhost:8000
    uvicorn run_api:app --reload --port 8000
"""
import os

import uvicorn

from agentic_os.interfaces.api.rest import app

__all__ = ["app"]


if __name__ == "__main__":
    uvicorn.run(
        "run_api:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        reload=os.environ.get("RELOAD", "").lower() in ("1", "true", "yes"),
    )