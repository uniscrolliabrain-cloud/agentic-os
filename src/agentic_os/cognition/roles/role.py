from __future__ import annotations
from typing import List, Set
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Role(BaseModel):
    """Rol RBAC: permisos + tools prohibidas + herencia."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    description: str = ""
    permissions: List[str] = Field(default_factory=list, description="propose_intent, execute, read, write, approve...")
    forbidden_tools: List[str] = Field(default_factory=list, description="tools que nunca puede usar, * = todas")
    inherits: List[str] = Field(default_factory=list, description="roles de los que hereda permisos")
    allowed_tools: List[str] = Field(default_factory=list, description="si no vacio, whitelist")

    @field_validator("name")
    @classmethod
    def _name_nonblank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Role.name obligatorio")
        return v.strip().lower()

    def can(self, permission: str) -> bool:
        return permission in self.permissions

    def can_use_tool(self, tool_name: str) -> bool:
        if "*" in self.forbidden_tools:
            return False
        if tool_name in self.forbidden_tools:
            return False
        if self.allowed_tools:
            return tool_name in self.allowed_tools
        return True

    def effective_permissions(self, library: dict) -> Set[str]:
        perms = set(self.permissions)
        for parent_name in self.inherits:
            parent = library.get(parent_name)
            if parent:
                perms.update(parent.effective_permissions(library))
        return perms
