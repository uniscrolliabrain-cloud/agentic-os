"""Tools de Google Drive (FASE 6) — SIMULADAS con cache local por tenant.

Hasta que configuremos credenciales reales (GOOGLE_*), las tools leen de
`data/tenants/{tenant_id}/drive/...` como cache local de Drive. El tenant se
valida SIEMPRE: nunca se lee otro tenant. Si faltan credenciales reales,
seguirá usando la cache (diseño fail-safe sin conexión).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from .base import Tool, ToolValidationError

_DATA_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent / "data"


def _tenant_drive_dir(tenant_id: str) -> Path:
    if not tenant_id or ".." in tenant_id or "/" in tenant_id or "\\" in tenant_id:
        raise ToolValidationError(f"tenant_id inválido: {tenant_id!r}")
    d = _DATA_ROOT / "tenants" / tenant_id / "drive"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_resolve(root: Path, folder: str) -> Path:
    """Resuelve ``folder`` relativa a la raíz del tenant, sin escape.

    Usa comparación semántica de paths (``is_relative_to``) en lugar de
    ``str(...).startswith`` para evitar el bypass de prefijos, p.ej.
    ``tenants/acme/drive_evil`` compartiendo prefijo con ``tenants/acme/drive``.
    """
    root_resolved = root.resolve()
    target = (root_resolved / folder).resolve()
    if not target.is_relative_to(root_resolved):
        raise ToolValidationError(f"ruta fuera de la cache del tenant: {folder!r}")
    return target


class DriveListFilesTool(Tool):
    """Lista los ficheros de una carpeta de la cache local de Drive del tenant."""

    name = "drive_list_files"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        tenant_id = params.get("tenant_id", "")
        folder = params.get("folder", "")
        if not tenant_id:
            raise ToolValidationError("faltan campos: tenant_id es obligatorio")
        root = _tenant_drive_dir(tenant_id)
        target = _safe_resolve(root, folder) if folder else root
        files: List[Dict[str, str]] = []
        if target.exists():
            for p in sorted(target.iterdir()):
                if p.is_file():
                    files.append({
                        "name": p.name,
                        "path": str(p.relative_to(root)),
                        "size": str(p.stat().st_size),
                    })
        return {
            "status": "SIMULATED",
            "real_execution": False,
            "folder": folder,
            "files": files,
        }


class DriveReadFileTool(Tool):
    """Lee el contenido de un fichero de la cache local de Drive del tenant."""

    name = "drive_read_file"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        tenant_id = params.get("tenant_id", "")
        path = params.get("path", "")
        if not tenant_id or not path:
            raise ToolValidationError("faltan campos: tenant_id y path son obligatorios")
        root = _tenant_drive_dir(tenant_id)
        target = _safe_resolve(root, path)
        if not target.is_file():
            raise ToolValidationError(f"fichero no encontrado en cache Drive: {path}")
        content = target.read_text(encoding="utf-8", errors="replace")
        return {
            "status": "SIMULATED",
            "real_execution": False,
            "name": target.name,
            "content": content,
        }


class DriveSearchTool(Tool):
    """Busca ficheros por nombre (glob) en la cache local de Drive del tenant."""

    name = "drive_search"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        tenant_id = params.get("tenant_id", "")
        query = params.get("query", "")
        if not tenant_id or not query:
            raise ToolValidationError("faltan campos: tenant_id y query son obligatorios")
        root = _tenant_drive_dir(tenant_id)
        results: List[Dict[str, str]] = []
        if root.exists():
            for p in sorted(root.rglob("*")):
                if p.is_file() and query.lower() in p.name.lower():
                    results.append({
                        "name": p.name,
                        "path": str(p.relative_to(root)),
                    })
        return {
            "status": "SIMULATED",
            "real_execution": False,
            "query": query,
            "matches": results,
        }