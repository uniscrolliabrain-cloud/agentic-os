from pydantic import BaseModel, Field
class ProceduralMemory(BaseModel):
    skills: dict = Field(default_factory=dict)
