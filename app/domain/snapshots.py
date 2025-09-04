# app/domain/snapshots.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
from datetime import datetime, timezone
import hashlib, json

def utcnow(): return datetime.now(tz=timezone.utc)

@dataclass(frozen=True)
class IncidentSnapshot:
    key: str                 # "glpi:v11:123"
    title: str | None
    description: str | None
    status: str              # canonical "NEW|ASSIGNED|..."
    updated_at: str          # ISO string (normalized)

    def to_canonical(self) -> Dict[str, Any]:
        # exclude volatile fields if needed (e.g., updated_at) or round them
        return {
            "key": self.key,
            "title": self.title,
            "description": self.description,
            "status": self.status,
        }

class Hasher:
    def fingerprint(self, snap: IncidentSnapshot) -> str:
        # canonical JSON: sorted keys, no whitespace, utf-8
        blob = json.dumps(snap.to_canonical(), sort_keys=True, separators=(",",":")).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()
