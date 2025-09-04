from sqlmodel import Session, select
from app.core.database import sync_engine
from app.models.club_model import Club
from app.models.league_model import League
from app.models.stadium_model import Stadium, StadiumPart
from app.core.stadium_config import LEVEL_TO_PITCH, LEVEL_TO_CAPACITY

# Define the 5 default parts
PART_TYPES = ["stand_home", "stand_away", "stand_north", "stand_south", "pitch"]

def seed_stadiums():
    print("🏟 Starting optimized stadium seeding (active leagues only)...")
    
    with Session(sync_engine) as session:
        # ✅ ONLY get clubs from active leagues
        clubs_in_active_leagues = session.exec(
            select(Club)
            .join(League, Club.league_id == League.id)
            .where(League.is_active == True)
        ).all()

        print(f"🎯 Found {len(clubs_in_active_leagues)} clubs in active leagues")

        # Get existing stadiums to avoid duplicates
        existing_stadiums = session.exec(select(Stadium)).all()
        clubs_with_stadiums = {s.club_id for s in existing_stadiums}

        # Batch creation for better performance
        new_stadiums = []
        new_stadium_parts = []

        for club in clubs_in_active_leagues:
            if club.id in clubs_with_stadiums:
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
            new_stadiums.append(stadium)

        # ✅ Batch insert all stadiums first
        if new_stadiums:
            print(f"🚀 Batch creating {len(new_stadiums)} stadiums...")
            session.add_all(new_stadiums)
            session.commit()

            # Refresh stadiums to get their IDs
            for stadium in new_stadiums:
                session.refresh(stadium)

            # ✅ Create stadium parts for all new stadiums
            print(f"🏗️ Creating stadium parts for {len(new_stadiums)} stadiums...")
            for stadium in new_stadiums:
                for part_type in PART_TYPES:
                    level = 1 if part_type == "pitch" else 1  # All start at level 1
                    part = StadiumPart(
                        stadium_id=stadium.id,
                        type=part_type,
                        level=level,
                        durability=100
                    )
                    new_stadium_parts.append(part)

            # ✅ Batch insert all stadium parts
            session.add_all(new_stadium_parts)
            session.commit()

            print(f"✅ Created {len(new_stadiums)} stadiums with {len(new_stadium_parts)} parts successfully")
        else:
            print("✅ All clubs in active leagues already have stadiums")

        print("✅ Stadium seeding complete!")

if __name__ == "__main__":
    seed_stadiums()