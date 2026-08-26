# 09 — Catálogo de pipelines

Pipeline = secuencia **explícita y ordenada** de microacciones. Nada se ejecuta
fuera de un pipeline definido aquí (o en la librería de skills `cognition/skills/`).

## 01 research.research_company_pipeline

```text
PURPOSE: Investigar una empresa de forma estructurada
INPUT: ResearchCompanyRequest {company_name: str}

STEPS:
01 research.resolve_entity         → normaliza nombre
02 web.search_web                  → fuentes candidatas
03 web.open_url                    → valida cada fuente
04 web.extract_page                → extrae contenido
05 research.extract_company_data   → extrae campos de empresa
06 research.identify_people        → personas clave
07 research.extract_contact_data   → datos de contacto
08 research.verify_information     → cruza con 2+ fuentes
09 data.normalize_data             → estandariza
10 research.classify_company       → industria/tamaño
11 research.build_research_report  → compone informe

OUTPUT: ResearchResult {company, sources, summary}
```

## 02 sales.enrich_prospect_pipeline

```text
PURPOSE: Enriquecer un prospecto con datos públicos
INPUT: {company_name: str, website?: str}

01 web.search_web
02 web.open_url
03 web.extract_page
04 research.extract_company_data
05 data.normalize_data
06 crm.create_company          (si no existe)
07 sales.score_lead            → puntuación

OUTPUT: {company: Company, enrichment: dict, lead_score: int}
```

## 03 communication.email_pipeline

```text
PURPOSE: Redactar y enviar un email con revisión
INPUT: {to: [str], brief: str, tone?: str}

01 content.generate_brief      → de razonamiento (LLM)
02 content.write_email         → de razonamiento (LLM)
03 communication.send_email    → requiere aprobación humana
04 crm.add_note                → registra en CRM
05 sales.track_response        → (opcional, agendado)

OUTPUT: {message_id: str, status: str}
```

## 04 data.analysis_pipeline

```text
PURPOSE: Analizar un dataset y producir un informe
INPUT: {source: str, format?: str}

01 data.extract_data
02 data.clean_data
03 data.normalize_data
04 data.deduplicate
05 data.validate_data
06 analytics.calculate_kpis
07 analytics.generate_chart
08 analytics.generate_report

OUTPUT: {report: Document, dataset: Dataset}
```

## 05 content.campaign_pipeline

```text
PURPOSE: Generar una campaña de contenidos (multiformato)
INPUT: {goal: str, audience: str, brand?: str}

01 content.generate_brief
02 content.generate_outline
03 content.write_article
04 content.repurpose_content     → post social
05 content.generate_metadata     → SEO
06 social.create_post            → requiere aprobación
07 social.schedule_post
08 analytics.generate_report     → (opcional, tras publicación)

OUTPUT: {campaign_id: str, assets: [Document]}
```

## Reglas de pipeline

1. Todo `step` referencia un id existente en `08_MICROACTION_CATALOG.md`.
2. El output de un paso se valida contra su schema **antes** de pasarse al siguiente.
3. Los pasos marcados `de razonamiento (LLM)` son los ÚNICOS que pueden llamar a
   un LLM (con schema de salida cerrado). El resto es 100% determinista.
4. Ramificaciones solo vía `if_else` declarado en el `PipelineStep` (nunca "lógica libre").
5. Si un paso falla, se aplica `error_recovery` del pipeline o el estado pasa a `FAILED`/`BLOCKED` (ver `12_ERROR_HANDLING.md`).