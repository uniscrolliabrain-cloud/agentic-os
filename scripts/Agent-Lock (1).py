#!/usr/bin/env python3
"""
agent_lock.py - Lock de archivo para trabajo multi-agente
Cumple invariantes: idempotencia vía command_id, trazabilidad vía queue.jsonl

Uso:
  python scripts/agent_lock.py --agent cline --file data/policies/bor-agencia.json --acquire
  python scripts/agent_lock.py --agent cline --file data/policies/bor-agencia.json --release
  python scripts/agent_lock.py --status

Un lock expira a los 30 min (configurable) para evitar deadlocks si un agente muere.
"""
import argparse
import json
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import sys

LOCK_DIR = Path("data/agents/locks")
QUEUE_FILE = Path("data/agents/queue.jsonl")
LOCK_EXPIRY_MIN = 30

def ensure_dirs():
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not QUEUE_FILE.exists():
        QUEUE_FILE.touch()

def lock_path_for(target_file: str) -> Path:
    # normaliza path a nombre seguro
    safe = target_file.replace("/", "__").replace("\\", "__")
    return LOCK_DIR / f"{safe}.lock"

def read_lock(lp: Path):
    if not lp.exists():
        return None
    try:
        return json.loads(lp.read_text())
    except:
        return None

def write_queue(agent: str, action: str, target_file: str, command_id: str):
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "agent": agent,
        "action": action,
        "file": target_file,
        "command_id": command_id,
        "type": "lock_event"
    }
    with QUEUE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def acquire(agent: str, target_file: str, force: bool = False):
    ensure_dirs()
    lp = lock_path_for(target_file)
    existing = read_lock(lp)
    
    if existing:
        # check expiry
        try:
            ts = datetime.fromisoformat(existing["ts"].replace("Z", ""))
            if datetime.utcnow() - ts > timedelta(minutes=LOCK_EXPIRY_MIN) or force:
                print(f"[LOCK] Lock expirado (> {LOCK_EXPIRY_MIN}min) o forzado, robando lock de {existing['agent']}")
            else:
                print(f"[LOCK] DENY - {target_file} ya bloqueado por {existing['agent']} desde {existing['ts']}")
                print(f"       Usa --force si lleva >{LOCK_EXPIRY_MIN}min colgado")
                sys.exit(1)
        except Exception:
            if not force:
                print(f"[LOCK] DENY - lock corrupto, usa --force para robarlo")
                sys.exit(1)

    command_id = str(uuid.uuid4())
    lock_data = {
        "agent": agent,
        "file": target_file,
        "ts": datetime.utcnow().isoformat() + "Z",
        "command_id": command_id,
        "worktree": str(Path.cwd())
    }
    lp.write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    write_queue(agent, "acquire", target_file, command_id)
    print(f"[LOCK] OK - {target_file} bloqueado por {agent} ({command_id[:8]})")
    return 0

def release(agent: str, target_file: str, force: bool = False):
    ensure_dirs()
    lp = lock_path_for(target_file)
    existing = read_lock(lp)
    
    if not existing:
        print(f"[LOCK] No hay lock para {target_file}")
        return 0
    
    if existing["agent"] != agent and not force:
        print(f"[LOCK] DENY - lock es de {existing['agent']}, no de {agent}. Usa --force")
        sys.exit(1)
    
    command_id = str(uuid.uuid4())
    lp.unlink(missing_ok=True)
    write_queue(agent, "release", target_file, command_id)
    print(f"[LOCK] OK - {target_file} liberado por {agent}")
    return 0

def status():
    ensure_dirs()
    print(f"\n=== LOCKS en {LOCK_DIR} ===")
    locks = list(LOCK_DIR.glob("*.lock"))
    if not locks:
        print("Sin locks activos")
        return
    for lp in locks:
        data = read_lock(lp)
        if data:
            age = datetime.utcnow() - datetime.fromisoformat(data["ts"].replace("Z", ""))
            expired = " [EXPIRADO]" if age > timedelta(minutes=LOCK_EXPIRY_MIN) else ""
            print(f"  {data['file']} -> {data['agent']} hace {int(age.total_seconds()//60)}min{expired}")
        else:
            print(f"  {lp.name} -> corrupto")

    print(f"\n=== QUEUE (últimas 10) en {QUEUE_FILE} ===")
    if QUEUE_FILE.exists():
        lines = QUEUE_FILE.read_text(encoding="utf-8").strip().split("\n")[-10:]
        for l in lines:
            try:
                j = json.loads(l)
                print(f"  {j['ts'][:19]} {j['agent']:6} {j['action']:8} {j['file']}")
            except:
                pass

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--agent", required=False, help="cline|roo|kilo")
    p.add_argument("--file", required=False, help="archivo a bloquear")
    p.add_argument("--acquire", action="store_true")
    p.add_argument("--release", action="store_true")
    p.add_argument("--status", action="store_true")
    p.add_argument("--force", action="store_true", help="forzar robo de lock expirado")
    args = p.parse_args()

    if args.status or (not args.acquire and not args.release):
        status()
    elif args.acquire:
        if not args.agent or not args.file:
            print("Falta --agent y --file")
            sys.exit(1)
        acquire(args.agent, args.file, args.force)
    elif args.release:
        if not args.agent or not args.file:
            print("Falta --agent y --file")
            sys.exit(1)
        release(args.agent, args.file, args.force)
