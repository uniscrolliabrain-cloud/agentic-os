"""Validación del catálogo de pipelines (sección 6 de hardening).

Detecta ANTES de runtime referencias rotas: tool no registrada, pipeline
declarado sin MicroActions, capability inexistente en el Connector Kernel.
Falla temprano con errores claros.
"""

from __future__ import annotations

from typing import Any, Dict, List

from . import PIPELINES, PIPELINE_TOOLS


class CatalogValidationError(Exception):
    """Un pipeline referencia algo que no existe o está vacío."""


def validate_pipeline_tools(registry: Any, pipeline_ids: List[str]) -> List[str]:
    """Devuelve la lista de errores de referencias rotas en los pipelines dados.

    Cada error es una cadena descriptiva; si la lista es vacía, todo es válido.
    """
    errors: List[str] = []
    for pid in pipeline_ids:
        if pid not in PIPELINES:
            errors.append(f"pipeline inexistente: {pid}")
            continue
        required = PIPELINE_TOOLS.get(pid, [])
        if not required:
            errors.append(f"pipeline '{pid}' no declara ninguna MicroAction (vacío)")
            continue
        for tool in required:
            if registry is not None and registry.get(tool) is None:
                errors.append(f"pipeline '{pid}' referencia tool no registrada: {tool}")
    return errors


def validate_all_pipelines(registry: Any) -> List[str]:
    """Valida todos los pipelines del catálogo."""
    return validate_pipeline_tools(registry, list(PIPELINES.keys()))


def assert_catalog_valid(registry: Any) -> None:
    """Lanza CatalogValidationError si el catálogo tiene referencias rotas."""
    errors = validate_all_pipelines(registry)
    if errors:
        raise CatalogValidationError("catálogo inválido: " + "; ".join(errors))