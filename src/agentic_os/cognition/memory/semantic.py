from pydantic import BaseModel, Field
class SemanticMemory(BaseModel):
    facts: dict = Field(default_factory=dict)
