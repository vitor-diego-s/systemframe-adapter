from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone

def utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)

class Status(Enum):
    NEW="NEW"; 
    ASSIGNED="ASSIGNED"; 
    WAITING="WAITING";
    READY_FOR_VALIDATION="READY_FOR_VALIDATION";
    RESOLVED="RESOLVED"; 
    CLOSED="CLOSED"; 

# precedence wins on merge
STATUS_ORDER = {Status.NEW:0, Status.ASSIGNED:1, Status.WAITING:2,
                Status.READY_FOR_VALIDATION:3, Status.RESOLVED:4, Status.CLOSED:5}

@dataclass(frozen=True)
class SystemId:
    name: str  # e.g. "glpi:v11" | "glpi:sf"
    def __str__(self): return self.name

@dataclass(frozen=True)
class IncidentKey:
    system: SystemId
    vendor_key: str
    def __str__(self): return f"{self.system}:{self.vendor_key}"

@dataclass(frozen=True)
class BindingId:
    origin: IncidentKey
    target_system: SystemId
    def __str__(self): return f"{self.origin}::{self.target_system}"
