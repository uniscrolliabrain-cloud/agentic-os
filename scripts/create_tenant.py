"""Crea el tenant real 'uniscroll-prod' con API key sk_uniscroll_test_123.

Uso: python scripts/create_tenant.py
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from agentic_os.infrastructure.tenancy import TenantRegistry  # noqa: E402


def main() -> None:
    registry = TenantRegistry()
    existing = registry.get("uniscroll-prod")
    if existing is not None:
        key = existing.config.credentials.get("api_key", "")
        print(f"EXISTS id={existing.id} slug={existing.slug} api_key={key}")
        return
    tenant = registry.create(
        name="Uniscroll Prod",
        slug="uniscroll-prod",
        config={
            "domain": "generic",
            "credentials": {"api_key": "sk_uniscroll_test_123"},
            "enabled_capabilities": [],
        },
    )
    print(f"CREATED id={tenant.id} slug={tenant.slug} api_key={tenant.config.credentials.get('api_key')}")


if __name__ == "__main__":
    main()