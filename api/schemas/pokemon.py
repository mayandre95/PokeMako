from pydantic import BaseModel, ConfigDict, field_validator


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
    types: list[str] = []

    @field_validator("types", mode="before")
    @classmethod
    def coerce_types(cls, v: list) -> list[str]:
        # Accepte str (depuis le cache Redis) et PokemonType ORM (depuis la DB)
        return [item if isinstance(item, str) else item.type.name for item in v]
