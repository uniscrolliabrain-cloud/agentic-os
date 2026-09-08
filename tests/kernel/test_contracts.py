from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_os.contracts.core import (
    InputContract,
    InputField,
    OutputContract,
    OutputField,
)


# ── InputField ─────────────────────────────────────────────────────────────


class TestInputField:
    def test_creates_valid_input_field(self) -> None:
        field = InputField(
            name="email",
            type_str="str",
            description="Email del destinatario",
        )
        assert field.name == "email"
        assert field.type_str == "str"
        assert field.description == "Email del destinatario"
        assert field.required is True

    def test_required_defaults_to_true(self) -> None:
        field = InputField(name="x", type_str="int", description="")
        assert field.required is True

    def test_optional_field(self) -> None:
        field = InputField(
            name="cc",
            type_str="str",
            description="Copia",
            required=False,
        )
        assert field.required is False

    def test_frozen_immutable(self) -> None:
        field = InputField(name="x", type_str="int", description="")
        with pytest.raises(ValidationError):
            field.name = "y"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            InputField(name="x", type_str="int", description="", extra_field="bad")

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            InputField(name="", type_str="str", description="")

    def test_empty_type_str_rejected(self) -> None:
        with pytest.raises(ValidationError):
            InputField(name="x", type_str="", description="")


# ── OutputField ────────────────────────────────────────────────────────────


class TestOutputField:
    def test_creates_valid_output_field(self) -> None:
        field = OutputField(
            name="status",
            type_str="str",
            description="Estado de la operación",
        )
        assert field.name == "status"
        assert field.type_str == "str"
        assert field.description == "Estado de la operación"

    def test_frozen_immutable(self) -> None:
        field = OutputField(name="x", type_str="int", description="")
        with pytest.raises(ValidationError):
            field.name = "y"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            OutputField(name="x", type_str="int", description="", unknown="bad")

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            OutputField(name="", type_str="str", description="")

    def test_empty_type_str_rejected(self) -> None:
        with pytest.raises(ValidationError):
            OutputField(name="x", type_str="", description="")


# ── InputContract ──────────────────────────────────────────────────────────


class TestInputContract:
    def test_creates_empty_contract(self) -> None:
        contract = InputContract()
        assert contract.fields == []

    def test_creates_contract_with_fields(self) -> None:
        contract = InputContract(
            fields=[
                InputField(name="email", type_str="str", description="Email"),
                InputField(name="subject", type_str="str", description="Asunto"),
            ]
        )
        assert len(contract.fields) == 2
        assert contract.fields[0].name == "email"
        assert contract.fields[1].name == "subject"

    def test_rejects_duplicate_field_names(self) -> None:
        with pytest.raises(ValidationError, match="duplicado"):
            InputContract(
                fields=[
                    InputField(name="email", type_str="str", description=""),
                    InputField(name="email", type_str="str", description=""),
                ]
            )

    def test_rejects_empty_field_name(self) -> None:
        with pytest.raises(ValidationError):
            InputContract(
                fields=[
                    InputField(name="", type_str="str", description=""),
                ]
            )

    def test_frozen_immutable(self) -> None:
        contract = InputContract(
            fields=[InputField(name="x", type_str="int", description="")]
        )
        with pytest.raises(ValidationError):
            contract.fields = []

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            InputContract(fields=[], unknown_field="bad")


# ── OutputContract ─────────────────────────────────────────────────────────


class TestOutputContract:
    def test_creates_empty_contract(self) -> None:
        contract = OutputContract()
        assert contract.fields == []

    def test_creates_contract_with_fields(self) -> None:
        contract = OutputContract(
            fields=[
                OutputField(name="status", type_str="str", description=""),
                OutputField(name="message", type_str="str", description=""),
            ]
        )
        assert len(contract.fields) == 2
        assert contract.fields[0].name == "status"
        assert contract.fields[1].name == "message"

    def test_rejects_duplicate_field_names(self) -> None:
        with pytest.raises(ValidationError, match="duplicado"):
            OutputContract(
                fields=[
                    OutputField(name="result", type_str="str", description=""),
                    OutputField(name="result", type_str="str", description=""),
                ]
            )

    def test_rejects_empty_field_name(self) -> None:
        with pytest.raises(ValidationError):
            OutputContract(
                fields=[
                    OutputField(name="", type_str="str", description=""),
                ]
            )

    def test_frozen_immutable(self) -> None:
        contract = OutputContract(
            fields=[OutputField(name="x", type_str="int", description="")]
        )
        with pytest.raises(ValidationError):
            contract.fields = []

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            OutputContract(fields=[], unknown_field="bad")

            contract.fields = []

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            InputContract(fields=[], unknown_field="bad")
