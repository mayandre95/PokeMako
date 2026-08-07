from typing import Literal

from pydantic import BaseModel


class MovesetRequest(BaseModel):
    role: Literal["attacker", "tank", "support", "sweeper", "versatility"]
    version_group: str
    exclude_hm: bool = False
    exclude_tm: bool = False
