from sqlmodel import Session, SQLModel, create_engine, select
from models import Club, League

# Connect to the database
sqlite_file_name = "tactera.db"
engine = create_engine(f"sqlite:///{sqlite_file_name}")

# Club names to seed
club_names = [
    "FC Placeholder 1", "FC Placeholder 2", "AC Sampletown",
    "Real Test FC", "Demo United", "Beta Ballers",
    "Mockington Rovers", "Scripted FC", "Debug City",
    "Codeford FC", "Devton Wanderers", "Queryville SC",
    "Stacktrace Athletic", "Versionvale FC", "Import Albion", "Lollern FC"
]

with Session(engine) as session:
    # Get Superliga
    league = session.exec(
        select(League).where(League.name == "Superliga")
    ).first()

    if not league:
        print("❌ Superliga not found. Run seed_leagues.py first.")
    else:
        for name in club_names:
            existing = session.exec(select(Club).where(Club.club_name == name)).first()
            if existing:
                print(f"⚠️ {name} already exists. Skipping.")
                continue

            club = Club(
                club_name=name,
                manager_email="bot@tactera.ai",  # placeholder manager
                league_id=league.id
            )
            session.add(club)
        
        session.commit()
        print(f"✅ Seeded {len(club_names)} placeholder clubs into Superliga")
