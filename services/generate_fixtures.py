from sqlmodel import Session, SQLModel, create_engine, select
from tactera_backend.models.models import Club, League,
from tactera_backend.services.match import Match
from itertools import combinations
import random

# Connect to DB
sqlite_file_name = "tactera.db"
engine = create_engine(f"sqlite:///{sqlite_file_name}")

def generate_double_round_robin(club_ids):
    fixtures = []

    # One home & one away per opponent = 2 fixtures per pair
    for home, away in combinations(club_ids, 2):
        fixtures.append((home, away))
        fixtures.append((away, home))

    # Shuffle for randomness
    random.shuffle(fixtures)

    return fixtures

with Session(engine) as session:
    league = session.exec(select(League).where(League.name == "Superliga")).first()
    if not league:
        print("❌ League not found.")
        exit()

    # Get all clubs in this league
    clubs = session.exec(select(Club).where(Club.league_id == league.id)).all()
    club_ids = [club.id for club in clubs]

    if len(club_ids) != 16:
        print(f"⚠️ Expected 16 clubs, found {len(club_ids)}. Fixture generation cancelled.")
        exit()

    # Clear existing fixtures for this league + season (season = 1 for now)
    existing_matches = session.exec(
    select(Match).where(Match.league_id == league.id, Match.season == 1)
    ).all()

    for match in existing_matches:
        session.delete(match)


    # Generate fixtures
    fixtures = generate_double_round_robin(club_ids)

    # Split fixtures into 30 rounds (1 per week)
    rounds = [[] for _ in range(30)]
    for i, fixture in enumerate(fixtures):
        round_number = i % 30
        rounds[round_number].append(fixture)

    # Save matches to DB
    match_id = 1
    for round_num, matchups in enumerate(rounds, start=1):
        for home_id, away_id in matchups:
            match = Match(
                league_id=league.id,
                home_club_id=home_id,
                away_club_id=away_id,
                round_number=round_num,
                season=1,
                is_played=False
            )
            session.add(match)
            match_id += 1

    session.commit()
    print("✅ Fixtures for Superliga (Season 1) generated.")
