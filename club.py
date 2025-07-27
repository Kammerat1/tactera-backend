# club.py

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models import Club, Player, TrainingGround
from player_stat import PlayerStat
from database import get_session
from club_models import ClubRegister
from datetime import datetime
import random
from training import calculate_training_xp


router = APIRouter()

@router.post("/register")
def register_club(data: ClubRegister, session: Session = Depends(get_session)):
    # Step 1: Check if the manager already has a club
    existing_club = session.exec(
        select(Club).where(Club.manager_email == data.manager_email)
    ).first()
    if existing_club:
        raise HTTPException(status_code=400, detail="Manager already has a club.")

    # Step 2: Assign the first training ground from the seeded list
    training_ground = session.get(TrainingGround, 1)
    if not training_ground:
        raise HTTPException(status_code=500, detail="Default training ground not found")


    # Step 3: Now create the club with a link to the training ground
    new_club = Club(
        name=data.club_name,
        manager_email=data.manager_email,
        trainingground_id=training_ground.id
    )
    session.add(new_club)
    session.commit()
    session.refresh(new_club)


    # Step 3: Create 11 players linked to this club
    for i in range(11):
        player = Player(
            name=f"Player {i+1}",
            age=random.randint(18, 34),
            position="CM",  # or random.choice([...])
            height_cm=random.randint(165, 200),
            weight_kg=random.randint(60, 95),
            preferred_foot=random.choice(["left", "right"]),
            is_goalkeeper=(i == 0),  # First player as goalkeeper

            ambition=random.randint(30, 100),
            consistency=random.randint(30, 100),
            injury_proneness=random.randint(10, 60),
            potential=random.randint(60, 95),

            pace=random.randint(50, 99),
            passing=random.randint(50, 99),
            defending=random.randint(50, 99),

            pace_xp=random.randint(0, 99),
            passing_xp=random.randint(0, 99),
            defending_xp=random.randint(0, 99),

            club_id=new_club.id
        )

        session.add(player)

    # Step 5: Final commit (saves players + training ground)
    session.commit()

    return {
        "message": "Club, squad, and training ground created successfully.",
        "club_id": new_club.id
    }

# === TRAINING ENDPOINT ===

@router.post("/{club_id}")
def train_club(club_id: int, session: Session = Depends(get_session)):

    print("Training club:", club_id)

    players = session.query(Player).filter_by(club_id=club_id).all()
    print("Found players:", len(players))

    for player in players:
        print(f" - Player: {player.name} (id: {player.id}, potential: {player.potential})")

        stat = session.query(PlayerStat).filter_by(player_id=player.id).first()
        if stat.stat_name == "pace":
            print(f"   - Found 'pace' stat. Current XP: {stat.xp}")

        else:
            print("   - No PlayerStat found for this player")



    # Step 1: Fetch the club
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")

    # Step 2: Get the club's training ground using its direct reference
    training_ground = session.get(TrainingGround, club.trainingground_id)
    if not training_ground:
        raise HTTPException(status_code=404, detail="Training ground not found.")


    # Step 3: Get the squad
    players = session.exec(
        select(Player).where(Player.club_id == club_id)
    ).all()
    if not players:
        raise HTTPException(status_code=400, detail="Squad is empty.")

    # Step 4: Apply training
    xp_gain = training_ground.xp_boost
    updated_players = []

    def required_xp(stat_value: int) -> int:
        if stat_value <= 10:
            return 100
        return 100 + (stat_value - 10) * 10

    for player in players:

        stat = session.query(PlayerStat).filter_by(player_id=player.id).first()
        if not stat:
            continue  # or optionally create a new PlayerStat row

        # === Pace ===
        # Calculate XP based on potential, ambition, consistency, and training ground
        xp = calculate_training_xp(
            potential=player.potential,
            ambition=player.ambition,
            consistency=player.consistency,
            training_ground_boost=training_ground.xp_boost
        )

        if stat.stat_name == "pace":
            stat.xp += int(xp)
            print(f"   - Added {int(xp)} XP to 'pace'. New XP: {stat.xp}")


        # === Passing ===
        xp = calculate_training_xp(
            potential=player.potential,
            ambition=player.ambition,
            consistency=player.consistency,
            training_ground_boost=training_ground.xp_boost
        )
        if stat.stat_name == "passing":
            stat.xp += int(xp)
            print(f"   - Added {int(xp)} XP to 'passing'. New XP: {stat.xp}")


        # === Defending ===
        xp = calculate_training_xp(
            potential=player.potential,
            ambition=player.ambition,
            consistency=player.consistency,
            training_ground_boost=training_ground.xp_boost
        )
        if stat.stat_name == "defending":
            stat.xp += int(xp)
            print(f"   - Added {int(xp)} XP to 'defending'. New XP: {stat.xp}")

        session.add(player)

        updated_players.append({
            "player_id": player.id,
            "name": player.name,
            "pace": player.pace,
            "pace_xp": player.pace_xp,
            "passing": player.passing,
            "passing_xp": player.passing_xp,
            "defending": player.defending,
            "defending_xp": player.defending_xp
        })
        

    # Step 5: Save changes and return
    session.commit()

    return {
        "xp_gain": xp_gain,
        "players_trained": updated_players
    }
    



    session.commit()
