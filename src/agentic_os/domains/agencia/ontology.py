"""Ontología del dominio `agencia` (FASE 1 — PLAN_AGENCIA_TENANT.md).

Extiende el vocabulario del kernel con los kinds *de dominio* (namespace
``agencia.*``) sin tocar ``DEFAULT_VOCAB``. La compilación fail-closed
(``compile_ontology``) valida contra el metamodelo y produce un
``OntologyBundle`` versionado.
"""
from __future__ import annotations

from typing import Set

from ..base import BaseDomain
from .entities import AGENCIA_ENTITY_KINDS


class AgenciaDomain(BaseDomain):
    """Dominio de la agencia: clientes finales, leads, citas, deals, quotes y auditorías."""

    domain: str = "agencia"
    entity_kinds: Set[str] = set(AGENCIA_ENTITY_KINDS)
    relation_kinds: Set[str] = {
        "agencia.belongs_to_client",  # lead/deal/quote/cita → cliente final
        "agencia.generates",          # lead → deal/quote
        "agencia.programs",           # lead → appointment
    }
    capability_kinds: Set[str] = {
        "agencia.capture_lead",
        "agencia.validate_lead",
        "agencia.schedule",
        "agencia.quote_service",
    }


__all__ = ["AgenciaDomain"]