"""Ontologia del dominio `agencia` (FASE 1 - PLAN_AGENCIA_TENANT.md)."""
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
    SocialPost,
)


class AgenciaDomain(BaseDomain):
    domain: str = "agencia"
    entity_kinds: Set[str] = set(AGENCIA_ENTITY_KINDS)
    relation_kinds: Set[str] = {
        "agencia.belongs_to_client",
        "agencia.generates",
        "agencia.programs",
    }
    capability_kinds: Set[str] = {
        "agencia.capture_lead",
        "agencia.validate_lead",
        "agencia.schedule",
        "agencia.quote_service",
    }

    @classmethod
    def register_entities(cls, registry: Dict[str, type] | None = None) -> None:
        from ...kernel.ontology.domain_models import register_entity_types

        cls.compile_ontology()
        register_entity_types(
            AgencyClient,
            AgencyLead,
            AgencyAppointment,
            AgencyDeal,
            ServiceQuote,
            AuditReport,
            SocialPost,
            registry=registry,
        )


__all__ = ["AgenciaDomain"]