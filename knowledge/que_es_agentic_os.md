# AGENTE OS

Sistema operativo agéntico determinista para empresas. El kernel impone invariantes,
el LLM solamente propone y el sistema decide.

## Principios

- **Event Sourcing**: el EventLog es la fuente de verdad; el WorldState es derivado.
- **Policy gobierna Capability**: ninguna acción se ejecuta sin pasar por la política.
- **El LLM nunca ejecuta directamente**: solo propone Intents.
- **Dos velocidades**: el usuario habla con el asistente frontal (rápido); el
  orquestador real procesa en segundo plano en el backend.

## Módulos

- kernel: invariantes (world, policy, ontology, types)
- cognition: beliefs, reasoning, planning, memory, skills, roles
- execution: executor + tools (gmail, slack, whatsapp, calendar, scraper, documentation)
- orchestration: loops, scheduler, orchestrator
- interfaces: api (FastAPI), llm, mcp, events
- infrastructure: persistence, config, telemetry, tenancy
- frontend: interfaz React + Tailwind (Vite) — el usuario habla aquí