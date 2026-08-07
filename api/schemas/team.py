from pydantic import BaseModel, Field


class TeamRequest(BaseModel):
    pokemon_ids: list[int] = Field(min_length=1, max_length=6)
    generation: int | None = None
