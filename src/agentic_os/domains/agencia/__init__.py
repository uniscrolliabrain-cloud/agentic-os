"""domains.agencia: tenant `bor-agencia`.

Sin side-effects en import. El registro de entidades es EXPLICITO
(``AgenciaDomain.register_entities()``). Los pipelines y SOPs son modelos
Pydantic propios del tenant.
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
    SocialPost,
)
from .handlers import HANDLERS
from .ontology import AgenciaDomain
from .pipelines import PIPELINES, AgencyPipeline, PipelineStep
from .sops import SOPS, SOP


class _AgenciaDomainPack:
    slug = "bor-agencia"
    pipelines = PIPELINES
    handlers = HANDLERS
    sops = SOPS

    @staticmethod
    def register_entities() -> None:
        AgenciaDomain.register_entities()


DOMAIN = _AgenciaDomainPack()

__all__ = [
    "DOMAIN",
    "AGENCIA_ENTITY_KINDS",
    "AgenciaDomain",
    "AgencyClient",
    "AgencyLead",
    "AgencyAppointment",
    "AgencyDeal",
    "ServiceQuote",
    "ServiceItem",
    "AuditReport",
    "SocialPost",
    "PIPELINES",
    "AgencyPipeline",
    "PipelineStep",
    "SOPS",
    "SOP",
    "HANDLERS",
]