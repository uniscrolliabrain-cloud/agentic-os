# Skills y herramientas

## Skills (SOPs)

Procedimientos reutilizables. Ejemplos: inbox_zero (procesar email), schedule_meeting
(agendar reunión). Cada skill tiene pasos definidos.

## Tools (herramientas de ejecución)

El Executor tiene estas tools registradas:

- gmail_send, gmail_read → correo
- slack_send, slack_read → Slack
- whatsapp_send, whatsapp_read → WhatsApp
- calendar_create_event, calendar_list_events → calendario
- web_scrape, web_search → web
- documentation_create, documentation_search → documentación interna

## Invariantes

- Una tool se ejecuta SOLO si la policy del tenant lo permite.
- Toda ejecución queda auditada en el EventLog.
- El LLM de orquestación propone el action, no lo ejecuta.