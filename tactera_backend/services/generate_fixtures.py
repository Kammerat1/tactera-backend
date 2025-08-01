# generate_fixtures.py
# Service for generating league fixtures (double round-robin) tied to an active season.

from datetime import datetime, timedelta
from sqlmodel import Session, select
from tactera_backend.models.league_model import League
from tactera_backend.models.club_model import Club
from tactera_backend.models.match_model import Match
from tactera_backend.models.season_model import Season, SeasonState


def generate_fixtures_for_league(session: Session, league_id: int):
    """
    Generates fixtures for the active season of a given league.
    - Double round-robin (home & away)
    - Scheduled on Tue/Thu/Sat/Sun (with AM/PM slots for double rounds)
    """

    # ✅ Fetch league
    league = session.get(League, league_id)
    if not league:
        raise ValueError(f"League {league_id} not found.")

    # ✅ Fetch active season via SeasonState
    season_state = session.exec(
        select(SeasonState)
        .join(Season, Season.id == SeasonState.season_id)
        .where(Season.league_id == league_id)
    ).first()

    if not season_state:
        raise ValueError(f"No active season found for league {league.name}.")

    season = session.get(Season, season_state.season_id)

    # ✅ Fetch clubs in this league
    clubs = session.exec(select(Club).where(Club.league_id == league_id)).all()
    if len(clubs) < 2:
        raise ValueError(f"Not enough clubs in {league.name} to generate fixtures.")

    # ✅ Clear existing fixtures for this league + season (if any)
    existing_fixtures = session.exec(
        select(Match).where(Match.league_id == league.id, Match.season_id == season.id)
    ).all()
    for match in existing_fixtures:
        session.delete(match)
    session.commit()

    # =====================================
    # ROUND-ROBIN FIXTURE GENERATION
    # =====================================
    # Algorithm: "Circle Method" for round-robin scheduling
    club_ids = [club.id for club in clubs]
    if len(club_ids) % 2 != 0:
        club_ids.append(None)  # Add a dummy "bye" if odd number of clubs

    num_rounds = (len(club_ids) - 1) * 2  # Double round-robin
    half = len(club_ids) // 2

    fixtures = []  # Collect fixtures before saving
    round_number = 1

    for cycle in range(2):  # Two cycles (home/away)
        rotated = club_ids[:]
        for r in range(len(club_ids) - 1):  # Each round in this cycle
            round_fixtures = []
            for i in range(half):
                home = rotated[i]
                away = rotated[-i - 1]

                if home is None or away is None:
                    continue  # Skip bye rounds

                # Swap home/away in second cycle
                if cycle == 1:
                    home, away = away, home

                round_fixtures.append((home, away))

            # Rotate clubs (keep the first club fixed)
            rotated = [rotated[0]] + [rotated[-1]] + rotated[1:-1]

            # Append fixtures for this round
            for home_id, away_id in round_fixtures:
                fixtures.append({
                    "league_id": league.id,
                    "season_id": season.id,
                    "round_number": round_number,
                    "home_club_id": home_id,
                    "away_club_id": away_id,
                })
            round_number += 1

    # =====================================
    # ASSIGN MATCH DATES
    # =====================================
    matchdays = ["Tuesday", "Thursday", "Saturday", "Sunday"]
    am_time = (10, 0)   # AM matches: 10:00 UTC
    pm_time = (18, 0)   # PM matches: 18:00 UTC

    current_date = season.start_date
    match_index = 0

    for round_data in fixtures:
        weekday = matchdays[(match_index // 2) % len(matchdays)]  # Rotate through Tue/Thu/Sat/Sun

        # Advance to the correct weekday
        while current_date.strftime("%A") != weekday:
            current_date += timedelta(days=1)

        # Pick AM or PM slot
        if match_index % 2 == 0:
            match_time = current_date.replace(hour=am_time[0], minute=am_time[1])
        else:
            match_time = current_date.replace(hour=pm_time[0], minute=pm_time[1])
            current_date += timedelta(days=1)  # After PM, next day

        # Create match entry
        match = Match(
            league_id=round_data["league_id"],
            season_id=round_data["season_id"],
            round_number=round_data["round_number"],
            home_club_id=round_data["home_club_id"],
            away_club_id=round_data["away_club_id"],
            match_time=match_time
        )
        session.add(match)
        match_index += 1

    session.commit()
    print(f"✅ Fixtures generated for {league.name}, Season {season.season_number} ({len(fixtures)} matches total)")
