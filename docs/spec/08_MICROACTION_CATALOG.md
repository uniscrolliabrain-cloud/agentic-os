# 08 — Catálogo de microacciones

> **EL CORAZÓN DEL SISTEMA.** Cada microacción es una operación atómica con
> contrato cerrado. Todo pipeline y todo miniagente se construye combinando
> estas microacciones. Las primeras familias (WEB, RESEARCH, DATA,
> COMMUNICATION, CRM/SALES, CONTENT) se documentan con contrato completo;
> el resto sigue exactamente el mismo patrón.

## Formato de una microacción

```text
ID: <familia>.<nombre>
ONTOLOGY: action=<ACTION>, entity=<ENTITY>, taxonomy=<FAMILIA>
PURPOSE: <qué consigue>
INPUT: <input schema>
PRECONDITIONS: <lista>
SOP/TOOL: <tool del registry>
OUTPUT: <output schema>
VALIDATION: <reglas QA>
ERROR_STATES: <lista>
HANDOFF: <microacciones/pipelines que pueden continuar>
TIMEOUT: <s> | RETRY: <política>
```

---

## Familia WEB

### 01 WEB.SearchWeb
- ONTOLOGY: action=Search, entity=URL, taxonomy=WEB
- PURPOSE: Buscar en la web y devolver resultados rankeados
- INPUT: `{query: str, max_results?: int=10}`
- PRECONDITIONS: query no vacía
- SOP/TOOL: `web_search`
- OUTPUT: `{results: [{title, url, snippet}]}`
- VALIDATION: resultados con URL válida; query devuelta en el output
- ERROR_STATES: `SearchUnavailable`
- HANDOFF: `web.open_url`, `web.extract_page`

### 02 WEB.OpenURL
- ONTOLOGY: action=Read, entity=URL, taxonomy=WEB
- PURPOSE: Abrir una URL y obtener su estado
- INPUT: `{url: str}`
- PRECONDITIONS: url tiene scheme http/https
- SOP/TOOL: `web_scrape`
- OUTPUT: `{url, status_code, title}`
- VALIDATION: status_code 200
- ERROR_STATES: `SourceUnavailable`
- HANDOFF: `web.extract_page`

### 03 WEB.ExtractPage
- ONTOLOGY: action=Read, entity=Document, taxonomy=WEB
- PURPOSE: Extraer el contenido estructurado de una página
- INPUT: `{url: str}`
- PRECONDITIONS: página accesible
- SOP/TOOL: `web_scrape`
- OUTPUT: `{url, text, links: [str], title}`
- VALIDATION: text no vacío
- ERROR_STATES: `ExtractionFailed`
- HANDOFF: `research.extract_entities`, `data.extract_data`, `documents.create_document`

### 04 WEB.ExtractMetadata
- ONTOLOGY: action=Read, entity=Website, taxonomy=WEB
- PURPOSE: Extraer metadatos (title, description, og:, canonical)
- INPUT: `{url: str}`
- SOP/TOOL: `web_scrape`
- OUTPUT: `{url, meta: dict}`
- HANDOFF: `research.cross_validate`

### 05 WEB.DetectChange
- ONTOLOGY: action=Monitor, entity=URL, taxonomy=WEB
- PURPOSE: Comprobar si una página cambió desde una firma previa
- INPUT: `{url: str, prev_hash?: str}`
- OUTPUT: `{changed: bool, new_hash: str}`
- ERROR_STATES: `SourceUnavailable`
- HANDOFF: `automation.monitor_workflow`

---

## Familia RESEARCH

### 01 RESEARCH.ResearchCompany
- ONTOLOGY: action=Search, entity=Company, taxonomy=RESEARCH
- PURPOSE: Investigar una empresa: datos, actividad, web, gente
- INPUT: `{company_name: str}`
- PRECONDITIONS: nombre no vacío
- SOP/TOOL: pipeline `research.research_company_pipeline`
- OUTPUT: `{company: Company, sources: [URL], summary: str}`
- VALIDATION: company con al menos nombre y una fuente
- ERROR_STATES: `InsufficientEvidence`, `ValidationFailed`
- HANDOFF: `research.build_research_report`, `crm.create_company`, `sales.enrich_prospect`

### 02 RESEARCH.ResearchPerson
- ONTOLOGY: action=Search, entity=Person, taxonomy=RESEARCH
- PURPOSE: Investigar una persona (rol, contacto, empresa)
- INPUT: `{full_name: str, company?: str}`
- SOP/TOOL: pipeline `research.research_person_pipeline`
- OUTPUT: `{person: Person, sources: [URL], summary: str}`
- ERROR_STATES: `InsufficientEvidence`
- HANDOFF: `research.verify_information`, `crm.create_contact`

### 03 RESEARCH.FactCheck
- ONTOLOGY: action=Validate, entity=Document, taxonomy=RESEARCH
- PURPOSE: Contrastar una afirmación contra varias fuentes
- INPUT: `{claim: str}`
- OUTPUT: `{claim, verdict: str, sources: [URL], confidence: float}`
- ERROR_STATES: `InsufficientEvidence`
- HANDOFF: `research.cross_validate`, `content.write_article`

### 04 RESEARCH.CrossValidate
- ONTOLOGY: action=Validate, entity=Dataset, taxonomy=RESEARCH
- PURPOSE: Confirmar datos con 2+ fuentes independientes
- INPUT: `{items: [{value, source}], min_sources: int=2}`
- OUTPUT: `{validated: [dict], conflicts: [dict]}`
- HANDOFF: `data.normalize_data`, `research.build_research_report`

### 05 RESEARCH.BuildResearchReport
- ONTOLOGY: action=Create, entity=Document, taxonomy=RESEARCH
- PURPOSE: Componer un informe de investigación estructurado
- INPUT: `{topic: str, findings: [dict], sources: [URL]}`
- SOP/TOOL: `documentation_create`
- OUTPUT: `{report: Document}`
- HANDOFF: `documents.convert_format`, `communication.create_email`

---

## Familia DATA

### 01 DATA.ExtractData
- ONTOLOGY: action=Read, entity=Dataset, taxonomy=DATA
- PURPOSE: Extraer datos estructurados de una fuente (CSV, PDF, web)
- INPUT: `{source: str, format?: str}`
- OUTPUT: `{dataset: Dataset}`
- ERROR_STATES: `ExtractionFailed`
- HANDOFF: `data.clean_data`

### 02 DATA.CleanData
- ONTOLOGY: action=Transform, entity=Dataset, taxonomy=DATA
- PURPOSE: Quitar duplicados, vacíos y errores de formato
- INPUT: `{dataset_id: str, rules?: [str]}`
- OUTPUT: `{dataset: Dataset, removed: int}`
- VALIDATION: schema del dataset intacto
- HANDOFF: `data.normalize_data`

### 03 DATA.NormalizeData
- ONTOLOGY: action=Transform, entity=Dataset, taxonomy=DATA
- PURPOSE: Estandarizar formatos (fechas, emails, teléfonos, mayúsculas)
- INPUT: `{dataset_id: str, columns: [str]}`
- OUTPUT: `{dataset: Dataset, changes: int}`
- HANDOFF: `data.deduplicate`

### 04 DATA.JoinDatasets
- ONTOLOGY: action=Transform, entity=Dataset, taxonomy=DATA
- PURPOSE: Combinar dos datasets por clave
- INPUT: `{left_id, right_id, on: str, how: str="inner"}`
- OUTPUT: `{dataset: Dataset}`
- ERROR_STATES: `ValidationFailed`
- HANDOFF: `data.aggregate_data`

### 05 DATA.ValidateData
- ONTOLOGY: action=Validate, entity=Dataset, taxonomy=DATA
- PURPOSE: Validar un dataset contra un schema
- INPUT: `{dataset_id, schema: dict}`
- OUTPUT: `{valid: bool, errors: [str]}`
- HANDOFF: `analytics.generate_report`, `data.export_data`

### 06 DATA.ExportData
- ONTOLOGY: action=Write, entity=File, taxonomy=DATA
- PURPOSE: Exportar dataset a fichero (CSV/JSON/Excel)
- INPUT: `{dataset_id, format: str}`
- OUTPUT: `{file: File}`
- HANDOFF: `documents.create_document`, `communication.notify_user`

---

## Familia COMMUNICATION

### 01 COMMUNICATION.CreateEmail
- ONTOLOGY: action=Create, entity=Email, taxonomy=COMMUNICATION
- PURPOSE: Redactar un email a partir de un brief
- INPUT: `{to: [str], subject?: str, brief: str, tone?: str}`
- SOP/TOOL: `content.write_email` (paso de razón del pipeline email)
- OUTPUT: `{email: Email}`
- HANDOFF: `communication.send_email`

### 02 COMMUNICATION.SendEmail
- ONTOLOGY: action=Communicate, entity=Email, taxonomy=COMMUNICATION
- PURPOSE: Enviar un email
- INPUT: `{to: [str], subject: str, body: str, cc?: [str]}`
- SOP/TOOL: `gmail_send`
- PRECONDITIONS: destinatarios con formato válido; **human_approval requerido por defecto**
- OUTPUT: `{status: str, message_id: str}`
- VALIDATION: message_id devuelto
- ERROR_STATES: `SendFailed`
- HANDOFF: `crm.add_note`, `sales.track_response`

### 03 COMMUNICATION.ReadEmail
- ONTOLOGY: action=Read, entity=Email, taxonomy=COMMUNICATION
- PURPOSE: Leer emails de la bandeja
- INPUT: `{max_results?: int=10, query?: str}`
- SOP/TOOL: `gmail_read`
- OUTPUT: `{emails: [Email]}`
- HANDOFF: `communication.classify_email`

### 04 COMMUNICATION.ClassifyEmail
- ONTOLOGY: action=Classify, entity=Email, taxonomy=COMMUNICATION
- PURPOSE: Clasificar un email (acción requerida / info / spam / urgente)
- INPUT: `{email: Email}`
- OUTPUT: `{category: str, priority: str, suggested_action?: str}`
- HANDOFF: `communication.reply_email`, `crm.create_task`

### 05 COMMUNICATION.NotifyUser
- ONTOLOGY: action=Communicate, entity=Message, taxonomy=COMMUNICATION
- PURPOSE: Avisar al usuario del resultado de una operación
- INPUT: `{channel: str, text: str}`
- OUTPUT: `{status: str}`
- HANDOFF: —

---

## Familia CRM / SALES

### 01 CRM.CreateContact
- ONTOLOGY: action=Create, entity=Person, taxonomy=CRM
- PURPOSE: Crear un contacto en el CRM
- INPUT: `{name: str, email?: str, phone?: str, company_id?: str}`
- SOP/TOOL: `api_crm.contacts` (API tool)
- OUTPUT: `{contact: Person}`
- HANDOFF: `crm.create_lead`

### 02 CRM.CreateLead
- ONTOLOGY: action=Create, entity=Task, taxonomy=CRM
- PURPOSE: Crear un lead a partir de un contacto o prospecto
- INPUT: `{contact_id, source: str, score?: int}`
- OUTPUT: `{lead_id: str}`
- HANDOFF: `sales.qualify_lead`

### 03 SALES.EnrichProspect
- ONTOLOGY: action=Search, entity=Company, taxonomy=SALES
- PURPOSE: Enriquecer un prospecto con datos públicos (web, red social, tamaño)
- INPUT: `{company_name: str, website?: str}`
- SOP/TOOL: pipeline `sales.enrich_prospect_pipeline`
- OUTPUT: `{company: Company, enrichment: dict}`
- HANDOFF: `sales.score_lead`, `crm.create_company`

### 04 SALES.GenerateOutreach
- ONTOLOGY: action=Create, entity=Email, taxonomy=SALES
- PURPOSE: Redactar mensaje de prospección personalizado
- INPUT: `{prospect: Company, value_prop: str, tone?: str}`
- OUTPUT: `{email: Email}`
- HANDOFF: `communication.send_email`

### 05 SALES.TrackResponse
- ONTOLOGY: action=Monitor, entity=Email, taxonomy=SALES
- PURPOSE: Detectar respuesta a un outreach
- INPUT: `{thread_id: str}`
- OUTPUT: `{answered: bool, reply?: Email}`
- HANDOFF: `sales.update_sequence`, `crm.add_note`

---

## Familia CONTENT

### 01 CONTENT.GenerateBrief
- ONTOLOGY: action=Create, entity=Document, taxonomy=CONTENT
- PURPOSE: Crear un brief de contenido a partir de un objetivo
- INPUT: `{goal: str, audience?: str, format?: str}`
- OUTPUT: `{brief: Document}`
- HANDOFF: `content.generate_outline`

### 02 CONTENT.GenerateOutline
- ONTOLOGY: action=Create, entity=Document, taxonomy=CONTENT
- PURPOSE: Generar esquema estructurado
- INPUT: `{brief: Document, max_sections?: int=6}`
- OUTPUT: `{outline: Document}`
- HANDOFF: `content.write_article`

### 03 CONTENT.WriteArticle
- ONTOLOGY: action=Create, entity=Document, taxonomy=CONTENT
- PURPOSE: Escribir un artículo a partir del esquema
- INPUT: `{outline: Document, sources?: [URL], tone?: str}`
- OUTPUT: `{article: Document}`
- VALIDATION: no fabricar datos fuera de sources
- HANDOFF: `content.summarize_content`, `content.repurpose_content`

### 04 CONTENT.SummarizeContent
- ONTOLOGY: action=Transform, entity=Document, taxonomy=CONTENT
- PURPOSE: Resumir contenido
- INPUT: `{document_id, max_words?: int}`
- OUTPUT: `{summary: Document}`
- HANDOFF: `communication.create_email`, `social.create_post`

---

## Resto de familias

`DOCUMENTS`, `CREATIVE`, `SOCIAL`, `MARKETING`, `SOFTWARE`, `DATABASE`,
`AUTOMATION`, `ANALYTICS` siguen **exactamente el mismo formato**. Su contenido
detallado se añade en iteraciones siguientes rellenando cada contrato sin
cambiar el patrón. El catálogo es un fichero vivo: se amplía por PR, nunca
rompiendo los ids ya publicados.