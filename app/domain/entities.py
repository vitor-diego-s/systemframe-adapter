from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from .value_objects import Status, STATUS_ORDER, IncidentKey, BindingId, utcnow

@dataclass
class Incident:
    key: IncidentKey
    title: str | None = None
    description: str | None = None
    status: Status = Status.NEW
    updated_at: datetime = field(default_factory=utcnow)
    version: int = 0

    def apply_status(self, new_status: Status) -> bool:
        """Returns True if changed."""
        curr, new = STATUS_ORDER[self.status], STATUS_ORDER[new_status]
        if new >= curr:
            if new_status != self.status:
                self.status = new_status
                self.version += 1
                self.updated_at = utcnow()
                return True
        return False

@dataclass
class Binding:
    id: BindingId
    target_key: str | None = None
    version: int = 0
    last_success_at: datetime | None = None
    
