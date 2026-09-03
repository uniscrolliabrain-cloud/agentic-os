"""Proyecciones de lectura del dominio finance.

CONTRATO: las proyecciones devuelven modelos Pydantic explícitos o fallan.
NUNCA devuelven {} fingiendo una vista vacía válida: si la funcionalidad no
está implementada en esta versión, se marca explícitamente.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class InvoiceView(BaseModel):
    """Contrato de la vista de factura (estado explícito)."""

    model_config = ConfigDict(frozen=True)

    invoice_id: str
    status: str  # p.ej. "draft" | "issued" | "paid" | "not_implemented"
    total: str = "0.00"


def invoice_view(state):
    """NO IMPLEMENTADO en esta versión.

    Se marca explícitamente en lugar de devolver {} (respuesta vacía que
    aparentaría una factura real sin datos). Cuando exista el modelo de
    WorldState del dominio finance, esta función debe poblar InvoiceView
    desde el estado real.
    """
    raise NotImplementedError(
        "domains.finance.invoice_view no está implementado en esta versión; "
        "no hay aún un modelo de estado del que proyectar facturas"
    )

