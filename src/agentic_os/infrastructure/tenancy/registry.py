from __future__ import annotations

import json
import os
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

from ...kernel.types.ids import new_id
from .models import Tenant, TenantConfig, validate_slug


class TenantRegistry:
    """Gestiona el registro de clientes (tenants) del sistema multi-tenant.

    Los tenants se persisten en disco (data/tenants/registry.json) para que
    sobrevivan a reinicios. En producción esto se movería a una base de datos.

    SINGLETON dentro del proceso: todas las instancias comparten el estado en
    memoria (PolicyEngine._tenant() y rest.py usan el mismo registro), de modo
    que un tenant creado/inyectado por la API es visible para las decisiones
    de policy.
    """

    _SHARED_INSTANCE = None

    def __new__(cls, *args, **kwargs):
        if cls._SHARED_INSTANCE is None:
            cls._SHARED_INSTANCE = super().__new__(cls)
        return cls._SHARED_INSTANCE

    def __init__(self, registry_path: Optional[Path] = None):
        if getattr(self, "_initialized", False):
            return
        self.path = registry_path or Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "tenants" / "registry.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._tenants: Dict[str, Tenant] = {}  # key: id
        self._slug_index: Dict[str, str] = {}  # slug -> id
        self._lock = RLock()
        self._last_mtime: Optional[int] = None
        self._initialized = True
        self._load()

    def _load(self) -> None:
        with self._lock:
            if not self.path.exists():
                self._save()
                self._last_mtime = self.path.stat().st_mtime_ns if self.path.exists() else None
                return
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                new_tenants: Dict[str, Tenant] = {}
                new_slug: Dict[str, str] = {}
                for item in raw:
                    t = Tenant(**item)
                    new_tenants[t.id] = t
                    new_slug[t.slug] = t.id
                self._tenants = new_tenants
                self._slug_index = new_slug
                self._last_mtime = self.path.stat().st_mtime_ns
            except Exception as e:
                # NO wipe: mantener tenants en memoria, loguear el error
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    "Error cargando registry.json (posible corrupción): %s. "
                    "Manteniendo %d tenants en memoria.",
                    e, len(self._tenants),
                )
                # Escribir backup del archivo corrupto para diagnóstico
                try:
                    if self.path.exists():
                        backup = self.path.with_suffix(".json.corrupt.bak")
                        self.path.replace(backup)
                        logger.info("Backup de archivo corrupto guardado en: %s", backup)
                except Exception:
                    pass

    def _maybe_reload(self) -> None:
        """Recarga desde disco si el fichero cambió (multi-worker safe).

        Cada worker mantiene su copia en memoria; al detectar un mtime distinto
        (escritura de otro worker) se sincroniza con la fuente de verdad en
        disco antes de resolver lecturas.
        """
        try:
            if not self.path.exists():
                return
            current = self.path.stat().st_mtime_ns
        except OSError:
            return
        if current == self._last_mtime:
            return
        with self._lock:
            # Re-chequear dentro del lock (doble-check)
            try:
                current = self.path.stat().st_mtime_ns
            except OSError:
                return
            if current == self._last_mtime:
                return
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                new_tenants: Dict[str, Tenant] = {}
                new_slug: Dict[str, str] = {}
                for item in raw:
                    t = Tenant(**item)
                    new_tenants[t.id] = t
                    new_slug[t.slug] = t.id
                self._tenants = new_tenants
                self._slug_index = new_slug
                self._last_mtime = current
            except Exception:
                # Corrupción transitoria: mantener estado en memoria, sin wipe.
                return

    def _save(self) -> None:
        with self._lock:
            # Escritura atómica: fichero temporal + os.replace para que un
            # fallo a mitad de escritura nunca corrompa registry.json.
            tmp = self.path.with_suffix(".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump([t.model_dump(mode="json") for t in self._tenants.values()], f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
            try:
                self._last_mtime = self.path.stat().st_mtime_ns
            except OSError:
                self._last_mtime = None

    # --- API usada por rest.py ---

    def list_all(self) -> List[Tenant]:
        self._maybe_reload()
        return list(self._tenants.values())

    def create(self, name: str, slug: str, config: Optional[Dict[str, Any]] = None) -> Tenant:
        self._maybe_reload()
        slug = validate_slug(slug)
        if slug in self._slug_index:
            raise ValueError(f"Ya existe un tenant con slug '{slug}'")

        tenants_root = (Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "tenants").resolve()
        base = (tenants_root / slug).resolve()
        try:
            base.relative_to(tenants_root)
        except ValueError:
            raise ValueError(f"Ruta no permitida para el slug: '{slug}'")

        creds = dict(config.get("credentials", {})) if config else {}
        if "api_key" not in creds:
            creds["api_key"] = f"tk_{new_id().replace('-', '')}"

        t = Tenant(
            id=new_id(),
            slug=slug,
            config=TenantConfig(
                name=name,
                domain=config.get("domain", "generic") if config else "generic",
                data_dir=str(base),
                enabled_capabilities=config.get("enabled_capabilities", []) if config else [],
                credentials=creds,
            ),
        )
        self._tenants[t.id] = t
        self._slug_index[t.slug] = t.id
        self._save()
        return t

    def get(self, identifier: str) -> Optional[Tenant]:
        self._maybe_reload()
        if not isinstance(identifier, str) or not identifier:
            return None
        try:
            needle = validate_slug(identifier)
        except ValueError:
            # Identidad malformada o con path traversal no puede resolver a un tenant.
            return None
        if needle in self._slug_index:
            needle = self._slug_index[needle]
        return self._tenants.get(needle)

    def update(self, tenant: Tenant) -> Tenant:
        self._maybe_reload()
        self._tenants[tenant.id] = tenant
        self._slug_index[tenant.slug] = tenant.id
        self._save()
        return tenant

    def delete(self, identifier: str) -> bool:
        self._maybe_reload()
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