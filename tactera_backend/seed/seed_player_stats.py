from sqlmodel import Session, select
from tactera_backend.models.player_model import Player
from tactera_backend.models.player_stat_model import PlayerStat
from tactera_backend.core.database import sync_engine
import random

# 🧠 Full 10-stat list for field players
STAT_NAMES = [
    "passing", "finishing", "dribbling", "tackling", "first_touch",
    "vision", "positioning", "pace", "stamina", "strength"
]

def seed_player_stats():
    with Session(sync_engine) as session:
        print("🎯 Starting optimized player stats seeding...")
        
        # Get all players
        players = session.exec(select(Player)).all()
        print(f"📊 Found {len(players)} players")
        
        # Get all existing stats to avoid duplicates
        existing_stats = session.exec(select(PlayerStat)).all()
        existing_set = {(stat.player_id, stat.stat_name) for stat in existing_stats}
        print(f"🔍 Found {len(existing_stats)} existing stats")
        
        # Batch create new stats
        new_stats = []
        for player in players:
            for stat in STAT_NAMES:
                if (player.id, stat) not in existing_set:
                    xp_amount = random.randint(0, 300)
                    new_stats.append(PlayerStat(
                        player_id=player.id,
                        stat_name=stat,
                        xp=xp_amount
                    ))
        
        print(f"➕ Creating {len(new_stats)} new player stats...")
        
        # Batch insert all at once
        if new_stats:
            session.add_all(new_stats)
            session.commit()
        
        print(f"✅ Player stats seeded: {len(new_stats)} new stats created")

if __name__ == "__main__":
    seed_player_stats()