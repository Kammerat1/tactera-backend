# club.py

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models import Club, Player, TrainingGround, TrainingHistory, TrainingHistoryStat
from player_stat import PlayerStat, get_stat_level
from database import get_session
from club_models import ClubRegister
from datetime import datetime, date
import random
from training import calculate_training_xp, split_xp_among_stats, DRILLS
from pydantic import BaseModel

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

    print("Training club:", club_id)

    players = session.query(Player).filter_by(club_id=club_id).all()
    print("Found players:", len(players))

    # Step 1: Fetch the club
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")

    # Step 2: Get the club's training ground using its direct reference
    training_ground = session.get(TrainingGround, club.trainingground_id)
    if not training_ground:
        raise HTTPException(status_code=404, detail="Training ground not found.")
    
    # ✅ Training cooldown check - WORKING - DEACTIVATED.
    # if club.last_training_date == date.today():
    #    raise HTTPException(status_code=400, detail="Training already completed today. Try again tomorrow.")

    # Validate the chosen drill
    selected_drill = next((d for d in DRILLS if d["name"].lower() == data.drill_name.lower()), None)

    if not selected_drill:
        raise HTTPException(status_code=400, detail=f"Invalid drill: {data.drill_name}")

    affected_stats = selected_drill["affected_stats"]


    # Step 3: Get the squad
    players = session.exec(
        select(Player).where(Player.club_id == club_id)
    ).all()
    if not players:
        raise HTTPException(status_code=400, detail="Squad is empty.")

    # Step 4: Apply training
    xp_gain = training_ground.xp_boost
    updated_players = []
    
    for player in players:
        # Get all PlayerStat rows for this player
        player_stats = session.exec(
            select(PlayerStat).where(PlayerStat.player_id == player.id)
        ).all()

                # === Step 1: Calculate total XP for this player ===
        total_xp = calculate_training_xp(
            potential=player.potential,
            ambition=player.ambition,
            consistency=player.consistency,
            training_ground_boost=training_ground.xp_boost
        )

        # === Step 2: Split XP among affected stats ===
        stat_xp_map = split_xp_among_stats(total_xp, affected_stats)

        # === Step 3: Apply split XP to each affected stat ===
        delta_map = {}
        for stat_name, xp_gain in stat_xp_map.items():
            stat = next((s for s in player_stats if s.stat_name == stat_name), None)

            if not stat:
                stat = PlayerStat(
                    player_id=player.id,
                    stat_name=stat_name,
                    value=1,
                    xp=0
                )
                session.add(stat)
                session.commit()
                session.refresh(stat)
                player_stats.append(stat)

            stat.xp += int(xp_gain)
            delta_map[stat_name] = int(xp_gain)
            stat.value = get_stat_level(stat.xp, session)
            session.add(stat)


        # 📦 After all stats have been updated, prepare return data
        stat_summary = {}
        for stat in player_stats:
            stat_summary[stat.stat_name] = {
                "value": stat.value,
                "xp": stat.xp,
                "delta_xp": delta_map.get(stat.stat_name, 0)
            }
        updated_players.append({
            "player_id": player.id,
            "name": player.name,
            "total_xp_earned": int(total_xp),
            "stats": stat_summary
            })

    # ✅ Update last training date on success
    club.last_training_date = date.today()
    session.add(club)

    # 1️⃣ Create main history record
    history = TrainingHistory(
        club_id=club.id,
        drill_name=selected_drill["name"],
        total_xp=sum([p["total_xp_earned"] for p in updated_players])
    )
    session.add(history)
    session.commit()  # Commit so history gets an ID

    # 2️⃣ Add detailed per-player stat logs
    for player_data in updated_players:
        player_id = player_data["player_id"]
        for stat_name, stat_info in player_data["stats"].items():
            stat_history = TrainingHistoryStat(
                history_id=history.id,
                player_id=player_id,
                stat_name=stat_name,
                xp_gained=stat_info["delta_xp"],
                new_value=stat_info["value"]
            )
            session.add(stat_history)



        

    # Step 5: Save changes and return
    session.commit()

    # NEEDS UPDATE
    return {
        "total_xp_earned": xp_gain,
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
    page: int = 1,            # ✅ Optional page number (default 1)
    limit: int = 600          # ✅ Default limit stays 600
):
    """
    Returns paginated training history for a club.
    - Default: last 600 sessions (page=1, limit=600)
    - Supports pagination: ?page=2&limit=50
    """
    # 1️⃣ Validate club
    club = session.get(Club, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found.")

    # 1.1 Count total training sessions for this club
    total_count = session.exec(
        select(TrainingHistory).where(TrainingHistory.club_id == club_id)
    ).all()

    total_count = len(total_count)


    # 2️⃣ Calculate offset for pagination
    offset = (page - 1) * limit

    # 3️⃣ Fetch paginated sessions
    history_records = session.exec(
        select(TrainingHistory)
        .where(TrainingHistory.club_id == club_id)
        .order_by(TrainingHistory.date.desc())
        .offset(offset)        # ✅ Skip previous pages
        .limit(limit)          # ✅ Fetch only this page
    ).all()

    result = []
    for history in history_records:
        stat_entries = session.exec(
            select(TrainingHistoryStat).where(TrainingHistoryStat.history_id == history.id)
        ).all()

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
            "date": history.date,
            "drill_name": history.drill_name,
            "total_xp": history.total_xp,
            "player_stats": player_stats
        })

    return {
        "club_id": club_id,
        "page": page,
        "limit": limit,
        "total_count": total_count,
        "history": result
    }

