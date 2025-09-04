from sqlmodel import SQLModel, Field

class StatLevelRequirement(SQLModel, table=True):
    __tablename__ = "stat_level_requirement"
    level: int = Field(primary_key=True)
    xp_required: int
