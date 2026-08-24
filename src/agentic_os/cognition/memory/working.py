from pydantic import BaseModel, Field
from typing import List
class WorkingMemory(BaseModel):
    beliefs: List[dict] = Field(default_factory=list)
    capacity: int = 7
