# app/domain/reducer.py
from app.domain.snapshots import IncidentSnapshot, utcnow

def reduce_snapshot(curr: IncidentSnapshot | None, *, 
                    title: str | None = None,
                    description: str | None = None,
                    status: str | None = None,
                    key: str | None = None) -> IncidentSnapshot:
    if curr is None:
        return IncidentSnapshot(
            key=key or "",
            title=title,
            description=description,
            status=status or "NEW",
            updated_at=utcnow().isoformat(),
        )
    # declarative: build new snapshot from curr + provided fields
    return IncidentSnapshot(
        key=curr.key,
        title=title if title is not None else curr.title,
        description=description if description is not None else curr.description,
        status=status if status is not None else curr.status,
        updated_at=utcnow().isoformat(),
    )
