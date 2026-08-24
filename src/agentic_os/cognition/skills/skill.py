from pydantic import BaseModel, ConfigDict
class Skill(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    description: str
    requires_tool: str
