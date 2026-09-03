from __future__ import annotations

from .base import BaseAgent


class AgentRegistry:
    """Registro tipado de agentes (contrato mínimo; NO orquesta).

    - register/get/exists/remove sobre ``BaseAgent`` (no ``Any``).
    - Falla explícitamente en duplicados y en agentes ausentes.
    """

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent_id: str, agent: BaseAgent) -> None:
        if not agent_id:
            raise ValueError("agent_id es obligatorio")
        if agent_id in self._agents:
            raise ValueError(f"agente duplicado: {agent_id!r}")
        self._agents[agent_id] = agent

    def get(self, agent_id: str) -> BaseAgent:
        try:
            return self._agents[agent_id]
        except KeyError:
            raise KeyError(f"agente no registrado: {agent_id!r}") from None

    def exists(self, agent_id: str) -> bool:
        return agent_id in self._agents

    def remove(self, agent_id: str) -> None:
        try:
            del self._agents[agent_id]
        except KeyError:
            raise KeyError(f"agente no registrado: {agent_id!r}") from None

    def ids(self) -> list[str]:
        return sorted(self._agents)

    def __len__(self) -> int:
        return len(self._agents)

