from sqlmodel import Session, SQLModel, create_engine
from models import Country, League

# Connect to the database
sqlite_file_name = "tactera.db"
engine = create_engine(f"sqlite:///{sqlite_file_name}")

# Create tables if they don't exist
SQLModel.metadata.create_all(engine)

# Seed data
with Session(engine) as session:
    # Check if Denmark already exists
    from sqlmodel import select

    existing_country = session.exec(
    select(Country).where(Country.name == "Denmark")
    ).first()

    if not existing_country:
        denmark = Country(name="Denmark")
        session.add(denmark)
        session.commit()
        session.refresh(denmark)

        # Add a top league
        top_league = League(
            name="Superliga",
            level=1,
            country_id=denmark.id
        )
        session.add(top_league)
        session.commit()

        print("✅ Seeded Denmark and Superliga")
    else:
        print("ℹ️ Denmark already seeded")
