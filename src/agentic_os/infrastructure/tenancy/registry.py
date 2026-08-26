from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...kernel.types.ids import new_id
from .models import Tenant, TenantConfig


class TenantRegistry:
    """Gestiona el registro de clientes (tenants) del sistema multi-tenant.

    Los tenants se persisten en disco (data/tenants/registry.json) para que
    sobrevivan a reinicios. En producción esto se movería a una base de datos.
    """

    def __init__(self, registry_path: Optional[Path] = None):
        self.path = registry_path or Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "tenants" / "registry.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._tenants: Dict[str, Tenant] = {}  # key: id
        self._slug_index: Dict[str, str] = {}  # slug -> id
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._save()
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for item in raw:
                t = Tenant(**item)
                self._tenants[t.id] = t
                self._slug_index[t.slug] = t.id
        except Exception:
            self._tenants = {}
            self._slug_index = {}

    def _save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([t.model_dump(mode="json") for t in self._tenants.values()], f, ensure_ascii=False, indent=2)

    # --- API usada por rest.py ---

    def list_all(self) -> List[Tenant]:
        return list(self._tenants.values())

    def create(self, name: str, slug: str, config: Optional[Dict[str, Any]] = None) -> Tenant:
        if slug in self._slug_index:
            raise ValueError(f"Ya existe un tenant con slug '{slug}'")
        base = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "tenants" / slug
        t = Tenant(
            id=new_id(),
            slug=slug,
            config=TenantConfig(
                name=name,
                domain=config.get("domain", "generic") if config else "generic",
                data_dir=str(base),
                enabled_capabilities=config.get("enabled_capabilities", []) if config else [],
                credentials=config.get("credentials", {}) if config else {},
            ),
        )
        self._tenants[t.id] = t
        self._slug_index[t.slug] = t.id
        self._save()
        return t

    def get(self, identifier: str) -> Optional[Tenant]:
        if identifier in self._slug_index:
            identifier = self._slug_index[identifier]
        return self._tenants.get(identifier)

    def update(self, tenant: Tenant) -> Tenant:
        self._tenants[tenant.id] = tenant
        self._slug_index[tenant.slug] = tenant.id
        self._save()
        return tenant

    def delete(self, identifier: str) -> bool:
        t = self.get(identifier)
        if t is None:
            return False
        del self._tenants[t.id]
        del self._slug_index[t.slug]
        self._save()
        return True

    # --- Compatibilidad con la API anterior ---

    def register(self, tenant: Tenant) -> Tenant:
        return self.update(tenant)

    def all(self) -> List[Tenant]:
        return self.list_all()

    def remove(self, slug: str) -> bool:
        if slug in self._slug_index:
            return self.delete(slug)
        return False