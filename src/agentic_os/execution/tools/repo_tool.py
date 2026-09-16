"""Tools READ-ONLY del repositorio (FASE 3 — PLAN_CLINE_AGENTE_COMPILADOR.md).

El agente compilador necesita *ver* el repo para proponer blueprints con
fundamento: listar ficheros, leerlos y buscar patrones. Estas tools son el
unico camino de lectura del codigo y son deliberadamente conservadoras:

- **Solo lectura**: ninguna escribe, borra ni publica. El camino a escritura
  sigue siendo `repo.file.write` resuelto por Gate 1 humano.
- **Contenidas**: toda ruta se resuelve relativa a la raiz del repo y se
  comprueba con ``is_relative_to`` (nunca ``str.startswith``, que permite el
  bypass de prefijos). Un path fuera del repo lanza ``ToolValidationError``.
- **Sin secretos**: directorios de VCS/dependencias y ficheros de credenciales
  (``.git``, ``node_modules``, ``.env*``, ``*.pem``, ``*.key``) quedan vetados.
- **Acotadas**: limites explicitos de ficheros, tamano leido y coincidencias
  para que una lectura no agote memoria ni bloquee el proceso.

Ninguna tool decide permisos: quien autoriza es la ``Policy`` del tenant
(`repo.file.read`/`repo.file.list`/`repo.search` -> allow). Si la policy no lo
permite, el Executor no llega aqui.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List

from .base import Tool, ToolValidationError

# Raiz del repo: .../<repo>/src/agentic_os/execution/tools/repo_tool.py
_REPO_ROOT = Path(__file__).resolve().parents[4]

# Directorios vetados (VCS, entornos virtuales y dependencias).
_BLOCKED_DIRS = frozenset(
    {".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules", "__pycache__"}
)

# Nombres/sufijos vetados: material sensible que jamas debe salir por el chat.
_BLOCKED_NAMES = frozenset({".env", "credentials.json", "secrets.json"})
_BLOCKED_SUFFIXES = frozenset({".pem", ".key", ".p12", ".pfx", ".keystore"})

# Limites explicitos (fail-closed: se trunca y se reporta, no se ignora).
_MAX_FILES = 200
_MAX_READ_BYTES = 200_000
_MAX_SCAN_BYTES = 2_000_000
_MAX_MATCHES = 200
_MAX_PATTERN_LEN = 200
_MAX_LINE_CHARS = 200

# Sufijos que se consideran texto (evita intentar leer binarios).
_TEXT_SUFFIXES = frozenset(
    {
        ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".json", ".jsonl", ".yaml",
        ".yml", ".toml", ".ini", ".cfg", ".md", ".txt", ".rst", ".sql", ".sh",
        ".ps1", ".html", ".css", ".lock",
    }
)


def _is_blocked(path: Path) -> bool:
    """True si la ruta (o alguno de sus padres) es material vetado."""
    if path.name in _BLOCKED_NAMES or path.suffix.lower() in _BLOCKED_SUFFIXES:
        return True
    if path.name.startswith(".env"):
        return True
    return any(part in _BLOCKED_DIRS for part in path.parts)


def _resolve_in_repo(rel_path: str) -> Path:
    """Resuelve ``rel_path`` dentro de la raiz del repo, sin escape.

    Fail-closed: rutas absolutas, con traversal (``..``) o que resuelvan fuera
    del repo lanzan ``ToolValidationError``.
    """
    if not isinstance(rel_path, str):
        raise ToolValidationError("ruta invalida: se espera una cadena")
    raw = rel_path.strip().replace("\\", "/")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:/", raw):
        raise ToolValidationError(f"ruta absoluta no permitida: {rel_path!r}")
    root = _REPO_ROOT.resolve()
    target = (root / raw).resolve()
    if target != root and not target.is_relative_to(root):
        raise ToolValidationError(f"ruta fuera del repositorio: {rel_path!r}")
    if _is_blocked(target.relative_to(root)):
        raise ToolValidationError(f"ruta vetada (material sensible): {rel_path!r}")
    return target


def _iter_repo_files(root: Path, limit: int) -> Iterator[Path]:
    """Itera ficheros de texto del repo podando directorios vetados.

    ``os.walk`` con poda in-place de ``dirnames``: nunca se desciende a
    ``.git`` ni a ``node_modules``, de modo que el coste no depende de ellos.
    """
    repo = _REPO_ROOT.resolve()
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in _BLOCKED_DIRS)
        for name in sorted(filenames):
            path = Path(dirpath) / name
            if _is_blocked(path.relative_to(repo)):
                continue
            if path.suffix.lower() not in _TEXT_SUFFIXES:
                continue
            yield path
            count += 1
            if count >= limit:
                return


class RepoFileListTool(Tool):
    """Lista ficheros de un directorio del repo (relativo a la raiz)."""

    name = "repo_file_list"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        rel = params.get("path") or "."
        target = _resolve_in_repo(str(rel))
        if not target.exists():
            raise ToolValidationError(f"directorio no encontrado: {rel!r}")
        if not target.is_dir():
            raise ToolValidationError(f"no es un directorio: {rel!r}")
        repo = _REPO_ROOT.resolve()
        entries: List[Dict[str, Any]] = []
        for entry in sorted(target.iterdir(), key=lambda p: p.name):
            if _is_blocked(entry.relative_to(repo)):
                continue
            entries.append(
                {
                    "name": entry.name,
                    "path": entry.relative_to(repo).as_posix(),
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size if entry.is_file() else 0,
                }
            )
            if len(entries) >= _MAX_FILES:
                break
        return {
            "status": "READONLY",
            "real_execution": True,
            "path": str(rel),
            "entries": entries,
            "count": len(entries),
            "truncated": len(entries) >= _MAX_FILES,
        }


class RepoFileReadTool(Tool):
    """Lee un fichero de texto del repo (con tope de bytes, fail-closed)."""

    name = "repo_file_read"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        rel = params.get("path", "")
        if not rel:
            raise ToolValidationError("faltan campos: path es obligatorio")
        target = _resolve_in_repo(str(rel))
        if not target.is_file():
            raise ToolValidationError(f"fichero no encontrado: {rel!r}")
        size = target.stat().st_size
        with open(target, "rb") as fh:
            blob = fh.read(_MAX_READ_BYTES)
        return {
            "status": "READONLY",
            "real_execution": True,
            "path": target.relative_to(_REPO_ROOT.resolve()).as_posix(),
            "size": size,
            "truncated": size > _MAX_READ_BYTES,
            "content": blob.decode("utf-8", errors="replace"),
        }


class RepoSearchTool(Tool):
    """Busca un patron (texto o regex) en los ficheros de texto del repo."""

    name = "repo_search"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        pattern = str(params.get("pattern") or params.get("query") or "")
        if not pattern:
            raise ToolValidationError("faltan campos: pattern es obligatorio")
        if len(pattern) > _MAX_PATTERN_LEN:
            raise ToolValidationError(
                f"patron demasiado largo: maximo {_MAX_PATTERN_LEN} caracteres"
            )
        rel = params.get("path") or "."
        target = _resolve_in_repo(str(rel))
        if not target.exists():
            raise ToolValidationError(f"ruta no encontrada: {rel!r}")
        try:
            rx = re.compile(pattern, re.IGNORECASE)
        except re.error as exc:
            raise ToolValidationError(f"patron invalido: {exc}")

        repo = _REPO_ROOT.resolve()
        base = target if target.is_dir() else target.parent
        candidates: Iterable[Path] = (
            _iter_repo_files(base, _MAX_FILES) if base.is_dir() else [target]
        )
        matches: List[Dict[str, Any]] = []
        scanned = 0
        for path in candidates:
            if scanned >= _MAX_SCAN_BYTES:
                break
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read(_MAX_SCAN_BYTES - scanned)
            except OSError:
                continue
            scanned += len(text)
            for lineno, line in enumerate(text.splitlines(), start=1):
                if rx.search(line):
                    matches.append(
                        {
                            "path": path.relative_to(repo).as_posix(),
                            "line": lineno,
                            "text": line.strip()[:_MAX_LINE_CHARS],
                        }
                    )
                    if len(matches) >= _MAX_MATCHES:
                        break
            if len(matches) >= _MAX_MATCHES:
                break
        return {
            "status": "READONLY",
            "real_execution": True,
            "pattern": pattern,
            "path": str(rel),
            "matches": matches,
            "count": len(matches),
            "truncated": len(matches) >= _MAX_MATCHES,
        }


class RepoScanTool(Tool):
    """Resumen deterministico del repo: ficheros de texto y conteo por sufijo.

    Es la vista «mapa» que el compilador usa para orientarse sin leer nada
    entero; el detalle llega con ``repo_file_read``/``repo_search``.
    """

    name = "repo_scan"

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        rel = params.get("path") or "."
        target = _resolve_in_repo(str(rel))
        if not target.exists():
            raise ToolValidationError(f"ruta no encontrada: {rel!r}")
        base = target if target.is_dir() else target.parent
        repo = _REPO_ROOT.resolve()
        files: List[Dict[str, Any]] = []
        by_suffix: Dict[str, int] = {}
        for path in _iter_repo_files(base, _MAX_FILES):
            suffix = path.suffix.lower() or path.name.lower()
            by_suffix[suffix] = by_suffix.get(suffix, 0) + 1
            files.append(
                {
                    "path": path.relative_to(repo).as_posix(),
                    "size": path.stat().st_size,
                }
            )
        return {
            "status": "READONLY",
            "real_execution": True,
            "path": str(rel),
            "files": files,
            "count": len(files),
            "by_suffix": dict(sorted(by_suffix.items())),
            "truncated": len(files) >= _MAX_FILES,
        }


__all__ = [
    "RepoFileListTool",
    "RepoFileReadTool",
    "RepoScanTool",
    "RepoSearchTool",
]