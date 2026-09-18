# 09 — Catálogo de pipelines

> **status:** diseno (aspiracional). Este fichero describe un diseno
> objetivo; no todas sus partes estan implementadas. Ver `docs/STATUS.md`.


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


---

# Correcciones C0.4 - Referencias normalizadas

> PENDIENTE DE REVISION HUMANA. Resuelve referencias rotas entre spec 09
> y spec 08 (marcadas como CONTRADICCION en AUDIT_MATRIX.md). No sustituye
> los pasos originales: solo declara el nombre canonico de cada uno.
>
> Estados:
> - OK: la microaccion existe en spec 08 con ese nombre.
> - REUSE: el paso se resuelve con otra microaccion de spec 08.
> - PENDIENTE_EXTENDER: no existe en spec 08. Se extendera en una
>   iteracion futura con aprobacion humana antes de implementarla.

| Referencia en pipeline (spec 09) | Canonico (spec 08) | Estado |
|---|---|---|
| research.resolve_entity | (no existe) | PENDIENTE_EXTENDER |
| web.search_web | web.search_web | OK |
| web.open_url | web.open_url | OK |
| web.extract_page | web.extract_page | OK |
| research.extract_company_data | research.research_company | REUSE |
| research.identify_people | research.research_person | REUSE |
| research.extract_contact_data | crm.create_contact | REUSE |
| research.verify_information | research.fact_check | REUSE |
| research.classify_company | (no existe) | PENDIENTE_EXTENDER |
| research.build_research_report | research.build_research_report | OK |
| data.normalize_data | data.normalize_data | OK |
| sales.score_lead | (no existe) | PENDIENTE_EXTENDER |
| crm.create_company | (no existe) | PENDIENTE_EXTENDER |
| crm.add_note | (no existe) | PENDIENTE_EXTENDER |
| sales.track_response | sales.track_response | OK |
| content.generate_brief | content.generate_brief | OK |
| content.write_email | communication.create_email | REUSE |
| communication.send_email | communication.send_email | OK |
| data.deduplicate | data.clean_data (parcial) | REUSE |
| data.extract_data | data.extract_data | OK |
| data.clean_data | data.clean_data | OK |
| data.validate_data | data.validate_data | OK |
| content.generate_outline | content.generate_outline | OK |
| content.write_article | content.write_article | OK |
| content.repurpose_content | (no existe) | PENDIENTE_EXTENDER |
| content.generate_metadata | (no existe) | PENDIENTE_EXTENDER |
| analytics.calculate_kpis | analytics.calculate_kpis | OK (nueva C0.4) |
| analytics.generate_chart | analytics.generate_chart | OK (nueva C0.4) |
| analytics.generate_report | analytics.generate_report | OK (nueva C0.4) |
| social.create_post | social.create_post | OK (nueva C0.4) |
| social.schedule_post | social.schedule_post | OK (nueva C0.4) |

## Resumen

- OK o REUSE: 25 referencias.
- PENDIENTE_EXTENDER: 6 (research.resolve_entity,
  research.classify_company, sales.score_lead, crm.create_company,
  crm.add_note, content.repurpose_content, content.generate_metadata).

## Consecuencia para C3-C4

- Los pipelines de spec 09 podran ejecutarse sobre microacciones
  existentes (OK + REUSE) en C3.
- Los PENDIENTE_EXTENDER se documentan antes de implementar el pipeline
  correspondiente (extension spec 08 + aprobacion).
- C3 (pipeline de referencia de agencia) solo usara microacciones OK
  o REUSE, nunca PENDIENTE_EXTENDER.
