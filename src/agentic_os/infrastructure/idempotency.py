from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
IDEMPOTENCY_DIR = DATA_DIR / "idempotency"
TTL_SECONDS = 24 * 60 * 60 # 24h como Stripe

class IdempotencyStore:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir) if base_dir else IDEMPOTENCY_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, tenant_id: str, command_id: str) -> Path:
        # sanitize
        safe_tenant = "".join(c for c in tenant_id if c.isalnum() or c in "-_")[:64]
        safe_cmd = "".join(c for c in command_id if c.isalnum() or c in "-_")[:128]
        d = self.base_dir / safe_tenant
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{safe_cmd}.json"

    def get(self, tenant_id: str, command_id: str) -> Optional[Dict[str, Any]]:
        if not command_id:
            return None
        p = self._path(tenant_id, command_id)
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            # TTL check
            created = data.get("_created_at", 0)
            if time.time() - created > TTL_SECONDS:
                p.unlink(missing_ok=True)
                return None
            return data.get("result")
        except Exception:
            return None

    def save(self, tenant_id: str, command_id: str, result: Dict[str, Any]) -> None:
        if not command_id:
            return
        p = self._path(tenant_id, command_id)
        tmp = p.with_suffix(".tmp")
        payload = {
            "_created_at": time.time(),
            "_tenant_id": tenant_id,
            "_command_id": command_id,
            "result": result,
        }
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(p)

    def exists(self, tenant_id: str, command_id: str) -> bool:
        return self.get(tenant_id, command_id) is not None
