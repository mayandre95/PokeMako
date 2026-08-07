from typing import Annotated

import httpx
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Request
from limiter import limiter
from models import Pokemon
from moveset_optimizer import recommend_moveset
from schemas.moveset import MovesetRequest
from sqlalchemy.orm import Session

from routers.pokemon import _build_movepool

router = APIRouter(prefix="/pokemon", tags=["Moveset"])

RATE_LIMIT = "30/minute"
NOT_FOUND_DETAIL = "Pokémon introuvable"


@router.post(
    "/{pokemon_id}/recommend-moveset",
    responses={
        404: {"description": NOT_FOUND_DETAIL},
        429: {"description": "Trop de requêtes — réessayez dans 60s"},
    },
)
@limiter.limit(RATE_LIMIT)
def recommend_moveset_endpoint(
    request: Request,
    pokemon_id: int,
    body: MovesetRequest,
    db: Annotated[Session, Depends(get_db)] = None,
):
    pokemon = db.query(Pokemon).filter_by(id=pokemon_id).first()
    if not pokemon:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    movepool = _build_movepool(pokemon_id)
    with httpx.Client(timeout=10.0) as client:
        moves = recommend_moveset(
            db,
            pokemon,
            movepool,
            body.role,
            body.version_group,
            body.exclude_hm,
            body.exclude_tm,
            client,
        )
    return {"role": body.role, "version_group": body.version_group, "moves": moves}
