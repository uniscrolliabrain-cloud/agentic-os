"""TaskScheduler (spec 11, 14). Ejecuta TaskPlan en orden topologico."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from ..cognition.agents.schemas import TaskNode, TaskPlan
from ..kernel.world.events import Event


NodeRunner = Callable[[TaskNode, Dict[str, Any]], Dict[str, Any]]


class SchedulerError(RuntimeError):
    """Error de planificacion (ciclo, dep huerfana)."""


class PlanPausedForApproval(RuntimeError):
    """El plan se ha pausado esperando aprobacion humana."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        super().__init__(f"plan pausado en node {node_id!r} esperando aprobacion")


class TaskScheduler:
    """Ejecuta un TaskPlan llamando a un `node_runner` inyectado.

    - No construye Executor ni ejecuta tools: delega todo.
    - Un node se despacha cuando sus depends_on estan COMPLETED.
    - Un node que devuelve state="NEEDS_APPROVAL" pausa el plan.
    - `resume(node_id, approved=True)` reanuda el plan.
    - Un node FAILED bloquea a sus dependientes.
    """

    def __init__(
        self,
        plan: TaskPlan,
        node_runner: NodeRunner,
        event_log: Any = None,
        tenant_id: str = "system",
        correlation_id: Optional[str] = None,
        command_id: Optional[str] = None,
    ):
        self.plan = plan
        self.node_runner = node_runner
        self.event_log = event_log
        self.tenant_id = tenant_id
        self.correlation_id = correlation_id
        self.command_id = command_id
        self._states: Dict[str, str] = {n.id: n.state for n in plan.nodes}
        self._outputs: Dict[str, Any] = {}

    def _emit(self, kind: str, node_id: str, payload: Dict[str, Any]) -> None:
        if self.event_log is None:
            return
        self.event_log.append(Event(
            kind=kind, entity_id=node_id, tenant_id=self.tenant_id,
            actor_id="task_scheduler", payload=payload,
            correlation_id=self.correlation_id, command_id=self.command_id,
        ))

    def _topological_order(self) -> List[TaskNode]:
        incoming = {n.id: 0 for n in self.plan.nodes}
        adj: Dict[str, List[str]] = {n.id: [] for n in self.plan.nodes}
        for n in self.plan.nodes:
            for dep in n.depends_on:
                if dep not in incoming:
                    raise SchedulerError(
                        f"node {n.id!r} depende de {dep!r} inexistente"
                    )
                adj[dep].append(n.id)
                incoming[n.id] += 1
        frontier = [i for i, c in incoming.items() if c == 0]
        order: List[str] = []
        while frontier:
            cur = frontier.pop(0)
            order.append(cur)
            for nxt in adj[cur]:
                incoming[nxt] -= 1
                if incoming[nxt] == 0:
                    frontier.append(nxt)
        if len(order) != len(self.plan.nodes):
            raise SchedulerError("TaskPlan tiene un ciclo")
        by_id = {n.id: n for n in self.plan.nodes}
        return [by_id[i] for i in order]

    def _deps_ready(self, node: TaskNode) -> bool:
        return all(self._states.get(d) == "COMPLETED" for d in node.depends_on)

    def _deps_blocked(self, node: TaskNode) -> bool:
        return any(self._states.get(d) in ("FAILED", "BLOCKED", "CANCELLED")
                   for d in node.depends_on)

    def run(self) -> Dict[str, Any]:
        """Ejecuta hasta terminar, fallar o pausar. Devuelve resumen."""
        for node in self._topological_order():
            if self._states[node.id] == "COMPLETED":
                continue
            if self._deps_blocked(node):
                self._states[node.id] = "BLOCKED"
                self._emit("NodeStateChanged", node.id,
                           {"from": node.state, "to": "BLOCKED"})
                continue
            if not self._deps_ready(node):
                continue

            self._states[node.id] = "RUNNING"
            self._emit("NodeDispatched", node.id,
                       {"agent_id": node.agent_id})
            try:
                result = self.node_runner(node, dict(self._outputs)) or {}
            except PlanPausedForApproval:
                raise
            except Exception as exc:  # noqa: BLE001
                self._states[node.id] = "FAILED"
                self._emit("NodeFailed", node.id,
                           {"agent_id": node.agent_id, "error": str(exc)[:300]})
                continue

            state = result.get("state", "COMPLETED")
            if state == "NEEDS_APPROVAL":
                self._states[node.id] = "NEEDS_APPROVAL"
                self._emit("PlanPausedForApproval", node.id,
                           {"agent_id": node.agent_id})
                raise PlanPausedForApproval(node.id)

            self._states[node.id] = state
            if state == "COMPLETED":
                self._outputs[node.id] = result.get("output")
                self._emit("NodeCompleted", node.id,
                           {"agent_id": node.agent_id,
                            "output_keys": sorted((result.get("output") or {}).keys())})

        status = "COMPLETED"
        if any(s == "FAILED" for s in self._states.values()):
            status = "FAILED"
        elif any(s == "BLOCKED" for s in self._states.values()):
            status = "BLOCKED"
        elif any(s == "NEEDS_APPROVAL" for s in self._states.values()):
            status = "PAUSED_FOR_APPROVAL"

        return {
            "plan_id": self.plan.id,
            "status": status,
            "states": dict(self._states),
            "outputs": dict(self._outputs),
        }

    def resume(self, node_id: str, approved: bool = True) -> Dict[str, Any]:
        """Reanuda un plan pausado. `approved=False` cancela el nodo."""
        if self._states.get(node_id) != "NEEDS_APPROVAL":
            raise SchedulerError(
                f"node {node_id!r} no esta en NEEDS_APPROVAL"
            )
        if not approved:
            self._states[node_id] = "CANCELLED"
            self._emit("NodeStateChanged", node_id,
                       {"from": "NEEDS_APPROVAL", "to": "CANCELLED"})
            return {"plan_id": self.plan.id, "status": "CANCELLED",
                    "states": dict(self._states)}
        self._states[node_id] = "RUNNING"
        self._emit("PlanResumed", node_id, {"decision": "approve"})
        # Re-ejecutar el nodo aprobado
        node = next((n for n in self.plan.nodes if n.id == node_id), None)
        if node is None:
            raise SchedulerError(f"node {node_id!r} no existe")
        try:
            result = self.node_runner(node, dict(self._outputs)) or {}
        except Exception as exc:  # noqa: BLE001
            self._states[node_id] = "FAILED"
            self._emit("NodeFailed", node_id, {"error": str(exc)[:300]})
            return self.run()
        self._states[node_id] = result.get("state", "COMPLETED")
        if self._states[node_id] == "COMPLETED":
            self._outputs[node_id] = result.get("output")
        return self.run()


__all__ = ["NodeRunner", "SchedulerError", "PlanPausedForApproval", "TaskScheduler"]

