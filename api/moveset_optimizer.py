import httpx
from cache.redis import get_cached, set_cache
from models import Type
from scoring import _load_type_chart

ATTACKING_ROLES = {"attacker", "sweeper"}
UTILITY_ROLES = {"tank", "support"}

# Un point de couverture (un type supplémentaire touché en super efficace) pèse
# comme 15 points de DPS théorique — assez pour départager deux attaques de DPS
# proches en faveur de la plus polyvalente, sans qu'une attaque faible mais très
# couvrante ne dépasse une attaque nettement plus puissante.
COVERAGE_WEIGHT = 15

# Priorité de méthode : plus petit = plus "naturel". Sert à choisir quelle
# occurrence garder quand une attaque est apprenable par plusieurs méthodes
# dans la même version (déduplication), et à départager le tri final.
METHOD_PRIORITY = {"level-up": 0, "egg": 1, "tutor": 1, "machine": 2}
METHOD_BONUS = {"level-up": 5, "egg": 2, "tutor": 2, "machine": 0}
METHOD_LABEL_FR = {"egg": "Œuf", "tutor": "Tuteur"}

MACHINE_TTL = 60 * 60 * 24 * 60  # 60 jours — un mapping CT/CS ↔ move ne change jamais

# Attaques dont l'effet exige que la cible ait déjà un état précis pour
# fonctionner — PokéAPI ne structure pas cette dépendance ("requires"),
# seulement ce qu'une attaque INFLIGE (meta.ailment.name, structuré, utilisé
# par _has_enabler ci-dessous). Liste volontairement minimale et stable : dans
# toute la licence, seules Dévorêve et Cauchemar ont cette contrainte.
REQUIRES_AILMENT = {138: "sleep", 171: "sleep"}  # Dévorêve, Cauchemar
AILMENT_FR = {"sleep": "endormie"}


def filter_by_version_group(movepool: list[dict], version_group: str) -> list[dict]:
    return [m for m in movepool if m["version_group"] == version_group]


def deduplicate_moves(movepool: list[dict]) -> list[dict]:
    """Une même attaque peut être apprenable par plusieurs méthodes dans une
    même version (ex. connue par niveau ET disponible en CT) — on garde la
    méthode la plus "naturelle" (pas d'objet nécessaire si déjà apprise par
    niveau), pas une occurrence arbitraire."""
    best: dict[int, dict] = {}
    for move in movepool:
        current = best.get(move["id"])
        if (
            current is None
            or METHOD_PRIORITY[move["method"]] < METHOD_PRIORITY[current["method"]]
        ):
            best[move["id"]] = move
    return list(best.values())


def _has_enabler(movepool: list[dict], ailment: str) -> bool:
    """Le Pokémon a-t-il, dans son movepool disponible, une attaque qui
    infligerait l'état requis (ex. le sommeil pour Dévorêve) ?"""
    return any(m.get("ailment") == ailment for m in movepool)


def _move_dps(move: dict) -> float:
    power = move["power"] or 0
    accuracy = move["accuracy"] if move["accuracy"] is not None else 100
    return power * accuracy / 100


def _type_coverage(
    move_type_id: int | None, chart: dict, all_type_ids: list[int]
) -> int:
    if not move_type_id:
        return 0
    return sum(
        1
        for defender_id in all_type_ids
        if chart.get((move_type_id, defender_id), 1.0) > 1.0
    )


def _dominant_damage_class(pokemon) -> str:
    return (
        "physical" if (pokemon.attack or 0) >= (pokemon.sp_attack or 0) else "special"
    )


def _score_damage_move(move: dict) -> float:
    return (
        move["dps"]
        + move["types_covered"] * COVERAGE_WEIGHT
        + METHOD_BONUS[move["method"]]
    )


def _score_status_move(move: dict) -> float:
    return (move["pp"] or 0) + METHOD_BONUS[move["method"]]


def _move_machines(client: httpx.Client, move_id: int) -> dict[str, str]:
    """{version_group: url du /machine/{id}} pour cette attaque, depuis PokéAPI.
    Mis en cache dans un wrapper {"machines": ...} : beaucoup d'attaques n'ont
    aucune CT/CS (dict vide {}), qui serait "falsy" et referait l'appel HTTP à
    chaque fois si on le cachait tel quel (`if cached := get_cached(...)` ne
    distingue pas "pas en cache" de "en cache, mais vide")."""
    cache_key = f"move-machines:{move_id}"
    if cached := get_cached(cache_key):
        return cached["machines"]
    resp = client.get(f"https://pokeapi.co/api/v2/move/{move_id}/", timeout=10.0)
    machines = {}
    if resp.status_code == 200:
        for entry in resp.json().get("machines", []):
            machines[entry["version_group"]["name"]] = entry["machine"]["url"]
    set_cache(cache_key, {"machines": machines}, ttl=MACHINE_TTL)
    return machines


def _machine_item_name(client: httpx.Client, machine_url: str) -> str | None:
    cache_key = f"machine-item:{machine_url}"
    if cached := get_cached(cache_key):
        return cached["item"]
    resp = client.get(machine_url, timeout=10.0)
    item = resp.json()["item"]["name"] if resp.status_code == 200 else None
    set_cache(cache_key, {"item": item}, ttl=MACHINE_TTL)
    return item


def is_hm(client: httpx.Client, move_id: int, version_group: str) -> bool:
    url = _move_machines(client, move_id).get(version_group)
    if not url:
        return False
    item = _machine_item_name(client, url)
    return bool(item and item.startswith("hm"))


def method_label(client: httpx.Client, move: dict, version_group: str) -> str | None:
    method = move["method"]
    if method == "level-up":
        return None
    if method in METHOD_LABEL_FR:
        return METHOD_LABEL_FR[method]
    url = _move_machines(client, move["id"]).get(version_group)
    item = _machine_item_name(client, url) if url else None
    if not item:
        return "CT"
    number = "".join(ch for ch in item if ch.isdigit())
    return ("CS" if item.startswith("hm") else "CT") + number


def _reason(move: dict, role: str) -> str:
    if move["damage_class"] == "status":
        base = (
            f"Attaque de statut ({move['pp']} PP) — priorisée pour un rôle "
            f"{role} axé sur la durabilité plutôt que les dégâts directs"
        )
    else:
        accuracy = move["accuracy"] if move["accuracy"] is not None else 100
        base = (
            f"DPS théorique {move['dps']} (Puissance {move['power']} × Précision "
            f"{accuracy}%), super efficace contre {move['types_covered']} type(s)"
        )
    required = REQUIRES_AILMENT.get(move["id"])
    if required:
        base += (
            f" — ne fonctionne que si la cible est {AILMENT_FR.get(required, required)} : "
            "à combiner avec une attaque qui inflige cet état"
        )
    return base


def recommend_moveset(
    db,
    pokemon,
    movepool: list[dict],
    role: str,
    version_group: str,
    exclude_hm: bool,
    exclude_tm: bool,
    client: httpx.Client,
) -> list[dict]:
    moves = deduplicate_moves(filter_by_version_group(movepool, version_group))

    if exclude_hm:
        moves = [
            m
            for m in moves
            if m["method"] != "machine" or not is_hm(client, m["id"], version_group)
        ]
    if exclude_tm:
        moves = [
            m
            for m in moves
            if m["method"] != "machine" or is_hm(client, m["id"], version_group)
        ]

    # Une attaque comme Dévorêve, sans aucune attaque infligeant le sommeil
    # disponible pour ce Pokémon dans cette version, est inutile seule.
    moves = [
        m
        for m in moves
        if m["id"] not in REQUIRES_AILMENT
        or _has_enabler(moves, REQUIRES_AILMENT[m["id"]])
    ]

    type_name_to_id = {t.name: t.id for t in db.query(Type).all()}
    chart = _load_type_chart(db, pokemon.generation or 1)
    all_type_ids = list(type_name_to_id.values())

    scored = [
        {
            **move,
            "dps": round(_move_dps(move), 1),
            "types_covered": _type_coverage(
                type_name_to_id.get(move["type"]), chart, all_type_ids
            ),
        }
        for move in moves
    ]

    damage_moves = [m for m in scored if m["damage_class"] != "status" and m["power"]]
    status_moves = [m for m in scored if m["damage_class"] == "status"]
    damage_moves.sort(key=_score_damage_move, reverse=True)
    status_moves.sort(key=_score_status_move, reverse=True)

    if role in ATTACKING_ROLES:
        dominant = _dominant_damage_class(pokemon)
        specialized = [m for m in damage_moves if m["damage_class"] == dominant]
        is_mixed = abs((pokemon.attack or 0) - (pokemon.sp_attack or 0)) <= 15
        candidates = (
            specialized if (len(specialized) >= 4 or not is_mixed) else damage_moves
        )
    elif role in UTILITY_ROLES:
        candidates = status_moves + damage_moves
    else:  # versatility
        candidates = []
        for i in range(max(len(damage_moves), len(status_moves))):
            if i < len(damage_moves):
                candidates.append(damage_moves[i])
            if i < len(status_moves):
                candidates.append(status_moves[i])

    selected = candidates[:4]
    for move in selected:
        move["method_label"] = method_label(client, move, version_group)
        move["reason"] = _reason(move, role)
    return selected
