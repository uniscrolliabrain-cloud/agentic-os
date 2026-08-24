from pydantic import BaseModel, Field, ConfigDict
class Role(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    permissions: list[str] = Field(default_factory=list)
    forbidden_tools: list[str] = Field(default_factory=list)
