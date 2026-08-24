from __future__ import annotations
from .entities import Entity
from .relations import Relation
from .vocabulary import Vocabulary, DEFAULT_VOCAB
class OntologyValidator:
    def __init__(self, vocab: Vocabulary = DEFAULT_VOCAB):
        self.vocab = vocab
    def validate_entity(self, e: Entity) -> bool:
        return e.kind in self.vocab.entities
    def validate_relation(self, r: Relation) -> bool:
        return r.kind in self.vocab.relations
