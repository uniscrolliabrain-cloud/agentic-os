#!/usr/bin/env python3
"""
agent_queue.py - Cola EventLog para 3 agentes (append-only, idempotente)

Es tu EventLog pero para desarrollo. Cada acción deja traza.
Cumple invariantes 2 (traza), 7 (idempotencia via command_id)

Uso:
  python scripts/agent_queue.py --agent cline --action start_task --task "Fase 1 entities"
  python scripts/agent_queue.py --agent roo --action intent --to kilo --msg "necesito client_id"
  python scripts/agent_queue.py --tail 20
"""
import argparse
import json
import uuid
from datetime import datetime
from pathlib import Path

QUEUE_FILE = Path("data/agents/queue.jsonl")
INTENTS_DIR = Path("data/agents/intents")

def ensure():
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    INTENTS_DIR.mkdir(parents=True, exist_ok=True)
    if not QUEUE_FILE.exists():
        QUEUE_FILE.touch()

def log_event(agent: str, action: str, details: dict):
    ensure()
    command_id = details.pop("command_id", str(uuid.uuid4()))
    
    # idempotencia: si command_id ya existe, no duplicar
    if QUEUE_FILE.exists():
        text = QUEUE_FILE.read_text(encoding="utf-8")
        if command_id in text:
            print(f"[QUEUE] SKIP - command_id {command_id[:8]} ya existe (idempotente)")
            return command_id

    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "agent": agent,
        "action": action,
        "command_id": command_id,
        **details
    }
    with QUEUE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[QUEUE] {action} por {agent} -> {command_id[:8]}")
    return command_id

def create_intent(from_agent: str, to_agent: str, msg: str, file: str = ""):
    ensure()
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    cid = str(uuid.uuid4())[:8]
    fname = f"{ts}_{from_agent}-to-{to_agent}_{cid}.md"
    path = INTENTS_DIR / fname
    
    content = f"""---
from: {from_agent}
to: {to_agent}
ts: {datetime.utcnow().isoformat()}Z
command_id: {str(uuid.uuid4())}
file: {file}
---

## Intent: {msg}

### Contexto
- Archivo afectado: {file}
- De: {from_agent} -> Para: {to_agent}

### Acción requerida
Describe aquí que necesitas.

### Respuesta esperada
- [ ] Hecho
- [ ] Bloqueado por: ...
"""
    path.write_text(content, encoding="utf-8")
    log_event(from_agent, "create_intent", {"to": to_agent, "file": str(path), "msg": msg})
    print(f"[INTENT] Creado {path}")
    return path

def tail(n: int):
    ensure()
    if not QUEUE_FILE.exists():
        print("Queue vacía")
        return
    lines = QUEUE_FILE.read_text(encoding="utf-8").strip().split("\n")
    lines = [l for l in lines if l.strip()][-n:]
    print(f"\n=== Últimos {n} eventos ===")
    for l in lines:
        try:
            j = json.loads(l)
            print(f"{j['ts'][:19]} | {j['agent']:5} | {j['action']:15} | {j.get('file','')[:50]} | {j['command_id'][:8]}")
        except:
            print(l)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--agent", help="cline|roo|kilo|director")
    p.add_argument("--action", help="start_task|finish_task|modify|create_intent|merge")
    p.add_argument("--task", help="descripción tarea")
    p.add_argument("--file", help="archivo afectado")
    p.add_argument("--to", help="agente destino para intent")
    p.add_argument("--msg", help="mensaje intent")
    p.add_argument("--tail", type=int, help="ver últimos N")
    p.add_argument("--command-id", help="para idempotencia")
    args = p.parse_args()

    if args.tail:
        tail(args.tail)
    elif args.action == "intent" or args.to:
        if not args.agent or not args.to or not args.msg:
            print("Falta --agent --to --msg")
        else:
            create_intent(args.agent, args.to, args.msg, args.file or "")
    elif args.agent and args.action:
        details = {}
        if args.task: details["task"] = args.task
        if args.file: details["file"] = args.file
        if args.command_id: details["command_id"] = args.command_id
        if args.to: details["to"] = args.to
        log_event(args.agent, args.action, details)
    else:
        print("Uso: --agent X --action Y  | --tail 20 | --agent X --to Y --msg ...")
