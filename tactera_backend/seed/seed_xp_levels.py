from tactera_backend.core.database import get_sync_session
from tactera_backend.models.stat_level_requirement_model import StatLevelRequirement
import pandas as pd
import os

def safe_seed_stat_levels():
    session = get_sync_session()
    count = session.query(StatLevelRequirement).count()
    if count > 0:
        print("✅ Stat level requirements already seeded.")
        return

    # Resolve Excel path relative to project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "xp_levels.xlsx")

    df = pd.read_excel(file_path)
    for _, row in df.iterrows():
        level = int(row["Level"])
        xp = int(row["Accumulated xp"])
        session.add(StatLevelRequirement(level=level, xp_required=xp))

    session.commit()
    print("✅ Stat level requirements seeded successfully.")
