# seed_traininggrounds.py
# This script seeds the TrainingGround table with 10 fixed entries.

from sqlmodel import Session, select
from tactera_backend.core.database import engine
from tactera_backend.models.training_model import TrainingGround

def seed_traininggrounds():
    """
    Seeds the TrainingGround table with 10 predefined entries if empty.
    """
    training_grounds_data = [
        {"id": 1, "tier": 1, "name": "Basic Ground", "xp_boost": 0},
        {"id": 2, "tier": 1, "name": "Standard Ground", "xp_boost": 5},
        {"id": 3, "tier": 1, "name": "Extended Ground", "xp_boost": 10},
        {"id": 4, "tier": 2, "name": "Modern Complex", "xp_boost": 25},
        {"id": 5, "tier": 2, "name": "Advanced Complex", "xp_boost": 30},
        {"id": 6, "tier": 2, "name": "Professional Complex", "xp_boost": 35},
        {"id": 7, "tier": 3, "name": "Standard Facility", "xp_boost": 55},
        {"id": 8, "tier": 3, "name": "Advanced Facility", "xp_boost": 65},
        {"id": 9, "tier": 3, "name": "Elite Facility", "xp_boost": 75},
        {"id": 10, "tier": 4, "name": "World-Class Center", "xp_boost": 100},
    ]

    with Session(engine) as session:
        # Check if the table already has data
        existing = session.exec(select(TrainingGround)).all()
        if existing:
            print("✅ TrainingGround table already seeded.")
            return

        # Insert each training ground
        for tg in training_grounds_data:
            session.add(TrainingGround(**tg))

        session.commit()
        print("✅ TrainingGround table seeded successfully.")

def safe_seed_traininggrounds():
    """
    Safe wrapper to call the seed function without crashing the app.
    """
    try:
        seed_traininggrounds()
    except Exception as e:
        print(f"⚠️ TrainingGround seeding failed: {e}")
