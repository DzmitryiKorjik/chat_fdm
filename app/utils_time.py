from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo  # stdlib (Python 3.9+)

PARIS = ZoneInfo("Europe/Paris")

def to_paris_iso(dt: datetime) -> str:
    """Convertit un datetime UTC -> ISO8601 à l'heure de Paris."""
    if dt is None:
        return None
    # on suppose dt en UTC (timezone aware)
    return dt.astimezone(PARIS).isoformat()
