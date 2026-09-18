"""TaxonomyFamily: las 15 familias de capacidades (spec 02) + futuras."""
from __future__ import annotations

from typing import FrozenSet


class TaxonomyFamily(str):
    WEB = "WEB"
    RESEARCH = "RESEARCH"
    DOCUMENTS = "DOCUMENTS"
    DATA = "DATA"
    CONTENT = "CONTENT"
    CREATIVE = "CREATIVE"
    COMMUNICATION = "COMMUNICATION"
    SOCIAL = "SOCIAL"
    CRM = "CRM"
    SALES = "SALES"
    MARKETING = "MARKETING"
    SOFTWARE = "SOFTWARE"
    DATABASE = "DATABASE"
    AUTOMATION = "AUTOMATION"
    ANALYTICS = "ANALYTICS"


ALL_FAMILIES: FrozenSet[str] = frozenset({
    TaxonomyFamily.WEB, TaxonomyFamily.RESEARCH, TaxonomyFamily.DOCUMENTS,
    TaxonomyFamily.DATA, TaxonomyFamily.CONTENT, TaxonomyFamily.CREATIVE,
    TaxonomyFamily.COMMUNICATION, TaxonomyFamily.SOCIAL, TaxonomyFamily.CRM,
    TaxonomyFamily.SALES, TaxonomyFamily.MARKETING, TaxonomyFamily.SOFTWARE,
    TaxonomyFamily.DATABASE, TaxonomyFamily.AUTOMATION, TaxonomyFamily.ANALYTICS,
})

assert len(ALL_FAMILIES) == 15, "spec 02 declara 15 familias"


FUTURE_FAMILIES: FrozenSet[str] = frozenset({
    "CALENDAR", "PROJECT_MANAGEMENT", "CLOUD", "AUTH", "PAYMENTS",
    "ECOMMERCE", "SUPPORT", "KNOWLEDGE_BASE", "VECTOR_DB", "FILESYSTEM",
    "GIT", "API_GATEWAY", "NOTIFICATIONS", "FORMS", "SCHEDULING",
    "COMPLIANCE",
})


def is_valid_taxonomy(family: str) -> bool:
    return family in ALL_FAMILIES


__all__ = [
    "TaxonomyFamily",
    "ALL_FAMILIES",
    "FUTURE_FAMILIES",
    "is_valid_taxonomy",
]

