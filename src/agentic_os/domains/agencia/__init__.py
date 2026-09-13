"""domains.agencia: entidades y ontología del tenant «bor-agencia» (FASE 1).

Sin side-effects en import: el registro de entidades en
``ENTITY_TYPE_REGISTRY`` es EXPLICITO, via ``AgenciaDomain.register_entities()``
(camino canónico ``compile_ontology`` -> registro). Ver docs/INVARIANTS.md.
"""
from .entities import (
    AGENCIA_ENTITY_KINDS,
    AgencyAppointment,
    AgencyClient,
    AgencyDeal,
    AgencyLead,
    AuditReport,
    ServiceItem,
    ServiceQuote,
)
from .ontology import AgenciaDomain

__all__ = [
    "AGENCIA_ENTITY_KINDS",
    "AgenciaDomain",
    "AgencyClient",
    "AgencyLead",
    "AgencyAppointment",
    "AgencyDeal",
    "ServiceQuote",
    "ServiceItem",
    "AuditReport",
]
