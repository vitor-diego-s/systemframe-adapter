from collections import defaultdict
from ..domain.entities import Incident, Binding
from ..domain.value_objects import IncidentKey, BindingId

class InMemoryIncidents:
    def __init__(self): self.store: dict[str, Incident] = {}
    def get(self, key: IncidentKey): return self.store.get(str(key))
    def upsert(self, inc: Incident): self.store[str(inc.key)] = inc

class InMemoryBindings:
    def __init__(self): self.targets: dict[str, list[Binding]] = defaultdict(list)
    def add(self, b: Binding): self.targets[str(b.id.origin)].append(b)
    def targets_for(self, incident_key: IncidentKey): return list(self.targets.get(str(incident_key), []))
    def upsert(self, b: Binding): pass  # not needed for demo

class InMemoryIdem:
    def __init__(self): self.keys=set()
    def seen(self, k:str)->bool: return k in self.keys
    def mark(self, k:str)->None: self.keys.add(k)
