"""Tests de proyecciones clinic/finance (#18 del hardening).

CONTRATO: proyección = modelo Pydantic explícito o NotImplementedError.
Nunca {} fingiendo una vista válida.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_os.domains.clinic.projections import PatientView, patient_view
from agentic_os.domains.finance.projections import InvoiceView, invoice_view


def test_invoice_view_modelo_valido() -> None:
    v = InvoiceView(invoice_id="inv-1", status="issued", total="120.00")
    assert v.invoice_id == "inv-1"
    assert v.status == "issued"


def test_invoice_view_requiere_campos() -> None:
    with pytest.raises(ValidationError):
        InvoiceView()  # type: ignore[call-arg]


def test_invoice_view_no_implementado_es_explícito() -> None:
    with pytest.raises(NotImplementedError):
        invoice_view(state=None)  # nunca devuelve {} fingiendo factura


def test_patient_view_modelo_valido() -> None:
    v = PatientView(patient_id="pat-1", name="Ana", status="active")
    assert v.patient_id == "pat-1"


def test_patient_view_no_implementado_es_explícito() -> None:
    with pytest.raises(NotImplementedError):
        patient_view(state=None)


def test_views_frozen() -> None:
    v = InvoiceView(invoice_id="i", status="draft")
    with pytest.raises(ValidationError):
        v.status = "paid"  # type: ignore[misc]
