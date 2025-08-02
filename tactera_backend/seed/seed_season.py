# seed_season.py
# Seeds initial seasons for all leagues in the database.

from datetime import datetime, timedelta
from sqlmodel import Session, select
from tactera_backend.core.database import sync_engine
from tactera_backend.models.league_model import League
from tactera_backend.models.season_model import Season, SeasonState

def seed_seasons():
    """
    Seeds a Season and SeasonState for every league in the database.
    Each league starts at Season 1, beginning on the next Monday (UTC).
    """

    print("Seeding seasons...")

    # Open database session
    with Session(sync_engine) as session:
        # Fetch all leagues from DB
        leagues = session.exec(select(League)).all()

        if not leagues:
            print("⚠️ No leagues found. Run seed_leagues.py first.")
            return

        for league in leagues:
            # Check if this league already has a season
            existing_season = session.exec(
                select(Season).where(Season.league_id == league.id)
            ).first()

            if existing_season:
                print(f"✅ Season already exists for league: {league.name}")
                continue

            # Calculate season start (always a Monday)
            today = datetime.utcnow()
            days_until_monday = (7 - today.weekday()) % 7  # 0 if today is Monday
            season_start = today + timedelta(days=days_until_monday)
            season_start = season_start.replace(hour=0, minute=0, second=0, microsecond=0)
            season_end = season_start + timedelta(days=28)

            # Create new Season entry
            new_season = Season(
                league_id=league.id,
                season_number=1,
                start_date=season_start,
                end_date=season_end
            )
            session.add(new_season)
            session.commit()
            session.refresh(new_season)

            # Create SeasonState linked to this Season
            season_state = SeasonState(
                season_id=new_season.id,
                current_round=1,
                last_round_advanced=None
            )
            session.add(season_state)
            session.commit()

            print(f"✅ Created Season 1 for {league.name} (Start: {season_start.date()}, End: {season_end.date()})")

    print("🎉 Season seeding complete!")