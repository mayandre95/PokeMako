from typing import Annotated

from cache.redis import get_cached, set_cache
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Request
from limiter import limiter
from models import Pokemon, PokemonScore, PokemonType, Type
from schemas.team import TeamRequest
from scoring import _load_type_chart
from sqlalchemy.orm import Session, joinedload
from team_analyzer import (
    analyze_member_matchups,
    analyze_offensive_coverage,
    analyze_remaining_weaknesses,
    analyze_weaknesses,
    suggest_recruits,
)

router = APIRouter(prefix="/team", tags=["Team Builder"])

RATE_LIMIT = "20/minute"
NOT_FOUND_DETAIL = "Aucun Pokémon trouvé pour ces IDs"


def _summary(p: Pokemon) -> dict:
    return {
        "id": p.id,
        "name_fr": p.name_fr,
        "name_en": p.name_en,
        "sprite_url": p.sprite_url,
        "generation": p.generation,
        "types": [pt.type.name for pt in p.types],
        "type_ids": [pt.type_id for pt in p.types],
    }


@router.post(
    "/analyze",
    responses={
        404: {"description": NOT_FOUND_DETAIL},
        429: {"description": "Trop de requêtes — réessayez dans 60s"},
    },
)
@limiter.limit(RATE_LIMIT)
def analyze_team(
    request: Request,
    body: TeamRequest,
    db: Annotated[Session, Depends(get_db)] = None,
):
    cache_key = (
        f"team:{','.join(map(str, body.pokemon_ids))}:{body.generation or 'auto'}"
    )
    if cached := get_cached(cache_key):
        return cached

    pokemons = (
        db.query(Pokemon)
        .options(joinedload(Pokemon.types).joinedload(PokemonType.type))
        .filter(Pokemon.id.in_(body.pokemon_ids))
        .all()
    )
    if not pokemons:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    pokemon_map = {p.id: p for p in pokemons}
    team = [
        _summary(pokemon_map[pid]) for pid in body.pokemon_ids if pid in pokemon_map
    ]

    # Un Pokémon ne peut pas exister avant sa propre génération d'introduction —
    # la génération choisie ne peut donc jamais être inférieure à celle du
    # membre le plus récemment introduit de l'équipe.
    min_generation = max(p.generation or 1 for p in pokemons)
    generation = body.generation or min_generation
    if generation < min_generation:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Génération {generation} incompatible avec l'équipe "
                f"(minimum {min_generation})"
            ),
        )

    chart = _load_type_chart(db, generation)
    type_id_to_name = {t.id: t.name for t in db.query(Type).all()}
    all_type_ids = list(type_id_to_name)

    weaknesses = analyze_weaknesses(team, chart, all_type_ids)
    offensive = analyze_offensive_coverage(team, chart, all_type_ids)
    remaining = analyze_remaining_weaknesses(team, weaknesses, chart)
    matchups = analyze_member_matchups(team, chart, all_type_ids)

    team_with_matchups = [
        {
            **m,
            "weaknesses": [type_id_to_name[t] for t in matchups[m["id"]]["weaknesses"]],
            "resistances": [
                type_id_to_name[t] for t in matchups[m["id"]]["resistances"]
            ],
        }
        for m in team
    ]

    team_ids = set(body.pokemon_ids)
    scores = {s.pokemon_id: s.power_score for s in db.query(PokemonScore).all()}
    candidates = [
        {**_summary(p), "power_score": scores.get(p.id)}
        for p in db.query(Pokemon)
        .options(joinedload(Pokemon.types).joinedload(PokemonType.type))
        .filter(~Pokemon.id.in_(team_ids), Pokemon.generation <= generation)
        .all()
    ]
    suggestions = suggest_recruits(weaknesses, offensive["gaps"], candidates, chart)

    result = {
        "team": team_with_matchups,
        "generation_used": generation,
        "min_generation": min_generation,
        "weaknesses": [
            {
                "type": type_id_to_name[w["type_id"]],
                "weak_count": w["weak_count"],
                "members": w["members"],
            }
            for w in weaknesses
        ],
        "remaining_weaknesses": [
            {
                "type": type_id_to_name[w["type_id"]],
                "weak_count": w["weak_count"],
                "members": w["members"],
            }
            for w in remaining
        ],
        "offensive_coverage": {
            "covered": [type_id_to_name[t] for t in offensive["covered"]],
            "gaps": [type_id_to_name[t] for t in offensive["gaps"]],
        },
        "suggestions": [
            {
                "id": s["id"],
                "name_fr": s["name_fr"],
                "name_en": s["name_en"],
                "sprite_url": s["sprite_url"],
                "types": s["types"],
                "score": s["score"],
                "covers": [type_id_to_name[t] for t in s["covers"]],
            }
            for s in suggestions
        ],
    }
    set_cache(cache_key, result, ttl=60 * 60)
    return result
