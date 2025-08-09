from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from tactera_backend.models.club_model import Club
from tactera_backend.models.match_model import MatchResult
from tactera_backend.core.database import get_session
from tactera_backend.models.player_model import Player
import random
from tactera_backend.models.player_stat_model import PlayerStat
from datetime import datetime, timedelta, timezone, date
from typing import List, Set
from tactera_backend.models.suspension_model import Suspension

# --- Injury imports ---
from tactera_backend.core.injury_generator import calculate_injury_risk, generate_injury
from tactera_backend.core.injury_config import REINJURY_MULTIPLIER
from tactera_backend.models.stadium_model import Stadium
from tactera_backend.models.injury_model import Injury
from tactera_backend.core.config import TEST_MODE

# ✅ Define router BEFORE using it
router = APIRouter()

# ============================
# 📌 Reinjury Risk Multiplier
# ============================
# This helper adjusts injury probability during matches based on:
# - Whether the player is in rehab
# - Whether the player is recently healed
# - Whether the player has low energy

from tactera_backend.models.injury_model import Injury
from tactera_backend.core.injury_config import (
    REHAB_INJURY_MULTIPLIER,
    RECENT_HEALED_WINDOW_DAYS,
    RECENT_HEALED_MULTIPLIER,
    LOW_ENERGY_THRESHOLD,
    LOW_ENERGY_MAX_MULTIPLIER
)

def calculate_reinjury_risk_multiplier(player, session) -> float:
    """
    Calculate a risk multiplier for a player's injury chance in a match.

    Rules:
    - If the player has an active injury and is in rehab, apply REHAB_INJURY_MULTIPLIER.
    - If the player's most recent injury healed within RECENT_HEALED_WINDOW_DAYS,
      apply RECENT_HEALED_MULTIPLIER.
    - If the player's energy is below LOW_ENERGY_THRESHOLD, scale risk up smoothly
      until LOW_ENERGY_MAX_MULTIPLIER at 0 energy.

    Args:
        player: Player object with at least .id and .energy.
        session: SQLModel session for DB access.

    Returns:
        float: Multiplier to apply to base injury probability.
    """
    multiplier = 1.0

    # Get today's date for healed window calculations
    today = datetime.utcnow().date()

    # 1) ACTIVE REHAB CHECK
    #    We consider an "active injury" as days_remaining > 0.
    #    Rehab phase starts when days_remaining <= rehab_start.
    active_injury = session.exec(
        select(Injury)
        .where(Injury.player_id == player.id, Injury.days_remaining > 0)
        .order_by(Injury.start_date.desc())
    ).first()

    if active_injury:
        # Player is still injured — check if they are in the rehab segment
        try:
            if active_injury.days_remaining <= active_injury.rehab_start:
                multiplier *= REHAB_INJURY_MULTIPLIER
        except Exception:
            # Be defensive if fields are missing/None; fail closed (no rehab bump)
            pass

    # 2) RECENTLY HEALED CHECK
    #    If there is no active injury, find the most recent injury and
    #    compute healed_date = start_date + days_total. If healed_date is
    #    within RECENT_HEALED_WINDOW_DAYS days before today, apply multiplier.
    if not active_injury:
        last_injury = session.exec(
            select(Injury)
            .where(Injury.player_id == player.id)
            .order_by(Injury.start_date.desc())
        ).first()

        if last_injury and last_injury.start_date and last_injury.days_total:
            try:
                healed_date = (last_injury.start_date.date()
                               if hasattr(last_injury.start_date, "date")
                               else last_injury.start_date) + timedelta(days=last_injury.days_total)
                if healed_date < today:
                    days_since_healed = (today - healed_date).days
                    if days_since_healed <= RECENT_HEALED_WINDOW_DAYS:
                        multiplier *= RECENT_HEALED_MULTIPLIER
            except Exception:
                # If anything odd with date math, skip "recently healed" bump safely
                pass

    # 3) LOW ENERGY SCALING
    #    Below LOW_ENERGY_THRESHOLD, scale from 1.0 (at threshold) to
    #    LOW_ENERGY_MAX_MULTIPLIER (at 0 energy).
    try:
        if player.energy < LOW_ENERGY_THRESHOLD:
            safe_energy = max(0, int(player.energy))
            energy_ratio = safe_energy / float(LOW_ENERGY_THRESHOLD)
            low_energy_factor = 1.0 + (LOW_ENERGY_MAX_MULTIPLIER - 1.0) * (1.0 - energy_ratio)
            multiplier *= low_energy_factor
    except Exception:
        # If energy is missing/bad, don't apply the low energy factor
        pass

    return multiplier

# =========================================
# 🟨🟥 Booking & Suspension Configuration
# =========================================
YELLOW_CARDS_MIN = 0
YELLOW_CARDS_MAX = 4
DIRECT_RED_PROB = 0.10        # 10% chance a team gets a direct red
RED_SUSPENSION_MIN = 1
RED_SUSPENSION_MAX = 3
TWO_YELLOWS_SUSPENSION = 1    # two yellows in SAME match => 1 match ban

# =========================================
# 🕐 NEW: Minute-based event tracking
# =========================================
# Events happen throughout the match (0-90 minutes)
# Players sent off after minute X cannot contribute to events after minute X

def simulate_minute_based_events(home_players: List[Player], away_players: List[Player]) -> dict:
    """
    Simulates minute-by-minute events during a match.
    Returns:
    - Goals for each team
    - Bookings with minute stamps
    - Players sent off (and when)
    - Active players remaining at match end
    """
    # Track which players are still on the pitch
    home_active: Set[int] = {p.id for p in home_players}
    away_active: Set[int] = {p.id for p in away_players}
    
    # Track bookings throughout the match
    home_yellows = {}  # player_id -> count
    away_yellows = {}  # player_id -> count
    
    # Store events with minute stamps
    bookings_with_minutes = []
    send_offs = []  # [{player_id, minute, reason}]
    
    # Simulate goals (simplified - just random for now)
    home_goals = random.randint(0, 4)
    away_goals = random.randint(0, 4)
    
    # Simulate bookings throughout 90 minutes
    for minute in range(1, 91):
        # Random chance of booking each minute (very low)
        if random.random() < 0.02:  # 2% chance per minute
            # Pick a random team
            if random.choice([True, False]) and home_active:
                # Home team booking
                player_id = random.choice(list(home_active))
                
                # Chance of direct red vs yellow
                if random.random() < 0.15:  # 15% chance of direct red
                    bookings_with_minutes.append({
                        "player_id": player_id,
                        "minute": minute,
                        "type": "red"
                    })
                    send_offs.append({
                        "player_id": player_id,
                        "minute": minute,
                        "reason": "direct_red"
                    })
                    home_active.discard(player_id)  # Remove from active players
                    if TEST_MODE:
                        print(f"   🟥 MINUTE {minute}: Player {player_id} (HOME) sent off for direct red!")
                        
                else:  # Yellow card
                    home_yellows[player_id] = home_yellows.get(player_id, 0) + 1
                    bookings_with_minutes.append({
                        "player_id": player_id,
                        "minute": minute,
                        "type": "yellow"
                    })
                    
                    # Check for second yellow = red
                    if home_yellows[player_id] >= 2:
                        bookings_with_minutes.append({
                            "player_id": player_id,
                            "minute": minute,
                            "type": "second_yellow_red"
                        })
                        send_offs.append({
                            "player_id": player_id,
                            "minute": minute,
                            "reason": "second_yellow"
                        })
                        home_active.discard(player_id)  # Remove from active players
                        if TEST_MODE:
                            print(f"   🟥 MINUTE {minute}: Player {player_id} (HOME) sent off for second yellow!")
                            
            elif away_active:
                # Away team booking (same logic)
                player_id = random.choice(list(away_active))
                
                if random.random() < 0.15:  # Direct red
                    bookings_with_minutes.append({
                        "player_id": player_id,
                        "minute": minute,
                        "type": "red"
                    })
                    send_offs.append({
                        "player_id": player_id,
                        "minute": minute,
                        "reason": "direct_red"
                    })
                    away_active.discard(player_id)
                    if TEST_MODE:
                        print(f"   🟥 MINUTE {minute}: Player {player_id} (AWAY) sent off for direct red!")
                        
                else:  # Yellow card
                    away_yellows[player_id] = away_yellows.get(player_id, 0) + 1
                    bookings_with_minutes.append({
                        "player_id": player_id,
                        "minute": minute,
                        "type": "yellow"
                    })
                    
                    # Check for second yellow = red
                    if away_yellows[player_id] >= 2:
                        bookings_with_minutes.append({
                            "player_id": player_id,
                            "minute": minute,
                            "type": "second_yellow_red"
                        })
                        send_offs.append({
                            "player_id": player_id,
                            "minute": minute,
                            "reason": "second_yellow"
                        })
                        away_active.discard(player_id)
                        if TEST_MODE:
                            print(f"   🟥 MINUTE {minute}: Player {player_id} (AWAY) sent off for second yellow!")
    
    return {
        "home_goals": home_goals,
        "away_goals": away_goals,
        "bookings_with_minutes": bookings_with_minutes,
        "send_offs": send_offs,
        "final_active_players": {
            "home": list(home_active),
            "away": list(away_active)
        }
    }

# ---------------------------------------------
# Helper: create suspension AFTER match ends
# ---------------------------------------------
def create_or_update_suspension_sync(session: Session, player_id: int, matches: int, reason: str):
    """
    Creates or updates a player's suspension.
    If a Suspension exists, ADD to matches_remaining. Otherwise create a new one.
    """
    existing = session.exec(select(Suspension).where(Suspension.player_id == player_id)).first()
    if existing:
        existing.matches_remaining = max(0, existing.matches_remaining) + max(0, matches)
        existing.reason = reason
        existing.updated_at = datetime.utcnow()
        session.add(existing)
    else:
        sus = Suspension(
            player_id=player_id,
            reason=reason,
            matches_remaining=max(0, matches)
        )
        session.add(sus)
    session.commit()

# ------------------------------------------------------------
# Helper: decrement suspensions for both clubs after the match
# ------------------------------------------------------------
def decrement_suspensions_after_match_sync(session: Session, home_club_id: int, away_club_id: int, newly_suspended_players: Set[int]) -> None:
    """
    For all players in the two clubs with matches_remaining > 0,
    decrement by 1 (never below 0).
    
    NEW: Skip players who got suspended in THIS match (newly_suspended_players)
    so their suspension countdown doesn't start until the NEXT match.
    """
    suspensions = session.exec(
        select(Suspension)
        .join(Player, Player.id == Suspension.player_id)
        .where(Player.club_id.in_([home_club_id, away_club_id]), Suspension.matches_remaining > 0)
    ).all()

    changed = False
    for sus in suspensions:
        # Skip players who got suspended in this same match
        if sus.player_id in newly_suspended_players:
            if TEST_MODE:
                print(f"   ⏭️  Skipping suspension decrement for player {sus.player_id} (suspended this match)")
            continue
            
        sus.matches_remaining = max(0, sus.matches_remaining - 1)
        sus.updated_at = datetime.utcnow()
        session.add(sus)
        changed = True
        
        if TEST_MODE:
            print(f"   ⏬ Player {sus.player_id} suspension decremented to {sus.matches_remaining} matches")

    if changed:
        session.commit()

@router.post("/simulate")
def simulate_match(home_email: str, away_email: str, session: Session = Depends(get_session)):
    """
    Simulates a match between two clubs.
    NEW: Implements proper send-off timing and suspension logic.
    """
    # ---------------------------------------------
    # 🩺 Debug collector: per-player injury risk info
    # ---------------------------------------------
    injury_risk_debug = []

    # 1️⃣ Fetch clubs
    home_club = session.exec(select(Club).where(Club.manager_email == home_email)).first()
    away_club = session.exec(select(Club).where(Club.manager_email == away_email)).first()
    if not home_club or not away_club:
        raise HTTPException(status_code=404, detail="One or both clubs not found.")

    # 2️⃣ Fetch home stadium for pitch quality
    stadium = session.exec(select(Stadium).where(Stadium.club_id == home_club.id)).first()
    if not stadium:
        raise HTTPException(status_code=404, detail="Home stadium not found.")
    pitch_quality = stadium.pitch_quality

    # 3️⃣ Fetch players (including rehab-phase players)
    home_players = session.exec(select(Player).where(Player.club_id == home_club.id)).all()
    away_players = session.exec(select(Player).where(Player.club_id == away_club.id)).all()
    if not home_players or not away_players:
        raise HTTPException(status_code=400, detail="One or both clubs have no players.")

    # 4️⃣ Build stat dictionaries for goal simulation
    expected_stats = ["pace", "passing", "defending", "stamina", "vision", "finishing"]

    def get_average_stat(stat: str, players: list) -> float:
        if not players:
            return 0
        player_ids = [p.id for p in players]
        stat_records = session.exec(
            select(PlayerStat).where(
                PlayerStat.player_id.in_(player_ids),
                PlayerStat.stat_name == stat
            )
        ).all()
        if not stat_records:
            return 0
        return sum(s.value for s in stat_records) / len(stat_records)

    home_stats = {stat: get_average_stat(stat, home_players) for stat in expected_stats}
    away_stats = {stat: get_average_stat(stat, away_players) for stat in expected_stats}

    # =========================================
    # 🕐 NEW: Minute-based event simulation
    # =========================================
    if TEST_MODE:
        print(f"\n🏁 Starting match simulation: {home_club.name} vs {away_club.name}")
        print(f"   Initial squad sizes: Home={len(home_players)}, Away={len(away_players)}")

    match_events = simulate_minute_based_events(home_players, away_players)
    
    goals_home = match_events["home_goals"]
    goals_away = match_events["away_goals"]
    bookings_payload = match_events["bookings_with_minutes"]
    send_offs = match_events["send_offs"]
    
    if TEST_MODE:
        print(f"   Final score: {goals_home}-{goals_away}")
        print(f"   Total bookings: {len(bookings_payload)}")
        print(f"   Players sent off: {len(send_offs)}")

    # =========================================
    # 🟥 NEW: Create suspensions AFTER match
    # =========================================
    newly_suspended_players = set()
    
    # Process send-offs and create suspensions
    for send_off in send_offs:
        player_id = send_off["player_id"]
        reason = send_off["reason"]
        
        if reason == "second_yellow":
            suspension_length = TWO_YELLOWS_SUSPENSION
            create_or_update_suspension_sync(session, player_id, suspension_length, "two_yellows")
            newly_suspended_players.add(player_id)
            if TEST_MODE:
                print(f"   📋 Created {suspension_length}-match suspension for player {player_id} (two yellows)")
                
        elif reason == "direct_red":
            suspension_length = random.randint(RED_SUSPENSION_MIN, RED_SUSPENSION_MAX)
            create_or_update_suspension_sync(session, player_id, suspension_length, "red_card")
            newly_suspended_players.add(player_id)
            if TEST_MODE:
                print(f"   📋 Created {suspension_length}-match suspension for player {player_id} (red card)")

    # =========================================
    # 📉 Decrement existing suspensions (but skip this match's new ones)
    # =========================================
    if TEST_MODE and newly_suspended_players:
        print(f"   🔄 Decrementing existing suspensions (skipping {len(newly_suspended_players)} new ones)")
    
    decrement_suspensions_after_match_sync(session, home_club.id, away_club.id, newly_suspended_players)

    # 6️⃣ Injury & Reinjury Risk Logic (only for players who weren't sent off)
    all_players = home_players + away_players
    active_at_end = set(match_events["final_active_players"]["home"] + match_events["final_active_players"]["away"])
    
    base_risk = 0.05
    tz = timezone(timedelta(hours=2))
    injuries = []

    for player in all_players:
        # Skip injury calculation for players who were sent off
        if player.id not in active_at_end:
            if TEST_MODE:
                print(f"   🚫 Skipping injury risk for sent-off player: {player.first_name} {player.last_name}")
            continue
            
        energy = 100  # placeholder until fatigue system added
        proneness = 1.0  # placeholder until hidden trait added

        # Check for active rehab injury
        rehab_injury = session.exec(
            select(Injury).where(Injury.player_id == player.id, Injury.days_remaining > 0)
        ).first()

        risk = calculate_injury_risk(base_risk, pitch_quality, energy, proneness)
        
        # Apply full reinjury risk multiplier system
        multiplier = calculate_reinjury_risk_multiplier(player, session)
        final_risk = risk * multiplier
        
        if TEST_MODE:
            print(f"   🩺 Injury risk: {player.first_name} {player.last_name} - {final_risk:.2%} (base: {risk:.2%}, multiplier: {multiplier:.2f})")

        # Collect reason flags for debug
        reason_flags = []
        try:
            if hasattr(player, "energy") and player.energy < LOW_ENERGY_THRESHOLD:
                reason_flags.append("low_energy")
            if rehab_injury and rehab_injury.days_remaining <= rehab_injury.rehab_start:
                reason_flags.append("rehab")
            # Add recently healed check here if needed
        except Exception:
            pass

        # Store debug entry
        injury_risk_debug.append({
            "player": f"{player.first_name} {player.last_name}",
            "base_risk": round(risk, 6),
            "multiplier": round(multiplier, 6),
            "final_risk": round(final_risk, 6),
            "reasons": reason_flags,
        })

        # Roll for injury
        if random.random() < final_risk:
            injury_data = generate_injury()

            if rehab_injury and rehab_injury.days_remaining <= rehab_injury.rehab_start:
                # 🔁 Reinjury: overwrite current injury
                rehab_injury.name = injury_data["name"]
                rehab_injury.type = injury_data["type"]
                rehab_injury.severity = injury_data["severity"]
                rehab_injury.start_date = datetime.now(tz)
                rehab_injury.days_total = injury_data["days_total"]
                rehab_injury.rehab_start = injury_data["rehab_start"]
                rehab_injury.rehab_xp_multiplier = injury_data["rehab_xp_multiplier"]
                rehab_injury.fit_for_matches = False
                rehab_injury.days_remaining = injury_data["days_total"]

                if TEST_MODE:
                    print(f"   🔁 Reinjury: {player.first_name} aggravated existing injury!")
                reinjury_flag = True
            else:
                # Fresh injury
                new_injury = Injury(
                    player_id=player.id,
                    name=injury_data["name"],
                    type=injury_data["type"],
                    severity=injury_data["severity"],
                    start_date=datetime.now(tz),
                    days_total=injury_data["days_total"],
                    rehab_start=injury_data["rehab_start"],
                    rehab_xp_multiplier=injury_data["rehab_xp_multiplier"],
                    fit_for_matches=False,
                    days_remaining=injury_data["days_total"]
                )
                session.add(new_injury)
                reinjury_flag = False

            injuries.append({
                "player": f"{player.first_name} {player.last_name}",
                "player_id": player.id,
                "reinjury": reinjury_flag,
                **injury_data
            })

            if TEST_MODE:
                print(f"   🩺 New injury: {player.first_name} {player.last_name} - {injury_data['name']} ({injury_data['severity']})")

    session.commit()

    # 🧠 Energy drain after match
    def drain_energy(players: List[Player], minutes_played: int = 90, intensity_factor: float = 1.0):
        """Reduce energy based on minutes played and tactical intensity."""
        base_energy_loss = minutes_played * 0.2 * intensity_factor
        for player in players:
            player.energy = max(0, player.energy - int(base_energy_loss))
            session.add(player)

    # Apply energy drain to both teams
    drain_energy(home_players)
    drain_energy(away_players)
    session.commit()

    # ✅ Calculate summaries
    reinjuries = sum(1 for inj in injuries if inj["reinjury"])
    new_injuries = len(injuries) - reinjuries
    home_injuries = [inj for inj in injuries if any(p.id == inj["player_id"] for p in home_players)]
    away_injuries = [inj for inj in injuries if any(p.id == inj["player_id"] for p in away_players)]
    
    if TEST_MODE:
        print(f"\n📊 Match Summary:")
        print(f"   Score: {goals_home}-{goals_away}")
        print(f"   Injuries: {len(injuries)} total ({new_injuries} new, {reinjuries} reinjuries)")
        print(f"   Send-offs: {len(send_offs)}")
        print(f"   New suspensions: {len(newly_suspended_players)}")
        print("🏁 Match simulation complete!\n")

    return {
        "home_goals": goals_home,
        "away_goals": goals_away,
        "bookings": bookings_payload,  # Now includes minute stamps
        "send_offs": send_offs,  # NEW: List of players sent off with minutes
        "injuries": injuries,
        "reinjury_count": reinjuries,
        "new_injury_count": new_injuries,
        "home_injuries": home_injuries,
        "away_injuries": away_injuries,
        "injury_risk_debug": injury_risk_debug
    }