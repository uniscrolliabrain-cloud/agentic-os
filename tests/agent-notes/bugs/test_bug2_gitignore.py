"""Bug 2 - Falta .gitignore: riesgo de fuga .env, .credentials/, *.pem"""

from pathlib import Path


def test_gitignore_exists():
    """Debe existir .gitignore en la raíz del repo."""
    gitignore = Path(__file__).resolve().parents[3] / ".gitignore"
    assert gitignore.exists(), ".gitignore no existe en la raíz del repo"


def test_gitignore_blocks_env_files():
    """.gitignore debe bloquear archivos .env (secretos)."""
    gitignore = Path(__file__).resolve().parents[3] / ".gitignore"
    content = gitignore.read_text(encoding="utf-8")
    assert ".env" in content, ".gitignore no bloquea archivos .env"


def test_gitignore_blocks_credentials_dir():
    """.gitignore debe bloquear el directorio de credenciales (CredentialStore)."""
    gitignore = Path(__file__).resolve().parents[3] / ".gitignore"
    content = gitignore.read_text(encoding="utf-8")
    assert ".credentials" in content, ".gitignore no bloquea el directorio .credentials/"


def test_gitignore_blocks_pem_keys():
    """.gitignore debe bloquear archivos .pem (claves privadas)."""
    gitignore = Path(__file__).resolve().parents[3] / ".gitignore"
    content = gitignore.read_text(encoding="utf-8")
    assert "*.pem" in content, ".gitignore no bloquea archivos .pem"


def test_gitignore_blocks_pycache():
    """.gitignore debe bloquear __pycache__/."""
    gitignore = Path(__file__).resolve().parents[3] / ".gitignore"
    content = gitignore.read_text(encoding="utf-8")
    assert "__pycache__/" in content, ".gitignore no bloquea __pycache__/"
