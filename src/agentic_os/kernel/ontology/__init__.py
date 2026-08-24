from .metamodel import EntityMeta, RelationMeta, CapabilityMeta
from .entities import Entity
from .relations import Relation
from .capabilities import Capability
from .vocabulary import Vocabulary, DEFAULT_VOCAB
from .validator import OntologyValidator
__all__=["EntityMeta","RelationMeta","CapabilityMeta","Entity","Relation","Capability","Vocabulary","DEFAULT_VOCAB","OntologyValidator"]
