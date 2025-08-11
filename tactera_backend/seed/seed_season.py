from datetime import datetime, timedelta
from sqlmodel import Session, select
from tactera_backend.core.database import sync_engine
from tactera_backend.models.league_model import League
from tactera_backend.models.season_model import Season, SeasonState

def seed_seasons():
    """
    Seeds a Season and SeasonState for every ACTIVE league in the database.
    Each active league starts at Season 1, beginning on the next Monday (UTC).
    """

    print("📅 Starting optimized season seeding (active leagues only)...")

    with Session(sync_engine) as session:
        # ✅ ONLY get active leagues
        active_leagues = session.exec(
            select(League).where(League.is_active == True)
        ).all()

        if not active_leagues:
            print("⚠️ No active leagues found. Run seed_leagues first.")
            return

        print(f"🎯 Found {len(active_leagues)} active leagues")

        # Get existing seasons to avoid duplicates
        existing_seasons = session.exec(select(Season)).all()
        leagues_with_seasons = {s.league_id for s in existing_seasons}

        # Calculate season start (always a Monday)
        today = datetime.utcnow()
        days_until_monday = (7 - today.weekday()) % 7  # 0 if today is Monday
        season_start = today + timedelta(days=days_until_monday)
        season_start = season_start.replace(hour=0, minute=0, second=0, microsecond=0)
        season_end = season_start + timedelta(days=28)

        # Batch creation for better performance
        new_seasons = []
        new_season_states = []

        for league in active_leagues:
            if league.id in leagues_with_seasons:
                print(f"✅ Season already exists for league: {league.name}")
                continue

            # Create new Season entry
            new_season = Season(
                league_id=league.id,
                season_number=1,
                start_date=season_start,
                end_date=season_end
            )
            new_seasons.append(new_season)

        # ✅ Batch insert all seasons first
        if new_seasons:
            print(f"🚀 Batch creating {len(new_seasons)} seasons...")
            session.add_all(new_seasons)
            session.commit()

            # Refresh seasons to get their IDs
            for season in new_seasons:
                session.refresh(season)

            # ✅ Create SeasonStates for all new seasons
            print(f"📊 Creating season states for {len(new_seasons)} seasons...")
            for season in new_seasons:
                season_state = SeasonState(
                    season_id=season.id,
                    current_round=1,
                    is_completed=False
                )
                new_season_states.append(season_state)

                # Find league name for logging
                league_name = next((l.name for l in active_leagues if l.id == season.league_id), "Unknown")
                print(f"✅ Created Season 1 for {league_name} (Start: {season_start.date()}, End: {season_end.date()})")

            # ✅ Batch insert all season states
            session.add_all(new_season_states)
            session.commit()

            print(f"✅ Created {len(new_seasons)} seasons with states successfully")
        else:
            print("✅ All active leagues already have seasons")

    print("🎉 Season seeding complete!")

if __name__ == "__main__":
    seed_seasons()