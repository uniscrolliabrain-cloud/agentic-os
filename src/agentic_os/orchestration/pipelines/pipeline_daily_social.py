"""Pipeline diario de contenido social (FASE 6).

1) drive_list_files(folder="content_to_post/{tenant_id}")  -> cache local
2) Elige el fichero de hoy (por fecha en el nombre)
3) Genera copy con GeminiProvider (o mock si no hay API key)
4) meta_post_publish (simulado)
5) Guarda el resultado en data/tenants/{tenant_id}/artifacts/{date}/
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from . import register

_DATA_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "data"


def _today() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _summarize(content: str, max_len: int = 200) -> str:
    return content if len(content) <= max_len else content[: max_len - 3] + "..."


@register("daily_social")
def run_daily_social(executor: Any, registry: Any, tenant_id: str) -> Dict[str, Any]:
    drive_list = registry.get("drive_list_files")
    meta_post = registry.get("meta_post_publish")

    if drive_list is None or meta_post is None:
        return {"status": "SKIPPED", "reason": "tools drive/meta no registradas"}

    folder = f"content_to_post/{tenant_id}"
    listing = drive_list.run({"tenant_id": tenant_id, "folder": folder})
    files = listing.get("files", [])
    if not files:
        return {"status": "NO_CONTENT", "tenant_id": tenant_id, "folder": folder}

    # Elige el de hoy por nombre o el más reciente
    today = _today()
    candidate = next((f for f in files if today in f["name"]), files[0])

    read = registry.get("drive_read_file")
    content = read.run({"tenant_id": tenant_id, "path": candidate["path"]}).get("content", "")

    # Genera copy con el LLM real si está disponible (fallback determinista)
    copy = _summarize(content)
    llm = getattr(executor, "_llm", None) if executor else None
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

    publish = meta_post.run({
        "page_id": params_or(executor, "page_id", f"page_{tenant_id}"),
        "message": copy,
        "image_url": params_or(executor, "image_url", candidate.get("path", "asset.jpg")),
    })

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


def params_or(executor: Any, key: str, default: Any) -> Any:
    ctx = getattr(executor, "_pipeline_params", None)
    if isinstance(ctx, dict):
        return ctx.get(key, default)
    return default