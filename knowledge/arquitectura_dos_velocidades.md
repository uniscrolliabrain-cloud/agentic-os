# Arquitectura de dos velocidades

El chat tiene dos capas para que el usuario nunca espere:

1. **Asistente frontal (PR)** — con quien habla el usuario. Rápido, natural,
   con knowledge base local. Responde en segundos usando GEMINI_CHAT_MODEL.

2. **Orquestador (back office)** — se dispara en segundo plano tras cada mensaje.
   El rol "director" (GEMINI_MODEL) propone una Intent estructurada, pasa por el
   PolicyEngine (permiso del tenant), el Executor la ejecuta si aplica y todo se
   registra en el EventLog (auditable). El usuario nunca le habla en la línea
   de espera: si falla o tarda, la conversación ya está servida.

## Flujo

```
Usuario escribe
   │
   ├─ (rápido)  FrontAssistant: persona PR + knowledge base → responde al momento
   │
   └─ (background) Orchestrator: propone Intent → Policy valida → Executor ejecuta
                                     → EventLog (auditable)
```

## Configuración

- `GEMINI_CHAT_MODEL` → modelo del asistente frontal (rápido)
- `GEMINI_MODEL` → modelo del orquestador (back office)