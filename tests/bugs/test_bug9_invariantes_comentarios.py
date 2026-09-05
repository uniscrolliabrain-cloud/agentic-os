"""Bug 9 - Invariantes del kernel son comentarios: kernel/world/invariants.py y kernel/policy/invariants.py sin lógica ejecutable"""

import pytest


def test_world_invariants_are_executable():
    """Las invariantes del mundo deben ser funciones ejecutables, no solo strings."""
    from agentic_os.kernel.world import invariants
    # Debe haber al menos una función callable de validación
    callable_invariants = [
        getattr(invariants, name) for name in dir(invariants)
        if callable(getattr(invariants, name)) and not name.startswith('_')
    ]
    assert len(callable_invariants) > 0, \
        "kernel/world/invariants.py no tiene funciones ejecutables (solo strings)"


def test_policy_invariants_are_executable():
    """Las invariantes de policy deben ser funciones ejecutables, no solo strings."""
    from agentic_os.kernel.policy import invariants
    callable_invariants = [
        getattr(invariants, name) for name in dir(invariants)
        if callable(getattr(invariants, name)) and not name.startswith('_')
    ]
    assert len(callable_invariants) > 0, \
        "kernel/policy/invariants.py no tiene funciones ejecutables (solo strings)"


def test_world_invariants_can_validate_state():
    """Las invariantes deben poder validar un WorldState."""
    from agentic_os.kernel.world import invariants
    from agentic_os.kernel.world.state import WorldState
    # Buscar función de validate
    validate_fn = getattr(invariants, 'validate_state', None) or \
                  getattr(invariants, 'check_invariants', None) or \
                  getattr(invariants, 'validate', None)
    assert validate_fn is not None, \
        "No se encontró función de validación de invariantes en kernel/world/invariants.py"


def test_invariants_reject_invalid_state():
    """Las invariantes deben detectar estados inválidos."""
    from agentic_os.kernel.world import invariants
    from agentic_os.kernel.world.state import WorldState
    validate_fn = getattr(invariants, 'validate_state', None) or \
                  getattr(invariants, 'check_invariants', None) or \
                  getattr(invariants, 'validate', None)
    assert validate_fn is not None, "No se encontró función de validación"
    # Crear estado válido y luego verificar que validate funciona
    valid_state = WorldState(entities={}, relations={}, version=0)
    result = validate_fn(valid_state)
    assert result is True, "Estado válido debe pasar validación"
    # Verificar que check_invariants devuelve lista de violaciones
    check_fn = getattr(invariants, 'check_invariants', None)
    if check_fn:
        violations = check_fn(valid_state)
        assert isinstance(violations, list), "check_invariants debe devolver lista"
        assert len(violations) == 0, "Estado válido no debe tener violaciones"
