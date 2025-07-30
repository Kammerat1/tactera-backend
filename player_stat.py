# player_stat.py

from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlmodel import select
from models import StatLevelRequirement

# PlayerStat model tracks individual stats for each player
class PlayerStat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Link this stat to a player
    player_id: int = Field(foreign_key="player.id")

    # Name of the stat (e.g. "pace", "passing")
    stat_name: str

    # Stat value, from 1–100 for now (can scale up later)
    value: int = Field(default=1, ge=1, le=100)

    # XP earned toward leveling up this stat
    xp: int = Field(default=0)

    # Links both sides of the relationship.
    player: Optional["Player"] = Relationship(back_populates="stats")

# ✅ Manually bind Player.stats <-> PlayerStat.player relationship here.
# This is necessary because Player is defined in models.py and PlayerStat here.
# Defining it in models.py directly caused SQLAlchemy class resolution errors,
# so we defer the binding until both classes exist.
from models import Player
Player.stats = Relationship(back_populates="player")

# HELPER FUNCTION
def get_stat_level(xp: int, session) -> int:
    """
    Given the current XP for a stat, return the correct level
    using the StatLevelRequirement table.

    It finds the highest level where xp_required <= current XP.
    """
    # Query all levels where xp_required <= xp, sorted by highest XP first
    result = session.exec(
        select(StatLevelRequirement)
        .where(StatLevelRequirement.xp_required <= xp)
        .order_by(StatLevelRequirement.xp_required.desc())
    ).first()

    # If we found a matching level, return it
    if result:
        return result.level

    # Default fallback: Level 1
    return 1
