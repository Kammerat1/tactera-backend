# seed_xp_levels.py
# Seeds XP level requirements into StatLevelRequirement model.

from sqlmodel import Session
from tactera_backend.core.database import engine
from tactera_backend.models.stat_level_requirement_model import StatLevelRequirement

def seed_xp_levels():
    """
    Seeds XP requirements for each stat level using StatLevelRequirement.
    Level 1 starts at 0 XP, levels 2–10 increase by 50 XP each,
    and levels beyond 10 increase gradually.
    """

    print("Seeding XP level requirements...")

    xp_levels = []
    base_xp = 0

    # Levels 1–10: +50 XP per level
    for level in range(1, 11):
        xp_levels.append((level, base_xp))
        base_xp += 50

    # Levels 11–50: Incremental scaling
    for level in range(11, 51):
        xp_levels.append((level, base_xp))
        base_xp += 50 + (level - 10)  # Slight scaling increase

    with Session(engine) as session:
        for level, xp in xp_levels:
            existing = session.get(StatLevelRequirement, level)
            if existing:
                continue
            session.add(StatLevelRequirement(level=level, xp_required=xp))

        session.commit()

    print("✅ XP level requirements seeded successfully.")
