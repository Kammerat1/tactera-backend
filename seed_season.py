from sqlmodel import Session, select
from database import engine
from models import SeasonState

# 🚀 Create the new table if not already present
from models import SQLModel
SQLModel.metadata.create_all(engine)

with Session(engine) as session:
    # Check if already seeded
    existing = session.exec(
        select(SeasonState).where(SeasonState.league_id == 1)
    ).first()

    if existing:
        print("🔁 SeasonState already exists.")
    else:
        season = SeasonState(
            league_id=1,
            current_season=1,
            current_round=1,
        )
        session.add(season)
        session.commit()
        print("✅ Seeded initial SeasonState.")
