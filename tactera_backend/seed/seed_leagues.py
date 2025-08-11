"""
seed_leagues.py
---------------
Seeds nations (countries) and leagues into the database from league_config.py.

✅ Supports "delta seeding":
   - Only inserts missing countries or leagues (won't overwrite existing data).
   - Safe to run multiple times or after adding new nations/leagues.

Usage:
    python seed_leagues.py
"""

from sqlmodel import Session, select
from tactera_backend.core.database import sync_engine
# Import only what's needed for seeding to avoid triggering PlayerStat
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from tactera_backend.models.country_model import Country
from tactera_backend.models.league_model import League


from tactera_backend.core.league_config import league_config


def seed_leagues():
    with Session(sync_engine) as session:
        print("🌍 Starting league seeding...")

        # Loop through countries in league_config
        for country_name, country_data in league_config.items():
            # Check if this country already exists
            existing_country = session.exec(
                select(Country).where(Country.name == country_name)
            ).first()

            if existing_country:
                print(f"✅ Country already exists: {country_name}")
                country = existing_country
            else:
                print(f"➕ Adding new country: {country_name}")
                country = Country(name=country_name)
                session.add(country)
                session.commit()
                session.refresh(country)

            # Loop through leagues in this country
            for league_data in country_data["leagues"]:
                level = league_data["level"]
                # NEW: Get the active status from country config
                is_active = country_data.get("active", True)

                # If league has no divisions (tier 1, single table)
                if "teams" in league_data:
                    _add_league_if_missing(session, league_data["name"], level, country.id, is_active=is_active)

                # If league has multiple divisions (tier 2+)
                if "divisions" in league_data:
                    num_groups = len(league_data["divisions"])
                    for group_num in range(1, num_groups + 1):
                        _add_league_if_missing(
                            session,
                            name=league_data["name"],  # base name (e.g., "Division 2")
                            level=level,
                            country_id=country.id,
                            group=group_num,
                            is_active=is_active
                        )



        print("✅ League seeding complete!")


def _add_league_if_missing(session: Session, name: str, level: int, country_id: int, group: Optional[int] = None, is_active: bool = True):
    """
    Adds a league if it doesn't already exist in the database.
    NEW: Now includes is_active flag for beta control.
    """
    existing_league = session.exec(
        select(League).where(
            League.name == name,
            League.country_id == country_id,
            League.group == group
        )
    ).first()

    if existing_league:
        # Update existing league's active status if it differs
        if existing_league.is_active != is_active:
            existing_league.is_active = is_active
            session.add(existing_league)
            session.commit()
            print(f"   🔄 Updated {name} active status to {is_active}")
        else:
            print(f"   🔁 League already exists: {name}")
        return

    # Create new league with active status
    print(f"   ➕ Adding new league: {name} (level {level}, active: {is_active})")
    league = League(
        name=name, 
        level=level, 
        country_id=country_id, 
        group=group,
        is_active=is_active
    )
    session.add(league)
    session.commit()