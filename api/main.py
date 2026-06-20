from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Pokemon

app = FastAPI(title="PokéMako API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-health")
def db_health(db: Session = Depends(get_db)):
    count = db.query(Pokemon).count()
    return {"status": "ok", "pokemon_count": count}
