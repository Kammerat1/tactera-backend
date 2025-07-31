# country_models.py
# Defines the Country model, representing a nation with its leagues.

from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class Country(SQLModel, table=True):
    """Represents a nation which can contain multiple leagues."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    # Relationship: One country can have multiple leagues
    leagues: List["League"] = Relationship(back_populates="country")
