from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

from database import get_db
from limiter import limiter
from models import Pokemon
from routers.pokemon import router as pokemon_router
from security import verify_api_key

app = FastAPI(
    title="PokéMako API",
    description="API Pokémon avec rate limiting et cache Redis.",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pokemon_router)


@app.get("/health", tags=["Infra"])
def health():
    return {"status": "ok"}


@app.get("/db-health", tags=["Admin"], dependencies=[Depends(verify_api_key)])
def db_health(db: Session = Depends(get_db)):
    count = db.query(Pokemon).count()
    return {"status": "ok", "pokemon_count": count}
