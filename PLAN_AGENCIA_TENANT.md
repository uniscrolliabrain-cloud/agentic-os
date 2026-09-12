# PLAN MAESTRO — Tenant «BOR Agency» (agencia agéntica)

> **Documento de planificación detallado** para construir el primer tenant
> productivo sobre **Agentic OS**: una agencia agéntica de captación y validación
> de leads, venta semiautomática por WhatsApp, agendado de citas que escribe
> directamente en el calendario/CRM de **cada cliente final**, cobro
> semiautomático vía **links de Stripe**, y venta de servicios digitales
> (rediseño/web nueva económica, community management, servicios IA y agénticos,
> Google Business Profile, SEO) decididos según una **auditoría** previa del
> prospecto.
>
> - **Estado:** v1.0 — plan alineado con el estado actual del kernel; se ejecuta
>   por fases y cada fase termina con sus pruebas en verde.
> - **Regla inviolable:** el LLM nunca ejecuta nada directamente. Solo propone
>   Intents; la Policy decide y el Executor ejecuta. Todo se audita en el
>   EventLog.
> - **Convención de rutas:** `src/agentic_os/…` hace referencia a la raíz del
>   paquete; los datos viven en `data/` y el conocimiento en `knowledge/`.

## Índice

| #  | Sección |
|----|---------|
| 1  | Contexto y visión de negocio |
| 2  | Decisiones de modelo (la base de todo) |
| 3  | Auditoría del estado actual del código |
| 4  | Principios e invariantes del kernel — el «por qué» |
| 5  | Plan de implementación por fases (0 → 10) |
| 6  | Flujos end-to-end: walkthrough de un lead |
| 7  | Decisiones pendientes / preguntas abiertas |
| 8  | Glosario |
| 9  | Anexo: mapa completo de archivos a crear/modificar |

## 1. Contexto y visión de negocio

BOR Agency vende servicios digitales a pymes y autónomos. El primer hito
agentizado es un **embudo comercial end-to-end**:

1. **Captación.** Los leads entran por varios canales — webhook de WhatsApp,
   formulario web, CSV/hoja de cálculo en Drive, leads de Meta Ads — y entran en
   el pipeline `lead_capture`.
2. **Validación automática.** Formato de teléfono/email, campos obligatorios y
   deduplicación contra el CRM del cliente final. Un lead que no valida **no**
   avanza (fail-closed) y se reporta con el motivo tipado.
3. **Venta semiautomática por WhatsApp (BOR).** El FrontAssistant (knowledge
   base) responde al instante; el orquestador propone Intents; la Policy decide
   qué se envía solo (plantillas aprobadas) y qué requiere **aprobación humana**
   (primer contacto con un lead nuevo, envíos con ofertas).
4. **Agendado de citas.** Detectada la intención de cita, el pipeline crea el
   evento en el **calendario del cliente final** (credenciales per-client) y lo
   refleja como `crm.deal`/`crm.task` en su CRM.
5. **Cobro semiautomático.** Cualquier cobro se aprueba antes (riesgo
   FINANCIAL → `require_approval`); aprobado, el bot envía el **link de Stripe**
   por WhatsApp.
6. **Auditoría → propuesta.** Para servicios (web, CM, IA/agénticos, GMB, SEO)
   se audita la presencia digital del prospecto (`audit_website`) y el LLM
   genera un `AuditReport` tipado desde el que se arma una `ServiceQuote`
   («servicio completo» o «partes», según el resultado de la auditoría).

**Por qué este tenant primero:** ejercita las capacidades más delicadas del
sistema — credenciales por cliente, aprobación humana por clase de riesgo,
pipelines mixtos automáticos/semiautomáticos e idempotencia — sin tocar un solo
invariante del kernel (sección 4).

## 2. Decisiones de modelo (la base de todo)

### 2.1 Un solo tenant = la agencia

`TenantRegistry` ya soporta multi-tenant, pero la agencia es **un único tenant**
(slug propuesto: `bor-agencia`). Los clientes finales a los que la agencia presta
servicio **no son tenants**: son entidades del dominio `agencia.client` que viven
dentro del tenant agencia.

**Por qué:**
- El multi-tenancy de Agentic OS aísla datos y credenciales por *facturador*
  (el dueño del `data_dir`, la API key y la policy). Aquí el facturador es BOR.
- Las políticas de venta (qué se puede enviar/crear/cobrar) son únicas para la
  agencia; no cambian por cliente final.
- Convertir a cada cliente final en tenant multiplicaría la complejidad de
  orquestación, policy y datos sin aportar un aislamiento real que BOR necesite.
- Si en el futuro un cliente final se convierte en tenant (white-label), la
  entidad `agencia.client` guarda el mapeo 1:1 para migrarlo.

### 2.2 Credenciales por cliente final (decisión confirmada)

El bot escribe en el calendario/CRM de **cada cliente final usando SUS propias
credenciales**, centralizadas de forma segura en el tenant agencia:

```json
// data/tenants/registry.json → TenantConfig.credentials
{
  "api_key": "tk_...",
  "clients": {
    "cli_xxxx": {
      "name": "Clínica XYZ",
      "providers": {
        "google":  { "refresh_token": "...", "impersonation": "agenda@clinicaxyz.com" },
        "hubspot": { "access_token": "..." },
        "stripe":  { "secret_key": "sk_...", "account_id": "acct_..." }
      }
    }
  }
}
```

**Consecuencias técnicas** (desarrolladas en sus fases):
1. `TenantConfigPublic.from_config()` recalculará `connected_providers` (hoy
   deriva de `credentials.keys()` y la key `clients` se colaría como provider) y
   nunca expondrá credenciales.
2. Nuevo resolver `resolve_client_credentials(tenant_id, client_id, provider)`
   en `infrastructure/tenancy` (o `connectors/auth`): lee del dict, nunca se
   loguea, nunca se expone por API.
3. `Command` (`connectors/core/models.py`) gana el campo
   `client_id: Optional[str]` — el agente declara *a qué cliente* va dirigida la
   acción, sin ver nunca sus credenciales.
4. Nuevo `ScopedConnectorRouter` que construye/cachea connectors con las
   credenciales del cliente final reutilizando `Connector` + adapters.
5. Gate de seguridad por cliente (estilo `GOOGLE_REAL`): sin flag + credenciales
   del cliente, el conector queda stub (`CONNECTOR_NOT_CONFIGURED`).
6. **Auditoría por cliente:** `client_id` también viaja al `ExecutionResult` y a
   los eventos de auditoría del EventLog para poder responder «qué hizo el bot en
   la clínica X vs Y» — desarrollado en Fase 3 (tool) y Fase 4.0
   (executor + eventlog).

### 2.3 Semiautomático = 3 niveles de control

| Nivel              | Qué incluye                                                       | Mecanismo kernel                                |
|--------------------|-------------------------------------------------------------------|-------------------------------------------------|
| **Automático**     | captación, validación, auditoría web, generación de propuesta, confirmaciones de cita, lecturas | regla `allow` en la policy del tenant + pipeline |
| **Semiautomático** | primer WhatsApp a un lead, envío de ofertas, publicación social, **links de Stripe** | regla `require_approval` (cola de aprobación)   |
| **Denegado**       | capacidades destructivas y cualquier capability fuera de `enabled_capabilities` | default-deny del kernel                         |

### 2.4 La auditoría decide «completo o partes»

El servicio vendido depende del resultado de la auditoría, nunca de un prompt
libre del LLM:

```
audit_website(url)  →  AuditReport tipado (Pydantic, fail-closed)
                     →  reglas deterministas deciden:
                         - completo (web + CM + SEO + GMB + IA)  o
                         - partes   (solo lo que el report recomienda)
                     →  ServiceQuote con ítems, precios y link de Stripe
```

La `ServiceQuote` se genera con el LLM pero se **valida contra el esquema
Pydantic**; una propuesta que no valida no se envía (fail-closed).

## 3. Auditoría del estado actual del código

### 3.1 Tenancy (`infrastructure/tenancy/`)
- `models.py`: `TenantConfig` (frozen: `name`, `domain`, `data_dir`,
  `enabled_capabilities`, `credentials: Dict[str,Any]`,
  `credentials_expires_at`), `Tenant` (frozen: `id`, `slug` validado por regex +
  anti path-traversal, `config`), `TenantConfigPublic` (enmascara credenciales),
  `TenantContext`.
- `registry.py`: singleton con persistencia JSON
  (`data/tenants/registry.json`), escritura atómica `tmp+replace`, recarga por
  mtime (multi-worker), y **anti-wipe** si el JSON se corrompe (backup
  `.corrupt.bak`).
- **HALLAZGO:** el `registry.json` real está lleno de tenants residuales de
  tests (`con-cap` ×N, `tenant-a`, `tenant-b-nokey`, `acme` con rutas temporales
  de pytest). Hay que sanearlo (Fase 0).

### 3.2 Policy (`kernel/policy/`)
- `engine.py`: **default-deny**. Para decidir: (1) el tenant debe existir;
  (2) la capability debe estar en `enabled_capabilities` del tenant;
  (3) se carga `data/policies/{tenant_id}.json` y se evalúa con
  `PolicyEvaluator`. Efectos: `allow | deny | require_approval`.
  `DEV_ALLOW_ALL=true` es el único bypass (dev) y además está bloqueado si existe
  regla allow-`*`.
- `models.py`: `PolicyRule(id, description, capability, resource_kind, effect,
  requires_roles)` y `Policy(id, name, rules, version)`.

### 3.3 Dominios (`domains/`)
- `base.py`: `BaseDomain` con `entity_kinds`, `relation_kinds`,
  `capability_kinds` y `compile_ontology()` → valida fail-closed contra el
  metamodelo (`validate_against_metamodel`) y produce `OntologyBundle` versionado.
- `clinic/`: ejemplo completo (`clinic.patient`, `clinic.appointment`,
  `clinic.has_appointment`, `clinic.schedule`).
- `finance/`: solo `VOCAB` legacy, sin compilar.
- `marketing_ficticio/`: **solo `ontology.yaml`** (sin módulo Python) — un
  borrador anterior exactamente de este caso: mapea `lead → crm.contact.*`,
  `cita → calendar.event.*`, `campaña → ads.campaign.*`. Sirve de referencia
  para el dominio real `agencia`.

### 3.4 Entidades tipadas (`kernel/ontology/domain_models.py`)
`ENTITY_TYPE_REGISTRY` fail-closed con `Lead`, `Proposal`, `Brand`, `Campaign`,
`BlogPost`, `CoachingClient`, `SessionNote`, `TherapyClient`, `Appointment`.
`entity_from_payload(kind, data)` lanza `UnknownEntityTypeError` para kinds no
registrados y `ValidationError` si el payload no valida.

### 3.5 Catálogo de capabilities (`connectors/providers/`)
44 providers declarados **sin conectar** (stubs; `connected=False`;
`CONNECTOR_NOT_CONFIGURED` hasta que existan credenciales). Relevantes para el
tenant de la agencia:

| Familia            | Providers                                            | Capabilities canónicas clave                                          |
|--------------------|------------------------------------------------------|-----------------------------------------------------------------------|
| Comms/social       | `whatsapp`, `meta`, `linkedin`, `tiktok`, `telegram` | `whatsapp.message.send/template.send/receive`, `social.post.*`, `social.comment.*`, `social.metrics.get`, `ads.campaign.*` |
| CRM                | `hubspot`, `salesforce`, `pipedrive`                 | `crm.contact.*`, `crm.deal.*`, `crm.task.*`, `crm.note.*`, `crm.pipeline.read` |
| Google             | `google`                                             | `email.message.*`, `calendar.event.*`, `file.*`, `analytics.*`        |
| Contenido/web      | `wordpress`, `shopify`, `cloudflare`, `vercel`, `github`, `n8n` | `cms.post/page/media.*`, `commerce.*`, `software.*`, `cloud.*`, `automation.workflow.*` |
| IA/web/extracción  | `openai`, `anthropic`, `tavily`, `serpapi`, `exa`, `brave_search`, `firecrawl`, `jina_reader`, `browser` | `ai.text.*`, `web.search`, `web.page.extract`, `web.site.crawl`       |

**FALTAN en el catálogo** (se crean en Fase 2):

- **Stripe** → `payment.link.create`, `payment.link.read`,
  `payment.checkout.create` (riesgo FINANCIAL automático por prefijo).
- **Google Business Profile** → `local.business.profile.read/update`.
- **SEO** → `web.seo.audit`, `web.seo.keywords`.
- **Validación de leads** → `data.lead.validate`.

### 3.6 Tools (`execution/tools/`)
Mocks deterministas SIMULADOS (`whatsapp_send/read`, `calendar_create_event`,
`gmail_*`, `drive_*`, `web_*`, `meta_post_publish`, `documentation_*`,
`scheduler_*`) + `ConnectorBridgeTool`: si la capability canónica existe en el
catálogo del Connector Kernel, **gana el kernel**; el mock es el fallback
(`build_default_registry` + `CANONICAL_ALIASES`).

### 3.7 Pipelines (`orchestration/pipelines/`)
Registro por `@register(id, tools=[...])`. Existen: `leads_to_draft` (leads →
validación `Lead` → Gmail **drafts**, nunca envía), `daily_social` (contenido →
`BlogPost` → `meta_post_publish`), `inbox_watcher`. El `PipelineRunner` pasa
SIEMPRE por `Executor` (Policy + auditoría); idempotencia por
`tenant+command_id` con TTL 24h; el fallo de una microacción =
`PipelineStepError` (detiene el pipeline).

### 3.8 API (`interfaces/api/rest.py`)
CRUD de tenants (admin), `/execute`, `/chat` (FrontAssistant + orquestador en
background), `/pipelines`, `/schedules`, `/drafts`, `/artifacts`, `/tasks`,
`/skills`, `/tools`. Auth: `X-Tenant-Id` + `X-Api-Key` (guardada en el registry)
y `X-Admin-Key` como bypass global; credenciales expiradas → 401 (fail-closed).

### 3.9 Webhooks (`connectors/webhook/`)
`WebhookReceiver` con verificación HMAC (sha1/sha256), ventana de timestamp y
dedup por `event_id`; `WebhookRegistry`/`WebhookDispatcher`. **No existe aún una
ruta REST** para recibir webhooks de WhatsApp (Fase 7 lo resuelve).

### 3.10 Scheduler y Temporal
- `orchestration/scheduler.py`: APScheduler `BackgroundScheduler` + persistencia
  por tenant (`data/tenants/{tid}/schedules.json`), jobs *interval* y *daily*,
  dispara `on_trigger` → orquestador/pipeline.
- `orchestration/temporal/`: client, worker, activities y workflows para
  ejecución durable (docker-compose ya levanta Temporal). Estrategia: MVP con
  APScheduler; ejecución durable cuando haga falta.

## 4. Principios e invariantes del kernel — el «por qué»

Todo el plan respeta estos invariantes (ver `docs/INVARIANTS.md`, `docs/spec/`):

| #  | Invariante                                                     | Cómo lo respeta el plan                                  |
|----|----------------------------------------------------------------|----------------------------------------------------------|
| I1 | **El LLM nunca ejecuta directo.** Solo propone Intents; la Policy decide; el Executor ejecuta. | Todos los pipelines pasan por `PipelineRunner → Executor → Policy → Tool → EventLog`. |
| I2 | **EventLog es la fuente de verdad;** WorldState es derivado.   | Cada microacción y cada entidad emitida como evento (`entity_created`, `ToolCompleted`, `BackgroundProcessingDone`…). |
| I3 | **Default-deny.** Capability no habilitada ⇒ deny.             | `enabled_capabilities` del tenant = lista exacta permitida; policy explícita en `data/policies/{slug}.json`. |
| I4 | **Fail-closed tipado.** Entidades desconocidas o inválidas no existen. | Toda entidad nueva se registra en `ENTITY_TYPE_REGISTRY`; payloads que no validan ⇒ error reportado, nunca avance. |
| I5 | **Sin credenciales en código.** Se inyectan por `.env`/CredentialStore. | Las de clientes finales viven en `TenantConfig.credentials["clients"]`, resueltas por scope, nunca logueadas ni expuestas por API. |
| I6 | **Los stubs mienten estructuradamente** (`SIMULATED`/`CONNECTOR_NOT_CONFIGURED`), nunca fallan en silencio. | Toda capability nueva tiene stub determinista + dry-run con preview. |
| I7 | **Idempotencia.** `tenant+command_id` (TTL 24h) ⇒ reejecutar no duplica efecto. | Pipelines idempotentes (`command_id` propagado desde webhook/API). |
| I8 | **Aprobación humana por riesgo.** `require_approval` para EXTERNAL_COMMUNICATION y FINANCIAL. | Primer WhatsApp y todo Stripe pasan por la cola de aprobación. |

## 5. Plan de implementación por fases

Cada fase define **objetivo, por qué, archivos, cambios concretos, riesgos y
validación**. El orden minimiza riesgo: primero sanear, luego declarar (dominio
y catálogo), después ejecutar (tools y pipelines), por último exponer
(policy, tenant, webhooks, API).

### Fase 0 — Sanear el estado base

**Objetivo:** partir de un `data/tenants/registry.json` limpio (hoy contiene
decenas de tenants residuales de tests: `con-cap` duplicado, `tenant-a`,
`tenant-b-nokey`, `acme` con rutas de `pytest`).

**Por qué:** un registry sucio rompe la resolución de policy (un slug repetido
hace `TenantRegistry.get()` ambiguo), puebla la API de basura y puede mezclar
`data_dir` de entornos temporales con el real.

**Cómo:**
1. Backup: `cp data/tenants/registry.json data/tenants/registry.json.bak-<fecha>`.
2. Dejar el mínimo: el tenant virtual `system`/`acme` de back-compat o un
   registry vacío `[]` (el registry lo recrea y se autogenera la carpeta).
3. Verificar que la suite actual sigue verde: `pytest -q tests/`.
4. (Opcional) script `scripts/clean_registry.py` que lista slugs con duplicados
   y permite borrarlos por slug conservando backups — reutilizable en el futuro.

**Riesgos:** romper tests que esperan `acme`. Mitigación: los tests de tenancy
usan `tmp_path` (los rutas de pytest del registry lo confirman), por lo que
limpiar el fichero real no debería romperlos; se valida con la suite.

### Fase 1 — Dominio `agencia` (ontología + entidades tipadas)

**Objetivo:** declarar formalmente el vocabulario del negocio como extensión del
metamodelo del kernel.

**Por qué:** el kernel define qué *puede* existir (`DEFAULT_VOCAB`); el dominio
define qué *existe*. Sin ontología compilada no hay entidades, sin entidades no
hay WorldState tipado, y el systema queda en modo genérico.

**Cómo — archivos nuevos en `src/agentic_os/domains/agencia/`:**

- `__init__.py` — re-exporta `AgenciaDomain`, `AGENCIA_VOCAB`.
- `ontology.py` — subclase de `BaseDomain` (patrón de `clinic/ontology.py`):

```python
class AgenciaDomain(BaseDomain):
    domain: str = "agencia"
    entity_kinds: set[str] = {
        "agencia.client",          # cliente final servido por BOR
        "agencia.lead",            # prospecto (con phone/source/status)
        "agencia.appointment",     # cita (calendar del cliente final)
        "agencia.deal",            # oportunidad comercial
        "agencia.quote",           # propuesta/servicio cotizado
        "agencia.audit_report",    # auditoría web/SEO
    }
    relation_kinds: set[str] = {
        "agencia.belongs_to_client",   # lead → client
        "agencia.generates",           # lead → deal/quote
        "agencia.programs",            # lead → appointment
    }
    capability_kinds: set[str] = {
        "agencia.capture_lead", "agencia.validate_lead",
        "agencia.schedule", "agencia.quote_service",
    }
```

- `entities.py` (o extender `kernel/ontology/domain_models.py`) — modelos
  Pydantic `BaseDomainModel` strict (`frozen=True`, `extra="forbid"`):

| Modelo | Campos clave | Validaciones (fail-closed) |
|--------|--------------|----------------------------|
| `AgencyClient` | `name`, `slug`, `timezone`, `providers: list[str]` | slug regex; sin providers vacíos |
| `AgencyLead` | `client_id`, `name`, `email`, `phone`, `source`, `status` | email contiene `@`; phone con patrón E.164 básico; `status ∈ {capturado, validado, contactado, cita, deal, cerrado, invalido}` |
| `AgencyAppointment` | `client_id`, `lead_id`, `calendar_provider`, `scheduled_at`, `external_id` | `scheduled_at` en futuro; `external_id` opcional |
| `AgencyDeal` | `client_id`, `lead_id`, `quote_id?`, `stage`, `total`, `stripe_link?`, `payment_status` | `total ≥ 0`; stage tipado |
| `ServiceQuote` | `client_id`, `lead_id`, `service_items: list[ServiceItem]`, `total`, `stripe_link?` | `ServiceItem(service ∈ {web_design, web_redesign, community_management, ai_services, agentic_services, gmb_update, seo}, description, price ≥ 0)`; total = Σ |
| `AuditReport` | `client_id`, `url`, `checklist: dict`, `score`, `recommendations: list[str]` | `url` parseable http(s); score 0-100 |

- Registrar los six modelos en `ENTITY_TYPE_REGISTRY` y comprobar con
  `validate_registry_integrity()`.
- `policies.py` — política del dominio (se materializa en Fase 5).
- `projections.py` — proyecciones del WorldState específicas del dominio
  (p. ej. `leads_por_estado`, `deals_abiertos`).
- `tests/` — `test_agencia_ontology.py`: `compile_ontology()` devuelve bundle
  válido; entidades válidas/inválidas; kinds no registrados → `KeyError`.

**Riesgos:** tocar `ENTITY_TYPE_REGISTRY` (kernel) sin romper los tests de
integridad existentes (`validate_registry_integrity` los protege).

### Fase 2 — Catálogo de capabilities nuevas (Stripe, GMB, SEO, validación)

**Objetivo:** que el Connector Kernel conozca las capabilities que hoy no
existen, declaradas de forma canónica (sin credenciales).

**Por qué:** el invariante del kernel es «declara la capability antes de usarla».
`ConnectorBridgeTool` solo deriva al kernel cuando la capability existe en el
catálogo (`CapabilityRegistry.has_capability`); si no existe, la resolución cae
al mock SIMULADO. Para poder resolver Stripe/GMB/SEO/validación por el camino
canónico hay que declararlos primero.

**Cómo — archivos a modificar/crear:**

1. **Nuevo catálogo** `connectors/providers/catalog_payments_web.py` (o extender
   los existentes) en `PROVIDER_SPECS`:

```python
PROVIDER_SPECS_PAYMENTS = {
  "stripe": {
    "connector_id": "stripe", "provider": "Stripe", "auth_type": "bearer",
    "caps": ["payment.link.create", "payment.link.read",
             "payment.checkout.create"],
    "risk": "FINANCIAL",                    # ← declarado EN EL CATÁLOGO (invariante I8)
    "token_env": "STRIPE_SECRET_KEY",
    "extra_env": ["STRIPE_ACCOUNT_ID"],
  },
  "google_business": {
    "connector_id": "google_business", "provider": "Google Business Profile",
    "auth_type": "oauth2",
    "caps": ["local.business.profile.read", "local.business.profile.update"],
    "oauth": {...scopes business profile...},
  },
  "seo": {
    "connector_id": "seo", "provider": "SEO Auditor", "auth_type": "none",
    "caps": ["web.seo.audit", "web.seo.keywords"],
    "base_url": None,
  },
  "lead_validation": {
    "connector_id": "lead_validation", "provider": "Lead Validator",
    "auth_type": "none",
    "caps": ["data.lead.validate"],
  },
}
```

2. **Riesgo FINANCIAL declarado en el catálogo, no solo en la policy:**
   - Cada capability del spec lleva su `"risk"` explícito (Stripe →
     `"FINANCIAL"`). `RISK_BY_CAPABILITY_PREFIX` ya cubre el prefijo `payment.`
     en `connectors/core/models.py` → cualquier `payment.*` se clasifica
     FINANCIAL automáticamente; el campo del spec es la **segunda capa**
     (defensa en profundidad).
   - Verificar con test:
     `risk_class_for("payment.link.create") == "FINANCIAL"`.
3. **Garantía I8 sin depender del JSON de policy:** la semiautomatización de
   cobros no puede descansar solo en `data/policies/{slug}.json` (un humano
   puede olvidar la regla). Añadir un check de hardening: la capa de
   aprobación/executor deriva `require_approval` del **riesgo del catálogo**
   cuando la capability es FINANCIAL, aunque la regla de policy no exista.
   Si el policy la repite, se usa el efecto explícito; si no, el riesgo del
   catálogo gana. Test: capability `payment.*` sin regla de policy ⇒ la
   ejecución NO se considera aprobable automáticamente.
4. **Registro:** añadir el import y el `PROVIDER_SPECS.update(...)` en
   `connectors/providers/__init__.py`. El `register_builtin_providers` los
   convierte en stubs sin tocar nada más.
5. **Validación:** `pytest` — test que `CapabilityRegistry` resuelve las novas
   capabilities; `connector.execute` en stub devuelve
   `CONNECTOR_NOT_CONFIGURED`; dry-run devuelve preview sin efecto; y el
   `risk` del spec de `stripe` es `FINANCIAL`.

**Riesgo:** no romper el recuento del README (44 providers). Se actualizará la
documentación del catálogo al cerrar la fase.

### Fase 3 — Tools de ejecución y puente con el kernel

**Objetivo:** herramientas deterministas (stubs SIMULADOS) para las nuevas
capabilities + registrarlas en el `ToolRegistry` con su `CANONICAL_ALIASES`,
para que el resolver vaya por el kernel cuando exista conector y por el stub
cuando no.

**Cómo — archivos nuevos en `execution/tools/`:**

| Tool (mock)                    | Capability canónica (alias)     | Params esenciales                          |
|--------------------------------|--------------------------------|--------------------------------------------|
| `StripePaymentLinkTool`        | `payment.link.create`          | `client_id`, `amount`, `currency`, `description`, `customer_email` |
| `WhatsAppTemplateSendTool`     | `whatsapp.template.send`       | `to`, `template_name`, `language`, `params` |
| `LeadValidationTool`           | `data.lead.validate`           | `name`, `email`, `phone`, `client_id`      |
| `CrmDealCreateTool`            | `crm.deal.create`              | `client_id`, `lead_id`, `title`, `value`, `stage` |
| `CrmTaskCreateTool`            | `crm.task.create`              | `client_id`, `subject`, `due_date`         |
| `GmbUpdateTool`                | `local.business.profile.update`| `client_id`, `business_name`, `fields: dict` |
| `AuditWebsiteTool`             | `web.seo.audit`                | `url` → combina `web_scrape`/`web_search` + checklist |

Cada mock sigue el patrón de `whatsapp_tool.py` / `calendar_tool.py`:

```python
class StripePaymentLinkTool(Tool):
    name = "stripe_create_payment_link"
    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # validación determinista de params obligatorios
        # → SIMULADO: devuelve link https://pay.stripe.test/link_<hash>
        #            + amount/currency/customer_email + created_at
```

**Cambios en el puente:**
- `execution/tools/connector_bridge.py` → ampliar `CANONICAL_ALIASES`:
  `stripe_create_payment_link → payment.link.create`, `whatsapp_template_send →
  whatsapp.template.send`, `lead_validate → data.lead.validate`,
  `crm_deal_create → crm.deal.create`, `crm_task_create → crm.task.create`,
  `gmb_update → local.business.profile.update`, `audit_website →
  web.seo.audit`.
- `execution/tools/__init__.py` → añadir las 7 tools a `ALL_TOOLS` y `__all__`.
- **Soporte de `client_id`:** cuando `ConnectorBridgeTool.run()` construye el
  `Command`, si `params` contiene `client_id` lo copia al `Command.client_id`
  (no se propaga a credenciales) **y lo estampa en el output normalizado que
  devuelve el bridge** (p. ej. `out["client_id"]`) para que el resultado de
  cada microacción se asocie al cliente final. Mientras
  `ScopedConnectorRouter` (Fase 4) no exista, el bridge ignora discretamente el
  scope y el stub sigue `SIMULATED`.

**Validación:** test de un pipeline mínimo que use `stripe_create_payment_link`
con policy `require_approval` → la ejecución devuelve la decisión de policy (no
ejecuta) y se registra `PolicyDecision` en el EventLog.

### Fase 4 — Pipelines de la agencia (y soporte de scope por cliente)

#### 4.0 Soporte transversal: `ScopedConnectorRouter` + `client_id`

**Objetivo:** que una microacción dirigida a un cliente final resuelva SUS
conectores/credenciales sin exponerlas al agente.

**Cómo:**
- `Command` (en `connectors/core/models.py`): añadir
  `client_id: Optional[str] = None`.
- Nuevo `connectors/scoped.py` → `ScopedConnectorRouter(router)`:
  - `async def route(command)` — si `command.client_id` está presente, obtiene
    credenciales con `resolve_client_credentials(tenant_id, client_id,
    provider)` y construye (y cachea) el connector del cliente con las
    credenciales; si no hay credenciales o el gate por cliente está off,
    delega al router global (stub).
  - Cache con `TTL` y expiración; jamás loguea credenciales.
- `infrastructure/tenancy/credentials.py` →
  `resolve_client_credentials(...)` descrito en §2.2.
- `execution/executor.py`: aceptar `client_id` en `execute(...)`, propagarlo en
  `run_params` (igual que `tenant_id`) **y persistirlo en la auditoría**:
  - `ExecutionResult` (en `execution/result.py`) gana
    `client_id: Optional[str] = None`.
  - `_audit(...)` y los eventos del rastro «MicroActionExecuted»
    (`ActionStarted`, `ToolCompleted`, `ToolFailed`) incluyen
    `"client_id": client_id` en su `payload` → el EventLog queda consultable por
    `tenant_id + client_id`: **«qué hizo el bot en la clínica X vs Y»**.
- `orchestration/pipelines/runner.py`: `tool()` acepta/forwards `client_id` y
  lo incluye en el resumen de cada paso (`PipelineStepError` y artefactos).

**Validación:** test que con credenciales de cliente en `TenantConfig` el router
construye un conector `connected=True` con las credenciales de ESE cliente y
con otro cliente (o sin credenciales) cae a stub.

#### 4.1 Pipelines nuevos (en `orchestration/pipelines/`)

Todos se registran con `@register(id, tools=[...])`, reciben
`(runner, tenant_id, params, correlation_id)` y **nunca** llaman a una Tool
directamente: solo `runner.tool(...)`.

| Pipeline | Disparo | Herramientas (`runner.tool`) | Salida/estado |
|----------|---------|------------------------------|---------------|
| `capture_lead` | webhook/API/Drive | `lead_validate`, `crm_contact_create` (vía bridge `crm.contact.create`) | `Lead` entity_created; status `capturado`→`validado` |
| `nurture_whatsapp` | scheduler (interval) | `whatsapp_template_send` (require_approval primer envío) | hilo de plantillas; status `validado`→`contactado` |
| `book_appointment` | intent/chat (kind `agendar_cita`) | `calendar_create_event`, `crm_deal_create`, `crm_task_create`, `whatsapp_send` | `AgencyAppointment` + confirmación; status `contactado`→`cita` |
| `audit_and_quote` | manual/API | `audit_website`, LLM (runner) | `AuditReport` → `ServiceQuote`; status `cita`→`deal` |
| `send_payment_link` | tras aprobación | `stripe_create_payment_link` (FINANCIAL require_approval), `whatsapp_send` | `AgencyDeal.stripe_link`; status `deal`→`cerrado` |
| `community_daily` | scheduler daily | `drive_read_file`, `meta_post_publish` (extensible LinkedIn/TikTok) | `BlogPost` + artefacto (como `daily_social`) |
| `gmb_update` | manual | `gmb_update` (stub) | evento `GmbUpdated` |
| `seo_monitor` | scheduler weekly | `web.seo.audit`, `web.seo.keywords` | `AuditReport` periódico + artefacto |

#### 4.2 Detalle de los pipelines críticos

**`capture_lead`** — idempotente por `command_id` (fuente + id externo):

```python
@register("capture_lead", tools=["lead_validate", "crm_contact_create"])
def run_capture(runner, tenant_id, params, correlation_id=None):
    payload = params["payload"]          # del webhook/API/Drive
    res = runner.tool("lead_validate", {"email": ..., "phone": ...
                                        "client_id": ...}, tenant_id)
    if not res.get("valid"):             # fail-closed
        emit("LeadRejected", reason=res["reason"]); return {"status": "REJECTED"}
    entity = AgencyLead(tenant_id=..., client_id=..., ...)   # Pydantic strict
    runner.emit_event("entity_created", entity.id, tenant_id, entity.model_dump())
    runner.tool("crm_contact_create", {...}, tenant_id)      # CRM del cliente
    return {"status": "CAPTURED", "lead_id": entity.id}
```

**`nurture_whatsapp`** — secuencia de plantillas con paso de aprobación:

1. Consulta leads `validado` del tenant (WorldState/proyección).
2. Para cada uno, si no tiene eventos previos de `whatsapp_template_send`
   → paso `require_approval` (humano aprueba el borrador); si ya está
   aprobado/en cola → envía (`runner.tool("whatsapp_template_send", ...)`).
3. Programa el siguiente paso con `SchedulerCreateJobTool` (no en el mismo
   pipeline; la reentrada es idempotente por `command_id`).

**`book_appointment`** — cuando el intent es `agendar_cita`:

```python
# 1. validar lead y cliente final (scope)
# 2. runner.tool("calendar_create_event", {title, start, end, attendees,
#        client_id}) → el evento se crea en el CALENDARIO DEL CLIENTE FINAL
# 3. runner.tool("crm_deal_create", {"client_id": ..., value: ...})   # CRM cliente
# 4. runner.tool("crm_task_create", {"subject": "Seguimiento post-cita"...})
# 5. runner.tool("whatsapp_send", {"to": lead.phone,
#        "text": f"Confirmada tu cita el {start}..."})   # require_approval? no: ya hay cita
# 6. emitter: entity_created(AgencyAppointment)
```

**`audit_and_quote`** — «completo o partes»:

```python
report_ok = runner.tool("audit_website", {"url": q["url"], "client_id": ...})
report = AuditReport(..., checklist=report_ok["checklist"], score=...)
# reglas deterministas (no LLM libre):
if report.score < 40:  items = ALL_PACKAGES            # "servicio completo"
else:                  items = recommend_partial(report)  # solo gaps
llm.generate → ServiceQuote(items...)  → valida Pydantic (fail-closed)
runner.tool("stripe_create_payment_link", ServiceQuote.total...)  # require_approval
# tras aprobación humana → send_payment_link envía por WhatsApp
```

### Fase 5 — Policy del tenant (semi-automatización con aprobación)

**Objetivo:** materializar los 3 niveles de control (§2.3) en
`data/policies/bor-agencia.json`.

**Por qué:** sin policy explícita el kernel aplica default-deny: nada se mueve.
La policy ES el contrato de semiautomatización: qué se hace solo, qué espera
aprobación humana y qué está prohibido.

**Cómo — `data/policies/{slug}.json`:**

```json
{
  "id": "bor-agencia",
  "name": "BOR Agency - policy de venta",
  "version": 1,
  "rules": [
    { "id": "r1",  "capability": "web.search",            "effect": "allow" },
    { "id": "r2",  "capability": "web.page.extract",      "effect": "allow" },
    { "id": "r3",  "capability": "web.seo.audit",         "effect": "allow" },
    { "id": "r4",  "capability": "data.lead.validate",    "effect": "allow" },
    { "id": "r5",  "capability": "crm.contact.create",    "effect": "allow" },
    { "id": "r6",  "capability": "crm.contact.read",      "effect": "allow" },
    { "id": "r7",  "capability": "crm.deal.create",       "effect": "allow" },
    { "id": "r8",  "capability": "crm.task.create",       "effect": "allow" },
    { "id": "r9",  "capability": "calendar.event.create", "effect": "allow" },
    { "id": "r10", "capability": "calendar.event.read",   "effect": "allow" },
    { "id": "r11", "capability": "whatsapp.message.send",
      "effect": "require_approval",
      "requires_roles": ["director"] },
    { "id": "r12", "capability": "whatsapp.template.send",
      "effect": "require_approval",
      "requires_roles": ["director"] },
    { "id": "r13", "capability": "payment.link.create",
      "effect": "require_approval",
      "requires_roles": ["director"] },
    { "id": "r14", "capability": "payment.checkout.create",
      "effect": "require_approval",
      "requires_roles": ["director"] },
    { "id": "r15", "capability": "social.post.publish",
      "effect": "require_approval",
      "requires_roles": ["director"] },
    { "id": "r16", "capability": "*", "effect": "deny" }
  ]
}
```

**Nota importante:** reglas más específicas ganan por `PolicyEvaluator`
(primera coincidencia por capability/resource). La regla `* → deny` es la red de
seguridad explícita. **El `enabled_capabilities` del tenant y la policy deben
coincidir**: si una capability no está en la lista del tenant, el default-deny
del engine NUNCA llega siquiera a leer la policy.

**Validación:** tests parametrizados — cada capability del listado anterior
devuelve `allow`/`require_approval`, y una no listada devuelve `deny`.

### Fase 6 — Alta del tenant y knowledge base

**Objetivo:** crear el tenant `bor-agencia` en el registry y dotar al
FrontAssistant de conocimiento de negocio (respuestas instantáneas en WhatsApp).

**Por qué:** el tenant es el contenedor de datos/policy/credenciales; la
knowledge base es lo que hace al asistente frontal útil sin depender del
orquestador en la línea de espera.

**Cómo:**
1. Registrar el tenant (API o script):

```python
from agentic_os.infrastructure.tenancy import TenantRegistry
TenantRegistry().create(
    name="BOR Agency",
    slug="bor-agencia",
    config={
        "domain": "agencia",
        "enabled_capabilities": [
            "web.search", "web.page.extract", "web.seo.audit", "web.seo.keywords",
            "data.lead.validate", "crm.contact.create", "crm.contact.read",
            "crm.deal.create", "crm.task.create",
            "calendar.event.create", "calendar.event.read",
            "whatsapp.message.send", "whatsapp.template.send",
            "payment.link.create", "payment.checkout.create",
            "social.post.publish", "local.business.profile.update",
        ],
        "credentials": {"api_key": "tk_<generar>"},
    },
)
```

2. `credentials_expires_at`: rotación periódica de API key (el engine ya
   bloquea tenants con credenciales vencidas).
3. **Knowledge base** en `knowledge/` (ficheros `.md`) para que el asistente
   frontal responda: `servicios.md` (catálogo de servicios y precios
   orientativos), `proceso_auditoria.md` (qué incluye la auditoría), `faq.md`,
   `politicas_contacto.md`. La `KnowledgeBase` soporta ya
   `directories=[knowledge/_shared/, data/tenants/bor-agencia/knowledge/]` →
   conocimiento específico del tenant en su `data_dir`.
4. High-level: estructura `data/tenants/bor-agencia/`:
   `leads/`, `quotes/`, `drafts/`, `artifacts/`, `knowledge/`, `schedules.json`.

**Validación:** `GET /api/v1/tenants` con `X-Admin-Key` devuelve el tenant sin
credenciales; `GET /api/v1/state` con `X-Tenant-Id: bor-agencia` + API key
responde y cuenta eventos.

### Fase 7 — Webhook entrante de WhatsApp

**Objetivo:** recibir mensajes entrantes de un número de BOR (cliente final o
prospectos) y convertir cada mensaje en un evento interno que dispara el flujo
de atención.

**Por qué:** la venta semiautomática necesita recibir: consultas de prospects,
respuestas a plantillas, confirmación de cita. El `WebhookReceiver` ya provee la
mecánica segura (HMAC + anti-replay + dedup); falta exponerla por HTTP y
conectarla al orquestador.

**Cómo:**
1. Nueva ruta en `interfaces/api/rest.py` (o `webhooks.py`):

```python
@app.post("/api/v1/webhooks/whatsapp")
async def whatsapp_webhook(payload: dict, request: Request):
    result = default_receiver.receive(
        provider="whatsapp", event_type="whatsapp.message.in",
        payload=payload,
        headers=dict(request.headers),
        secret_env_key="WHATSAPP_WEBHOOK_SECRET",
    )
    return JSONResponse(result)
```

2. **Handler registrado** que normaliza `WebhookEvent` → `Intent`/pipeline:
   - extrae `from` (teléfono), `text`, `timestamp` → `Lead` o continuación de
     conversación (buscando por `phone` en el WorldState).
   - emite `MessageReceived` al EventLog con `correlation_id`/`command_id`
     nuevos (idempotencia del pipeline `capture_lead`).
   - responde al instante con el FrontAssistant (knowledge base del tenant).
3. Registro en `WebhookRegistry` (en el arranque de la API) y verify **handshake**
   de Meta/WhatsApp Cloud API (token de verificación en query string).
4. La verificación HMAC usa un secreto distinto por entorno (env), nunca el del
   código.

**Validación:** tests del receiver con firma correcta/incorrecta, timestamp
fuera de ventana, evento duplicado; e2e: `POST /api/v1/webhooks/whatsapp` con
firma válida → aparece `MessageReceived` en el EventLog y se dispara
`capture_lead` (con `DEV_ALLOW_ALL=false` → policy deny si falta capability).

### Fase 8 — Scheduler (APScheduler) y Temporal

**Objetivo:** ejecución temporal de los pipelines (`nurture_whatsapp`,
`community_daily`, `seo_monitor`).

**Por qué:** el embudo depende de disparos programados; los endpoints de
schedules ya existen en la API (`POST /api/v1/schedules`), y Temporal existe en
el repo para flujos durables.

**Cómo:**
1. **MVP con APScheduler** (ya integrado): tras Fase 6, crear schedules por
   tenant:
   - `nurture_whatsapp` → intervalo (p. ej. cada 60 min, escaneando leads
     `validado`).
   - `community_daily` → diario a las 09:00.
   - `seo_monitor` → semanal.
   Vía API: `POST /api/v1/schedules` con `X-Tenant-Id: bor-agencia`.
2. **Idempotencia entre disparos:** los pipelines generan `command_id` a partir
   de (pipeline, fecha/hora o fuente) para que reejecuciones dentro del TTL de
   24h no dupliquen efectos.
3. **Temporal (durable)** en `orchestration/temporal/`:
   - `workflows.py`: workflow `agency_pipeline` que ejecuta las activities
     `lead_capture`, `scheduled_nurture`, `scheduled_community`…
   - `activities.py`: cada activity encapsula un pipeline (mismo contrato
     `(tenant_id, params, correlation_id)`).
   - `worker.py`: registrar activities y arrancar con `docker-compose`.
   Decisión de adopción: cuando el MVP demuestre que los disparos se pierden o
   hay que reintentar, se migra; no antes.

**Validación:** crear un schedule vía API y verificar en
`data/tenants/bor-agencia/schedules.json`; disparar manualmente el job y
comprobar el artefacto/EventLog.

### Fase 9 — API y exposición (opcional para MVP)

**Objetivo:** exponer de forma tenant-safe las operaciones de la agencia.

**Por qué:** para operar el embudo (aprobar mensajes/links, ver leads, lanzar
auditorías) hace falta superficie de API.

**Cambios en `interfaces/api/rest.py`:**
- `GET /api/v1/clients` — clientes finales del tenant (solo nombres/slugs, sin
  credenciales).
- `POST /api/v1/clients` — alta de cliente final (el cuerpo incluye SOLO
  metadatos; las credenciales se cargan aparte con admin, nunca por el mismo
  endpoint).
- `GET /api/v1/leads` — leads del tenant con filtro por status/client.
- `GET /api/v1/quotes` — propuestas y su estado de aprobación/pago.
- `POST /api/v1/run-pipeline` — ya existe `/api/v1/pipelines/...`
  (verificar contrato actual) → invocar `audit_and_quote`/`capture_lead`
  manualmente con `client_id` y `payload`.
- **Cola de aprobación** (clave de la semiautomatización): `GET
  /api/v1/approvals` (pendientes), `POST /api/v1/approvals/{id}/approve` y
  `/reject` → resuelven la decisión `require_approval` (el `ApprovalRequest` de
  `kernel/policy/approval.py` ya existe como vaqueta).
- **Frontend (React/Vite):** sección «Agencia» con cola de aprobación y estado
  del embudo; **no** se tocan los invariantes (el front solo llama a la API con
  headers de tenant/admin).

**Validación:** pruebas de aislamiento — un tenant A no ve leads/clientes de B
(respeta `scope`); aprobaciones requieren admin o rol `director`.

### Fase 10 — Pruebas y validación final

**Objetivo:** suite verde que garantice los invariantes.

**Cómo — tests nuevos (patrón del repo, `pytest` + `pytest-asyncio`):**

| Fichero | Qué valida |
|---------|------------|
| `tests/tenants/test_bor_agencia.py` | alta/lectura del tenant, `TenantConfigPublic` no expone `clients` ni credenciales |
| `tests/domains/test_agencia_ontology.py` | `compile_ontology()` ok; entidades válidas/inválidas; kinds no registrados |
| `tests/connectors/test_scoped_router.py` | credenciales de cliente → connector scoped; sin credenciales → stub |
| `tests/policy/test_agencia_policy.py` | allow/require_approval/deny por capability (matriz de la Fase 5) |
| `tests/pipelines/test_pipelines_agencia.py` | `capture_lead` (valid→capturado, inválido→REJECTED), `audit_and_quote` (completo/partes), idempotencia por `command_id` |
| `tests/webhooks/test_whatsapp_webhook.py` | HMAC ok/bad, replay, handshake, e2e MessageReceived→capture_lead |
| `tests/security/test_client_isolation.py` | un tenant nunca accede a leads/credenciales de otro |

**Comandos:** `pytest -q` (kernel+regresiones), `ruff check`
(baseline del repo), `mypy --strict` (deuda conocida del repo: solo archivos
nuevos), `python -c "from agentic_os.domains.agencia import AgenciaDomain"`.

**Criterio de salida de la Fase 10:** suite completa en verde, `data/` con el
tenant `bor-agencia` operativo, y `GET /health` + `GET /ready` OK.

## 6. Flujos end-to-end: walkthrough de un lead

### 6.1 El flujo completo (nuevo)

```
 1. [WEBHOOK]  Prospecto escribe por WhatsApp al número de BOR
        │  POST /api/v1/webhooks/whatsapp (HMAC válida, dedup ok)
        ▼
 2. [EVENTO]   WebhookEvent → normalizado a MessageReceived (correlation_id/cmd_id)
        ▼
 3. [FRONT]    FrontAssistant responde al instante desde la KB del tenant
        ▼  (background)
 4. [PIPELINE] capture_lead (idempotente):
        lead_validate (email+teléfono, dedupe contra CRM del cliente)
        ├─ NO válido → LeadRejected + notificación interna (nada externo)
        └─ válido   → AgencyLead entity_created + crm.contact.create
                       status: capturado → validado
        ▼
 5. [SCHED]    nurture_whatsapp encuentra el lead validado
        whatsapp.message.send → require_approval → cola de aprobación (director)
        director aprueba → se envía plantilla → status: contactado
        ▼
 6. [CHAT]     Prospecto responde "¿me podéis agendar una llamada?"
        orquestador propone Intent(kind=agendar_cita) → book_appointment:
        calendar.event.create (CALENDARIO DEL CLIENTE FINAL, credenciales scope)
        crm.deal.create + crm.task.create (CRM del cliente)
        whatsapp_send confirmación al prospecto → status: cita
        ▼
 7. [API]      Director lanza audit_and_quote sobre la web del prospecto
        audit_website → AuditReport (Pydantic) → reglas deterministas
        → "completo" o "partes" → ServiceQuote (Pydantic, fail-closed)
        ▼
 8. [APPROVAL] Director aprueba el importe (puede editar la quote)
        send_payment_link:
        payment.link.create (FINANCIAL → require_approval ya resuelto)
        → se genera link Stripe → whatsapp_send link → status: deal → cerrado
        ▼
 9. [EVENTLOG] Todo el recorrido queda en el EventLog, reconstruible por
        correlation_id/command_id; WorldState derivado actualizado.
```

### 6.2 Flujo «servicio completo o partes» (detalle)

```
audit_website(url):
    web_scrape(html) + web_search(dominio/marca) + checklist técnico
    → AuditReport { score, checklist: {movil: bool, velocidad: bool,
        seo_basico: bool, redes: bool, gmb: bool, https: bool, ... },
        recommendations: [...] }

regla determinista (en el pipeline, no LLM libre):
    score < 40  → paquete COMPLETO  (web + CM + SEO + GMB + IA)
    score 40-69 → recomendar POR PARTES (solo los gaps del checklist)
    score ≥ 70  → solo OPCIONALES (mantenimiento/IA), sin empujar

ServiceQuote(items=..., total=Σ precios) → validada contra Pydantic
    → require_approval (director) → payment.link.create → envío WhatsApp
```

### 6.3 Matriz de aprobación humana (resumen)

| Capability                              | Efecto            | Frontera de la semiautomatización |
|-----------------------------------------|-------------------|-----------------------------------|
| `crm.contact.create/read`, `crm.deal.create`, `crm.task.create` | `allow`           | El CRM del cliente es fricción necesaria |
| `calendar.event.create/read`            | `allow`           | Agendar cita es el objetivo, no un riesgo |
| `web.*`, `data.lead.validate`           | `allow`           | Lecturas y validación, cero riesgo |
| `whatsapp.message.send` / `template.send` | `require_approval` | Nada se envía a un humano sin visto bueno del director |
| `payment.link.create` / `checkout.create` | `require_approval` | FINANCIAL: nada de cobros sin aprobación |
| `social.post.publish`                   | `require_approval` | Publicar en redes de un cliente requiere aprobación |
| cualquier otra                          | `deny`            | Default-deny |

## 7. Decisiones pendientes / preguntas abiertas

| # | Pregunta | Estado |
|---|----------|--------|
| P1 | **Slug y nombre real del tenant** (`bor-agencia` provisional) | POR DEFINIR |
| P2 | **Provider real prioritario** para conectar primero (¿WhatsApp Cloud API, Google Calendar, HubSpot, Stripe?) o empezar 100% simulado | POR DEFINIR |
| P3 | ¿El **calendario** creado por el bot incluye a BOR como organizador y al cliente final como recurso, o solo el calendario del cliente? | POR DEFINIR |
| P4 | ¿El **primer contacto por WhatsApp** es siempre `require_approval` o solo en horario no comercial / leads sin propietario? | POR DEFINIR |
| P5 | **Servicios IA/agénticos**: ¿se auditan con la misma checklist (`audit_website`) o con checklist propia? | POR DEFINIR |
| P6 | ¿Los **clientes finales** se cargan con credenciales reales desde el inicio o con placeholders para probar el scoped router? | POR DEFINIR |
| P7 | ¿La **cola de aprobación** es solo API o debe tener UI en el frontend React? | POR DEFINIR |
| P8 | ¿Publicar en redes del cliente requiere aprobación **por red** (p. ej. Meta sí, LinkedIn no)? | POR DEFINIR |

## 8. Glosario

| Término | Definición |
|---------|------------|
| **Tenant** | Unidad de aislamiento de datos/credenciales/policy (el facturador). Aquí: la agencia BOR. |
| **Cliente final** | Empresa servida por BOR; entidad `agencia.client` con sus propias credenciales en `TenantConfig.credentials["clients"]`. |
| **Capability** | Verbo canónico del kernel (`crm.contact.create`); el agente solo emite `Command` tipados, nunca SDKs. |
| **MicroAction / Tool** | Ejecución concreta; pasa SIEMPRE por Executor → Policy → Tool. |
| **Pipeline** | Secuencia idempotente de microacciones registrada en `PIPELINES`. |
| **Intent** | Propuesta tipada que el rol `director` (LLM) genera; nunca ejecuta. |
| **require_approval** | Efecto de policy: la acción queda en la cola de aprobación humana. |
| **Scoped connector** | Connector construido con las credenciales de un cliente final concreto. |
| **FrontAssistant (PR)** | Asistente frontal con knowledge base; responde al instante y NO ejecuta acciones. |
| **Orquestador (GA)** | Rol director; propone Intents en background. |
| **Stub / SIMULADO** | Ejecución determinista sin efecto externo real, siempre marcada como tal. |
| **EventLog** | Fuente de verdad (event sourcing); WorldState es derivado por replay. |

## 9. Anexo — mapa completo de archivos a crear/modificar

**Nuevos:**
```
src/agentic_os/domains/agencia/{__init__,ontology,entities,policies,projections}.py
src/agentic_os/connectors/providers/catalog_payments_web.py
src/agentic_os/connectors/scoped.py
src/agentic_os/infrastructure/tenancy/credentials.py
src/agentic_os/execution/tools/{stripe_tool,whatsapp_template_tool,lead_validation_tool,
                              crm_tool,gmb_tool,audit_website_tool}.py
src/agentic_os/orchestration/pipelines/{pipeline_capture_lead,pipeline_nurture_whatsapp,
                              pipeline_book_appointment,pipeline_audit_quote,
                              pipeline_send_payment,pipeline_community_daily,
                              pipeline_gmb_update,pipeline_seo_monitor}.py
data/tenants/bor-agencia/…  data/policies/bor-agencia.json
knowledge/{servicios,proceso_auditoria,faq,politicas_contacto}.md
tests/tenants/test_bor_agencia.py  tests/domains/test_agencia_ontology.py
tests/connectors/test_scoped_router.py  tests/policy/test_agencia_policy.py
tests/pipelines/test_pipelines_agencia.py  tests/webhooks/test_whatsapp_webhook.py
tests/security/test_client_isolation.py
scripts/clean_registry.py (opcional)
```

**Modificados:**
```
src/agentic_os/infrastructure/tenancy/models.py        (TenantConfigPublic: providers por clientes)
src/agentic_os/kernel/ontology/domain_models.py        (registro de entidades del dominio agencia)
src/agentic_os/connectors/core/models.py               (Command.client_id)
src/agentic_os/connectors/providers/__init__.py        (PROVIDER_SPECS.update + validación de campo risk)
src/agentic_os/execution/tools/{__init__,connector_bridge}.py   (ALL_TOOLS + CANONICAL_ALIASES + stamp client_id en output)
src/agentic_os/execution/result.py                     (ExecutionResult.client_id)
src/agentic_os/execution/executor.py                   (propagar client_id y auditar en ActionStarted/ToolCompleted/ToolFailed)
src/agentic_os/orchestration/pipelines/{__init__,runner}.py     (registrar pipelines; tool(client_id) + client_id en PipelineStepError)
src/agentic_os/orchestration/temporal/{workflows,activities}.py (durable, opcional)
src/agentic_os/interfaces/api/rest.py                  (webhook, clients, leads, quotes, approvals)
README.md / docs/spec/*                                (actualizar catálogo y recuentos)
data/tenants/registry.json                             (saneo Fase 0 + alta Fase 6)
```

---

*Fin del documento — v1.0 del plan para el tenant «BOR Agency».*