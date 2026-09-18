from __future__ import annotations
import re
from pydantic import BaseModel, ConfigDict
from typing import FrozenSet

_KIND_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class Vocabulary(BaseModel):
    model_config = ConfigDict(frozen=True)
    entities: FrozenSet[str] = {"actor","user","agent","tool","resource","goal","event"}
    relations: FrozenSet[str] = {"uses","accesses","governs","requires","belongs_to","triggers"}
    capabilities: FrozenSet[str] = {"read","write","execute_tool","approve","plan","reason"}


def is_canonical_kind(kind: str) -> bool:
    """True si *kind* es un slug canónico del metamodelo.

    Un kind canónico empieza en minúscula, usa solo ``[a-z0-9]`` y los
    separadores ``.`` / ``_`` / ``-`` para namespaces de dominio
    (p. ej. ``actor``, ``clinic.patient``, ``belongs_to``).

    NOTA: el propio ``Vocabulary`` no impone este regex (el ``EVENT_VOCAB``
    del kernel usa PascalCase para tipos de evento). La validación canónica
    se aplica de forma explícita en :func:`validate_against_metamodel`.
    """
    return bool(_KIND_RE.match(kind))


_RELATION_KIND_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


def is_canonical_relation_kind(kind: str) -> bool:
    """True si kind es un slug de relacion canonico.

    Las relaciones no permiten puntos (solo [a-z][a-z0-9_-]*): 'uses',
    'accesses', 'belongs_to'.
    """
    return bool(_RELATION_KIND_RE.match(kind))


DEFAULT_VOCAB = Vocabulary()
