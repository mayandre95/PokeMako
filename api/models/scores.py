from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class PokemonScore(Base):
    __tablename__ = "pokemon_scores"
    id = Column(Integer, primary_key=True)
    pokemon_id = Column(Integer, ForeignKey("pokemon.id"), unique=True)
    power_score = Column(Integer)  # somme des 6 stats
    offensive_score = Column(Integer)  # atk + sp_atk + speed
    tank_score = Column(Integer)  # hp + def + sp_def
    meta_score = Column(Float)  # score composite
    pokemon = relationship("Pokemon", back_populates="score")
