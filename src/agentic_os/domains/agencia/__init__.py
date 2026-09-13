"""domains.agencia: entidades y ontología del tenant «bor-agencia» (FASE 1)."""
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
from ...kernel.ontology.domain_models import ENTITY_TYPE_REGISTRY

# Auto-registro: el dominio registra sus entidades en el kernel al importarse.
# (El kernel NO importa dominios para evitar import circular con domains.base.)
for _cls in (
    AgencyClient,
    AgencyLead,
    AgencyAppointment,
    AgencyDeal,
    ServiceQuote,
    AuditReport,
):
    ENTITY_TYPE_REGISTRY[_cls.model_fields["kind"].default] = _cls
del _cls

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