"""Ontología del dominio clinic.

Ejemplo de extensión de vocabulario: el dominio registra kinds con
namespace ``clinic.*`` **sin tocar** ``DEFAULT_VOCAB`` del kernel.

Entry point del kernel:
    tenant → declara ontología Pydantic → ``validate_against_metamodel``
    valida fail-closed → produce ``OntologyBundle`` frozen+versionado.
"""
from __future__ import annotations

from typing import Set

from ..base import BaseDomain


class ClinicDomain(BaseDomain):
    """Dominio clínico: pacientes, citas y su relación."""

    domain: str = "clinic"
    entity_kinds: Set[str] = {"clinic.patient", "clinic.appointment"}
    relation_kinds: Set[str] = {"clinic.has_appointment"}
    capability_kinds: Set[str] = {"clinic.schedule"}


# Backward-compat: dict reflectando el VOCAB namespaced (deribado del
# modelo tipado).  Nada en el kernel lo importa; se mantiene por si
# integraciones externas lo referencian.
CLINIC_VOCAB = {
    "entities": ClinicDomain.entity_kinds,
    "relations": ClinicDomain.relation_kinds,
    "capabilities": ClinicDomain.capability_kinds,
}
