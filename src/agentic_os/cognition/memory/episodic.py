from pydantic import BaseModel, Field
class EpisodicMemory(BaseModel):
    events: list = Field(default_factory=list)
