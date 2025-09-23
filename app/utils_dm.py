# app/utils_dm.py
# Utilitaires DM: nouveau format basé sur IDs + compat ancien format par usernames.

def canonical_dm_room_ids(id1: int, id2: int) -> str:
    """Crée un room_id canonique pour DM par IDs (dmid:<min>:<max>)."""
    a, b = sorted([int(id1), int(id2)])
    return f"dmid:{a}:{b}"

def is_dm_room_ids(room_id: str) -> bool:
    """Vrai si room_id est au format dmid:<idA>:<idB>."""
    return room_id.startswith("dmid:") and room_id.count(":") == 2

def parse_dm_ids(room_id: str) -> tuple[int, int]:
    """Extrait les deux IDs du room_id dmid:..."""
    _, a, b = room_id.split(":")
    return int(a), int(b)

# --- Compat ancien format par usernames ---

def canonical_dm_room(u1: str, u2: str) -> str:
    a, b = sorted([u1, u2])
    return f"dm:{a}:{b}"

def is_dm_room(room_id: str) -> bool:
    return room_id.startswith("dm:") and room_id.count(":") == 2
