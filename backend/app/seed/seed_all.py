# seed_all.py
# Orchestrates all seed scripts to populate the database in the correct order, with detailed logging.

from app.seed.seed_leagues import seed_leagues
from app.seed.seed_clubs import seed_clubs
from app.seed.seed_stadiums import seed_stadiums
from app.seed.seed_traininggrounds import seed_traininggrounds
from app.seed.seed_players import seed_players
from app.seed.seed_player_stats import seed_player_stats
from app.seed.seed_xp_levels import seed_xp_levels
from app.seed.seed_season import seed_seasons
from app.services.generate_fixtures import generate_fixtures_for_league
from app.seed.seed_formations import seed_formation_templates
from sqlmodel import Session, select
from app.core.database import sync_engine
from app.models.league_model import League

def seed_all():
    print("\nStarting full database seeding...\n")

    print("➡️  Step 1: Seeding leagues...")
    seed_leagues()

    print("➡️  Step 2: Seeding training grounds...")
    seed_traininggrounds()  # ✅ Move this up!

    print("➡️  Step 3: Seeding clubs...")
    seed_clubs()

    print("➡️  Step 4: Seeding stadiums...")
    seed_stadiums()

    print("➡️  Step 5: Seeding players...")
    seed_players()

    print("➡️  Step 6: Seeding player stats...")
    seed_player_stats()

    print("➡️  Step 7: Seeding XP levels...")
    seed_xp_levels()

    print("➡️  Step 8: Seeding formation templates...")
    seed_formation_templates()

    print("➡️  Step 9: Seeding seasons...")
    seed_seasons()

    print("➡️  Step 10: Generating fixtures for active leagues only...")

    with Session(sync_engine) as session:
        # ✅ ONLY generate fixtures for active leagues
        active_leagues = session.exec(select(League).where(League.is_active == True)).all()
        print(f"🎯 Found {len(active_leagues)} active leagues for fixture generation")
        
        for league in active_leagues:
            print(f"   ⚽ Generating fixtures for {league.name}...")
            generate_fixtures_for_league(session, league.id)

    print(f"\nDatabase seeding complete. {len(active_leagues)} active leagues initialized with fixtures.\n")


if __name__ == "__main__":
    seed_all()
