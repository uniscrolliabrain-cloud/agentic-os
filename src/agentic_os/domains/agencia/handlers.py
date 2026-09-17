"""Handlers de ejecucion de los pipelines del tenant bor-agencia."""
from __future__ import annotations

import csv
import io
import json
import logging
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ...kernel.types.time import now_utc
from .entities import AgencyLead, SocialPost

logger = logging.getLogger(__name__)

_DATA_ROOT = Path(__file__).resolve().parents[3] / "data"


def _today() -> str:
    return now_utc().strftime("%Y-%m-%d")


def _summarize(content: str, max_len: int = 200) -> str:
    return content if len(content) <= max_len else content[: max_len - 3] + "..."


def _parse_leads(content: str) -> List[Dict[str, Any]]:
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return [d for d in data if isinstance(d, dict)]
    except (json.JSONDecodeError, ValueError):
        pass
    reader = csv.DictReader(io.StringIO(content))
    leads: List[Dict[str, Any]] = []
    for row in reader:
        row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
        email = row.get("email") or row.get("correo") or ""
        name = row.get("name") or row.get("nombre") or ""
        if email:
            leads.append({"name": name, "email": email})
    return leads


def _emit_entity(runner: Any, tenant_id: str, entity: Any,
                 correlation_id: Optional[str]) -> None:
    emit = getattr(runner, "emit_event", None)
    if callable(emit):
        emit("entity_created", entity.id, tenant_id,
             entity.model_dump(), correlation_id)


def handle_leads_to_draft(runner: Any, tenant_id: str,
                          params: Dict[str, Any],
                          correlation_id: Optional[str]) -> Dict[str, Any]:
    folder = f"leads/{tenant_id}"
    listing = runner.tool("drive_list_files",
                          {"tenant_id": tenant_id, "folder": folder},
                          tenant_id, correlation_id)
    files = [f for f in listing.get("files", [])
             if f["name"].lower().endswith((".csv", ".json"))]
    if not files:
        return {"status": "NO_LEADS_FILE", "tenant_id": tenant_id, "folder": folder}

    lead_file = files[0]
    content = runner.tool("drive_read_file",
                          {"tenant_id": tenant_id, "path": lead_file["path"]},
                          tenant_id, correlation_id).get("content", "")

    leads = _parse_leads(content)
    created: List[Dict[str, Any]] = []
    errors: List[str] = []
    llm = getattr(runner, "llm", None)

    for lead in leads:
        name = lead.get("name", "")
        email = lead.get("email", "")

        try:
            entity = AgencyLead(
                tenant_id=tenant_id,
                entity_type="agencia.lead",
                client_id=params.get("client_id", tenant_id),
                name=name or "sin-nombre",
                email=email,
                phone=params.get("phone", "+34 600 000 000"),
                source="leads_to_draft",
            )
        except Exception as exc:
            errors.append(f"lead invalido (email={email!r}): {exc}")
            continue

        _emit_entity(runner, tenant_id, entity, correlation_id)

        subject = (f"Hola {name}, tenemos una propuesta para ti"
                   if name else "Propuesta para ti")
        body = (
            f"Hola {name},\n\nTe escribimos porque creemos que nuestra "
            f"solucion encaja con lo que buscas.\n\nUn saludo."
        )
        if llm is not None and hasattr(llm, "generate"):
            try:
                generated = llm.generate(
                    f"Escribe un email de ventas breve y profesional para "
                    f"{name or 'un lead'} ({email}). Max 80 palabras."
                )
                if generated and generated.strip():
                    body = generated.strip()
            except Exception:
                logger.warning("LLM copy fallo en leads_to_draft; fallback")

        draft = runner.tool("gmail_create_draft",
                            {"tenant_id": tenant_id, "to": email,
                             "subject": subject, "body": body},
                            tenant_id, correlation_id)
        created.append(draft)

    return {
        "status": "OK",
        "tenant_id": tenant_id,
        "drafts_created": len(created),
        "errors": errors,
    }


def _classify(subject: str, snippet: str) -> str:
    text = f"{subject} {snippet}".lower()
    if any(w in text for w in ("presupuesto", "queremos", "comprar", "propuesta",
                               "lead", "demo")):
        return "lead"
    if any(w in text for w in ("soporte", "problema", "factura", "error",
                               "no funciona")):
        return "soporte"
    return "spam"


def _classify_llm(llm: Any, subject: str, snippet: str) -> str:
    if llm is None:
        return _classify(subject, snippet)
    try:
        result = (llm.generate(
            "Clasifica este email como 'lead', 'soporte' o 'spam'. "
            "Responde solamente con una palabra.\n\n"
            f"Asunto: {subject}\nContenido: {snippet}"
        ) or "").strip().lower()
        if result in {"lead", "soporte", "spam"}:
            return result
    except Exception as exc:
        logger.warning("clasificacion LLM fallo, fallback: %s", exc)
    return _classify(subject, snippet)


def handle_inbox_watcher(runner: Any, tenant_id: str,
                         params: Dict[str, Any],
                         correlation_id: Optional[str]) -> Dict[str, Any]:
    emails_result = runner.tool("gmail_list_unread", {}, tenant_id, correlation_id)
    emails = emails_result.get("messages", [])
    llm = getattr(runner, "llm", None)

    processed = 0
    drafts_created = 0
    for email in emails:
        processed += 1
        subject = email.get("subject", "")
        snippet = email.get("snippet", "")
        category = _classify_llm(llm, subject, snippet)
        if category != "lead":
            continue
        runner.tool(
            "gmail_create_draft",
            {
                "to": email.get("from", ""),
                "subject": f"Re: {subject}",
                "body": (
                    "Hola,\n\nGracias por tu interes. Te respondere en breve "
                    "con toda la informacion.\n\nUn saludo."
                ),
            },
            tenant_id, correlation_id,
        )
        drafts_created += 1

    return {
        "status": "OK",
        "tenant_id": tenant_id,
        "processed": processed,
        "drafts_created": drafts_created,
    }

def handle_daily_social(runner: Any, tenant_id: str,
                        params: Dict[str, Any],
                        correlation_id: Optional[str]) -> Dict[str, Any]:
    folder = f"content_to_post/{tenant_id}"
    listing = runner.tool("drive_list_files",
                          {"tenant_id": tenant_id, "folder": folder},
                          tenant_id, correlation_id)
    files = listing.get("files", [])
    if not files:
        return {"status": "NO_CONTENT", "tenant_id": tenant_id, "folder": folder}

    today = _today()
    candidate = next((f for f in files if today in f["name"]), files[0])

    content = runner.tool("drive_read_file",
                          {"tenant_id": tenant_id, "path": candidate["path"]},
                          tenant_id, correlation_id).get("content", "")

    copy = _summarize(content)
    llm = getattr(runner, "llm", None)
    if llm is not None and hasattr(llm, "generate"):
        try:
            generated = llm.generate(
                f"Escribe un post de redes sociales profesional (max 120 "
                f"palabras) a partir de este contenido: {_summarize(content, 500)}"
            )
            if generated and generated.strip():
                copy = generated.strip()
        except Exception:
            logger.warning("LLM copy fallo en daily_social; fallback")

    try:
        entity = SocialPost(
            tenant_id=tenant_id,
            entity_type="agencia.social_post",
            channel="meta",
            copy=copy,
            source_asset=candidate.get("name", ""),
        )
    except Exception as exc:
        return {"status": "VALIDATION_ERROR", "tenant_id": tenant_id,
                "error": str(exc)}

    _emit_entity(runner, tenant_id, entity, correlation_id)

    publish = runner.tool("meta_post_publish",
                          {
                              "page_id": params.get("page_id", f"page_{tenant_id}"),
                              "message": copy,
                              "image_url": params.get("image_url",
                                                      candidate.get("path", "asset.jpg")),
                          },
                          tenant_id, correlation_id)

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


HANDLERS: Dict[str, Callable[..., Dict[str, Any]]] = {
    "leads_to_draft": handle_leads_to_draft,
    "inbox_watcher": handle_inbox_watcher,
    "daily_social": handle_daily_social,
}

__all__ = ["HANDLERS"]