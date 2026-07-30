import httpx
from cache.redis import get_cached, set_cache
from fastapi import APIRouter, HTTPException, Request
from limiter import limiter

router = APIRouter(prefix="/move", tags=["Attaques"])

RATE_LIMIT = "30/minute"
POKEAPI = "https://pokeapi.co/api/v2"
MOVE_TTL = 60 * 60 * 24 * 30  # 30 jours


def _move_detail(client: httpx.Client, move_id: int) -> dict | None:
    """Récupère les détails d'une attaque depuis PokéAPI, avec cache Redis 30 jours."""
    cache_key = f"move-detail:{move_id}"
    if cached := get_cached(cache_key):
        return cached

    resp = client.get(f"{POKEAPI}/move/{move_id}/", timeout=5.0)
    if resp.status_code != 200:
        return None

    data = resp.json()
    names = {n["language"]["name"]: n["name"] for n in data.get("names", [])}
    effects = {
        e["language"]["name"]: e["short_effect"] for e in data.get("effect_entries", [])
    }

    effect_chance = data.get("effect_chance")
    effect_fr = effects.get("fr")
    effect_en = effects.get("en")
    if effect_fr and effect_chance:
        effect_fr = effect_fr.replace("$effect_chance$", str(effect_chance))
    if effect_en and effect_chance:
        effect_en = effect_en.replace("$effect_chance$", str(effect_chance))

    result = {
        "id": data["id"],
        "name_en": names.get("en") or data["name"],
        "name_fr": names.get("fr"),
        "type": data["type"]["name"],
        "damage_class": data["damage_class"]["name"],
        "power": data.get("power"),
        "accuracy": data.get("accuracy"),
        "pp": data.get("pp"),
        "effect_fr": effect_fr,
        "effect_en": effect_en,
    }
    set_cache(cache_key, result, ttl=MOVE_TTL)
    return result


@router.get(
    "/{move_id}",
    responses={
        404: {"description": "Attaque introuvable"},
        429: {"description": "Trop de requêtes — réessayez dans 60s"},
    },
)
@limiter.limit(RATE_LIMIT)
def get_move(request: Request, move_id: int):
    with httpx.Client(timeout=10.0) as client:
        detail = _move_detail(client, move_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Attaque introuvable")
    return detail
