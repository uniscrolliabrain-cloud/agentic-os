from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InputField(BaseModel):
    """Campo de entrada tipado para contratos de Skills y Pipelines."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
    )

    name: str = Field(..., min_length=1, description="Nombre único del campo")
    type_str: str = Field(..., min_length=1, description="Tipo declarado del campo")
    description: str = Field("", description="Descripción del propósito del campo")
    required: bool = Field(True, description="Indica si el campo es obligatorio")


class OutputField(BaseModel):
    """Campo de salida tipado para contratos de Skills y Pipelines."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
    )

    name: str = Field(..., min_length=1, description="Nombre único del campo")
    type_str: str = Field(..., min_length=1, description="Tipo declarado del campo")
    description: str = Field("", description="Descripción del propósito del campo")


class InputContract(BaseModel):
    """Contrato de entrada: lista validada de campos requeridos por un Skill o Pipeline."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
    )

    fields: List[InputField] = Field(
        default_factory=list,
        description="Campos de entrada del contrato",
    )

    @field_validator("fields")
    @classmethod
    def _fields_unique_and_nonempty(cls, value: List[InputField]) -> List[InputField]:
        names = [f.name for f in value]
        seen = set()
        for name in names:
            if not name or not name.strip():
                raise ValueError("InputField.name no puede estar vacío")
            if name in seen:
                raise ValueError(f"InputField.name duplicado: '{name}'")
            seen.add(name)
        return value


class OutputContract(BaseModel):
    """Contrato de salida: lista validada de campos producidos por un Skill o Pipeline."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        validate_assignment=True,
    )

    fields: List[OutputField] = Field(
        default_factory=list,
        description="Campos de salida del contrato",
    )

    @field_validator("fields")
    @classmethod
    def _fields_unique_and_nonempty(cls, value: List[OutputField]) -> List[OutputField]:
        names = [f.name for f in value]
        seen = set()
        for name in names:
            if not name or not name.strip():
                raise ValueError("OutputField.name no puede estar vacío")
            if name in seen:
                raise ValueError(f"OutputField.name duplicado: '{name}'")
            seen.add(name)
        return value
