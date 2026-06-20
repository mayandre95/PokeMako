from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Move(Base):
    __tablename__ = "moves"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    power = Column(Integer)
    accuracy = Column(Integer)
    pp = Column(Integer)
    damage_class = Column(String(20))  # physical / special / status
    type_id = Column(Integer, ForeignKey("types.id"))
    type = relationship("Type")


class PokemonMove(Base):
    __tablename__ = "pokemon_moves"
    id = Column(Integer, primary_key=True)
    pokemon_id = Column(Integer, ForeignKey("pokemon.id"))
    move_id = Column(Integer, ForeignKey("moves.id"))
    learn_method = Column(String(50))  # level-up / machine / egg / tutor
    level_learned = Column(Integer)
    pokemon = relationship("Pokemon", back_populates="moves")
    move = relationship("Move")
