from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Literal
EntityCategory = Literal["actor","resource","tool","concept","event"]
class EntityMeta(BaseModel):
    model_config = ConfigDict(frozen=True)
    category: EntityCategory
    description: str = ""
class RelationMeta(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    src_category: EntityCategory
    dst_category: EntityCategory
    description: str = ""
class CapabilityMeta(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    description: str = ""
