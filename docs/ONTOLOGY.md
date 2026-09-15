# ONTOLOGY

## Metamodelo vs Vocabulario

| Nivel | Qué es | Dónde vive | Mutable en runtime |
|---|---|---|---|
| **Metamodelo** | categorías (actor, tool, resource…) | `kernel/ontology/metamodel.py` | ❌ |
| **Vocab base** | `DEFAULT_VOCAB` | `kernel/ontology/vocabulary.py` | ❌ |
| **Dom. vocab** | `clinic.*`, `agencia.*`, `finance.*` | `domains/<x>/ontology.py` | ✅ en bootstrap |
| **Bundle/tenant** | `OntologyBundle` frozen | generado por `compile_ontology()` | ❌ |

## Cómo se extiende el vocabulario

```python
class AgenciaDomain(BaseDomain):
    domain = "agencia"
    entity_kinds = {"agencia.client", "agencia.lead", ...}
    relation_kinds = {"agencia.belongs_to_client", ...}
    capability_kinds = {"agencia.capture_lead", ...}

    @classmethod
    def register_entities(cls, registry=None):
        cls.compile_ontology()
        register_entity_types(AgencyClient, AgencyLead, ...)
```

## Reglas

1. Un dominio **no puede** redefinir un kind del `DEFAULT_VOCAB`.
2. El kind debe ser slug canónico (`^[a-z][a-z0-9]*([._-][a-z0-9]+)*$`).
3. El registro en `ENTITY_TYPE_REGISTRY` es **explícito y fail-closed**.
4. Los `OntologyBundle` resultantes son **frozen** y **versionados**.

## Ficheros

- `kernel/ontology/vocabulary.py`    — `DEFAULT_VOCAB`, `is_canonical_kind`.
- `kernel/ontology/validator.py`     — `validate_against_metamodel`.
- `kernel/ontology/domain_models.py` — `ENTITY_TYPE_REGISTRY`, `register_entity_types`.
- `domains/base.py`                  — `BaseDomain.compile_ontology`.
- `domains/<x>/ontology.py`          — extensiones por dominio.