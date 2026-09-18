# 08 — Catálogo de microacciones

> **status:** diseno (aspiracional). Este fichero describe un diseno
> objetivo; no todas sus partes estan implementadas. Ver `docs/STATUS.md`.


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


---

# Familias extendidas (C0.4 - propuesta)

> PENDIENTE DE REVISION HUMANA. Estas familias extienden spec 08 con
> el mismo formato que las 6 originales. Cada microaccion declara
> `STUB: true` si depende de una tool no implementada (y por tanto no
> se implementa en codigo hasta C7). Sin aprobacion explicita de C0.6,
> no se crea codigo para ellas (spec 00: no inventes acciones).

## Familia DOCUMENTS

### 01 DOCUMENTS.CreateDocument
- ONTOLOGY: action=Create, entity=Document, taxonomy=DOCUMENTS
- PURPOSE: Crear un documento con contenido inicial
- INPUT: `{title: str, content?: str, format?: str="md"}`
- PRECONDITIONS: title no vacio
- SOP/TOOL: documentation_create
- OUTPUT: `{document: Document}`
- VALIDATION: document.id asignado
- ERROR_STATES: CreationFailed
- HANDOFF: documents.read_document, documents.generate_pdf
- TIMEOUT: 30s | RETRY: {max_retries: 1}
- STUB: false

### 02 DOCUMENTS.ReadDocument
- ONTOLOGY: action=Read, entity=Document, taxonomy=DOCUMENTS
- PURPOSE: Leer el contenido de un documento existente
- INPUT: `{document_id: str}`
- PRECONDITIONS: document_id no vacio
- SOP/TOOL: drive_read_file
- OUTPUT: `{document: Document, content: str}`
- VALIDATION: content no vacio
- ERROR_STATES: NotFound, ReadFailed
- HANDOFF: documents.extract_text, data.extract_data
- TIMEOUT: 30s | RETRY: {max_retries: 1}
- STUB: false

### 03 DOCUMENTS.ExtractText
- ONTOLOGY: action=Read, entity=Document, taxonomy=DOCUMENTS
- PURPOSE: Extraer texto plano de un documento (PDF, DOCX, HTML)
- INPUT: `{document_id: str, ocr?: bool=False}`
- PRECONDITIONS: documento accesible
- SOP/TOOL: (pendiente tool documents_parse)
- OUTPUT: `{text: str, pages?: int}`
- VALIDATION: text no vacio
- ERROR_STATES: ExtractionFailed
- HANDOFF: content.summarize_content, data.extract_data
- TIMEOUT: 120s | RETRY: {max_retries: 1}
- STUB: true

### 04 DOCUMENTS.ConvertFormat
- ONTOLOGY: action=Transform, entity=Document, taxonomy=DOCUMENTS
- PURPOSE: Convertir documento entre formatos (md, pdf, docx, html)
- INPUT: `{document_id: str, to_format: str}`
- PRECONDITIONS: formato destino soportado
- SOP/TOOL: (pendiente tool documents_convert)
- OUTPUT: `{document: Document, format: str}`
- VALIDATION: format == to_format
- ERROR_STATES: ConversionFailed
- HANDOFF: communication.send_email, documents.generate_pdf
- TIMEOUT: 60s | RETRY: {max_retries: 1}
- STUB: true

### 05 DOCUMENTS.GeneratePDF
- ONTOLOGY: action=Create, entity=File, taxonomy=DOCUMENTS
- PURPOSE: Generar un PDF a partir de un documento
- INPUT: `{document_id: str, template?: str}`
- PRECONDITIONS: documento existente
- SOP/TOOL: (pendiente tool documents_generate_pdf)
- OUTPUT: `{file: File, url?: str}`
- VALIDATION: file.format == "pdf"
- ERROR_STATES: GenerationFailed
- HANDOFF: communication.send_email, documents.convert_format
- TIMEOUT: 60s | RETRY: {max_retries: 1}
- STUB: true

### 06 DOCUMENTS.GenerateDOCX
- ONTOLOGY: action=Create, entity=File, taxonomy=DOCUMENTS
- PURPOSE: Generar un DOCX a partir de un documento
- INPUT: `{document_id: str, template?: str}`
- PRECONDITIONS: documento existente
- SOP/TOOL: (pendiente tool documents_generate_docx)
- OUTPUT: `{file: File}`
- VALIDATION: file.format == "docx"
- ERROR_STATES: GenerationFailed
- HANDOFF: communication.send_email
- TIMEOUT: 60s | RETRY: {max_retries: 1}
- STUB: true

## Familia CREATIVE

### 01 CREATIVE.GenerateImage
- ONTOLOGY: action=Create, entity=Image, taxonomy=CREATIVE
- PURPOSE: Generar una imagen a partir de un prompt
- INPUT: `{prompt: str, size?: str="1024x1024", style?: str}`
- PRECONDITIONS: prompt no vacio
- SOP/TOOL: (pendiente connector ai.image.generate)
- OUTPUT: `{image: Image}`
- VALIDATION: image.url o image.path presente
- ERROR_STATES: GenerationFailed, ContentPolicyViolation
- HANDOFF: social.create_post, creative.edit_image
- TIMEOUT: 120s | RETRY: {max_retries: 1}
- STUB: true

### 02 CREATIVE.EditImage
- ONTOLOGY: action=Transform, entity=Image, taxonomy=CREATIVE
- PURPOSE: Editar una imagen (recortar, ajustar, filtrar)
- INPUT: `{image_id: str, operations: list[dict]}`
- PRECONDITIONS: image_id existente
- SOP/TOOL: (pendiente tool image_edit)
- OUTPUT: `{image: Image}`
- VALIDATION: image generada
- ERROR_STATES: EditFailed
- HANDOFF: social.create_post, creative.optimize_asset
- TIMEOUT: 60s | RETRY: {max_retries: 1}
- STUB: true

### 03 CREATIVE.GenerateVoice
- ONTOLOGY: action=Create, entity: Audio, taxonomy=CREATIVE
- PURPOSE: Generar audio de voz desde texto (TTS)
- INPUT: `{text: str, voice?: str, language?: str="es"}`
- PRECONDITIONS: text no vacio
- SOP/TOOL: (pendiente connector media.voice.generate)
- OUTPUT: `{audio: Audio}`
- VALIDATION: audio.url o audio.path presente
- ERROR_STATES: GenerationFailed
- HANDOFF: social.create_reel, communication.notify_user
- TIMEOUT: 90s | RETRY: {max_retries: 1}
- STUB: true

### 04 CREATIVE.GenerateBrandAsset
- ONTOLOGY: action=Create, entity=Image, taxonomy=CREATIVE
- PURPOSE: Generar asset de marca (logo, banner, icono)
- INPUT: `{brand_id: str, asset_type: str, prompt?: str}`
- PRECONDITIONS: brand_id existente
- SOP/TOOL: (pendiente connector ai.image.generate)
- OUTPUT: `{image: Image}`
- VALIDATION: image generada
- ERROR_STATES: GenerationFailed
- HANDOFF: social.create_post, marketing.create_campaign
- TIMEOUT: 120s | RETRY: {max_retries: 1}
- STUB: true

### 05 CREATIVE.OptimizeAsset
- ONTOLOGY: action=Transform, entity=Image, taxonomy=CREATIVE
- PURPOSE: Optimizar un asset (compresion, resize, formato webp)
- INPUT: `{asset_id: str, target_format?: str="webp", max_width?: int}`
- PRECONDITIONS: asset_id existente
- SOP/TOOL: (pendiente tool asset_optimize)
- OUTPUT: `{image: Image, size_bytes: int}`
- VALIDATION: size_bytes < original
- ERROR_STATES: OptimizationFailed
- HANDOFF: social.create_post, documents.generate_pdf
- TIMEOUT: 60s | RETRY: {max_retries: 1}
- STUB: true

## Familia SOCIAL

### 01 SOCIAL.CreatePost
- ONTOLOGY: action=Create, entity=SocialPost, taxonomy=SOCIAL
- PURPOSE: Crear un post en memoria (sin publicar)
- INPUT: `{platform: str, content: str, media?: list[str]}`
- PRECONDITIONS: platform soportada, content no vacio
- SOP/TOOL: (creacion de entidad, sin tool)
- OUTPUT: `{post: SocialPost}`
- VALIDATION: post.id asignado
- ERROR_STATES: ValidationFailed
- HANDOFF: social.schedule_post, social.publish_post
- TIMEOUT: 10s | RETRY: {max_retries: 0}
- STUB: false

### 02 SOCIAL.GenerateCaption
- ONTOLOGY: action=Create, entity=SocialPost, taxonomy=SOCIAL
- PURPOSE: Generar caption a partir de un brief con el LLM
- INPUT: `{brief: str, tone?: str, platform: str}`
- PRECONDITIONS: brief no vacio
- SOP/TOOL: (LLM via cognition.reasoning.proposer)
- OUTPUT: `{caption: str, hashtags?: list[str]}`
- VALIDATION: caption no vacio
- ERROR_STATES: GenerationFailed
- HANDOFF: social.create_post
- TIMEOUT: 30s | RETRY: {max_retries: 1}
- STUB: false

### 03 SOCIAL.GenerateHashtags
- ONTOLOGY: action=Create, entity=SocialPost, taxonomy=SOCIAL
- PURPOSE: Generar hashtags relevantes para un contenido
- INPUT: `{content: str, platform: str, max_tags?: int=15}`
- PRECONDITIONS: content no vacio
- SOP/TOOL: (LLM)
- OUTPUT: `{hashtags: list[str]}`
- VALIDATION: 3 <= len(hashtags) <= max_tags
- ERROR_STATES: GenerationFailed
- HANDOFF: social.create_post
- TIMEOUT: 30s | RETRY: {max_retries: 1}
- STUB: false

### 04 SOCIAL.SchedulePost
- ONTOLOGY: action=Create, entity=Task, taxonomy=SOCIAL
- PURPOSE: Programar un post para una fecha/hora
- INPUT: `{post_id: str, scheduled_at: str}`
- PRECONDITIONS: post_id existente, scheduled_at ISO 8601
- SOP/TOOL: scheduler_create_job
- OUTPUT: `{task_id: str, scheduled_at: str}`
- VALIDATION: task_id asignado
- ERROR_STATES: SchedulingFailed
- HANDOFF: social.publish_post
- TIMEOUT: 15s | RETRY: {max_retries: 1}
- STUB: false

### 05 SOCIAL.PublishPost
- ONTOLOGY: action=Publish, entity=SocialPost, taxonomy=SOCIAL
- PURPOSE: Publicar un post (requiere aprobacion humana)
- INPUT: `{post_id: str, channel: str}`
- PRECONDITIONS: post_id existente, aprobacion humana
- SOP/TOOL: meta_post_publish (SIMULATED)
- OUTPUT: `{status: str, external_id: str}`
- VALIDATION: status en {published, simulated}
- ERROR_STATES: PublishFailed, RateLimited
- HANDOFF: social.retrieve_metrics, analytics.collect_metrics
- TIMEOUT: 60s | RETRY: {max_retries: 2}
- STUB: false

### 06 SOCIAL.RetrieveMetrics
- ONTOLOGY: action=Read, entity: Dataset, taxonomy=SOCIAL
- PURPOSE: Recuperar metricas de un post publicado
- INPUT: `{post_id: str, period?: str="7d"}`
- PRECONDITIONS: post_id existente y publicado
- SOP/TOOL: (pendiente connector social.metrics.get)
- OUTPUT: `{metrics: Dataset}`
- VALIDATION: metrics.columns no vacio
- ERROR_STATES: MetricsUnavailable
- HANDOFF: analytics.calculate_kpis, analytics.generate_report
- TIMEOUT: 30s | RETRY: {max_retries: 1}
- STUB: true


## Familia MARKETING

### 01 MARKETING.DefineAudience
- ONTOLOGY: action=Create, entity=Dataset, taxonomy=MARKETING
- PURPOSE: Definir la audiencia objetivo de una campana
- INPUT: `{segment: str, geographies: list[str], demographics?: dict}`
- PRECONDITIONS: segment no vacio
- SOP/TOOL: (creacion de entidad, sin tool externa)
- OUTPUT: `{audience: Dataset}`
- VALIDATION: audience.columns no vacio
- ERROR_STATES: ValidationFailed
- HANDOFF: marketing.create_offer, marketing.create_campaign
- TIMEOUT: 30s | RETRY: {max_retries: 0}
- STUB: false

### 02 MARKETING.DefinePositioning
- ONTOLOGY: action=Create, entity=Document, taxonomy=MARKETING
- PURPOSE: Definir el posicionamiento (value prop) de una marca
- INPUT: `{brand_id: str, competitive_landscape?: str}`
- PRECONDITIONS: brand_id existente
- SOP/TOOL: (LLM)
- OUTPUT: `{positioning: Document}`
- VALIDATION: positioning.content no vacio
- ERROR_STATES: GenerationFailed
- HANDOFF: marketing.create_offer, content.generate_brief
- TIMEOUT: 60s | RETRY: {max_retries: 1}
- STUB: false

### 03 MARKETING.CreateOffer
- ONTOLOGY: action=Create, entity=Document, taxonomy=MARKETING
- PURPOSE: Crear una oferta comercial a partir de posicionamiento
- INPUT: `{positioning_id: str, price_range?: dict}`
- PRECONDITIONS: positioning_id existente
- SOP/TOOL: (LLM)
- OUTPUT: `{offer: Document}`
- VALIDATION: offer.content no vacio
- ERROR_STATES: GenerationFailed
- HANDOFF: marketing.create_campaign, content.generate_brief
- TIMEOUT: 60s | RETRY: {max_retries: 1}
- STUB: false

### 04 MARKETING.CreateCampaign
- ONTOLOGY: action=Create, entity=Document, taxonomy=MARKETING
- PURPOSE: Crear una campana de marketing con brief ejecutable
- INPUT: `{audience_id: str, offer_id: str, channels: list[str], budget?: float}`
- PRECONDITIONS: audience_id y offer_id existentes
- SOP/TOOL: (LLM + creacion de entidad)
- OUTPUT: `{campaign: Document, plan: Dataset}`
- VALIDATION: campaign.content no vacio
- ERROR_STATES: ValidationFailed
- HANDOFF: content.campaign_pipeline, analytics.generate_report
- TIMEOUT: 90s | RETRY: {max_retries: 1}
- STUB: false

### 05 MARKETING.GenerateAdVariants
- ONTOLOGY: action=Create, entity=Document, taxonomy=MARKETING
- PURPOSE: Generar variantes de anuncio para A/B testing
- INPUT: `{campaign_id: str, n_variants: int=3, max_chars?: int}`
- PRECONDITIONS: campaign_id existente
- SOP/TOOL: (LLM)
- OUTPUT: `{variants: list[Document]}`
- VALIDATION: len(variants) == n_variants
- ERROR_STATES: GenerationFailed
- HANDOFF: social.publish_post, ads.campaign.create
- TIMEOUT: 90s | RETRY: {max_retries: 1}
- STUB: false

### 06 MARKETING.AnalyzeCampaign
- ONTOLOGY: action=Analyze, entity=Dataset, taxonomy=MARKETING
- PURPOSE: Analizar resultados de una campana
- INPUT: `{campaign_id: str, period?: str="30d"}`
- PRECONDITIONS: campaign_id existente y con datos
- SOP/TOOL: (pendiente connector ads.insights.get)
- OUTPUT: `{metrics: Dataset, recommendations: list[str]}`
- VALIDATION: metrics.columns no vacio
- ERROR_STATES: MetricsUnavailable
- HANDOFF: analytics.generate_report, marketing.optimize_campaign
- TIMEOUT: 60s | RETRY: {max_retries: 1}
- STUB: true

## Familia SOFTWARE

### 01 SOFTWARE.InspectRepository
- ONTOLOGY: action=Read, entity=File, taxonomy=SOFTWARE
- PURPOSE: Inspeccionar la estructura de un repositorio
- INPUT: `{path?: str="."}`
- PRECONDITIONS: path dentro del repo permitido por policy
- SOP/TOOL: repo_scan
- OUTPUT: `{tree: dict, file_count: int, by_suffix: dict}`
- VALIDATION: file_count >= 0
- ERROR_STATES: AccessDenied
- HANDOFF: software.read_code, software.inspect_schema
- TIMEOUT: 30s | RETRY: {max_retries: 1}
- STUB: false

### 02 SOFTWARE.ReadCode
- ONTOLOGY: action=Read, entity=File, taxonomy=SOFTWARE
- PURPOSE: Leer un fichero de codigo del repositorio
- INPUT: `{path: str}`
- PRECONDITIONS: path dentro del repo permitido por policy
- SOP/TOOL: repo_file_read
- OUTPUT: `{file: File, content: str}`
- VALIDATION: content no vacio
- ERROR_STATES: NotFound, AccessDenied
- HANDOFF: software.refactor_code, software.generate_tests
- TIMEOUT: 30s | RETRY: {max_retries: 1}
- STUB: false

### 03 SOFTWARE.WriteCode
- ONTOLOGY: action=Write, entity=File, taxonomy=SOFTWARE
- PURPOSE: Escribir o modificar un fichero de codigo (requiere aprobacion humana)
- INPUT: `{path: str, content: str, mode?: str="overwrite"}`
- PRECONDITIONS: path dentro del repo permitido por policy, aprobacion humana
- SOP/TOOL: repo_file_write (pendiente, gate humano)
- OUTPUT: `{file: File, written: bool}`
- VALIDATION: file.hash != previo (si mode=overwrite)
- ERROR_STATES: AccessDenied, WriteFailed
- HANDOFF: software.run_tests, software.commit_create
- TIMEOUT: 30s | RETRY: {max_retries: 0}
- STUB: true

### 04 SOFTWARE.RunTests
- ONTOLOGY: action=Execute, entity=Task, taxonomy=SOFTWARE
- PURPOSE: Ejecutar la suite de tests del proyecto
- INPUT: `{path?: str, selector?: str}`
- PRECONDITIONS: runner disponible (pytest, jest, ...)
- SOP/TOOL: (pendiente tool tests_run, ejecucion en sandbox)
- OUTPUT: `{passed: int, failed: int, output: str}`
- VALIDATION: passed + failed >= 0
- ERROR_STATES: RunnerUnavailable, ExecutionFailed
- HANDOFF: software.commit_create, software.debug
- TIMEOUT: 600s | RETRY: {max_retries: 0}
- STUB: true

### 05 SOFTWARE.CommitCreate
- ONTOLOGY: action=Write, entity=Task, taxonomy=SOFTWARE
- PURPOSE: Crear un commit con los cambios (requiere aprobacion humana)
- INPUT: `{message: str, files: list[str], branch?: str}`
- PRECONDITIONS: cambios staged, aprobacion humana
- SOP/TOOL: (pendiente tool git_commit, gate humano)
- OUTPUT: `{commit_sha: str, branch: str}`
- VALIDATION: commit_sha no vacio
- ERROR_STATES: CommitFailed, BranchProtected
- HANDOFF: software.push, software.pull_request_create
- TIMEOUT: 30s | RETRY: {max_retries: 0}
- STUB: true

### 06 SOFTWARE.PullRequestCreate
- ONTOLOGY: action=Create, entity=Task, taxonomy=SOFTWARE
- PURPOSE: Abrir un pull request desde una rama
- INPUT: `{title: str, body: str, head: str, base?: str="master"}`
- PRECONDITIONS: head != base, aprobacion humana
- SOP/TOOL: (pendiente connector software.pull_request.create)
- OUTPUT: `{pr_id: str, url: str}`
- VALIDATION: url http(s)
- ERROR_STATES: CreationFailed
- HANDOFF: communication.notify_user
- TIMEOUT: 30s | RETRY: {max_retries: 1}
- STUB: true

## Familia DATABASE

### 01 DATABASE.InspectSchema
- ONTOLOGY: action=Read, entity=Dataset, taxonomy=DATABASE
- PURPOSE: Inspeccionar el schema de una base de datos
- INPUT: `{connection_id: str}`
- PRECONDITIONS: connection_id existente y autorizada
- SOP/TOOL: (pendiente connector database.schema.inspect)
- OUTPUT: `{tables: list[dict], schema_version?: str}`
- VALIDATION: tables list
- ERROR_STATES: ConnectionFailed, AccessDenied
- HANDOFF: database.query_database, data.analyze
- TIMEOUT: 30s | RETRY: {max_retries: 1}
- STUB: true

### 02 DATABASE.QueryDatabase
- ONTOLOGY: action=Read, entity=Dataset, taxonomy=DATABASE
- PURPOSE: Ejecutar una consulta de lectura (SELECT parametrizado)
- INPUT: `{connection_id: str, query: str, params?: dict, limit?: int=1000}`
- PRECONDITIONS: query empieza por SELECT, connection_id autorizada
- SOP/TOOL: (pendiente connector database.query)
- OUTPUT: `{dataset: Dataset}`
- VALIDATION: solo SELECT (nunca INSERT/UPDATE/DELETE desde este id)
- ERROR_STATES: QueryFailed, AccessDenied, QueryTooBroad
- HANDOFF: data.clean_data, analytics.calculate_kpis
- TIMEOUT: 60s | RETRY: {max_retries: 1}
- STUB: true

### 03 DATABASE.InsertRecord
- ONTOLOGY: action=Create, entity=Dataset, taxonomy=DATABASE
- PURPOSE: Insertar un registro en una tabla (requiere aprobacion humana)
- INPUT: `{connection_id: str, table: str, values: dict}`
- PRECONDITIONS: tabla existente, aprobacion humana
- SOP/TOOL: (pendiente connector database.record.create)
- OUTPUT: `{row_id: str, inserted: int}`
- VALIDATION: inserted >= 1
- ERROR_STATES: InsertFailed, ConstraintViolation
- HANDOFF: analytics.collect_metrics
- TIMEOUT: 30s | RETRY: {max_retries: 0}
- STUB: true

### 04 DATABASE.UpdateRecord
- ONTOLOGY: action=Update, entity=Dataset, taxonomy=DATABASE
- PURPOSE: Actualizar registros (requiere aprobacion humana)
- INPUT: `{connection_id: str, table: str, filters: dict, changes: dict}`
- PRECONDITIONS: al menos un filtro no vacio, aprobacion humana
- SOP/TOOL: (pendiente connector database.record.update)
- OUTPUT: `{updated: int}`
- VALIDATION: updated >= 0
- ERROR_STATES: UpdateFailed, ConstraintViolation
- HANDOFF: analytics.collect_metrics
- TIMEOUT: 30s | RETRY: {max_retries: 0}
- STUB: true

### 05 DATABASE.BackupDatabase
- ONTOLOGY: action=Execute, entity=File, taxonomy=DATABASE
- PURPOSE: Generar un backup de la base de datos
- INPUT: `{connection_id: str, target_path: str}`
- PRECONDITIONS: connection_id autorizada, target_path escribible
- SOP/TOOL: (pendiente tool database_backup)
- OUTPUT: `{file: File, size_bytes: int}`
- VALIDATION: file.path == target_path
- ERROR_STATES: BackupFailed, InsufficientSpace
- HANDOFF: storage.upload, communication.notify_user
- TIMEOUT: 1800s | RETRY: {max_retries: 0}
- STUB: true

### 06 DATABASE.MigrateDatabase
- ONTOLOGY: action=Execute, entity=Task, taxonomy=DATABASE
- PURPOSE: Aplicar migraciones de schema (requiere aprobacion humana)
- INPUT: `{connection_id: str, migration_id: str, dry_run?: bool=True}`
- PRECONDITIONS: migracion existente, aprobacion humana
- SOP/TOOL: (pendiente tool database_migrate)
- OUTPUT: `{applied: bool, applied_at: str}`
- VALIDATION: applied es bool
- ERROR_STATES: MigrationFailed, RollbackTriggered
- HANDOFF: database.inspect_schema, communication.notify_user
- TIMEOUT: 600s | RETRY: {max_retries: 0}
- STUB: true


## Familia AUTOMATION

### 01 AUTOMATION.CreateWorkflow
- ONTOLOGY: action=Create, entity=Task, taxonomy=AUTOMATION
- PURPOSE: Definir un workflow como secuencia de pasos
- INPUT: `{name: str, steps: list[dict]}`
- PRECONDITIONS: al menos 1 step
- SOP/TOOL: (creacion de entidad, sin tool)
- OUTPUT: `{workflow_id: str}`
- VALIDATION: workflow_id asignado
- ERROR_STATES: ValidationFailed
- HANDOFF: automation.trigger_workflow, automation.schedule_workflow
- TIMEOUT: 15s | RETRY: {max_retries: 0}
- STUB: false

### 02 AUTOMATION.TriggerWorkflow
- ONTOLOGY: action=Execute, entity=Task, taxonomy=AUTOMATION
- PURPOSE: Disparar un workflow existente
- INPUT: `{workflow_id: str, params?: dict}`
- PRECONDITIONS: workflow_id existente y no archivado
- SOP/TOOL: (pendiente tool workflow_trigger)
- OUTPUT: `{run_id: str, status: str}`
- VALIDATION: run_id asignado
- ERROR_STATES: TriggerFailed, WorkflowDisabled
- HANDOFF: automation.monitor_workflow
- TIMEOUT: 30s | RETRY: {max_retries: 1}
- STUB: true

### 03 AUTOMATION.ScheduleWorkflow
- ONTOLOGY: action=Create, entity=Task, taxonomy=AUTOMATION
- PURPOSE: Programar un workflow (cron o intervalo)
- INPUT: `{workflow_id: str, cron?: str, interval_minutes?: int}`
- PRECONDITIONS: workflow_id existente
- SOP/TOOL: scheduler_create_job
- OUTPUT: `{schedule_id: str, next_run_at: str}`
- VALIDATION: schedule_id asignado
- ERROR_STATES: SchedulingFailed
- HANDOFF: automation.monitor_workflow
- TIMEOUT: 15s | RETRY: {max_retries: 1}
- STUB: false

### 04 AUTOMATION.RouteTask
- ONTOLOGY: action=Execute, entity=Task, taxonomy=AUTOMATION
- PURPOSE: Enrutar una tarea al agente o tool correspondiente
- INPUT: `{task_id: str, routing_key: str}`
- PRECONDITIONS: routing_key en la tabla de rutas
- SOP/TOOL: (pendiente tool task_router)
- OUTPUT: `{assigned_to: str, task_id: str}`
- VALIDATION: assigned_to no vacio
- ERROR_STATES: NoRouteFound
- HANDOFF: automation.transform_payload, communication.notify_user
- TIMEOUT: 15s | RETRY: {max_retries: 1}
- STUB: true

### 05 AUTOMATION.TransformPayload
- ONTOLOGY: action=Transform, entity=Dataset, taxonomy=AUTOMATION
- PURPOSE: Transformar un payload segun un mapping declarado
- INPUT: `{payload: dict, mapping: dict}`
- PRECONDITIONS: mapping no vacio
- SOP/TOOL: (funcion pura, sin tool externa)
- OUTPUT: `{payload: dict}`
- VALIDATION: payload tiene las claves del mapping
- ERROR_STATES: TransformFailed
- HANDOFF: automation.call_api, communication.notify_user
- TIMEOUT: 10s | RETRY: {max_retries: 0}
- STUB: false

### 06 AUTOMATION.MonitorWorkflow
- ONTOLOGY: action=Monitor, entity=Task, taxonomy=AUTOMATION
- PURPOSE: Consultar el estado de un run
- INPUT: `{run_id: str}`
- PRECONDITIONS: run_id existente
- SOP/TOOL: (pendiente tool workflow_status)
- OUTPUT: `{status: str, steps_done: int, steps_total: int}`
- VALIDATION: status en {running, completed, failed, cancelled}
- ERROR_STATES: NotFound
- HANDOFF: communication.notify_user, analytics.collect_metrics
- TIMEOUT: 15s | RETRY: {max_retries: 1}
- STUB: true

## Familia ANALYTICS

### 01 ANALYTICS.CollectMetrics
- ONTOLOGY: action=Read, entity=Dataset, taxonomy=ANALYTICS
- PURPOSE: Recoger metricas de una o varias fuentes
- INPUT: `{source: str, period: str, metrics: list[str]}`
- PRECONDITIONS: source autorizado por policy
- SOP/TOOL: (pendiente connector analytics.metrics.get)
- OUTPUT: `{dataset: Dataset}`
- VALIDATION: dataset.columns no vacio
- ERROR_STATES: MetricsUnavailable, AccessDenied
- HANDOFF: analytics.calculate_kpis, analytics.detect_anomaly
- TIMEOUT: 60s | RETRY: {max_retries: 1}
- STUB: true

### 02 ANALYTICS.CalculateKPIs
- ONTOLOGY: action=Analyze, entity=Dataset, taxonomy=ANALYTICS
- PURPOSE: Calcular KPIs sobre un dataset de metricas
- INPUT: `{dataset_id: str, kpi_definitions: list[dict]}`
- PRECONDITIONS: kpi_definitions no vacio
- SOP/TOOL: (funcion pura, sin tool externa)
- OUTPUT: `{kpis: Dataset}`
- VALIDATION: kpis.columns incluye cada kpi definido
- ERROR_STATES: CalculationFailed
- HANDOFF: analytics.generate_chart, analytics.generate_report
- TIMEOUT: 30s | RETRY: {max_retries: 0}
- STUB: false

### 03 ANALYTICS.DetectAnomaly
- ONTOLOGY: action=Analyze, entity=Dataset, taxonomy=ANALYTICS
- PURPOSE: Detectar anomalias en una serie temporal
- INPUT: `{dataset_id: str, method?: str="zscore", threshold?: float=3.0}`
- PRECONDITIONS: dataset_id existente y con columna temporal
- SOP/TOOL: (funcion pura, sin tool externa)
- OUTPUT: `{anomalies: Dataset, count: int}`
- VALIDATION: count >= 0
- ERROR_STATES: InsufficientData
- HANDOFF: analytics.generate_report, communication.notify_user
- TIMEOUT: 30s | RETRY: {max_retries: 0}
- STUB: false

### 04 ANALYTICS.ComparePeriods
- ONTOLOGY: action=Analyze, entity=Dataset, taxonomy=ANALYTICS
- PURPOSE: Comparar dos periodos de tiempo
- INPUT: `{dataset_id: str, period_a: str, period_b: str, metric: str}`
- PRECONDITIONS: periodos no solapados
- SOP/TOOL: (funcion pura, sin tool externa)
- OUTPUT: `{delta: float, delta_pct: float, summary: str}`
- VALIDATION: delta es float
- ERROR_STATES: InsufficientData
- HANDOFF: analytics.generate_report, content.write_article
- TIMEOUT: 30s | RETRY: {max_retries: 0}
- STUB: false

### 05 ANALYTICS.GenerateChart
- ONTOLOGY: action=Create, entity=Image, taxonomy=ANALYTICS
- PURPOSE: Generar un grafico a partir de un dataset
- INPUT: `{dataset_id: str, chart_type: str, x: str, y: str}`
- PRECONDITIONS: columnas x e y existen
- SOP/TOOL: (pendiente tool chart_generate)
- OUTPUT: `{image: Image}`
- VALIDATION: image.url o image.path presente
- ERROR_STATES: ChartFailed
- HANDOFF: analytics.generate_report, communication.send_email
- TIMEOUT: 60s | RETRY: {max_retries: 1}
- STUB: true

### 06 ANALYTICS.GenerateReport
- ONTOLOGY: action=Create, entity=Document, taxonomy=ANALYTICS
- PURPOSE: Componer un informe con KPIs, graficos y narrativa
- INPUT: `{dataset_ids: list[str], audience?: str, format?: str="md"}`
- PRECONDITIONS: dataset_ids no vacio
- SOP/TOOL: documentation_create + LLM
- OUTPUT: `{report: Document}`
- VALIDATION: report.content no vacio
- ERROR_STATES: GenerationFailed
- HANDOFF: communication.send_email, documents.generate_pdf
- TIMEOUT: 90s | RETRY: {max_retries: 1}
- STUB: false

### 07 ANALYTICS.GenerateRecommendation
- ONTOLOGY: action=Create, entity=Document, taxonomy=ANALYTICS
- PURPOSE: Generar una recomendacion accionable a partir de un informe
- INPUT: `{report_id: str, goal?: str}`
- PRECONDITIONS: report_id existente
- SOP/TOOL: (LLM)
- OUTPUT: `{recommendation: Document, priority: str}`
- VALIDATION: priority en {low, medium, high}
- ERROR_STATES: GenerationFailed
- HANDOFF: communication.notify_user, automation.trigger_workflow
- TIMEOUT: 60s | RETRY: {max_retries: 1}
- STUB: false

## Familias futuras (esqueleto, sin microacciones)

Estas familias estan declaradas en spec 02 pero no se expanden en C0.4.
Se rellenaran cuando haya una necesidad real y un caso de uso validado.
Su estructura sigue exactamente el mismo formato que las anteriores.

- CALENDAR
- PROJECT_MANAGEMENT
- CLOUD
- AUTH
- PAYMENTS
- ECOMMERCE
- SUPPORT
- KNOWLEDGE_BASE/RAG
- VECTOR_DB
- FILESYSTEM
- GIT
- API_GATEWAY
- NOTIFICATIONS
- FORMS
- SCHEDULING
- COMPLIANCE

## Nota de cierre de C0.4

Con esta extension, spec 08 cubre las 15 familias declaradas en spec 02.
Cada microaccion declara `STUB: true` si depende de una tool o conector
no implementado (por tanto NO se implementa en codigo hasta C7).

Total de microacciones propuestas en esta extension: ~65.
Todas PENDIENTES DE REVISION HUMANA (C0.6).


## Familia AUTOMATION

### 01 AUTOMATION.CreateWorkflow
- ONTOLOGY: action=Create, entity=Task, taxonomy=AUTOMATION
- PURPOSE: Definir un workflow como secuencia de pasos
- INPUT: `{name: str, steps: list[dict]}`
- PRECONDITIONS: al menos 1 step
- SOP/TOOL: (creacion de entidad, sin tool)
- OUTPUT: `{workflow_id: str}`
- VALIDATION: workflow_id asignado
- ERROR_STATES: ValidationFailed
- HANDOFF: automation.trigger_workflow, automation.schedule_workflow
- TIMEOUT: 15s | RETRY: {max_retries: 0}
- STUB: false

### 02 AUTOMATION.TriggerWorkflow
- ONTOLOGY: action=Execute, entity=Task, taxonomy=AUTOMATION
- PURPOSE: Disparar un workflow existente
- INPUT: `{workflow_id: str, params?: dict}`
- PRECONDITIONS: workflow_id existente y no archivado
- SOP/TOOL: (pendiente tool workflow_trigger)
- OUTPUT: `{run_id: str, status: str}`
- VALIDATION: run_id asignado
- ERROR_STATES: TriggerFailed, WorkflowDisabled
- HANDOFF: automation.monitor_workflow
- TIMEOUT: 30s | RETRY: {max_retries: 1}
- STUB: true

### 03 AUTOMATION.ScheduleWorkflow
- ONTOLOGY: action=Create, entity=Task, taxonomy=AUTOMATION
- PURPOSE: Programar un workflow (cron o intervalo)
- INPUT: `{workflow_id: str, cron?: str, interval_minutes?: int}`
- PRECONDITIONS: workflow_id existente
- SOP/TOOL: scheduler_create_job
- OUTPUT: `{schedule_id: str, next_run_at: str}`
- VALIDATION: schedule_id asignado
- ERROR_STATES: SchedulingFailed
- HANDOFF: automation.monitor_workflow
- TIMEOUT: 15s | RETRY: {max_retries: 1}
- STUB: false

### 04 AUTOMATION.RouteTask
- ONTOLOGY: action=Execute, entity=Task, taxonomy=AUTOMATION
- PURPOSE: Enrutar una tarea al agente o tool correspondiente
- INPUT: `{task_id: str, routing_key: str}`
- PRECONDITIONS: routing_key en la tabla de rutas
- SOP/TOOL: (pendiente tool task_router)
- OUTPUT: `{assigned_to: str, task_id: str}`
- VALIDATION: assigned_to no vacio
- ERROR_STATES: NoRouteFound
- HANDOFF: automation.transform_payload, communication.notify_user
- TIMEOUT: 15s | RETRY: {max_retries: 1}
- STUB: true

### 05 AUTOMATION.TransformPayload
- ONTOLOGY: action=Transform, entity=Dataset, taxonomy=AUTOMATION
- PURPOSE: Transformar un payload segun un mapping declarado
- INPUT: `{payload: dict, mapping: dict}`
- PRECONDITIONS: mapping no vacio
- SOP/TOOL: (funcion pura, sin tool externa)
- OUTPUT: `{payload: dict}`
- VALIDATION: payload tiene las claves del mapping
- ERROR_STATES: TransformFailed
- HANDOFF: automation.call_api, communication.notify_user
- TIMEOUT: 10s | RETRY: {max_retries: 0}
- STUB: false

### 06 AUTOMATION.MonitorWorkflow
- ONTOLOGY: action=Monitor, entity=Task, taxonomy=AUTOMATION
- PURPOSE: Consultar el estado de un run
- INPUT: `{run_id: str}`
- PRECONDITIONS: run_id existente
- SOP/TOOL: (pendiente tool workflow_status)
- OUTPUT: `{status: str, steps_done: int, steps_total: int}`
- VALIDATION: status en {running, completed, failed, cancelled}
- ERROR_STATES: NotFound
- HANDOFF: communication.notify_user, analytics.collect_metrics
- TIMEOUT: 15s | RETRY: {max_retries: 1}
- STUB: true

## Familia ANALYTICS

### 01 ANALYTICS.CollectMetrics
- ONTOLOGY: action=Read, entity=Dataset, taxonomy=ANALYTICS
- PURPOSE: Recoger metricas de una o varias fuentes
- INPUT: `{source: str, period: str, metrics: list[str]}`
- PRECONDITIONS: source autorizado por policy
- SOP/TOOL: (pendiente connector analytics.metrics.get)
- OUTPUT: `{dataset: Dataset}`
- VALIDATION: dataset.columns no vacio
- ERROR_STATES: MetricsUnavailable, AccessDenied
- HANDOFF: analytics.calculate_kpis, analytics.detect_anomaly
- TIMEOUT: 60s | RETRY: {max_retries: 1}
- STUB: true

### 02 ANALYTICS.CalculateKPIs
- ONTOLOGY: action=Analyze, entity=Dataset, taxonomy=ANALYTICS
- PURPOSE: Calcular KPIs sobre un dataset de metricas
- INPUT: `{dataset_id: str, kpi_definitions: list[dict]}`
- PRECONDITIONS: kpi_definitions no vacio
- SOP/TOOL: (funcion pura, sin tool externa)
- OUTPUT: `{kpis: Dataset}`
- VALIDATION: kpis.columns incluye cada kpi definido
- ERROR_STATES: CalculationFailed
- HANDOFF: analytics.generate_chart, analytics.generate_report
- TIMEOUT: 30s | RETRY: {max_retries: 0}
- STUB: false

### 03 ANALYTICS.DetectAnomaly
- ONTOLOGY: action=Analyze, entity=Dataset, taxonomy=ANALYTICS
- PURPOSE: Detectar anomalias en una serie temporal
- INPUT: `{dataset_id: str, method?: str="zscore", threshold?: float=3.0}`
- PRECONDITIONS: dataset_id existente y con columna temporal
- SOP/TOOL: (funcion pura, sin tool externa)
- OUTPUT: `{anomalies: Dataset, count: int}`
- VALIDATION: count >= 0
- ERROR_STATES: InsufficientData
- HANDOFF: analytics.generate_report, communication.notify_user
- TIMEOUT: 30s | RETRY: {max_retries: 0}
- STUB: false

### 04 ANALYTICS.ComparePeriods
- ONTOLOGY: action=Analyze, entity=Dataset, taxonomy=ANALYTICS
- PURPOSE: Comparar dos periodos de tiempo
- INPUT: `{dataset_id: str, period_a: str, period_b: str, metric: str}`
- PRECONDITIONS: periodos no solapados
- SOP/TOOL: (funcion pura, sin tool externa)
- OUTPUT: `{delta: float, delta_pct: float, summary: str}`
- VALIDATION: delta es float
- ERROR_STATES: InsufficientData
- HANDOFF: analytics.generate_report, content.write_article
- TIMEOUT: 30s | RETRY: {max_retries: 0}
- STUB: false

### 05 ANALYTICS.GenerateChart
- ONTOLOGY: action=Create, entity=Image, taxonomy=ANALYTICS
- PURPOSE: Generar un grafico a partir de un dataset
- INPUT: `{dataset_id: str, chart_type: str, x: str, y: str}`
- PRECONDITIONS: columnas x e y existen
- SOP/TOOL: (pendiente tool chart_generate)
- OUTPUT: `{image: Image}`
- VALIDATION: image.url o image.path presente
- ERROR_STATES: ChartFailed
- HANDOFF: analytics.generate_report, communication.send_email
- TIMEOUT: 60s | RETRY: {max_retries: 1}
- STUB: true

### 06 ANALYTICS.GenerateReport
- ONTOLOGY: action=Create, entity=Document, taxonomy=ANALYTICS
- PURPOSE: Componer un informe con KPIs, graficos y narrativa
- INPUT: `{dataset_ids: list[str], audience?: str, format?: str="md"}`
- PRECONDITIONS: dataset_ids no vacio
- SOP/TOOL: documentation_create + LLM
- OUTPUT: `{report: Document}`
- VALIDATION: report.content no vacio
- ERROR_STATES: GenerationFailed
- HANDOFF: communication.send_email, documents.generate_pdf
- TIMEOUT: 90s | RETRY: {max_retries: 1}
- STUB: false

### 07 ANALYTICS.GenerateRecommendation
- ONTOLOGY: action=Create, entity=Document, taxonomy=ANALYTICS
- PURPOSE: Generar una recomendacion accionable a partir de un informe
- INPUT: `{report_id: str, goal?: str}`
- PRECONDITIONS: report_id existente
- SOP/TOOL: (LLM)
- OUTPUT: `{recommendation: Document, priority: str}`
- VALIDATION: priority en {low, medium, high}
- ERROR_STATES: GenerationFailed
- HANDOFF: communication.notify_user, automation.trigger_workflow
- TIMEOUT: 60s | RETRY: {max_retries: 1}
- STUB: false

## Familias futuras (esqueleto, sin microacciones)

Estas familias estan declaradas en spec 02 pero no se expanden en C0.4.
Se rellenaran cuando haya una necesidad real y un caso de uso validado.
Su estructura sigue exactamente el mismo formato que las anteriores.

- CALENDAR
- PROJECT_MANAGEMENT
- CLOUD
- AUTH
- PAYMENTS
- ECOMMERCE
- SUPPORT
- KNOWLEDGE_BASE/RAG
- VECTOR_DB
- FILESYSTEM
- GIT
- API_GATEWAY
- NOTIFICATIONS
- FORMS
- SCHEDULING
- COMPLIANCE

## Nota de cierre de C0.4

Con esta extension, spec 08 cubre las 15 familias declaradas en spec 02.
Cada microaccion declara `STUB: true` si depende de una tool o conector
no implementado (por tanto NO se implementa en codigo hasta C7).

Total de microacciones propuestas en esta extension: ~65.
Todas PENDIENTES DE REVISION HUMANA (C0.6).
