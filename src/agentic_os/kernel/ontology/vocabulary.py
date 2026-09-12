from __future__ import annotations
import re
from pydantic import BaseModel, ConfigDict
from typing import Set

_KIND_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class Vocabulary(BaseModel):
    model_config = ConfigDict(frozen=True)
    entities: Set[str] = {"actor","user","agent","tool","resource","goal","event"}
    relations: Set[str] = {"uses","accesses","governs","requires","belongs_to","triggers"}
    capabilities: Set[str] = {"read","write","execute_tool","approve","plan","reason"}


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


DEFAULT_VOCAB = Vocabulary()
