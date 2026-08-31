"""Pipeline leads -> borradores de email (FASE 6).

1) drive_list_files(folder="leads/{tenant_id}")  -> CSV o JSON con leads
2) Por cada lead genera un email personalizado con el LLM
3) gmail_create_draft guarda en data/tenants/{tenant_id}/drafts/ (SIMULADO)
4) Evento LeadDraftCreated por lead
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, List

from . import register

_DATA_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "data"


def _parse_leads(content: str, name: str) -> List[Dict[str, Any]]:
    """Acepta JSON (lista) o CSV con cabecera (name/email o nombre/correo)."""
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return [d for d in data if isinstance(d, dict)]
    except Exception:  # noqa: BLE001
        pass
    reader = csv.DictReader(io.StringIO(content))
    leads = []
    for row in reader:
        row = {k.strip(): (v or "").strip() for k, v in row.items()}
        email = row.get("email") or row.get("correo") or ""
        name = row.get("name") or row.get("nombre") or ""
        if email:
            leads.append({"name": name, "email": email})
    return leads


@register("leads_to_draft")
def run_leads_to_draft(executor: Any, registry: Any, tenant_id: str) -> Dict[str, Any]:
    drive_list = registry.get("drive_list_files")
    drive_read = registry.get("drive_read_file")
    gmail_draft = registry.get("gmail_create_draft")

    if not (drive_list and drive_read and gmail_draft):
        return {"status": "SKIPPED", "reason": "tools drive/gmail_draft no registradas"}

    folder = f"leads/{tenant_id}"
    listing = drive_list.run({"tenant_id": tenant_id, "folder": folder})
    files = [f for f in listing.get("files", []) if f["name"].lower().endswith((".csv", ".json"))]
    if not files:
        return {"status": "NO_LEADS_FILE", "tenant_id": tenant_id, "folder": folder}

    lead_file = files[0]
    content = drive_read.run({"tenant_id": tenant_id, "path": lead_file["path"]}).get("content", "")
    leads = _parse_leads(content, lead_file["name"])

    created = []
    llm = getattr(executor, "_llm", None) if executor else None
    for lead in leads:
        name = lead.get("name", "")
        email = lead.get("email", "")
        subject = f"Hola {name}, tenemos una propuesta para ti" if name else "Propuesta para ti"
        body = (
            f"Hola {name},\n\nTe escribimos porque creemos que nuestra solución encaja "
            f"con lo que buscas. ¿Te va bien una llamada esta semana?\n\nUn saludo."
        )
        if llm is not None and hasattr(llm, "generate"):
            try:
                generated = llm.generate(
                    f"Escribe un email de ventas breve y profesional para {name or 'un lead'} "
                    f"({email}). Tema: propuesta de valor. Máx 80 palabras."
                )
                if generated and generated.strip():
                    body = generated.strip()
            except Exception:  # noqa: BLE001 - fallback determinista
                pass
        draft = gmail_draft.run({
            "tenant_id": tenant_id, "to": email, "subject": subject, "body": body,
        })
        created.append(draft)

    return {"status": "OK", "tenant_id": tenant_id, "drafts_created": len(created)}