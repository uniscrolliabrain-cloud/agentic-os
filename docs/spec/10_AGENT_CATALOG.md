# 10 — Catálogo de miniagentes

Miniagente = **módulo operativo cerrado** que cumple la plantilla obligatoria
(`AGENT_SPECIFICATION_TEMPLATE.md`). No es una IA genérica: tiene contrato,
microacciones, tools aisladas, políticas y handoffs. Cline NO puede crear un
agente que no cumpla la plantilla.

## 01 WEB_RESEARCH_AGENT

```text
AGENT: WEB_RESEARCH_AGENT
VERSION: 1.0

PURPOSE:
Obtener información estructurada de fuentes web.

INPUT:
ResearchRequest {query: str, max_results?: int}

PIPELINE:
01 ResolveResearchIntent
02 GenerateSearchQueries
03 ExecuteSearch
04 RankSources
05 OpenSource
06 ExtractContent
07 ExtractEntities
08 NormalizeEntities
09 CrossValidate
10 GenerateResearchResult
11 ValidateOutput

ALLOWED TOOLS:
- WebSearch (web_search)
- Browser (web_scrape)
- URLFetcher (web_scrape)
- HTMLParser (web_scrape)

DECISION_RULES:
- Solo razonamiento en GenerateSearchQueries y RankSources (schema cerrado).
- El resto de pasos es determinista.

OUTPUT:
ResearchResult {findings: [Document], sources: [URL], confidence: float}

FAILURE STATES:
- SearchUnavailable
- SourceUnavailable
- ExtractionFailed
- ValidationFailed
- InsufficientEvidence

RETRY_POLICY: {"max_retries": 1, "backoff": 1.5, "retryable": ["SearchUnavailable", "SourceUnavailable"]}
TIMEOUT: 180s

PERMISSION_POLICY: {"roles": ["operator", "director"], "deny_by_default": true}
HUMAN_APPROVAL: no

HANDOFF:
ResearchResult → ANALYTICS_AGENT
ResearchResult → CONTENT_AGENT
ResearchResult → LEAD_GENERATION_AGENT

DEPENDENCIES: []
STATE_TRANSITIONS: pending → running → completed/failed
```

## 02 LEAD_GENERATION_AGENT

```text
AGENT: LEAD_GENERATION_AGENT
VERSION: 1.0

PURPOSE:
Convertir una audiencia objetivo en leads enriquecidos y clasificados en el CRM.

INPUT:
LeadRequest {segment: str, geographies: [str], value_prop: str, limit?: int}

PIPELINE:
01 RESEARCH_AGENT.handoff → ResearchResult
02 EnrichProspect
03 NormalizeData
04 ScoreLead
05 SegmentLeads
06 CreateLead (CRM)
07 GenerateOutreach (borrador, NO enviado)

ALLOWED TOOLS: web_search, web_scrape, api_crm.*, documentation_*
HUMAN_APPROVAL: CREAR LEAD en CRM requiere aprobación (configurable por tenant)

HANDOFF:
LeadsList → COMMUNICATION_AGENT (outreach)
LeadsList → ANALYTICS_AGENT (informe)
```

## 03 COMMUNICATION_AGENT

```text
AGENT: COMMUNICATION_AGENT
VERSION: 1.0

PURPOSE:
Redactar, revisar y enviar comunicaciones (email, mensajería, notificaciones).

INPUT:
CommunicationRequest {channels: [str], recipients: [str], brief: str, tone?: str}

PIPELINE:
01 GenerateBrief (razonamiento)
02 WriteEmail / WriteMessage (razonamiento)
03 ValidateOutput (schema)
04 ENVÍO → NEEDS_APPROVAL por defecto
05 SendEmail / SendMessage (tras aprobación)
06 TrackResponse / NotifyUser

ALLOWED TOOLS: gmail_send, gmail_read, slack_send, whatsapp_send, documentation_*
HUMAN_APPROVAL: SIEMPRE antes de enviar (por defecto)

HANDOFF:
SentConfirmation → CRM_AGENT (add_note)
SentConfirmation → SALES_AGENT (track_response)
```

## 04 DATA_ANALYSIS_AGENT

```text
AGENT: DATA_ANALYSIS_AGENT
VERSION: 1.0

PURPOSE:
Analizar datasets, validarlos y producir informes y KPIs.

INPUT:
DataAnalysisRequest {source: str, format?: str, questions?: [str]}

PIPELINE: data.analysis_pipeline (ver 09)

ALLOWED TOOLS: filesystem_*, database_*, web_scrape (solo lectura), documentation_*
HUMAN_APPROVAL: no (solo lectura; publicación de informes → approval)

HANDOFF:
Report → COMMUNICATION_AGENT (notify/send)
Report → CONTENT_AGENT (repurpose)
```

## 05 CONTENT_AGENT

```text
AGENT: CONTENT_AGENT
VERSION: 1.0

PURPOSE:
Producir contenidos en múltiples formatos desde un brief.

INPUT:
ContentRequest {goal: str, audience: str, format: [str], brand?: str}

PIPELINE: content.campaign_pipeline (ver 09)

ALLOWED TOOLS: documentation_*, web_search (fuentes), api_image_gen (creative)
HUMAN_APPROVAL: publicación (social/publish) → SIEMPRE

HANDOFF:
Assets → SOCIAL_AGENT / PUBLISHING_AGENT
Assets → COMMUNICATION_AGENT
```

## Reglas del catálogo

1. El catálogo es la **única fuente** de agentes. Cline implementa exactamente estos; ninguno más.
2. Cada agente referencia **exclusivamente** microacciones de `08` y pipelines de `09`.
3. Cada agente declara sus `HANDOFF`; un agente solo puede ser llamado si su id está en `HANDOFF` de otro (composición explícita, ver `19_AGENT_COMPOSITION.md`).
4. Añadir un agente nuevo requiere: especificación con la plantilla + test (ver `18_TESTING.md`) + no tocar `kernel/`.