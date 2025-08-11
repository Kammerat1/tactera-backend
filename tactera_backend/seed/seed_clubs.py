from sqlmodel import Session, select, func
from tactera_backend.core.database import sync_engine
from tactera_backend.models.club_model import Club
from tactera_backend.models.league_model import League
from tactera_backend.models.training_model import TrainingGround
import random


from sqlmodel import Session, select, func
from tactera_backend.core.database import sync_engine
from tactera_backend.models.club_model import Club
from tactera_backend.models.league_model import League
from tactera_backend.models.training_model import TrainingGround
import random
from tactera_backend.models.country_model import Country
from tactera_backend.core.league_config import league_config


def seed_clubs():
    print("🏟 Starting optimized club seeding (active leagues only)...")

    with Session(sync_engine) as session:
        # ✅ ONLY get active leagues
        active_leagues = session.exec(
            select(League).where(League.is_active == True)
        ).all()
        
        print(f"🎯 Found {len(active_leagues)} active leagues")

        # Get the lowest-level training ground (tier 1, Basic Ground)
        lowest_trainingground = session.exec(
            select(TrainingGround).where(TrainingGround.id == 1)
        ).first()

        if not lowest_trainingground:
            print("❌ No training ground found! Run seed_traininggrounds first.")
            return

        # Batch creation for better performance
        new_clubs = []

        for league in active_leagues:
            print(f"⚽ Processing active league: {league.name}")

            # Count existing clubs in this league
            club_count = session.exec(
                select(func.count()).select_from(Club).where(Club.league_id == league.id)
            ).one()

            # Determine target based on league level
            if league.level == 1:
                # Tier 1: Check country system from league config
                from tactera_backend.core.league_config import league_config
                
                # Find the country for this league
                country = session.exec(
                    select(Country).where(Country.id == league.country_id)
                ).first()
                
                if country and country.name in league_config:
                    country_config = league_config[country.name]
                    # Find the tier 1 league config
                    tier1_leagues = [l for l in country_config["leagues"] if l["level"] == 1]
                    if tier1_leagues:
                        desired_club_count = tier1_leagues[0]["teams"]
                    else:
                        desired_club_count = 16  # fallback
                else:
                    desired_club_count = 16  # fallback
            else:
                # Tier 2+: Use 14 or 16 based on system
                desired_club_count = 14  # Most tier 2 leagues use 14

            print(f"   🏟 {club_count}/{desired_club_count} clubs currently in this league")
            
            if club_count < desired_club_count:
                clubs_needed = desired_club_count - club_count
                print(f"   ➕ Creating {clubs_needed} bot clubs...")
                
                # Create clubs for this league
                for i in range(clubs_needed):
                    # Calculate starting money based on league reputation

                    # Find country for this league
                    country = session.exec(
                        select(Country).where(Country.id == league.country_id)
                    ).first()

                    # Set starting money based on league reputation
                    if country and country.name in league_config:
                        country_config = league_config[country.name]
                        reputation = country_config.get("reputation", 70)
                        
                        # Higher reputation leagues = more money
                        if reputation >= 90:
                            starting_money = 200000  # Elite leagues (Germany, Spain, etc.)
                        elif reputation >= 80:
                            starting_money = 150000  # Strong leagues (France, Netherlands)
                        elif reputation >= 70:
                            starting_money = 100000  # Good leagues (Denmark, Portugal)
                        else:
                            starting_money = 75000   # Average leagues (Sweden, Norway)
                    else:
                        starting_money = 100000  # Default fallback

                    bot_club = Club(
                        name=f"Bot Club {league.id}-{i+1}",
                        league_id=league.id,
                        manager_email=f"bot_{league.id}_{i+1}@bots.tactera",
                        is_bot=True,
                        trainingground_id=lowest_trainingground.id,
                        money=starting_money
                    )
                    new_clubs.append(bot_club)

        # ✅ Batch insert all clubs at once
        if new_clubs:
            print(f"🚀 Batch creating {len(new_clubs)} clubs...")
            session.add_all(new_clubs)
            session.commit()
            print(f"✅ Created {len(new_clubs)} clubs successfully")
        else:
            print("✅ All active leagues already have enough clubs")

        print("✅ Club seeding complete!")


if __name__ == "__main__":
    seed_clubs()