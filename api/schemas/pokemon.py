from pydantic import BaseModel, ConfigDict


class PokemonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    name_en: str
    name_fr: str | None
    generation: int | None
    hp: int | None
    attack: int | None
    defense: int | None
    sp_attack: int | None
    sp_defense: int | None
    speed: int | None
    base_experience: int | None
    height: int | None
    weight: int | None
    is_legendary: bool
    is_mythical: bool
    sprite_url: str | None
    artwork_url: str | None
