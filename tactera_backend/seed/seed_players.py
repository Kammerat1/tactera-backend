from sqlmodel import Session, select
from tactera_backend.models.club_model import Club
from tactera_backend.models.player_model import Player
from tactera_backend.models.league_model import League
from tactera_backend.core.database import sync_engine
import random
from tactera_backend.models.contract_model import PlayerContract
from datetime import date, timedelta

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
    """Generate a single random player for a club."""
    position = random.choice(POSITIONS)
    is_goalkeeper = position == "GK"

    height_cm = random.randint(185, 205) if is_goalkeeper else random.randint(165, 205)
    weight_kg = height_cm - 100 + random.randint(-5, 10)

    return Player(
        first_name=f"Player {index}",
        last_name=f"Club{club_id}",
        age=random.randint(16, 34),
        position=position,
        height_cm=height_cm,
        weight_kg=weight_kg,
        preferred_foot=random.choice(PREFERRED_FEET),
        is_goalkeeper=is_goalkeeper,

        # Hidden stats
        ambition=random.randint(30, 100),
        consistency=random.randint(20, 100),
        injury_proneness=random.randint(10, 70),
        potential=random.randint(50, 200),
        
        club_id=club_id
    )

def generate_random_contract(player_id: int, club_id: int) -> PlayerContract:
    """Generate a random contract for a player."""
    return PlayerContract(
        player_id=player_id,
        club_id=club_id,
        daily_wage=random.randint(100, 300),
        contract_expires=date.today() + timedelta(days=random.randint(28, 84)),
        auto_generated=False
    )

def seed_players():
    print("⚽ Starting optimized player seeding (active leagues only)...")
    
    with Session(sync_engine) as session:
        # ✅ ONLY get clubs from active leagues
        clubs_in_active_leagues = session.exec(
            select(Club)
            .join(League, Club.league_id == League.id)
            .where(League.is_active == True)
        ).all()

        print(f"🎯 Found {len(clubs_in_active_leagues)} clubs in active leagues")

        # Get existing players to avoid duplicates
        existing_players = session.exec(select(Player)).all()
        clubs_with_players = {p.club_id for p in existing_players}

        # Batch creation for better performance
        new_players = []
        new_contracts = []

        for club in clubs_in_active_leagues:
            if club.id in clubs_with_players:
                print(f"⚠️ Club '{club.name}' already has players. Skipping.")
                continue

            print(f"⚽ Creating {PLAYERS_PER_CLUB} players for '{club.name}'")
            
            # Create players for this club
            club_players = []
            for i in range(PLAYERS_PER_CLUB):
                player = generate_random_player(i + 1, club.id)
                new_players.append(player)
                club_players.append(player)

        # ✅ Batch insert all players first
        if new_players:
            print(f"🚀 Batch creating {len(new_players)} players...")
            session.add_all(new_players)
            session.commit()

            # Refresh all players to get their IDs
            for player in new_players:
                session.refresh(player)

            # ✅ Create contracts for all new players
            print(f"📋 Creating contracts for {len(new_players)} players...")
            for player in new_players:
                contract = generate_random_contract(player.id, player.club_id)
                new_contracts.append(contract)

            # ✅ Batch insert all contracts
            session.add_all(new_contracts)
            session.commit()

            print(f"✅ Created {len(new_players)} players with contracts successfully")
        else:
            print("✅ All clubs in active leagues already have players")

        print("✅ Player seeding complete!")

if __name__ == "__main__":
    seed_players()