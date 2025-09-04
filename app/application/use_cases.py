from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List
from app.domain.snapshots import Hasher
from app.domain.reducer import reduce_snapshot
from app.domain.events import InboundEvent, MirrorCommand
from app.application.ports import IdempotencyStore, OutboxPort, SnapshotRepository
from app.adapters.memory_repos import InMemoryBindings  # your existing bindings

@dataclass
class ApplyInbound:
    snapshots: SnapshotRepository
    bindings: InMemoryBindings
    idem: IdempotencyStore
    outbox: OutboxPort
    status_maps: Dict[str, Dict[str, str]]
    hasher: Hasher = Hasher()

    def handle(self, ev: InboundEvent) -> None:
        if self.idem.seen(ev.idempotency_key): 
            return
        self.idem.mark(ev.idempotency_key)

        inc_key = str(ev.incident_key)
        curr_snap, curr_fp = self.snapshots.get(inc_key)

        new_snap = reduce_snapshot(
            curr_snap,
            key=inc_key if curr_snap is None else None,
            title=ev.title,
            description=ev.description,
            status=ev.status.value if ev.status else None,
        )

        new_fp = self.hasher.fingerprint(new_snap)
        if new_fp == (curr_fp or ""):
            return

        # persist new state atomically with the fingerprint
        self.snapshots.upsert(new_snap, new_fp)

        cmds: List[MirrorCommand] = []
        for b in self.bindings.targets_for(ev.incident_key):
            if str(b.id.target_system) == str(ev.source):
                continue
            cmds.append(MirrorCommand(
                binding_id=str(b.id),
                target_system=str(b.id.target_system),
                action="upsert_incident",
                payload={
                    "target_key": b.target_key or ev.incident_key.vendor_key,
                    "title": new_snap.title,
                    "description": new_snap.description,
                    "status": new_snap.status,
                },
                idempotency_key=new_fp,
            ))
        if cmds:
            self.outbox.enqueue(cmds)
