from sqlalchemy import Column, Float, ForeignKey, Integer, UniqueConstraint
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


class TypeEffectiveness(Base):
    __tablename__ = "type_effectiveness"
    id = Column(Integer, primary_key=True)
    attacker_type_id = Column(Integer, ForeignKey("types.id"), nullable=False)
    defender_type_id = Column(Integer, ForeignKey("types.id"), nullable=False)
    multiplier = Column(Float, nullable=False)
    from_generation = Column(Integer, nullable=False)

    attacker = relationship("Type", foreign_keys=[attacker_type_id])
    defender = relationship("Type", foreign_keys=[defender_type_id])

    __table_args__ = (
        UniqueConstraint("attacker_type_id", "defender_type_id", "from_generation"),
    )
