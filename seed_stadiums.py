# seed_stadiums.py
# ✅ This script creates one stadium per club and adds 5 default parts to each stadium

from sqlmodel import Session, select
from database import engine
from models import Club, Stadium, StadiumPart


# Define the 5 default parts
PART_TYPES = ["stand_home", "stand_away", "stand_north", "stand_south", "pitch"]

def seed_stadiums():
    with Session(engine) as session:
        clubs = session.exec(select(Club)).all()

        for club in clubs:
            # Check if the club already has a stadium
            existing = session.exec(select(Stadium).where(Stadium.club_id == club.id)).first()
            if existing:
                continue

            # Create the stadium
            stadium = Stadium(
                name=f"{club.name} Arena",
                sponsor_name=None,
                club_id=club.id
            )
            session.add(stadium)
            session.commit()
            session.refresh(stadium)

            # Create default parts for the stadium
            for part_type in PART_TYPES:
                part = StadiumPart(
                    stadium_id=stadium.id,
                    type=part_type,
                    level=1,
                    durability=100
                )
                session.add(part)

        session.commit()
        print("✅ Stadiums and parts seeded successfully.")


if __name__ == "__main__":
    seed_stadiums()
