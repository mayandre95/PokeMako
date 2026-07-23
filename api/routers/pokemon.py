from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Annotated

from cache.redis import get_cached, set_cache
from database import get_db
from limiter import limiter
from models import Pokemon
from schemas.pokemon import PokemonResponse
from routers.moves import _move_detail
from sqlalchemy.orm import Session, joinedload
import httpx

router = APIRouter(prefix="/pokemon", tags=["Pokémon"])

RATE_LIMIT = "30/minute"
POKEAPI = "https://pokeapi.co/api/v2"


@router.get(
    "/{pokemon_id}",
    response_model=PokemonResponse,
    responses={429: {"description": "Trop de requêtes — réessayez dans 60s"}},
)
@limiter.limit(RATE_LIMIT)
def get_pokemon(
    request: Request, pokemon_id: int, db: Annotated[Session, Depends(get_db)]
):
    cache_key = f"pokemon:{pokemon_id}"

    if cached := get_cached(cache_key):
        return cached

    pokemon = (
        db.query(Pokemon)
        .options(joinedload(Pokemon.types))
        .filter(Pokemon.id == pokemon_id)
        .first()
    )
    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokémon introuvable")

    response = PokemonResponse.model_validate(pokemon).model_dump()
    set_cache(cache_key, response)
    return response


def _area_name_fr(client: httpx.Client, slug: str) -> str | None:
    cache_key = f"area-fr:{slug}"
    if cached := get_cached(cache_key):
        return cached.get("name")
    resp = client.get(f"{POKEAPI}/location-area/{slug}/", timeout=5.0)
    if resp.status_code != 200:
        return None
    fr = next(
        (
            n["name"]
            for n in resp.json().get("names", [])
            if n["language"]["name"] == "fr"
        ),
        None,
    )
    set_cache(cache_key, {"name": fr}, ttl=60 * 60 * 24 * 30)
    return fr


@router.get(
    "/{pokemon_id}/moves",
    responses={
        404: {"description": "Pokémon introuvable"},
        429: {"description": "Trop de requêtes — réessayez dans 60s"},
    },
)
@limiter.limit(RATE_LIMIT)
def get_moves(request: Request, pokemon_id: int):
    cache_key = f"moves:{pokemon_id}"
    if cached := get_cached(cache_key):
        return cached

    with httpx.Client(timeout=10.0) as client:
        resp = client.get(f"{POKEAPI}/pokemon/{pokemon_id}")
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Pokémon introuvable")
        resp.raise_for_status()

        # Une entrée par (move_id, method, version_group)
        move_entries: dict[tuple[int, str, str], dict] = {}
        for mv in resp.json()["moves"]:
            move_id = int(mv["move"]["url"].rstrip("/").split("/")[-1])
            for vd in mv["version_group_details"]:
                method = vd["move_learn_method"]["name"]
                level = vd["level_learned_at"]
                vg = vd["version_group"]["name"]
                key = (move_id, method, vg)
                if key not in move_entries:
                    move_entries[key] = {
                        "id": move_id,
                        "method": method,
                        "level_learned": level,
                        "version_group": vg,
                    }
                elif method == "level-up":
                    # Même move, même version_group, même méthode → garder le niveau minimal
                    move_entries[key]["level_learned"] = min(
                        move_entries[key]["level_learned"], level
                    )

        unique_ids = {mid for (mid, _, _) in move_entries}
        detail_map = {mid: _move_detail(client, mid) for mid in unique_ids}

    METHOD_ORDER = ["level-up", "machine", "egg", "tutor"]
    moves = []
    for (move_id, method, vg), entry in move_entries.items():
        detail = detail_map.get(move_id)
        if not detail:
            continue
        moves.append(
            {
                **entry,
                "name_fr": detail["name_fr"],
                "name_en": detail["name_en"],
                "type": detail["type"],
                "damage_class": detail["damage_class"],
                "power": detail["power"],
                "accuracy": detail["accuracy"],
                "pp": detail["pp"],
            }
        )

    moves.sort(
        key=lambda m: (
            METHOD_ORDER.index(m["method"]) if m["method"] in METHOD_ORDER else 99,
            m["level_learned"],
            m["name_fr"] or m["name_en"],
        )
    )

    result = {"moves": moves}
    set_cache(cache_key, result)
    return result


@router.get(
    "/{pokemon_id}/encounters",
    responses={
        404: {"description": "Pokémon introuvable"},
        429: {"description": "Trop de requêtes — réessayez dans 60s"},
    },
)
@limiter.limit(RATE_LIMIT)
def get_encounters(request: Request, pokemon_id: int):
    cache_key = f"encounters:{pokemon_id}"
    if cached := get_cached(cache_key):
        return cached

    with httpx.Client(timeout=10.0) as client:
        resp = client.get(f"{POKEAPI}/pokemon/{pokemon_id}/encounters")
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Pokémon introuvable")
        resp.raise_for_status()

        encounters = []
        for area in resp.json():
            area_name = area["location_area"]["name"]
            for version_info in area["version_details"]:
                game = version_info["version"]["name"]
                for detail in version_info["encounter_details"]:
                    encounters.append(
                        {
                            "location_area": area_name,
                            "game": game,
                            "method": detail["method"]["name"],
                            "chance": detail["chance"],
                            "min_level": detail["min_level"],
                            "max_level": detail["max_level"],
                            "conditions": [
                                c["name"] for c in detail["condition_values"]
                            ],
                        }
                    )

        unique_slugs = {e["location_area"] for e in encounters}
        name_fr_map = {slug: _area_name_fr(client, slug) for slug in unique_slugs}

    for e in encounters:
        fr = name_fr_map.get(e["location_area"])
        if fr:
            e["location_area_fr"] = fr

    result = {"encounters": encounters, "has_encounters": bool(encounters)}
    set_cache(cache_key, result)
    return result
