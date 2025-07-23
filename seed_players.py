from sqlmodel import Session, select
from models import Club, Player
from database import engine
import random

# 👥 How many players to create per club
PLAYERS_PER_CLUB = 18

# 🧠 Generate a simple placeholder name
def generate_player_name(index):
    return f"Player {index}"

# 🚀 Main logic: Seed players for each club
def seed_players():
    with Session(engine) as session:
        clubs = session.exec(select(Club)).all()

        for club in clubs:
            # Check how many players already exist in the club
            existing_players = session.exec(
                select(Player).where(Player.club_id == club.id)
            ).all()

            if len(existing_players) >= PLAYERS_PER_CLUB:
                print(f"⚠️ Club '{club.name}' already has players. Skipping.")
                continue

            # Add new players
            for i in range(PLAYERS_PER_CLUB):
                player = Player(
                    name=generate_player_name(i + 1),
                    club_id=club.id
                )
                session.add(player)

            print(f"✅ Added {PLAYERS_PER_CLUB} players to '{club.name}'")

        session.commit()

if __name__ == "__main__":
    seed_players()
