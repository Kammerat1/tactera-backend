# club.py

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models import Club, Player, TrainingGround
from database import get_session
from club_models import ClubRegister
import random

router = APIRouter()

@router.post("/register")
def register_club(data: ClubRegister, session: Session = Depends(get_session)):
    # Step 1: Check if the manager already has a club
    existing_club = session.exec(
        select(Club).where(Club.manager_email == data.manager_email)
    ).first()
    if existing_club:
        raise HTTPException(status_code=400, detail="Manager already has a club.")

    # Step 2: Create the club
    new_club = Club(
        club_name=data.club_name,
        manager_email=data.manager_email
    )
    session.add(new_club)
    session.commit()
    session.refresh(new_club)  # This gives us new_club.id

    # Step 3: Create 11 players linked to this club
    for i in range(11):
        player = Player(
            name=f"Player {i+1}",
            pace=random.randint(50, 99),
            passing=random.randint(50, 99),
            defending=random.randint(50, 99),
            pace_xp=random.randint(0, 99),        # Optional: random starting XP
            passing_xp=random.randint(0, 99),
            defending_xp=random.randint(0, 99),
            club_id=new_club.id
        )
        session.add(player)

    # Step 4: Create the training ground
    training_ground = TrainingGround(
        club_id=new_club.id,
        level=1,
        tier="Basic",
        xp_boost=3
    )
    session.add(training_ground)

    # Step 5: Final commit (saves players + training ground)
    session.commit()

    return {
        "message": "Club, squad, and training ground created successfully.",
        "club_id": new_club.id
    }

# === TRAINING ENDPOINT ===

@router.post("/{club_id}")
def train_club(club_id: int, session: Session = Depends(get_session)):
    # Step 1: Fetch the club
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")

    # Step 2: Get the club's training ground
    training_ground = session.exec(
        select(TrainingGround).where(TrainingGround.club_id == club_id)
    ).first()
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
        # === Pace ===
        player.pace_xp += xp_gain
        while True:
            required = required_xp(player.pace)
            if player.pace_xp < required:
                break
            player.pace_xp -= required
            player.pace += 1

        # === Passing ===
        player.passing_xp += xp_gain
        while True:
            required = required_xp(player.passing)
            if player.passing_xp < required:
                break
            player.passing_xp -= required
            player.passing += 1

        # === Defending ===
        player.defending_xp += xp_gain
        while True:
            required = required_xp(player.defending)
            if player.defending_xp < required:
                break
            player.defending_xp -= required
            player.defending += 1

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
