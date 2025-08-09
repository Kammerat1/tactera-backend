# tactera_backend/models/formation_model.py
# Defines formation templates and club lineup management

from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from pydantic import BaseModel

class FormationTemplate(SQLModel, table=True):
    """
    Predefined formation templates (4-4-2, 3-5-2, etc.)
    These are static templates that define position layouts
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str  # e.g., "4-4-2", "3-5-2", "4-3-3"
    description: str  # e.g., "Balanced formation with wingers"
    
    # JSON field storing position data
    # Example: {"GK": {"x": 50, "y": 10}, "CB1": {"x": 30, "y": 25}, ...}
    positions: Dict[str, Any] = Field(sa_column=Column(JSON))
    
    # Tactical metadata
    attacking_mentality: int = Field(default=5, ge=1, le=10)  # 1=very defensive, 10=very attacking
    width: int = Field(default=5, ge=1, le=10)  # 1=narrow, 10=wide
    
    is_active: bool = Field(default=True)  # Allow disabling formations


class ClubFormation(SQLModel, table=True):
    """
    A club's current formation setup with assigned players
    This is the "live" formation that gets used in matches
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    club_id: int = Field(foreign_key="club.id")
    formation_template_id: int = Field(foreign_key="formationtemplate.id")
    
    # JSON field storing player assignments
    # Example: {"GK": 1, "CB1": 5, "CB2": 4, "LB": 3, "RB": 2, ...}
    player_assignments: Dict[str, int] = Field(sa_column=Column(JSON))
    
    # Match settings
    captain_id: Optional[int] = Field(default=None, foreign_key="player.id")
    penalty_taker_id: Optional[int] = Field(default=None, foreign_key="player.id")
    free_kick_taker_id: Optional[int] = Field(default=None, foreign_key="player.id")
    
    # Tactical instructions
    mentality: int = Field(default=5, ge=1, le=10)  # Override formation default
    pressing: int = Field(default=5, ge=1, le=10)  # 1=low, 10=high press
    tempo: int = Field(default=5, ge=1, le=10)  # 1=slow, 10=fast
    
    # Metadata
    name: str = Field(default="Main Formation")  # User-defined name
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    club: Optional["Club"] = Relationship(back_populates="formations")
    template: Optional["FormationTemplate"] = Relationship()


# Pydantic schemas for API requests/responses
class FormationTemplateRead(BaseModel):
    """Schema for returning formation template data"""
    id: int
    name: str
    description: str
    positions: Dict[str, Any]
    attacking_mentality: int
    width: int
    
    class Config:
        from_attributes = True


class ClubFormationRead(BaseModel):
    """Schema for returning club formation data with player details"""
    id: int
    formation_template_id: int
    template_name: str
    player_assignments: Dict[str, int]
    mentality: int
    pressing: int
    tempo: int
    name: str
    captain_id: Optional[int]
    penalty_taker_id: Optional[int]
    free_kick_taker_id: Optional[int]
    
    class Config:
        from_attributes = True


class FormationUpdateRequest(BaseModel):
    """Schema for updating a club's formation"""
    formation_template_id: Optional[int] = None
    player_assignments: Optional[Dict[str, int]] = None
    mentality: Optional[int] = None
    pressing: Optional[int] = None
    tempo: Optional[int] = None
    name: Optional[str] = None
    captain_id: Optional[int] = None
    penalty_taker_id: Optional[int] = None
    free_kick_taker_id: Optional[int] = None