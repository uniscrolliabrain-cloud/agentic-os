# Hardening v2 — Agentic OS

## Ejecutivo

Este documento define la estrategia de hardening para **Agentic OS**, un sistema operativo agente enterprise. La estrategia se basa en el audit de 11 fases y 100 micro-prompts (`AGENTIC OS — ENTERPRISE FOUNDATIONS.md`) y en el trabajo ya realizado (FASE 1.1, FASE 6.2, corrección de bugs críticos).

El principio rector es: **"El LLM propone, el sistema dispone"**. Todo efecto secundario debe fluir a través del Executor inyectado y ser gobernado por el PolicyEngine.

---

## Estado Actual del Repositorio

### Completado

| Fase | Descripción | Estado |
|------|-------------|--------|
| FASE 1.1 | Contratos de E/S Básicos (`contracts/core.py`) | ✅ Completada |
| FASE 6.2 | CredentialStore Cripto-Hardening | ✅ Completada |
| Bug Fix | Scheduler graceful handling + entity update | ✅ Completada |
| Bug Fix | Revert EventPayload (conflicto de imports) | ✅ Completada |

### En Progreso

| Fase | Descripción | Estado |
|------|-------------|--------|
| FASE 1 (Parcial) | Kernel: Contratos, Tipos e Invariantes | 🔄 1/10 completado |
| FASE 6 (Parcial) | Credenciales Atómicas | 🔄 1/10 completado |

### Pendiente

| Fase | Descripción | Prioridad |
|------|-------------|-----------|
| FASE 1 | Kernel (resto) | 🔴 Alta |
| FASE 2 | Ontología | 🔴 Alta |
| FASE 3 | Identidad | 🔴 Alta |
| FASE 4 | Model Mesh | 🟡 Media |
| FASE 5 | SMC | 🟡 Media |
| FASE 6 | Credenciales (resto) | 🟡 Media |
| FASE 7 | Conectores | 🟢 Baja |
| FASE 8 | Event Sourcing | 🟡 Media |
| FASE 9 | API REST | 🟢 Baja |
| FASE 10 | Hardening Final | 🟡 Media |


---

## Estrategia de Ejecución

### Principios Invariables

1. **Inspección antes de programar**: Leer imports y comportamiento real antes de modificar.
2. **Sin placeholders**: Prohibido `pass`, `TODO`, `...`, `Any` como sustitutos.
3. **Validación obligatoria**: Tests + lint + typecheck al finalizar cada paso.
4. **Ley del Kernel**: Todo efecto externo pasa por Executor + PolicyEngine.
5. **Fail-closed**: Si la auditoría no puede persistirse, la operación falla.

### Secuencia de Trabajo

Para evitar dependencias circulares e incoherencias de imports, el desarrollo sigue esta secuencia exacta:

```
FASE 1 (Kernel) → FASE 2 (Ontología) → FASE 3 (Identidad)
                                            ↓
FASE 4 (Model Mesh) ← FASE 3 (Identidad)
          ↓
FASE 5 (SMC) → FASE 6 (Credenciales) → FASE 7 (Conectores)
                                            ↓
FASE 8 (Event Sourcing) ← FASE 7
          ↓
FASE 9 (API REST) → FASE 10 (Hardening Final)
```

---

## Plan de Acción Detallado

### FASE 1: Kernel — Contratos, Tipos e Invariantes

| Paso | Descripción | Entregable |
|------|-------------|------------|
| 1.1 | Contratos de E/S Básicos | `contracts/core.py` ✅ |
| 1.2 | Tipar Command/Action | Modelos Pydantic discriminados |
| 1.3 | Tipar Relations | Relaciones ontológicas tipadas |
| 1.4 | Fortalecer invariantes | Invariantes ejecutables |
| 1.5 | Auditoría del runtime | Runtime audit |
| 1.6 | Unificación temporal | Reloj canónico |
| 1.7 | Trazabilidad del runtime | Correlation IDs |
| 1.8 | Regresión del runtime | Tests de regresión |
| 1.9 | Calidad estética | Consistencia de código |
| 1.10 | Gate de cierre | Validación final |

### FASE 2: Ontología — Inventario y Entidades

| Paso | Descripción | Entregable |
|------|-------------|------------|
| 2.1 | Inventario ontológico | Catálogo de entidades |
| 2.2 | Base física de entidades | Modelos Pydantic |
| 2.3 | Entidades Sales | Lead, Proposal |
| 2.4 | Entidades Marketing | Campaign, Brand |
| 2.5 | Entidades Content/Coaching | BlogPost, SessionNote |
| 2.6 | Entity Class Registry | Registro centralizado |
| 2.7 | WorldState | Estado del mundo tipado |
| 2.8 | World Applier | Aplicador de eventos |
| 2.9 | Replay seguro | Replay de eventos |
| 2.10 | Gate ontológico | Validación final |

### FASE 3: Identidad — JWT y Autenticación

| Paso | Descripción | Entregable |
|------|-------------|------------|
| 3.1 | Tenant Boundary Audit | Auditoría de tenants |
| 3.2 | User Context | Contexto de usuario |
| 3.3 | User Registry | Registro de usuarios |
| 3.4 | JWT | Tokens JWT |
| 3.5 | Dependencia canónica de autenticación | Auth centralizada |
| 3.6 | Policy Engine | Motor de políticas |
| 3.7 | Human Approval Invariant | Aprobación humana |
| 3.8 | Autorización por UserContext | Autorización |
| 3.9 | Tenant isolation end-to-end | Aislamiento |
| 3.10 | Gate de seguridad | Validación final |


### FASE 4: Model Mesh — Providers y Routing

| Paso | Descripción | Entregable |
|------|-------------|------------|
| 4.1 | Provider Registry | Registro de providers |
| 4.2 | Model Router | Router de modelos |
| 4.3 | Selección de provider | Selección automática |
| 4.4 | Rate Limiting | Limitar requests |
| 4.5 | Structured Routing | Routing estructurado |
| 4.6 | Parallel Structured Inference | Inferencia paralela |
| 4.7 | EventLog del Model Mesh | Eventos |
| 4.8 | Fallback | Fallback de providers |
| 4.9 | Settings | Configuración |
| 4.10 | Gate del Model Mesh | Validación final |

### FASE 5: SMC — Semantic Compiler

| Paso | Descripción | Entregable |
|------|-------------|------------|
| 5.1 | Estructura del Semantic Compiler | Arquitectura |
| 5.2 | Contratos de Matching | Matching de intents |
| 5.3 | Resultado del Compilador | Resultados |
| 5.4 | Classifier | Clasificador |
| 5.5 | Mapeo Intent-Contrato | Mapeo |
| 5.6 | Crystallizer | Cristalizador |
| 5.7 | Reprompt Autocorrectivo | Autocorrección |
| 5.8 | Compilador Principal | Compilador |
| 5.9 | SMC en API | Endpoints |
| 5.10 | Gate del SMC | Validación final |

### FASE 6: Credenciales — Atomic Credential Store

| Paso | Descripción | Entregable |
|------|-------------|------------|
| 6.1 | Auditoría de Secretos | Auditoría |
| 6.2 | CredentialStore Fernet | Store cifrado ✅ |
| 6.3 | Persistencia Atómica de Credenciales | Escritura atómica |
| 6.4 | OAuth Manager | OAuth |
| 6.5 | Token Manager | Tokens |
| 6.6 | Inyección del Token Manager | Inyección |
| 6.7 | Redacción de Secretos | Redacción |
| 6.8 | Aislamiento de Credenciales | Aislamiento |
| 6.9 | Ciclo de Vida Completo | Ciclo de vida |
| 6.10 | Gate de Credenciales | Validación final |

### FASE 7: Conectores — Gmail, Slack, etc.

| Paso | Descripción | Entregable |
|------|-------------|------------|
| 7.1 | Contrato Connector | Interfaz |
| 7.2 | Google Connector Base | Google base |
| 7.3 | Gmail | Gmail |
| 7.4 | Google Drive | Drive |
| 7.5 | Google Calendar | Calendar |
| 7.6 | HubSpot | HubSpot |
| 7.7 | Slack | Slack |
| 7.8 | Connector Router | Router |
| 7.9 | Auditoría de Efectos Externos | Auditoría |
| 7.10 | Gate de Connectivity | Validación final |

### FASE 8: Event Sourcing — Invariantes y Rate Limiting

| Paso | Descripción | Entregable |
|------|-------------|------------|
| 8.1 | EventLog JSONL | EventLog |
| 8.2 | AuditLog Real | Auditoría |
| 8.3 | Event Invariants | Invariantes |
| 8.4 | State Transition Invariants | Transiciones |
| 8.5 | Policy Invariants | Políticas |
| 8.6 | Sliding Window Correcta | Ventana deslizante |
| 8.7 | Rate Limiter Concurrente | Rate limiting |
| 8.8 | Cierre de API Execute | Cierre |
| 8.9 | Fail Closed Global | Fail-closed |
| 8.10 | Gate de Event Sourcing | Validación final |

### FASE 9: API REST — Chat, Tasks, Scheduler

| Paso | Descripción | Entregable |
|------|-------------|------------|
| 9.1 | Auditoría REST | Auditoría |
| 9.2 | Configuración API | Config |
| 9.3 | Chat LAIA SMC | Chat |
| 9.4 | Task State | Estado de tareas |
| 9.5 | Execution Plan | Planes |
| 9.6 | MiniAgent Contratos | MiniAgents |
| 9.7 | Failure Policy | Fallos |
| 9.8 | Scheduler | Scheduler |
| 9.9 | E2E sin red real | E2E |
| 9.10 | Gate End-to-End | Validación final |

### FASE 10: Hardening Final — Tests y Producción

| Paso | Descripción | Entregable |
|------|-------------|------------|
| 10.1 | PyProject | Configuración |
| 10.2 | Repositorio Limpio | Limpieza |
| 10.3 | Security Sweep | Seguridad |
| 10.4 | Auditoría Pydantic de Verdad | Pydantic |
| 10.5 | Error Handling | Manejo de errores |
| 10.6 | Matriz de Tests | Tests |
| 10.7 | Adversarial Testing | Tests adversarios |
| 10.8 | Auditoría Estética Final | Estética |
| 10.9 | Auditoría de Producción | Producción |
| 10.10 | Final Kernel Release Gate | Gate final |


---

## Métricas de Éxito

### Cobertura de Tests
- **Objetivo**: >90% coverage en módulos críticos
- **Actual**: ~70% (estimado)

### Seguridad
- **Objetivo**: 0 vulnerabilidades críticas
- **Checklist**:
  - [ ] Fail-closed en todos los stores
  - [ ] Escritura atómica de credenciales
  - [ ] Redacción de secretos en logs
  - [ ] Aislamiento multi-tenant verificado
  - [ ] Tests adversarios pasando

### Calidad de Código
- **Objetivo**: 0 errores de ruff, 0 errores de mypy

---

## Gestión de Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Conflictos de imports entre fases | Alta | Alta | Seguir secuencia estricta |
| Duplicación de modelos (PR #1) | Alta | Media | Revisión de PR antes de merge |
| Incompatibilidad de APIs | Media | Alta | Adapters para compatibilidad |
| Tests insuficientes | Media | Alta | Tests obligatorios por paso |
| Deuda técnica acumulada | Alta | Media | Gate de cierre por fase |

---

## Conclusión

La estrategia de hardening para Agentic OS se basa en:

1. **Ejecución secuencial**: Las fases deben completarse en orden para evitar conflictos.
2. **Fail-closed**: Cualquier operación que no pueda auditarse debe fallar.
3. **Validación obligatoria**: Tests + lint + typecheck al finalizar cada paso.
4. **Ley del Kernel**: Todo efecto externo pasa por Executor + PolicyEngine.

**Próximos pasos recomendados**:
1. Completar FASE 1 (Kernel) — 9 micro-prompts restantes
2. Completar FASE 2 (Ontología) — 10 micro-prompts
3. Completar FASE 3 (Identidad) — 10 micro-prompts
4. Resolver conflictos del PR #1 antes de mergear

---

*Documento generado: 2026-09-09*
*Autor: Cline (Agente de Hardening)*
*Versión: 1.0*
