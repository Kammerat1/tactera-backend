from sqlmodel import SQLModel, Field, Relationship, select
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


# === REQUEST MODELS ===

class ManagerRegister(BaseModel):
    email: str
    password: str

class ManagerLogin(BaseModel):
    email: str
    password: str

# === MANAGER MODEL ===

class Manager(SQLModel, table=True):
    email: str = Field(primary_key=True)
    password_hash: str

    # One-to-one: Manager owns one club
    club: Optional["Club"] = Relationship(back_populates="manager")


# === CLUB MODEL ===

class Club(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    club_name: str
    manager_email: str = Field(foreign_key="manager.email")

    # One-to-many: Club has many players
    squad: List["Player"] = Relationship(back_populates="club")

    # Backref to Manager
    manager: Optional[Manager] = Relationship(back_populates="club")


# === PLAYER MODEL ===

# === PLAYER MODEL ===

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # Base stat values
    pace: int
    passing: int
    defending: int

    # XP for each stat
    pace_xp: int = Field(default=0)
    passing_xp: int = Field(default=0)
    defending_xp: int = Field(default=0)

    club_id: int = Field(foreign_key="club.id")
    club: Optional["Club"] = Relationship(back_populates="squad")


# === MATCH RESULT MODEL ===

from datetime import datetime

class MatchResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    home_club_id: int
    away_club_id: int
    home_goals: int
    away_goals: int

    possession_home: int
    possession_away: int
    corners_home: int
    corners_away: int
    shots_home: int
    shots_away: int
    shots_on_target_home: int
    shots_on_target_away: int

    created_at: datetime = Field(default_factory=datetime.utcnow)

# === TRAINING GROUND MODEL ===

from datetime import datetime

class TrainingGround(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    club_id: int = Field(foreign_key="club.id")
    level: int  # From 1 (worst) to 10 (best)
    tier: str   # e.g. "Basic", "Elite"
    xp_boost: int  # XP awarded per training session
    built_when: datetime = Field(default_factory=datetime.utcnow)

    # Optional: Link back to club later if needed
    # club: Optional[Club] = Relationship(back_populates="training_ground")

from sqlmodel import SQLModel, Field

class StatLevelRequirement(SQLModel, table=True):
    level: int = Field(primary_key=True)
    xp_required: int

from sqlmodel import Session
from database import engine

def seed_level_requirements():
    """
    Fills the StatLevelRequirement table with XP thresholds for each level.
    Levels 1–10 increase by a flat 50 XP.
    Levels 11+ increase incrementally by 10 XP per level.
    """
    from models import StatLevelRequirement
    with Session(engine) as session:
        # Check if already seeded
        count = session.exec(select(StatLevelRequirement)).all()
        if count:
            return

        levels = []
        xp = 0

        for level in range(1, 101):
            if level <= 10:
                xp_required = (level - 1) * 50
            else:
                increment = 50 + (level - 11) * 10
                xp_required += increment

            levels.append(StatLevelRequirement(level=level, xp_required=xp_required))

        session.add_all(levels)
        session.commit()


#TEMPORARY FUNCTION FOR READING EXCEL FILES
from sqlmodel import delete
from sqlalchemy.exc import SQLAlchemyError

def reset_statlevel_table(session: Session):
    """
    Completely clears the statlevelrequirement table.
    Only use this before re-seeding.
    """
    try:
        session.exec(delete(StatLevelRequirement))
        session.commit()
        print("✅ statlevelrequirement table cleared.")
    except SQLAlchemyError as e:
        session.rollback()
        print("❌ Failed to clear table:", e)
