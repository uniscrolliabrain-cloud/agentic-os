"""El ENTITY_TYPE_REGISTRY del kernel ARRANCA VACIO."""
from agentic_os.kernel.ontology.domain_models import ENTITY_TYPE_REGISTRY


def test_kernel_registry_starts_empty_before_domains():
    assert ENTITY_TYPE_REGISTRY == {}, (
        f"el kernel trae entidades preinstaladas: {list(ENTITY_TYPE_REGISTRY)}"
    )