from sqlmodel import Session, select
from tactera_backend.models.models import Club, Player
from tactera_backend.core.database import engine
import random

PLAYERS_PER_CLUB = 18

# ⚽ Allowed positions (excluding CF)
POSITIONS = [
    "GK", "LB", "CB", "RB",
    "CDM", "CM", "CAM",
    "LM", "RM",
    "LW", "RW", "ST"
]

PREFERRED_FEET = ["left", "right", "right", "right", "both"]  # Weighted

def generate_random_player(index: int, club_id: int) -> Player:
    position = random.choice(POSITIONS)
    is_goalkeeper = position == "GK"

    height_cm = random.randint(185, 205) if is_goalkeeper else random.randint(165, 205)
    weight_kg = height_cm - 100 + random.randint(-5, 10)

    return Player(
        name=f"Player {index}",
        age=random.randint(16, 34),
        position=position,
        height_cm=height_cm,
        weight_kg=weight_kg,
        preferred_foot=random.choice(PREFERRED_FEET),
        is_goalkeeper=is_goalkeeper,

        #HIDDEN STATS
        ambition=random.randint(30, 100),
        consistency=random.randint(20, 100),
        injury_proneness=random.randint(10, 70),
        potential=random.randint(50, 200),
        
        club_id=club_id
    )

def seed_players():
    with Session(engine) as session:
        clubs = session.exec(select(Club)).all()

        for club in clubs:
            existing_players = session.exec(
                select(Player).where(Player.club_id == club.id)
            ).all()

            if len(existing_players) >= PLAYERS_PER_CLUB:
                print(f"⚠️ Club '{club.name}' already has players. Skipping.")
                continue

            for i in range(PLAYERS_PER_CLUB):
                player = generate_random_player(i + 1, club.id)
                session.add(player)

            print(f"✅ Added {PLAYERS_PER_CLUB} players to '{club.name}'")

        session.commit()

if __name__ == "__main__":
    seed_players()
