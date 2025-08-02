from sqlmodel import Session, select, SQLModel
from tactera_backend.models.player_model import Player
from tactera_backend.models.player_stat_model import PlayerStat
from tactera_backend.core.database import sync_engine
import random

# 🧠 List of stats each player should have
# 🧠 Full 10-stat list for field players
STAT_NAMES = [
    "passing",
    "finishing",
    "dribbling",
    "tackling",
    "first_touch",
    "vision",
    "positioning",
    "pace",
    "stamina",
    "strength"
]


def seed_player_stats():
    with Session(sync_engine) as session:
        players = session.exec(select(Player)).all()

        for player in players:
            for stat in STAT_NAMES:
                # Check if this stat already exists for the player
                exists = session.exec(
                    select(PlayerStat).where(
                        (PlayerStat.player_id == player.id) &
                        (PlayerStat.stat_name == stat)
                    )
                ).first()

                if exists:
                    continue  # Don't add duplicates

                # Create new stat entry with random XP
                xp_amount = random.randint(0, 300)
                player_stat = PlayerStat(
                    player_id=player.id,
                    stat_name=stat,
                    xp=xp_amount
                )
                session.add(player_stat)

        session.commit()
        print(f"✅ Player stats seeded for {len(players)} players.")

if __name__ == "__main__":
    seed_player_stats()
