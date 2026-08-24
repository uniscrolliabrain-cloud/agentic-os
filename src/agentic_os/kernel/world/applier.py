from __future__ import annotations
from .events import Event
from .state import WorldState
def apply(state: WorldState, event: Event) -> WorldState:
    new_entities = dict(state.entities)
    new_relations = dict(state.relations)
    if event.kind == "entity_created":
        new_entities[event.entity_id] = event.payload
    elif event.kind == "entity_updated":
        if event.entity_id in new_entities:
            new_entities[event.entity_id] = {**new_entities[event.entity_id], **event.payload}
    elif event.kind == "entity_deleted":
        new_entities.pop(event.entity_id, None)
    elif event.kind == "relation_created":
        new_relations[event.entity_id] = event.payload
    elif event.kind == "relation_deleted":
        new_relations.pop(event.entity_id, None)
    return WorldState(entities=new_entities, relations=new_relations, version=state.version+1)
