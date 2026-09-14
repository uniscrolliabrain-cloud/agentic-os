"""Ontología del dominio `agencia` (FASE 1 — PLAN_AGENCIA_TENANT.md).

Extiende el vocabulario del kernel con los kinds *de dominio* (namespace
``agencia.*``) sin tocar ``DEFAULT_VOCAB``. La compilación fail-closed
(``compile_ontology``) valida contra el metamodelo y produce un
``OntologyBundle`` versionado.
"""
from __future__ import annotations

from typing import Dict, Set

from ..base import BaseDomain
from .entities import (
    AgencyAppointment,
    AgencyClient,
    AgencyDeal,
    AgencyLead,
    AGENCIA_ENTITY_KINDS,
    AuditReport,
    ServiceQuote,
)


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

    @classmethod
    def register_entities(
        cls,
        registry: Dict[str, type] | None = None,
    ) -> None:
        """Registra las entidades del dominio en ENTITY_TYPE_REGISTRY.

        Camino canónico (docs/spec/01_ONTOLOGY.md, docs/INVARIANTS.md):
        primero compila la ontología fail-closed contra el metamodelo y
        después registra vía ``register_entity_types``. NUNCA como
        side-effect en import: el registro es una operación explícita de
        bootstrap, idempotente y fail-closed ante colisiones de kind.
        """
        from ...kernel.ontology.domain_models import register_entity_types

        cls.compile_ontology()  # fail-closed: vocabulario válido o no se registra
        register_entity_types(
            AgencyClient,
            AgencyLead,
            AgencyAppointment,
            AgencyDeal,
            ServiceQuote,
            AuditReport,
            registry=registry,
        )


__all__ = ["AgenciaDomain"]