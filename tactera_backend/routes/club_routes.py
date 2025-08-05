# club_routes.py
# Defines API routes for club operations (registration, training, etc.)

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from tactera_backend.core.database import get_session
from tactera_backend.models.club_model import Club
from tactera_backend.models.club_schemas import ClubRegister
from tactera_backend.models.player_model import Player
from tactera_backend.models.training_model import TrainingGround, TrainingHistory, TrainingHistoryStat
from tactera_backend.models.player_stat_model import PlayerStat, get_stat_level
from tactera_backend.services.training import calculate_training_xp, split_xp_among_stats, DRILLS
from datetime import datetime, date
from pydantic import BaseModel
from tactera_backend.core.config import TEST_MODE  # Import TEST_MODE for cooldown logic
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
            first_name=f"Player",
            last_name=f"Test{i+1}",
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

# Allow managers to pick their own drill
class TrainingRequest(BaseModel):
    drill_name: str

# Endpoint to train a club's squad
# Endpoint to train a club's squad
@router.post("/{club_id}")
def train_club(club_id: int, data: TrainingRequest, session: Session = Depends(get_session)):
    """
    Trains all players in a club using the selected drill.
    Applies injury-aware logic:
    - Fully injured players are skipped.
    - Rehab-phase players auto-train at light intensity (reduced XP).
    - Healthy players train normally.
    """
    print("Training club:", club_id)

    # ✅ Fetch the club and validate existence
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")

    # ✅ Get training ground
    training_ground = session.get(TrainingGround, club.trainingground_id)
    if not training_ground:
        raise HTTPException(status_code=404, detail="Training ground not found.")

    from tactera_backend.core.config import TEST_MODE  # ✅ Import locally inside the function

    # ✅ Cooldown check
    if not TEST_MODE:
        if club.last_training_date == date.today():
            raise HTTPException(status_code=403, detail="This club has already trained today.")


    # ✅ Fetch players
    players = session.exec(select(Player).where(Player.club_id == club_id)).all()
    if not players:
        raise HTTPException(status_code=404, detail="No players found for this club.")

    # ✅ Validate chosen drill
    drill = next((d for d in DRILLS if d["name"].lower() == data.drill_name.lower()), None)
    if not drill:
        raise HTTPException(status_code=400, detail="Invalid drill selected.")

    # ✅ Injury-aware training
    from tactera_backend.services.training import apply_training_with_injury_check
    updated_players = []

    for player in players:
        result = apply_training_with_injury_check(player, drill, session)
        updated_players.append(result)
    
        # ✅ Build summary counts based on status_flag
    summary = {
        "normal": sum(1 for p in updated_players if p["status_flag"] == "normal"),
        "rehab": sum(1 for p in updated_players if p["status_flag"] == "rehab-light"),
        "skipped": sum(1 for p in updated_players if p["status_flag"] == "skipped")
    }


    # ✅ Update last training date
    club.last_training_date = date.today()
    session.add(club)
    session.commit()
    
        # ✅ Debug summary logging (TEST_MODE only)
    from tactera_backend.core.config import TEST_MODE
    if TEST_MODE:
        print("\n=== TRAINING SESSION SUMMARY ===")
        print(f"Club: {club.name} (ID: {club.id}) | Drill: {drill['name']}")
        for result in updated_players:
            print(f" - {result['player']}: {result['status_flag']} | XP: {result['xp_applied']} | {result['notes']}")
        print("=== END SESSION SUMMARY ===\n")


    # ✅ Return training results
    return {
        "message": "Training complete",
        "summary": summary,
        "results": updated_players
    }


# GET TRAINING DRILLS ENDPOINT

@router.get("/training/drills")
def get_training_drills():
    """
    Returns all available training drills and their affected stats.
    """
    return {"available_drills": DRILLS}

# GET TRAINING HISTORY ENDPOINT
@router.get("/{club_id}/training/history")
def get_training_history(
    club_id: int,
    session: Session = Depends(get_session),
    page: int = 1,         # ✅ Page number for pagination
    limit: int = 50        # ✅ Default to 50 (you can adjust during testing)
):
    """
    Returns paginated training history for a club, ordered by newest session first.
    Each record includes drill, date, total XP, and detailed per-player stat updates.
    """

    # 1️⃣ Validate club
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")

    # 2️⃣ Count total sessions for pagination metadata
    total_count = session.exec(
        select(TrainingHistory).where(TrainingHistory.club_id == club_id)
    ).all()
    total_count = len(total_count)

    # 3️⃣ Calculate pagination offset
    offset = (page - 1) * limit

    # 4️⃣ Fetch ordered and paginated sessions
    history_records = session.exec(
        select(TrainingHistory)
        .where(TrainingHistory.club_id == club_id)
        .order_by(TrainingHistory.training_date.desc(), TrainingHistory.id.desc())  # ✅ Fix ordering
        .offset(offset)
        .limit(limit)
    ).all()

    # 5️⃣ Build response
    result = []
    for history in history_records:
        # Fetch all stat updates linked to this session
        stat_entries = session.exec(
            select(TrainingHistoryStat).where(TrainingHistoryStat.training_history_id == history.id)
        ).all()

        # Group stats per player
        player_stats = {}
        for stat in stat_entries:
            if stat.player_id not in player_stats:
                player_stats[stat.player_id] = []
            player_stats[stat.player_id].append({
                "stat_name": stat.stat_name,
                "xp_gained": stat.xp_gained,
                "new_value": stat.new_value
            })

        result.append({
            "training_id": history.id,
            "training_date": history.training_date,
            "drill_name": history.drill_name,
            "total_xp": history.total_xp,
            "players": [
                {
                    "player_id": pid,
                    "stats": stats
                }
                for pid, stats in player_stats.items()
            ]
        })

    return {
        "club_id": club_id,
        "page": page,
        "limit": limit,
        "total_sessions": total_count,
        "history": result
    }

# ===============================
# LATEST TRAINING SESSION ENDPOINT
# ===============================

@router.get("/clubs/{club_id}/training/history/latest")
def get_latest_training_session(
    club_id: int,
    session: Session = Depends(get_session),
):
    """
    Retrieve the LATEST training session for a given club.
    - Returns only the most recent training session.
    - Includes drill name, date, total XP, and per-player stat details (with stat names).
    """

    from tactera_backend.models.training_model import TrainingHistory, TrainingHistoryStat
    from tactera_backend.models.player_model import Player

    # Get the most recent training session for this club
    latest_training = (
        session.query(TrainingHistory)
        .filter(TrainingHistory.club_id == club_id)
        .order_by(TrainingHistory.training_date.desc(), TrainingHistory.id.desc())
        .first()
    )

    if not latest_training:
        return {"message": "No training history found for this club."}

    # Fetch all player XP gains (including stat names)
    stats = (
        session.query(TrainingHistoryStat, Player)
        .join(Player, TrainingHistoryStat.player_id == Player.id)
        .filter(TrainingHistoryStat.training_history_id == latest_training.id)
        .all()
    )

    players_data = []
    for stat_entry, player in stats:
        players_data.append({
            "player_id": player.id,
            f"{player.first_name} {player.last_name}"
            "stat_name": stat_entry.stat_name,  # ✅ Now included
            "xp_gained": stat_entry.xp_gained,
            "new_value": stat_entry.new_value,
        })

    return {
        "id": latest_training.id,
        "training_date": latest_training.training_date,
        "drill_name": latest_training.drill_name,
        "total_xp": latest_training.total_xp,
        "players": players_data,
    }

from tactera_backend.models.player_model import Player, PlayerRead
from tactera_backend.models.injury_model import Injury
import pytz

utc_plus_2 = pytz.timezone("Europe/Copenhagen")

@router.get("/clubs/{club_id}/squad")
def get_club_squad(club_id: int, session: Session = Depends(get_session)):
    """
    Returns the full squad for a given club.
    Each player includes active injury info (if injured).
    """
    # 1️⃣ Fetch the club
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")

    # 2️⃣ Fetch all players in the squad
    players = session.exec(select(Player).where(Player.club_id == club_id)).all()
    if not players:
        return {"club_id": club_id, "squad": []}

    squad_with_injuries = []

    # 3️⃣ Loop players, attach active injury info
    for player in players:
        active_injury = None
        if player.injuries:
            for injury in player.injuries:
                if injury.days_remaining > 0:
                    injury.start_date = injury.start_date.astimezone(utc_plus_2)
                    active_injury = injury
                    print(f"[DEBUG] Active injury for {player.first_name} {player.last_name}: {injury.name}")
                    break
        else:
            print(f"[DEBUG] Player {player.first_name} {player.last_name} has no injury history.")

        # Convert Player -> PlayerRead (with injury)
        player_data = PlayerRead.from_orm(player).copy(update={"active_injury": active_injury})
        squad_with_injuries.append(player_data)

    return {
        "club_id": club_id,
        "club_name": club.name,
        "squad": squad_with_injuries
    }
