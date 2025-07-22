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

    # Link to the training ground this club owns
    trainingground_id: Optional[int] = Field(default=None, foreign_key="trainingground.id")


    # One-to-many: Club has many players
    squad: List["Player"] = Relationship(back_populates="club")

    # Backref to Manager
    manager: Optional[Manager] = Relationship(back_populates="club")

# === PLAYER MODEL ===

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

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

        # 👇 NEW: Table to store each training session
class TrainingSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)  # unique ID for this session

    player_id: int = Field(foreign_key="player.id")  # which player trained
    player: Optional["Player"] = Relationship()      # optional relationship if needed later

    timestamp: datetime = Field(default_factory=datetime.utcnow)  # when the session happened

    # XP gained in this session — not total
    pace_xp: int = Field(default=0)
    passing_xp: int = Field(default=0)
    defending_xp: int = Field(default=0)

    drill: str  # short label like "Speed Drill"
    note: Optional[str] = None  # optional details or notes



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


