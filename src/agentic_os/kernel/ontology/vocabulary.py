from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Set
class Vocabulary(BaseModel):
    model_config = ConfigDict(frozen=True)
    entities: Set[str] = {"actor","user","agent","tool","resource","goal","event"}
    relations: Set[str] = {"uses","accesses","governs","requires","belongs_to","triggers"}
    capabilities: Set[str] = {"read","write","execute_tool","approve","plan","reason"}
DEFAULT_VOCAB = Vocabulary()
