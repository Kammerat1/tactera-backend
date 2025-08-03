# seed_stadiums.py
# ✅ This script creates one stadium per club and adds 5 default parts to each stadium

from sqlmodel import Session, select
from tactera_backend.core.database import sync_engine
from tactera_backend.models.club_model import Club
from tactera_backend.models.stadium_model import Stadium, StadiumPart
from tactera_backend.core.stadium_config import LEVEL_TO_PITCH, LEVEL_TO_CAPACITY
import random


# Define the 5 default parts
PART_TYPES = ["stand_home", "stand_away", "stand_north", "stand_south", "pitch"]

def seed_stadiums():
    with Session(sync_engine) as session:
        clubs = session.exec(select(Club)).all()

        for club in clubs:
            existing = session.exec(select(Stadium).where(Stadium.club_id == club.id)).first()
            if existing:
                continue

            # Default levels
            pitch_level = 1
            stand_level = 1

            # Create stadium
            stadium = Stadium(
                name=f"{club.name} Arena",
                sponsor_name=None,
                club_id=club.id,
                capacity=LEVEL_TO_CAPACITY[stand_level],
                pitch_quality=LEVEL_TO_PITCH[pitch_level],
                base_ticket_price=20.0
            )
            session.add(stadium)
            session.commit()
            session.refresh(stadium)

            # Create default parts
            for part_type in PART_TYPES:
                level = pitch_level if part_type == "pitch" else stand_level
                part = StadiumPart(
                    stadium_id=stadium.id,
                    type=part_type,
                    level=level,
                    durability=100
                )
                session.add(part)

        session.commit()
        print("✅ Stadiums seeded with levels and derived values.")



if __name__ == "__main__":
    seed_stadiums()
