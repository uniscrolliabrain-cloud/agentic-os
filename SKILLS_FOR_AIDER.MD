
### 📋 Prompt Maestro para Cline: Arquitectura Híbrida de Skills

```text
CONSIGNAS DE IMPLEMENTACIÓN: ARQUITECTURA HÍBRIDA DE SKILLS (PROMPT + EXECUTION)

Hola Cline. Vas a implementar el sistema híbrido de "Prompt Skills" (estilo Claude) y "Execution Skills" (Pydantic/SOP) en nuestro Agentic OS. Para evitar errores y mantener a salvo nuestras invariantes críticas, lee detenidamente este mapa de contexto y sigue las instrucciones paso a paso.

--------------------------------------------------------------------------------
1. MAPA DEL REPOSITORIO Y FUENTE DE VERDAD
--------------------------------------------------------------------------------
Nuestra estructura de archivos cognition, memory y execution es exactamente esta:

- 'src/agentic_os/cognition/skills/skill.py'
  Define las clases inmutables (frozen=True) de ejecución:
  * 'SkillStep': order, name, tool, requires, validation
  * 'Skill': name, description, requires_tool, steps, role_required, input_schema, output_schema

- 'src/agentic_os/cognition/skills/library.py'
  Contiene nuestro diccionario de registro 'SKILLS' con las instancias Pydantic preconfiguradas (como 'inbox_zero', 'schedule_meeting', etc.).

- 'src/agentic_os/cognition/memory/store.py'
  Contiene:
  * 'MemoryItem(frozen=True)': id, content, metadata
  * 'MemoryStore': Almacén en memoria con búsqueda determinista 'search(query)'.

- 'src/agentic_os/cognition/beliefs/belief.py'
  Define 'Belief(frozen=True)': id, kind, content, confidence, source_observation_id, created_at

- 'src/agentic_os/cognition/memory/working.py'
  Define 'WorkingMemory(BaseModel)': beliefs: List[dict], capacity: int = 7 (Ley de Miller)

- 'src/agentic_os/execution/executor.py'
  Contiene 'Executor': Clase encargada de validar políticas con PolicyEngine y correr las herramientas correspondientes.

- 'src/agentic_os/kernel/policy/engine.py'
  Contiene 'PolicyEngine': Motor que autoriza o deniega capacidades por tenant ('decide', 'is_allowed', 'can_for_tenant').

--------------------------------------------------------------------------------
2. NUESTRAS MATEMÁTICAS DETERMINISTAS ("MAGNETISMO")
--------------------------------------------------------------------------------
La búsqueda de recuerdos y prompts en 'MemoryStore.search' ya implementa de manera nativa nuestro score de polaridad determinista. Usa exactamente esta lógica de conteo de coincidencias sin añadir embeddings o Chroma:

```python
def search(self, query: str) -> list[MemoryItem]:
    q = (query or "").strip().lower()
    if not q:
        return []
    terms = q.split()
    scored: list[tuple[int, str, MemoryItem]] = []
    for item in self._items.values():
        haystack = " ".join(
            [item.id, item.content]
            + [str(v) for v in item.metadata.values()]
        ).lower()
        score = sum(haystack.count(t) for t in terms)
        if score > 0:
            scored.append((score, item.id, item))
    scored.sort(key=lambda t: (-t, t))
    return [item for _, _, item in scored]
```

--------------------------------------------------------------------------------
3. TAREAS DE IMPLEMENTACIÓN PASO A PASO
--------------------------------------------------------------------------------

REALIZA ESTAS TRES TAREAS RESPETANDO LA INMUTABILIDAD (frozen=True) DE LOS MODELOS:

TAREA 1: INSTALADOR DE PROMPT SKILLS ('install_skill')
1. En 'src/agentic_os/cognition/skills/library.py', añade la función:
   'install_skill(skill_md_content: str, tenant_id: str) -> MemoryItem'
2. Esta función debe:
   - Procesar una cadena Markdown que representa un prompt estilo Claude ('SKILL.md'). El archivo contiene obligatoriamente un frontmatter de YAML con las propiedades: 'name', 'description', 'version', y 'pipeline_id' (o triggers). Puedes usar el paquete 'yaml' (ya registrado en pyproject.toml).
   - Validar que el 'pipeline_id' o 'name' extraído del frontmatter exista en nuestro registro Pydantic inmutable de 'SKILLS' en 'library.py' (Mecanismo fail-closed: si no existe un Skill ejecutable correspondiente, cancela la instalación arrojando un ValueError).
   - Convertir el contenido completo del markdown en un 'MemoryItem' con 'id = f"skill:{name}:prompt"', 'content = markdown_body' y un diccionario de metadatos obligatorio que asocie: 'tenant_id', 'version', 'pipeline_id', 'triggers' y el hash MD5 del contenido para mitigar el drift.
   - Persistir la ficha guardándola en el 'MemoryStore' del sistema.
   - Obtener el repositorio de eventos usando 'from agentic_os.infrastructure.persistence import get_eventlog_repo' y registrar un evento de tipo 'SkillInstalled' asociado al respectivo 'tenant_id'.

TAREA 2: DISCOVERY Y DIVULGACIÓN PROGRESIVA EN EL PROPOSER
1. Modifica la lógica de preparación de contexto en 'LLMProposer' (o el Retriever de 'src/agentic_os/cognition/memory/retrieval.py' que usa el proposer) para que no cargue todo el catálogo de prompts en el prompt de sistema.
2. Al recibir una petición, usa el buscador determinista ('MemoryStore.search') filtrando por el 'tenant_id' activo para recuperar únicamente el top 3 de Prompt Skills instalados que tengan mayor magnetismo de atracción.
3. Convierte cada uno de estos top 3 'MemoryItem' recuperados en instancias de 'Belief' con 'kind="skill_available"' y una confianza de activación proporcional a su score.
4. Asegura que la inyección de creencias en la memoria de trabajo respete estrictamente el límite de capacidad de Miller ('WorkingMemory.capacity = 7') para evitar la saturación del contexto del LLM.
5. Inyecta el contenido de las instrucciones del 'SKILL.md' únicamente de los top 3 seleccionados dentro del prompt que genera 'build_intent_proposal_prompt'.

TAREA 3: BLINDAJE DE EJECUCIÓN (POLICY ENGINE GATE)
1. Bajo ningún concepto permitas que las instrucciones de texto libre ('SKILL.md') se interpreten o evalúen como comandos ejecutables directos por el sistema (prevención de Prompt Injection). El Prompt Skill es puramente consultivo para que el Proposer genere un 'Intent' estructurado de manera gobernada.
2. El 'Executor' ('src/agentic_os/execution/executor.py') recibe ese 'Intent' y lo mapea obligatoriamente a una de nuestras clases 'Skill' Pydantic congeladas en 'library.py'.
3. Antes de despachar la ejecución de cualquier herramienta real (ej. 'gmail_send' mediante 'ConnectorBridgeTool'), el 'Executor' debe llamar obligatoriamente al motor de políticas: 'self.policy.decide(tenant_id=tid, capability=action, roles=roles)'.
4. Si el rol del agente ejecutor (por ejemplo, 'operator') tiene la herramienta requerida listada dentro de su 'forbidden_tools' ('src/agentic_os/cognition/roles/library.py'), detén la ejecución en seco y devuelve un resultado fallido con el detalle del error de seguridad.

Por favor, confirma que has localizado las clases inmutables y el almacén de memoria antes de comenzar a editar los archivos.
```

---

### ¿Por qué este enfoque es perfecto para tu repositorio?
* **Alineado con tus tests existentes:** Al indicarle el comportamiento exacto de `search(query)` con el conteo de términos en el *haystack*, respetamos el test de pytest `test_search_coincidencia_y_orden` que ya tienes en verde.
* **Seguridad Multi-tenant Real:** Forzamos a Cline a asociar el `tenant_id` obligatorio en los metadatos de las fichas de memoria y a validar contra el `PolicyEngine`, respetando tus invariantes de aislamiento.
* **Integración limpia con el EventLog:** Se le pide explícitamente usar `get_eventlog_repo` para auditarlo de la forma canónica que espera tu base de datos de eventos.

