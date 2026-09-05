"""Bug 12 - Executor _tenant_from_context bug: getattr sobre string devuelve None"""

import pytest
from agentic_os.execution.executor import Executor


def test_tenant_from_context_with_dict_and_string_tenant():
    """Cuando context es dict y tenant es un string (id), debe devolver el string."""
    context = {"tenant": "tenant-123"}
    result = Executor._tenant_from_context(context)
    assert result == "tenant-123", \
        f"Debe devolver 'tenant-123', obtuvo: {result}"


def test_tenant_from_context_with_dict_and_dict_tenant():
    """Cuando context es dict y tenant es dict con 'id', debe devolver el id."""
    context = {"tenant": {"id": "tenant-456", "name": "ACME"}}
    result = Executor._tenant_from_context(context)
    assert result == "tenant-456", \
        f"Debe devolver 'tenant-456', obtuvo: {result}"


def test_tenant_from_context_with_tenant_object():
    """Cuando context tiene un objeto tenant con .id, debe devolver el id."""
    class FakeTenant:
        id = "tenant-789"
    class FakeContext:
        tenant = FakeTenant()
    result = Executor._tenant_from_context(FakeContext())
    assert result == "tenant-789", \
        f"Debe devolver 'tenant-789', obtuvo: {result}"


def test_tenant_from_context_with_none():
    """Cuando context es None, debe devolver None."""
    result = Executor._tenant_from_context(None)
    assert result is None, f"Debe devolver None, obtuvo: {result}"


def test_tenant_from_context_with_empty_dict():
    """Cuando context es dict vacío, debe devolver None."""
    result = Executor._tenant_from_context({})
    assert result is None, f"Debe devolver None, obtuvo: {result}"
