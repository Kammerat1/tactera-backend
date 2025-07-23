from sqlmodel import Session, select
from models import Player
from player_stat import PlayerStat
from database import engine
import random

# 🧠 List of stats each player should have
STAT_NAMES = ["pace", "passing", "defending"]

def seed_player_stats():
    with Session(engine) as session:
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
