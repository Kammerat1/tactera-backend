from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date
# Stadium model
class Stadium(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    sponsor_name: Optional[str] = None
    club_id: int = Field(foreign_key="club.id")

# StadiumPart model
class StadiumPart(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    stadium_id: int = Field(foreign_key="stadium.id")
    type: str
    level: int
    durability: int
