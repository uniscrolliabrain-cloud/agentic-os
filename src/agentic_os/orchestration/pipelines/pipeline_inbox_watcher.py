"""Pipeline inbox watcher (FASE 6): revisa email y deja drafts de respuesta.

1) gmail_list_unread (simulado)
2) Clasifica cada email (lead / soporte / spam) con LLM
3) Si es lead -> genera borrador de respuesta en drafts/
4) Evento InboxProcessed
"""

from __future__ import annotations

from typing import Any, Dict, List

from . import register


def _classify(subject: str, snippet: str) -> str:
    low = f"{subject} {snippet}".lower()
    if any(t in low for t in ("presupuesto", "queremos", "comprar", "propuesta", "lead", "demo")):
        return "lead"
    if any(t in low for t in ("soporte", "problema", "factura", "error", "no funciona")):
        return "soporte"
    return "spam"


def _classify_with_llm(llm: Any, subject: str, snippet: str) -> str:
    if llm is None or not hasattr(llm, "generate"):
        return _classify(subject, snippet)
    try:
        out = llm.generate(
            f"Clasifica este email como 'lead', 'soporte' o 'spam'. "
            f"Solo responde una palabra. Asunto: {subject} | Contenido: {snippet}"
        )
        out = (out or "").strip().lower()
        if out in ("lead", "soporte", "spam"):
            return out
    except Exception:  # noqa: BLE001 - fallback determinista
        pass
    return _classify(subject, snippet)


@register("inbox_watcher")
def run_inbox_watcher(executor: Any, registry: Any, tenant_id: str) -> Dict[str, Any]:
    list_unread = registry.get("gmail_list_unread")
    gmail_draft = registry.get("gmail_create_draft")

    if not (list_unread and gmail_draft):
        return {"status": "SKIPPED", "reason": "tools gmail no registradas"}

    emails = list_unread.run({"tenant_id": tenant_id}).get("messages", [])
    llm = getattr(executor, "_llm", None) if executor else None

    processed = 0
    drafts_created = 0
    for email in emails:
        processed += 1
        kind = _classify_with_llm(llm, email.get("subject", ""), email.get("snippet", ""))
        if kind == "lead":
            draft = gmail_draft.run({
                "tenant_id": tenant_id,
                "to": email.get("from", ""),
                "subject": f"Re: {email.get('subject', '')}",
                "body": (
                    "Hola,\n\nGracias por tu interés. Te respondo en breve con toda la "
                    "información para agendar una llamada.\n\nUn saludo."
                ),
            })
            drafts_created += 1

    return {
        "status": "OK",
        "tenant_id": tenant_id,
        "processed": processed,
        "drafts_created": drafts_created,
    }