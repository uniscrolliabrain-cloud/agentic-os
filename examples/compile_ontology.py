"""Compilador Ontológico (FASE 2).

Lee un ontology.yaml de dominio + el Vocabulary del kernel, construye las
Capability tipadas (Pydantic), valida que sean resolubles por el Connector
Kernel (que exista un connector con esa canonical capability), y prueba el
ConnectorRouter en modo dry-run (devuelve preview sin efecto externo).

Uso:
    python examples/compile_ontology.py [ruta_ontology.yaml]
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ / "src"))

from agentic_os.kernel.ontology.capabilities import Capability  # noqa: E402
from agentic_os.kernel.ontology.vocabulary import DEFAULT_VOCAB, Vocabulary  # noqa: E402
from agentic_os.connectors import CapabilityRegistry, ConnectorFactory, ConnectorRouter  # noqa: E402
from agentic_os.connectors.providers import PROVIDER_SPECS, register_builtin_providers  # noqa: E402

DEFAULT_YAML = PROJ / "src" / "agentic_os" / "domains" / "marketing_ficticio" / "ontology.yaml"


def load_domain(yaml_path: Path) -> dict:
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    assert data.get("domain"), "El YAML debe declarar 'domain'"
    return data


def build_vocabulary(data: dict) -> Vocabulary:
    vocab_dict = data.get("vocabulary", {})
    raw_caps = vocab_dict.get("capabilities", [])
    # las capabilities del YAML son dicts {name, canonical, ...}; extraer los name
    cap_names = {c["name"] for c in raw_caps} if raw_caps and isinstance(raw_caps[0], dict) else set(raw_caps)
    return Vocabulary(
        entities=set(vocab_dict.get("entities", [])) | DEFAULT_VOCAB.entities,
        relations=set(vocab_dict.get("relations", [])) | DEFAULT_VOCAB.relations,
        capabilities=cap_names | DEFAULT_VOCAB.capabilities,
    )


def build_capabilities(data: dict) -> tuple[list[Capability], dict]:
    """Genera Capability tipadas (Pydantic) + mapa name -> canonical desde el YAML."""
    caps: list[Capability] = []
    mapping: dict = {}
    for item in data["vocabulary"]["capabilities"]:
        canonical = item["canonical"]
        mapping[item["name"]] = canonical
        caps.append(
            Capability(
                name=item["name"],
                description=(
                    f"{item['action']} {item['entity']} "
                    f"(dominio {data['domain']}) -> {canonical}"
                ),
                requires_tools=item.get("tools", []),
            )
        )
    return caps, mapping


def validate_against_registry(caps: list[Capability], mapping: dict, registry: CapabilityRegistry) -> dict:
    """Valida que la canonical de cada capability existe en el registry.

    Si una canonical declarada en el YAML no existe en ningún connector,
    FALLA claro (mismo criterio que deny-by-default): no se silencia.
    """
    for item in caps:
        canonical = mapping.get(item.name)
        if not canonical:
            raise ValueError(f"Capability '{item.name}' sin canonical declarada en el YAML")
        if not registry.has_capability(canonical):
            raise ValueError(
                f"Canonical '{canonical}' (de '{item.name}') no resuelve en el Connector Kernel. "
                f"Familias disponibles: {sorted(registry.list_providers())}"
            )
    return dict(mapping)


def test_dry_run(router: ConnectorRouter, canonical: str) -> None:
    import asyncio

    from agentic_os.connectors.core.models import Command

    cmd = Command(
        capability=canonical,
        params={"name": "EmpresaX"},
        dry_run=True,
        execution_id=f"dry-compile-{canonical}",
    )
    res = asyncio.run(router.route(cmd))
    assert res.dry_run is True, "deberia ser dry-run"
    assert res.preview is not None, "dry-run debe devolver preview"
    assert res.preview["capability"] == canonical
    print(f"[dry-run] capability={canonical} -> preview={res.preview}")


def build_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    factory = ConnectorFactory()
    register_builtin_providers(factory)
    for provider in PROVIDER_SPECS:
        registry.register(factory.create(provider))
    return registry


def main() -> None:
    yaml_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_YAML
    data = load_domain(yaml_path)

    vocab = build_vocabulary(data)
    print(f"Dominio: {data['domain']} | entidades={sorted(vocab.entities - DEFAULT_VOCAB.entities)}")

    caps, mapping = build_capabilities(data)
    print(f"Capabilities generadas ({len(caps)}):")
    for c in caps:
        print(f"  - {c.name}  -> {mapping[c.name]}  (tools={c.requires_tools})")

    registry = build_registry()
    router = ConnectorRouter(registry)

    mapping_resolved = validate_against_registry(caps, mapping, registry)
    print(f"Canonical mapping validado: {mapping_resolved}")

    # dry-run con la primera canonical que resuelva
    test_cap = next(canonical for canonical in mapping_resolved.values() if canonical)
    test_dry_run(router, test_cap)
    print("COMPILADOR OK")


if __name__ == "__main__":
    main()