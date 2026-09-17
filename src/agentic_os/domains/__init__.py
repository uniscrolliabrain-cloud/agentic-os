"""Dominios: cada tenant es un DomainPack autodescubierto."""
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from .base import BaseDomain, DomainPack


class DomainRegistry:
    """Registry de DomainPacks poblado por auto-discovery de subpaquetes."""

    _instance: "DomainRegistry | None" = None

    def __new__(cls) -> "DomainRegistry":
        if cls._instance is None:
            inst = super().__new__(cls)
            inst._domains: dict[str, DomainPack] = {}
            inst._loaded = False
            cls._instance = inst
        return cls._instance

    def discover(self) -> None:
        if self._loaded:
            return
        pkg_dir = Path(__file__).parent
        for _, name, is_pkg in pkgutil.iter_modules([str(pkg_dir)]):
            if not is_pkg or name.startswith("_"):
                continue
            module = importlib.import_module(f"agentic_os.domains.{name}")
            pack = getattr(module, "DOMAIN", None)
            if pack is None:
                continue
            if not isinstance(pack, DomainPack):
                raise TypeError(
                    f"agentic_os.domains.{name}.DOMAIN debe cumplir DomainPack, "
                    f"recibido {type(pack).__name__}"
                )
            self._domains[pack.slug] = pack
        self._loaded = True

    def get(self, slug: str) -> DomainPack | None:
        self.discover()
        return self._domains.get(slug)

    def all_slugs(self) -> list[str]:
        self.discover()
        return sorted(self._domains)

    def reset(self) -> None:
        self._domains.clear()
        self._loaded = False
        DomainRegistry._instance = None


__all__ = ["BaseDomain", "DomainPack", "DomainRegistry"]
