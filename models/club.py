# club.py
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Club(SQLModel, table=True):
    """Database model for clubs in Tactera"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    manager_email: Optional[str] = Field(default=None, foreign_key="manager.email", nullable=True)
    is_bot: bool = Field(default=False)

    league_id: Optional[int] = Field(default=None, foreign_key="league.id")
    trainingground_id: Optional[int] = Field(default=None, foreign_key="trainingground.id")
    last_training_date: Optional["date"] = Field(default=None, nullable=True)

    squad: List["Player"] = Relationship(back_populates="club")
    manager: Optional["Manager"] = Relationship(back_populates="club")
    league: Optional["League"] = Relationship(back_populates="clubs")
    training_ground: Optional["TrainingGround"] = Relationship(back_populates="club")
