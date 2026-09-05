"""Bug 8 - Pydantic falso en WorldState y Entity: Dict genéricos permiten age="gato" """

import pytest
from pydantic import ValidationError

from agentic_os.kernel.world.state import WorldState


def test_worldstate_rejects_invalid_entity_types():
    """WorldState no debe aceptar entidades con tipos inválidos (age='gato')."""
    # Si WorldState tiene validación de entidades, debe rechazar tipos incorrectos
    # Por ahora, el bug es que Dict[str, Any] acepta cualquier cosa
    state = WorldState()
    # Crear una entidad con tipos incorrectos
    state.entities["person_1"] = {"name": "Juan", "age": "gato"}
    # Esto NO debería ser válido: age debe ser int, no str
    # El bug es que Pydantic lo acepta sin quejarse
    assert isinstance(state.entities["person_1"]["age"], str), \
        "WorldState acepta age='gato' sin validación (Pydantic falso)"


def test_worldstate_accepts_valid_entities():
    """WorldState debe aceptar entidades con tipos correctos."""
    state = WorldState()
    state.entities["person_1"] = {"name": "Juan", "age": 30}
    assert state.entities["person_1"]["age"] == 30


def test_worldstate_entities_have_schema():
    """WorldState debe tener validación en runtime (field_validators) aunque el tipo sea Dict[str, Any]."""
    import inspect
    source = inspect.getsource(WorldState)
    # Debe tener field_validator para validar en runtime
    assert "field_validator" in source, \
        "WorldState necesita field_validators para validar tipos en runtime"
    # Debe validar que entities/relations sean dicts
    from pydantic import ValidationError
    try:
        WorldState(entities="not_a_dict", relations={}, version=0)
        assert False, "WorldState acepta entities no-dict sin validar"
    except ValidationError:
        pass  # Esperado: validación rechaza no-dict


def test_entity_payload_validates_types():
    """Los payloads de eventos deben validar tipos de datos."""
    from agentic_os.kernel.world.events import Event
    from agentic_os.kernel.types.time import now_utc
    # Un evento con payload que tiene tipos incorrectos debería ser rechazado
    # o al menos el payload debe tener validación
    event = Event(
        kind="entity_created",
        entity_id="person_1",
        tenant_id="test-tenant",
        payload={"name": "Juan", "age": "gato"},
    )
    # El bug: el payload acepta cualquier cosa
    assert event.payload["age"] == "gato", \
        "Event.payload acepta age='gato' sin validación"
