from sqlmodel import Session, select
from tactera_backend.models.player_model import Player
from tactera_backend.models.player_stat_model import PlayerStat
from tactera_backend.models.club_model import Club
from tactera_backend.models.league_model import League
from tactera_backend.core.database import sync_engine
import random

# 🧠 Full 10-stat list for field players
STAT_NAMES = [
    "passing", "finishing", "dribbling", "tackling", "first_touch",
    "vision", "positioning", "pace", "stamina", "strength"
]

def seed_player_stats():
    with Session(sync_engine) as session:
        print("🎯 Starting optimized player stats seeding (active leagues only)...")
        
        # ✅ ONLY get players from clubs in active leagues
        players_in_active_leagues = session.exec(
            select(Player)
            .join(Club, Player.club_id == Club.id)
            .join(League, Club.league_id == League.id)
            .where(League.is_active == True)
        ).all()
        
        print(f"📊 Found {len(players_in_active_leagues)} players in active leagues")
        
        if not players_in_active_leagues:
            print("⚠️ No players found in active leagues. Run seed_players first.")
            return
        
        # Get all existing stats to avoid duplicates
        existing_stats = session.exec(select(PlayerStat)).all()
        existing_set = {(stat.player_id, stat.stat_name) for stat in existing_stats}
        print(f"🔍 Found {len(existing_stats)} existing stats")
        
        # Batch create new stats
        new_stats = []
        for player in players_in_active_leagues:
            for stat in STAT_NAMES:
                if (player.id, stat) not in existing_set:
                    xp_amount = random.randint(0, 300)
                    new_stats.append(PlayerStat(
                        player_id=player.id,
                        stat_name=stat,
                        xp=xp_amount
                    ))
        
        print(f"➕ Creating {len(new_stats)} new player stats...")
        
        # ✅ Batch insert all at once
        if new_stats:
            session.add_all(new_stats)
            session.commit()
            print(f"✅ Player stats seeded: {len(new_stats)} new stats created")
        else:
            print("✅ All players in active leagues already have stats")

if __name__ == "__main__":
    seed_player_stats()