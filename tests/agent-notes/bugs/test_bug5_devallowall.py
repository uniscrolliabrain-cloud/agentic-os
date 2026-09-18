"""Bug 5 - DEV_ALLOW_ALL=true bypass tenants en policy/engine.py"""

import os
import pytest
from unittest.mock import patch

from agentic_os.kernel.policy.engine import PolicyEngine
from agentic_os.kernel.policy.evaluator import Decision


def test_dev_allow_all_does_not_bypass_in_production():
    """Sin DEV_ALLOW_ALL (o en false), los tenants no registrados reciben deny.

    DEV_ALLOW_ALL es el ÃšNICO disparador del allow-all (default false). Aunque
    ENV=dev estÃ© activo, un tenant no registrado jamÃ¡s se abre sin el flag.
    """
    for value in (None, "false"):
        with patch.dict(os.environ, {"DEV_ALLOW_ALL": value} if value else {}, clear=False):
            import os as _os
            if value is None:
                _os.environ.pop("DEV_ALLOW_ALL", None)
            engine = PolicyEngine()
            result = engine.decide(
                tenant_id="nonexistent-tenant-xyz",
                capability="email.message.send",
            )
            assert result.effect == "deny", \
                f"ProducciÃ³n no debe abrir tenant no registrado: {result.reason}"


def test_dev_allow_all_true_permite_tenants_efimeros_dev():
    """DEV_ALLOW_ALL=true (dev) permite tenants efÃ­meros no registrados.

    Es el modo de desarrollo/tests con tenants efÃ­meros; NO es un vector en
    producciÃ³n porque el default es false.
    """
    with patch.dict(os.environ, {"DEV_ALLOW_ALL": "true"}, clear=False):
        engine = PolicyEngine()
        result = engine.decide(
            tenant_id="tenant-efimero-test",
            capability="file.read",
        )
        assert result.effect == "allow", f"Dev allow-all debe permitir: {result.reason}"


def test_dev_allow_all_respects_tenant_capabilities():
    """DEV_ALLOW_ALL=true NO debe saltarse las capabilities habilitadas del tenant."""
    with patch.dict(os.environ, {"DEV_ALLOW_ALL": "true"}):
        engine = PolicyEngine()
        # Incluso con DEV_ALLOW_ALL, un tenant registrado sin la capability
        # habilitada debe ser denegado (si el tenant existe)
        # Nota: este test verifica la lÃ³gica, no el registro
        result = engine.decide(
            tenant_id="system",
            capability="finance.refund.create",
        )
        # system tenant sin esa capability -> deny
        # AUD-13: DEV_ALLOW_ALL no suaviza el endurecimiento por riesgo.
        # finance.refund.create es FINANCIAL: ahora devuelve require_approval
        # (antes solo delete/publish disparaban el invariante).
        assert result.effect in ("deny", "require_approval"), (
            f"DEV_ALLOW_ALL no debe conceder FINANCIAL sin approval: {result.effect}"
        )


def test_dev_allow_all_false_denies_everything():
    """DEV_ALLOW_ALL=false debe mantener deny por defecto."""
    with patch.dict(os.environ, {"DEV_ALLOW_ALL": "false"}):
        engine = PolicyEngine()
        result = engine.decide(
            tenant_id="unknown-tenant",
            capability="email.message.send",
        )
        assert result.effect == "deny", \
            "Sin DEV_ALLOW_ALL, tenants desconocidos deben ser denegados"


def test_dev_allow_all_in_default_policy_only_dev():
    """default_policy con allow-all solo debe activarse en DEV, nunca en producciÃ³n."""
    from agentic_os.kernel.policy.engine import default_policy
    with patch.dict(os.environ, {"DEV_ALLOW_ALL": "true"}):
        policy = default_policy("test-tenant")
        # La policy debe marcarse claramente como DEV ONLY
        assert any("DEV" in (r.description or "") for r in policy.rules), \
            "Policy allow-all debe estar marcada como DEV ONLY"