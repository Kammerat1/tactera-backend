from sqlmodel import Session, select, func
from tactera_backend.core.database import engine
from tactera_backend.models.club_model import Club
from tactera_backend.models.league_model import League
from tactera_backend.models.training_model import TrainingGround
import random


def seed_clubs():
    print("🏟 Starting club seeding...")

    with Session(engine) as session:
        leagues = session.exec(select(League)).all()

        for league in leagues:
            print(f"⚽ Found league: {league.name} (Country ID: {league.country_id}, Tier: {league.level})")

            # Count existing clubs in this league
            club_count = session.exec(
                select(func.count()).select_from(Club).where(Club.league_id == league.id)
            ).one()

            desired_club_count = 16 if league.level == 1 else 14  # Example: top tier has 16, lower has 14
            print(f"   🏟 {club_count}/{desired_club_count} clubs currently in this league")
            
            if club_count < desired_club_count:
                clubs_needed = desired_club_count - club_count
                print(f"   ➕ Seeding {clubs_needed} bot clubs...")
                
                # ✅ Fetch the lowest-level training ground (tier 1, Basic Ground)
                lowest_trainingground = session.exec(
                    select(TrainingGround).where(TrainingGround.id == 1)
                ).first()


                for i in range(clubs_needed):
                    bot_club = Club(
                        name=f"Bot Club {league.id}-{i+1}",
                        league_id=league.id,
                        manager_email=f"bot_{league.id}_{i+1}@bots.tactera",
                        is_bot=True,
                        trainingground_id=lowest_trainingground.id
                    )
                    session.add(bot_club)

        session.commit()
        print("✅ Club seeding complete!")


if __name__ == "__main__":
    seed_clubs()
