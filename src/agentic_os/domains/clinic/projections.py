"""Proyecciones de lectura del dominio clinic.

CONTRATO: las proyecciones devuelven modelos Pydantic explícitos o fallan.
NUNCA devuelven {} fingiendo una vista vacía válida: si la funcionalidad no
está implementada en esta versión, se marca explícitamente.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PatientView(BaseModel):
    """Contrato de la vista de paciente (estado explícito)."""

    model_config = ConfigDict(frozen=True)

    patient_id: str
    name: str = ""
    status: str  # p.ej. "active" | "archived" | "not_implemented"


def patient_view(state):
    """NO IMPLEMENTADO en esta versión.

    Se marca explícitamente en lugar de devolver {} (respuesta vacía que
    aparentaría un paciente real sin datos). Cuando exista el modelo de
    WorldState del dominio clinic, esta función debe poblar PatientView
    desde el estado real.
    """
    raise NotImplementedError(
        "domains.clinic.patient_view no está implementado en esta versión; "
        "no hay aún un modelo de estado del que proyectar pacientes"
    )

