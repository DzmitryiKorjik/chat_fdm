# Utilitaires DM: nouveau format basé sur IDs + compat ancien format par usernames.


def canonical_dm_room_ids(id1: int, id2: int) -> str:
    """Crée un room_id canonique pour DM par IDs (dmid:<min>:<max>)."""
    a, b = sorted([int(id1), int(id2)])
    return f"dmid:{a}:{b}"


def is_dm_room_ids(room_id: str) -> bool:
    """Vrai si room_id est au format dmid:<idA>:<idB>."""
    return room_id.startswith("dmid:") and room_id.count(":") == 2


def parse_dm_ids(room_id: str) -> tuple[int, int]:
    if not room_id.startswith("dmid:"):
        raise ValueError("room_id n'est pas une DM par IDs (attendu 'dmid:a:b')")
    try:
        _, a, b = room_id.split(":")
        a_i, b_i = int(a), int(b)
    except Exception as exc:
        raise ValueError("room_id DM invalide (attendu 'dmid:a:b')") from exc
    if a_i == b_i:
        raise ValueError("room_id DM invalide: a == b")
    return (a_i, b_i)


def peer_id_for_sender(room_id: str, sender_id: int) -> int:
    a, b = parse_dm_ids(room_id)
    if sender_id == a:
        return b
    if sender_id == b:
        return a
    raise ValueError("sender_id n'appartient pas à cette DM")


# --- Compat ancien format par usernames ---
def canonical_dm_room(u1: str, u2: str) -> str:
    a, b = sorted([u1, u2])
    return f"dm:{a}:{b}"


def is_dm_room(room_id: str) -> bool:
    return room_id.startswith("dm:") and room_id.count(":") == 2
