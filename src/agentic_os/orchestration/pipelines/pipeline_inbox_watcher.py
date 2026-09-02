from __future__ import annotations

from typing import Any, Dict

from . import register


def _classify(
    subject: str,
    snippet: str,
) -> str:

    text = (
        f"{subject} {snippet}"
    ).lower()

    if any(
        value in text
        for value in (
            "presupuesto",
            "queremos",
            "comprar",
            "propuesta",
            "lead",
            "demo",
        )
    ):
        return "lead"

    if any(
        value in text
        for value in (
            "soporte",
            "problema",
            "factura",
            "error",
            "no funciona",
        )
    ):
        return "soporte"

    return "spam"


def _classify_with_llm(
    llm: Any,
    subject: str,
    snippet: str,
) -> str:

    if llm is None:
        return _classify(
            subject,
            snippet,
        )

    try:

        result = llm.generate(
            "Clasifica este email como "
            "'lead', 'soporte' o 'spam'. "
            "Responde solamente con una palabra.\n\n"
            f"Asunto: {subject}\n"
            f"Contenido: {snippet}"
        )

        result = (
            result
            or ""
        ).strip().lower()

        if result in {
            "lead",
            "soporte",
            "spam",
        }:
            return result

    except Exception:
        pass

    return _classify(
        subject,
        snippet,
    )


@register(
    "inbox_watcher",
    tools=[
        "gmail_list_unread",
        "gmail_create_draft",
    ],
)
def run_inbox_watcher(
    runner: Any,
    *args,
    **kwargs,
) -> Dict[str, Any]:

    # Compatibilidad con la invocación legacy (runner, registry, tenant_id)
    # usada por los tests de FASE 6, y con la canónica del PipelineRunner
    # (runner, tenant_id, params, correlation_id).
    if len(args) == 2 and hasattr(args[0], "get"):
        tenant_id = args[1]
        params = {}
        correlation_id = None
    elif len(args) >= 1:
        tenant_id = args[0]
        params = args[1] if len(args) > 1 else kwargs.get("params") or {}
        correlation_id = args[2] if len(args) > 2 else kwargs.get("correlation_id")
    else:
        tenant_id = kwargs.get("tenant_id", "system")
        params = kwargs.get("params") or {}
        correlation_id = kwargs.get("correlation_id")

    params = params or {}

    emails_result = runner.tool(
        "gmail_list_unread",
        {},
        tenant_id,
        correlation_id,
    )

    emails = (
        emails_result
        .get("messages", [])
    )

    llm = getattr(
        runner,
        "llm",
        None,
    )

    processed = 0
    drafts_created = 0

    for email in emails:

        processed += 1

        subject = email.get(
            "subject",
            "",
        )

        snippet = email.get(
            "snippet",
            "",
        )

        category = _classify_with_llm(
            llm,
            subject,
            snippet,
        )

        if category != "lead":
            continue

        runner.tool(
            "gmail_create_draft",
            {
                "to": email.get(
                    "from",
                    "",
                ),
                "subject": (
                    f"Re: {subject}"
                ),
                "body": (
                    "Hola,\n\n"
                    "Gracias por tu interés. "
                    "Te responderé en breve "
                    "con toda la información "
                    "para agendar una llamada.\n\n"
                    "Un saludo."
                ),
            },
            tenant_id,
            correlation_id,
        )

        drafts_created += 1

    return {
        "status": "OK",
        "tenant_id": tenant_id,
        "processed": processed,
        "drafts_created": drafts_created,
    }
