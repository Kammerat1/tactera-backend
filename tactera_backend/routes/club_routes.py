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

# Allow managers to pick their own drill
class TrainingRequest(BaseModel):
    drill_name: str

# Endpoint to train a club's squad
@router.post("/{club_id}")
def train_club(club_id: int, data: TrainingRequest, session: Session = Depends(get_session)):
    """
    Trains all players in a club using the selected drill.
    Distributes XP to affected stats and logs training history.
    """
    print("Training club:", club_id)

    # ✅ Fetch the club and validate existence
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")

    # ✅ Get training ground by direct reference
    training_ground = session.get(TrainingGround, club.trainingground_id)
    if not training_ground:
        raise HTTPException(status_code=404, detail="Training ground not found.")

    # ✅ Validate chosen drill
    selected_drill = next((d for d in DRILLS if d["name"].lower() == data.drill_name.lower()), None)
    if not selected_drill:
        raise HTTPException(status_code=400, detail=f"Invalid drill: {data.drill_name}")

    affected_stats = selected_drill["affected_stats"]

    # ✅ Get the squad (single query)
    players = session.exec(select(Player).where(Player.club_id == club_id)).all()
    if not players:
        raise HTTPException(status_code=400, detail="Squad is empty.")

    updated_players = []

    # === Apply training ===
    for player in players:
        # Get all PlayerStat rows for this player
        player_stats = session.exec(
            select(PlayerStat).where(PlayerStat.player_id == player.id)
        ).all()

        # 1️⃣ Calculate total XP for this player
        total_xp = calculate_training_xp(
            potential=player.potential,
            ambition=player.ambition,
            consistency=player.consistency,
            training_ground_boost=training_ground.xp_boost
        )

        # 2️⃣ Split XP among affected stats
        stat_xp_map = split_xp_among_stats(total_xp, affected_stats)

        # 3️⃣ Apply XP to each stat
        delta_map = {}
        for stat_name, xp_gain in stat_xp_map.items():
            stat = next((s for s in player_stats if s.stat_name == stat_name), None)

            # If stat record doesn't exist yet, create it
            if not stat:
                stat = PlayerStat(
                    player_id=player.id,
                    stat_name=stat_name,
                    value=1,
                    xp=0
                )
                session.add(stat)
                session.flush()  # Ensure stat has an ID before updating
                session.refresh(stat)
                player_stats.append(stat)

            stat.xp += int(xp_gain)
            delta_map[stat_name] = int(xp_gain)
            stat.value = get_stat_level(stat.xp, session)
            session.add(stat)

        # Prepare return payload for this player
        stat_summary = {
            stat.stat_name: {
                "value": stat.value,
                "xp": stat.xp,
                "delta_xp": delta_map.get(stat.stat_name, 0)
            }
            for stat in player_stats
        }

        updated_players.append({
            "player_id": player.id,
            "name": player.name,
            "total_xp_earned": int(total_xp),
            "stats": stat_summary
        })

    # ✅ Update last training date
    club.last_training_date = date.today()
    session.add(club)

    # 1️⃣ Log main training history record
    history = TrainingHistory(
        club_id=club.id,
        drill_name=selected_drill["name"],
        total_xp=sum(p["total_xp_earned"] for p in updated_players)
    )
    session.add(history)
    session.flush()  # ✅ Now history.id is available

    # 2️⃣ Log per-player stat updates
    for player_data in updated_players:
        for stat_name, stat_info in player_data["stats"].items():
            session.add(TrainingHistoryStat(
                training_history_id=history.id,
                player_id=player_data["player_id"],
                stat_name=stat_name,
                xp_gained=stat_info["delta_xp"],
                new_value=stat_info["value"]
            ))

    session.commit()

    # ✅ Fixed return payload: total XP is sum of all players' XP
    return {
        "total_xp_earned": sum(p["total_xp_earned"] for p in updated_players),
        "players_trained": updated_players
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
    - Includes drill name, date, total XP, and per-player stat details.
    """

    # Import models inside function to avoid circular imports
    from tactera_backend.models.training_model import TrainingHistory, TrainingHistoryStat
    from tactera_backend.models.player_model import Player
    from tactera_backend.models.player_stat_model import PlayerStat

    # Query: get the most recent training history record for this club
    latest_training = (
        session.query(TrainingHistory)
        .filter(TrainingHistory.club_id == club_id)
        .order_by(TrainingHistory.training_date.desc(), TrainingHistory.id.desc())
        .first()
    )

    # If no training history exists, return a clear message
    if not latest_training:
        return {"message": "No training history found for this club."}

    # Fetch all related stat improvements for this training session
    stats = (
        session.query(TrainingHistoryStat, Player, PlayerStat)
        .join(Player, TrainingHistoryStat.player_id == Player.id)
        .join(PlayerStat, TrainingHistoryStat.stat_id == PlayerStat.id)
        .filter(TrainingHistoryStat.training_history_id == latest_training.id)
        .all()
    )

    # Structure the response
    players_data = []
    for stat_entry, player, stat in stats:
        players_data.append({
            "player_id": player.id,
            "player_name": player.name,
            "stat_name": stat.name,
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

