# Plantilla obligatoria de especificación de miniagente

Todo miniagente nuevo debe completar esta plantilla en el catálogo. Cline NO crea
un agente que no la cumpla. Al lado de cada campo se indica la fuente del catálogo.

```
# AGENT SPECIFICATION

ID:   <familia_id>_<name_agent>
NAME: <Nombre>
VERSION: <semver>

## ONTOLOGY
ENTITY_TYPES:   [...de 03]
ACTION_TYPES:   [...de 04]
CONTEXT_TYPES:  [User, Client, Project, Brand, Campaign, Goal, Constraint, Permission]
STATE_TYPES:    [Pending, Running, Completed, Failed, Blocked, NeedsApproval, Cancelled]

## PROPÓSITO
PURPOSE: <qué consigue el agente>

## TRIGGERS
TRIGGERS: <patrones que disparan el agente>

## CONTRATO DE ENTRADA
INPUT_SCHEMA:      <JSON schema, ver 07>
INPUT_VALIDATION:  <reglas>

## PRECONDICIONES
PRECONDITIONS: <list>

## MICROACCIONES
MICROACTIONS: <ids de 08_MICROACTION_CATALOG.md usadas>

## HERRAMIENTAS
TOOLS: <tools permitidas, ver 06>

## DECISION RULES / SOP
DECISION_RULES: <reglas de razonamiento donde aplica>
SOP: <pipeline de 09 o descripción de pasos>

## CONTRATO DE SALIDA
POSTCONDITIONS: <list>
OUTPUT_SCHEMA:  <JSON schema>
OUTPUT_VALIDATION: <reglas QA de 16>

## ERRORES Y RECUPERACIÓN
ERROR_TYPES:    <de 12>
RETRY_POLICY:   <json>
TIMEOUT_POLICY: <json>

## POLÍTICAS
PERMISSION_POLICY:     <roles permitidos, deny_by_default>
HUMAN_APPROVAL_POLICY: <qué requiere humano, ver 14>

## ESTADOS / TRANSICIONES
STATE_TRANSITIONS: <05_STATE_MACHINE>

## COMPOSICIÓN
HANDOFFS: <ids de agentes que puede llamar, ver 19>
DEPENDENCIES: <list>

## OBSERVABILIDAD
OBSERVABILITY: <qué eventos emite, ver 17>

## TEST_CASES
TEST_CASES: <list, ver 18>
```

## Checklist de aceptación

- [ ] Todos los campos rellenos (nada en blanco).
- [ ] INPUT_SCHEMA y OUTPUT_SCHEMA validables con pydantic.
- [ ] MICROACTIONS existen en `08`.
- [ ] SOP referencia un pipeline de `09`.
- [ ] TOOLS existen en ToolRegistry.
- [ ] HANDOFFS/DEPENDENCIES referencian agentes y microacciones existentes.
- [ ] Policy define permisos y aprobación.
- [ ] Test implementado y `pytest` verde.
- [ ] No toca `kernel/`.