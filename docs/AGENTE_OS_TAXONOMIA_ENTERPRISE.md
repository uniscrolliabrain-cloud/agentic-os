# AGENTE OS - TAXONOMÍA ENTERPRISE v2.0

**Definición: Capa Operativa Inteligente sobre el software existente. No reemplaza CRM/ERP/Calendar. Los opera.**

### PRINCIPIO CORE: 1 Acción = 1 Mini-Agente con 1 Skill
No un agente gordo que hace todo. 30 micro-agentes tontos pero expertos, orquestados.

### I. KERNEL (lo que ya tienes y hay que blindar)

**WORLD =** EventLog append-only + tenant_id + entity_id
**ORQUESTADOR =** Solo hace: Objetivo -> Contexto -> Restricciones -> Plan -> Asignar a mini-agente -> Observar -> Corregir
**MEMORIA =** Hot Cache (resumen 1h) + RAG (Chroma con 10 eventos relevantes) + Cold Log (auditoría total). Así no es lento.
**POLICIES =** `agents.yaml` para tunear tono, goals, forbidden, tools por empresa sin tocar código.
**GUARDIAN =** Todo lo que cruce tenant o sea PII o sea acción destructiva -> aprobación humana obligatoria.

### II. TAXONOMÍA DE CAPACIDADES - 40 MINI-AGENTES

**A. COMUNICACIÓN OMNICANAL (Entrada/Salida)**
1. `whatsapp_listener` - webhook inbound Meta
2. `whatsapp_sender` - envía plantilla + variables
3. `slack_listener` - lee canales #ventas #soporte por Slack API
4. `slack_sender` - postea, responde threads, manda DM
5. `gmail_reader` - pulling cada 5 min, clasifica
6. `gmail_sender` - redacta y envía
7. `calendar_reader` - ve huecos en Google Calendar / Outlook del cliente via API
8. `calendar_scheduler` - agenda, mueve, cancela citas. Confirma con link Meet.
9. `notification_dispatcher` - manda push/email/telegram según regla

**B. CRM & DATA (El mundo real)**
10. `crm_reader` - pulling de contactos, deals, custom fields por API (Hubspot/Pipedrive/Salesforce)
11. `crm_writer` - crear cliente desde lenguaje natural: "mete a Juan de Acme como lead caliente"
12. `crm_updater` - "cambia el pipeline de 1042 a ganado y ponle 3000€"
13. `db_puller` - pulling de Sheets/Notion/Postgres del cliente
14. `db_writer` - escribe cambios con validación
15. `enricher_agent` - investiga empresa/persona en web + LinkedIn y completa CRM

**C. VENTAS - Pipeline Autónomo**
16. `lead_capturer`
17. `lead_qualifier` - scoring según SOP de la empresa
18. `proposal_builder` - genera propuesta con datos del CRM
19. `followup_agent` - si no responde en X, dispara secuencia
20. `loss_analyzer` - por qué se perdió el deal

**D. CONTENIDO Y REDES**
21. `copy_writer` - crea copy según tono de `agents.yaml`
22. `content_planner` - calendario de contenido
23. `social_publisher` - publica en IG/LinkedIn/FB via API (Buffer API)
24. `social_listener` - lee comentarios/DMs y los convierte en eventos
25. `image_brief_agent` - genera brief para diseñador / o prompt para imagen

**E. OPERACIONES & SOPs**
26. `sop_runner` - ejecuta YAML paso a paso: wait -> action -> if -> handoff
27. `document_reader` - lee PDFs, contratos, facturas (OCR)
28. `task_creator` - crea tarea en ClickUp/Asana/Trello
29. `exception_detector` - detecta que algo se salió de la SOP y escala a humano

**F. FINANZAS & LEGAL**
30. `invoice_reader` - lee factura vs orden de compra
31. `expense_classifier`
32. `report_builder`

### III. FLUJO EJEMPLO REAL - De lenguaje natural a acción

Tú dices en Slack: "@AGENTE OS mete a Clinica Las Palmas como cliente en Hubspot, agéndale demo mañana a las 10 con Alfonso y mándale whatsapp de confirmación con el copy que usamos"

1. `slack_listener` -> evento `command_inbound`
2. Orquestador -> genera 3 Intents:
   a) Intent(action, target=crm_writer, payload="create company Clinica Las Palmas")
   b) Intent(action, target=calendar_scheduler, payload="find slot tomorrow 10:00 Alfonso")
   c) Intent(action, target=copy_writer -> whatsapp_sender, payload="confirmación demo")
3. Cada mini-agente ejecuta su skill, reporta `tool_result` al EventLog
4. Si alguno falla, `exception_detector` -> pide aprobación en tu UI dark

### IV. LO QUE NOS FALTA PROGRAMAR YA (Próximos 7 días)

1. `slack_adapter` (listener + sender) - es igual que whatsapp
2. `crm_adapter` genérico con interfaz: `read/write/update` - luego haces `hubspot_impl`, `pipedrive_impl`
3. `calendar_adapter`
4. `agents.yaml` - para que puedas decir "el closer más agresivo" sin tocar prompt
5. `social_publisher` vía Buffer/Metricool API (mucho más fácil que API nativa de IG)