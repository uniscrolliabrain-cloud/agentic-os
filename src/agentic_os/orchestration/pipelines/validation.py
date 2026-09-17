"""Validacion de catalogo de pipelines por tenant."""
from __future__ import annotations

from typing import Any, List

from .runner import get_tenant_pipelines


class CatalogValidationError(Exception):
    """Pipeline con referencias rotas o vacio."""


def validate_tenant_pipelines(tenant_slug: str, registry: Any) -> List[str]:
    errors: List[str] = []
    pipelines = get_tenant_pipelines(tenant_slug)
    if not pipelines:
        errors.append(f"tenant '{tenant_slug}' no declara pipelines")
        return errors
    for pid, pipeline in pipelines.items():
        steps = getattr(pipeline, "steps", [])
        if not steps:
            errors.append(f"pipeline '{pid}' sin steps")
            continue
        for step in steps:
            tool_name = getattr(step, "tool", "")
            if registry is not None and registry.get_optional(tool_name) is None:
                errors.append(
                    f"pipeline '{pid}' referencia tool no registrada: {tool_name}"
                )
    return errors


def assert_tenant_catalog_valid(tenant_slug: str, registry: Any) -> None:
    errors = validate_tenant_pipelines(tenant_slug, registry)
    if errors:
        raise CatalogValidationError("; ".join(errors))


__all__ = [
    "CatalogValidationError",
    "validate_tenant_pipelines",
    "assert_tenant_catalog_valid",
]