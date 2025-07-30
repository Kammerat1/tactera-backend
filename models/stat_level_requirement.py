from sqlmodel import SQLModel, Field

class StatLevelRequirement(SQLModel, table=True):
    __tablename__ = "stat_level_requirement"

    id: int | None = Field(default=None, primary_key=True)
    stat_name: str
    level: int
    xp_required: int
