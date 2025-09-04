from dataclasses import dataclass
from datetime import datetime
from .value_objects import IncidentKey, Status, SystemId, utcnow

class Action(str):
    CREATE="create"
    UPDATE="update"
    RETRIEVE="find"

@dataclass(frozen=True)
class InboundEvent:
    idempotency_key: str
    source: SystemId
    kind: str            # "incident.created" | "status.changed" | etc.
    incident_key: IncidentKey
    status: Status | None = None
    title: str | None = None
    description: str | None = None
    occurred_at: datetime = utcnow()

@dataclass(frozen=True)
class MirrorCommand:
    binding_id: str
    target_system: str
    action: Action
    payload: dict
    idempotency_key: str
