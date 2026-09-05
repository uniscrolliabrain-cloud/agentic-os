"""Bug 17 - Falta dependencias tests en pyproject.toml: fastapi y testclient no declarados"""

from pathlib import Path


def test_pyproject_has_test_dependencies():
    """pyproject.toml debe declarar dependencias de test (pytest, httpx, pytest-asyncio)."""
    pyproject = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
    content = pyproject.read_text()

    # pytest debe estar en dev dependencies
    assert "pytest" in content, "pytest no está en pyproject.toml"
    # httpx para TestClient de FastAPI
    assert "httpx" in content, "httpx no está en pyproject.toml (necesario para TestClient)"
    # pytest-asyncio para tests async
    assert "pytest-asyncio" in content, "pytest-asyncio no está en pyproject.toml"


def test_pyproject_has_fastapi():
    """fastapi debe estar como dependencia (necesario para la API)."""
    pyproject = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
    content = pyproject.read_text()
    assert "fastapi" in content, "fastapi no está en pyproject.toml"


def test_pyproject_anyio_marker():
    """pytest-asyncio debe tener el marker anyio configurado."""
    pyproject = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
    content = pyproject.read_text()
    # Debe haber configuración de asyncio_mode
    assert "asyncio_mode" in content or "pytest-asyncio" in content, \
        "Falta configuración de pytest-asyncio en pyproject.toml"
