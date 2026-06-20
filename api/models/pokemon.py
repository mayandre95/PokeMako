from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class Type(Base):
    __tablename__ = "types"
    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)


class Pokemon(Base):
    __tablename__ = "pokemon"
    id = Column(Integer, primary_key=True)  # ID PokéAPI
    name_en = Column(String(100), nullable=False)
    name_fr = Column(String(100))
    base_experience = Column(Integer)

    @property
    def name(self) -> str:
        """Français en priorité, anglais en fallback."""
        return self.name_fr or self.name_en

    height = Column(Integer)
    weight = Column(Integer)
    sprite_url = Column(String(255))
    artwork_url = Column(String(255))
    generation = Column(Integer)
    is_legendary = Column(Boolean, default=False)
    is_mythical = Column(Boolean, default=False)
    # Stats de base
    hp = Column(Integer)
    attack = Column(Integer)
    defense = Column(Integer)
    sp_attack = Column(Integer)
    sp_defense = Column(Integer)
    speed = Column(Integer)
    # Relations
    types = relationship("PokemonType", back_populates="pokemon")
    abilities = relationship("PokemonAbility", back_populates="pokemon")
    moves = relationship("PokemonMove", back_populates="pokemon")
    score = relationship("PokemonScore", back_populates="pokemon", uselist=False)


class PokemonType(Base):
    __tablename__ = "pokemon_types"
    id = Column(Integer, primary_key=True)
    pokemon_id = Column(Integer, ForeignKey("pokemon.id"))
    type_id = Column(Integer, ForeignKey("types.id"))
    slot = Column(Integer)  # 1 = type principal, 2 = type secondaire
    pokemon = relationship("Pokemon", back_populates="types")
    type = relationship("Type")


class Ability(Base):
    __tablename__ = "abilities"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    is_hidden = Column(Boolean, default=False)


class PokemonAbility(Base):
    __tablename__ = "pokemon_abilities"
    id = Column(Integer, primary_key=True)
    pokemon_id = Column(Integer, ForeignKey("pokemon.id"))
    ability_id = Column(Integer, ForeignKey("abilities.id"))
    is_hidden = Column(Boolean, default=False)
    pokemon = relationship("Pokemon", back_populates="abilities")
    ability = relationship("Ability")


class Nature(Base):
    __tablename__ = "natures"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    increased_stat = Column(String(50))  # stat boostée (+10%)
    decreased_stat = Column(String(50))  # stat réduite (-10%)
