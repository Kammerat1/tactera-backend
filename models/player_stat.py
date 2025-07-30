from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, select
from tactera_backend.models.stat_level_requirement import StatLevelRequirement

class PlayerStat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id")
    stat_name: str
    value: int = Field(default=1, ge=1, le=100)
    xp: int = Field(default=0)

    player: Optional["Player"] = Relationship(back_populates="stats")

# Deferred import to avoid circular import issues
from tactera_backend.models.player import Player
Player.stats = Relationship(back_populates="player")

def get_stat_level(xp: int, session) -> int:
    """
    Given the current XP for a stat, return the correct level
    using the StatLevelRequirement table.
    """
    result = session.exec(
        select(StatLevelRequirement)
        .where(StatLevelRequirement.xp_required <= xp)
        .order_by(StatLevelRequirement.xp_required.desc())
    ).first()

    if result:
        return result.level
    return 1
