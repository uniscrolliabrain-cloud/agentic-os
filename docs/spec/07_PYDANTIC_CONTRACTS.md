# 07 — Contratos Pydantic (sistema nervioso tipado)

Estos son los `BaseModel` (frozen) que estructuran TODO el sistema. Se
implementan en `src/agentic_os/cognition/agents/schemas.py` (nuevo) y se
validan al cargar el catálogo (fallo de validación = el sistema no arranca el agente).

## MicroActionSchema

```python
class MicroActionSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str                      # p.ej. "web.extract_page"
    action_type: str             # de 04_ACTION_TYPES (p.ej. "Read")
    entity_type: str             # de 03_ENTITY_TYPES (p.ej. "Document")
    taxonomy: str                # familia de 02_TAXONOMY (p.ej. "WEB")
    purpose: str
    input_schema: dict           # JSON-schema del input
    preconditions: list[str]
    tool: str                    # nombre de tool del registry
    output_schema: dict          # JSON-schema del output
    validation: list[str]        # reglas QA (06.md)
    error_states: list[str]      # de 05_STATE_MACHINE / 12_ERROR_HANDLING
    handoff: list[str]           # ids de microacciones/pipelines que pueden seguir
    timeout_seconds: int = 60
    retry_policy: dict = Field(default_factory=dict)  # {"max_retries": 1, "backoff": 1.5}
```

## PipelineSchema

```python
class PipelineStep(BaseModel):
    model_config = ConfigDict(frozen=True)
    order: int
    microaction_id: str
    param_override: dict = Field(default_factory=dict)
    if_else: Optional[dict] = None   # {"condition": "...", "then": step, "else": step}


class PipelineSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    name: str
    purpose: str
    steps: list[PipelineStep]
    input_schema: dict
    output_schema: dict
    error_recovery: dict = Field(default_factory=dict)
```

## MiniAgentSchema (la plantilla 20-28 campos)

```python
class MiniAgentSchema(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str                        # p.ej. "web_research_agent"
    name: str
    version: str
    ontology: dict                 # entidades/acciones/contexto/estados que entiende
    purpose: str
    triggers: list[str]            # patrones que disparan este agente
    input_schema: dict
    input_validation: list[str]
    preconditions: list[str]
    microactions: list[str]        # ids
    tools: list[str]               # tools permitidas (aislamiento)
    decision_rules: list[str]      # reglas de razonamiento donde aplica
    sop: str                       # referencia al pipeline principal
    postconditions: list[str]
    output_schema: dict
    output_validation: list[str]
    error_types: list[str]
    retry_policy: dict
    timeout_policy: dict
    permission_policy: dict        # roles permitidos
    human_approval_policy: dict    # qué decisiones requieren humano
    state_transitions: dict
    handoffs: list[str]            # miniagentes que pueden continuar
    dependencies: list[str]
    observability: list[str]
    test_cases: list[str]
```

## TaskGraph

```python
class TaskNode(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    agent_id: str
    depends_on: list[str] = Field(default_factory=list)
    status: str = "pending"        # de 05_STATE_MACHINE
    input: dict = Field(default_factory=dict)
    output: Optional[dict] = None


class TaskPlan(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    mission: str
    nodes: list[TaskNode]
    owner_tenant_id: Optional[str] = None
```

## Reglas de validación del sistema nervioso

1. Cualquier agente/pipeline/microacción que no valide contra su schema se **rechaza en carga** (fail-fast).
2. Los `id` deben ser únicos y estables (son referencias del catálogo).
3. `tools` de un agente deben existir en `ToolRegistry`.
4. `handoffs` deben referenciar ids que existen en el catálogo.
5. Insertar un agente nuevo nunca modifica estos schemas (serían breaking → exige nueva versión).