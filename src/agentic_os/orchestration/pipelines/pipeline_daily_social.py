"""Pipeline diario de contenido social (FASE 6).

1) drive_list_files(folder="content_to_post/{tenant_id}")  -> cache local
2) Elige el fichero de hoy (por fecha en el nombre)
3) Genera copy con el LLM del runner (o fallback determinista)
4) meta_post_publish (simulado)
5) Guarda el resultado en data/tenants/{tenant_id}/artifacts/{date}/

Todas las MicroActions se ejecutan vía `runner.tool()` -> Executor -> Policy ->
Tool -> EventLog. NUNCA se llama a una Tool directamente.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from ...kernel.types.time import now_utc
from . import register

_DATA_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "data"


def _today() -> str:
    return now_utc().strftime("%Y-%m-%d")


def _summarize(content: str, max_len: int = 200) -> str:
    return content if len(content) <= max_len else content[: max_len - 3] + "..."


@register("daily_social", tools=["drive_list_files", "drive_read_file", "meta_post_publish"])
def run_daily_social(runner: Any, tenant_id: str, params: Optional[Dict[str, Any]] = None,
                     correlation_id: Optional[str] = None) -> Dict[str, Any]:
    params = params or {}
    folder = f"content_to_post/{tenant_id}"

    listing = runner.tool("drive_list_files",
                          {"tenant_id": tenant_id, "folder": folder},
                          tenant_id, correlation_id)
    files = listing.get("files", [])
    if not files:
        return {"status": "NO_CONTENT", "tenant_id": tenant_id, "folder": folder}

    # Elige el de hoy por nombre o el más reciente
    today = _today()
    candidate = next((f for f in files if today in f["name"]), files[0])

    content = runner.tool("drive_read_file",
                          {"tenant_id": tenant_id, "path": candidate["path"]},
                          tenant_id, correlation_id).get("content", "")

    # Genera copy con el LLM del runner (fallback determinista; nunca rompe)
    copy = _summarize(content)
    llm = getattr(runner, "llm", None)
    if llm is not None and hasattr(llm, "generate"):
        try:
            generated = llm.generate(
                f"Escribe un post de redes sociales profesional (máx 120 palabras) "
                f"a partir de este contenido: {_summarize(content, 500)}"
            )
            if generated and generated.strip():
                copy = generated.strip()
        except Exception:  # noqa: BLE001 - el copy fallback determinista nunca rompe
            pass

    publish = runner.tool("meta_post_publish", {
        "page_id": params.get("page_id", f"page_{tenant_id}"),
        "message": copy,
        "image_url": params.get("image_url", candidate.get("path", "asset.jpg")),
    }, tenant_id, correlation_id)

    artifact = {
        "id": f"art_{uuid.uuid4().hex[:10]}",
        "tenant_id": tenant_id,
        "pipeline": "daily_social",
        "date": today,
        "source_file": candidate.get("name"),
        "copy": copy,
        "publish": publish,
    }
    artifacts_dir = _DATA_ROOT / "tenants" / tenant_id / "artifacts" / today
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (artifacts_dir / f"{artifact['id']}.json").write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"status": "OK", "artifact": artifact}