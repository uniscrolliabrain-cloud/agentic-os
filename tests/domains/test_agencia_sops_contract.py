"""Contrato Pydantic de los SOPs del tenant bor-agencia."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_os.domains.agencia import PIPELINES, SOPS, SOP


def test_sops_ids_namespaced():
    for sop_id in SOPS:
        assert sop_id.startswith("bor-agencia."), sop_id


def test_sops_referencian_pipelines_existentes():
    for sop in SOPS.values():
        assert sop.pipeline_id in PIPELINES, (
            f"SOP {sop.id} apunta a pipeline inexistente {sop.pipeline_id}"
        )


def test_sop_id_sin_namespace_falla():
    with pytest.raises(ValidationError):
        SOP(id="leads_to_draft", name="X", trigger="manual",
            pipeline_id="leads_to_draft")


def test_sop_rol_invalido_falla():
    with pytest.raises(ValidationError):
        SOP(id="bor-agencia.x", name="X", trigger="manual",
            pipeline_id="leads_to_draft",
            requires_role="superadmin")  # type: ignore[arg-type]


def test_daily_social_sop_requiere_approval():
    assert SOPS["bor-agencia.daily_social"].requires_approval is True