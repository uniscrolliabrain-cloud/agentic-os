# Agentic OS - Deterministic Enterprise OS

Kernel = invariantes. LLM proposes, system disposes.

## Principios
- Event Sourcing: EventLog es fuente de verdad, WorldState es derivado
- Policy gobierna Capability, no el agente
- LLM nunca ejecuta directo
- Ontology separa metamodelo (invariante) de vocabulario (extensible por dominio)

## Estructura
```
kernel/ - invariantes, estable, versionado
cognition/ - beliefs, reasoning, planning, memory
execution/ - action, executor, tools
orchestration/ - loops, scheduler, VSM
interfaces/ - mcp, api, llm, events
domains/ - clinic, finance (extienden vocabulario)
infrastructure/ - persistence, config, telemetry
```

## Quickstart
```bash
pip install -e .
pytest
```
