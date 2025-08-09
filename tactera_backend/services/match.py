from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from tactera_backend.models.club_model import Club
from tactera_backend.models.match_model import MatchResult
from tactera_backend.core.database import get_session
from tactera_backend.models.player_model import Player
import random
from tactera_backend.models.player_stat_model import PlayerStat
from datetime import datetime, timedelta, timezone, date
from typing import List
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

# ============================
# 📌 Reinjury Risk Multiplier
# ============================
# This helper adjusts injury probability during matches based on:
# 1) Active rehab phase (days_remaining <= rehab_start)
# 2) Recently healed window (start_date + days_total within X days of today)
# 3) Low energy scaling (below a threshold, risk rises toward a max multiplier)

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


# ---------------------------------------------
# Helper: add/update a suspension (SYNC session)
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


# ----------------------------------------------------
# Helper: randomly generate bookings for a team squad
# ----------------------------------------------------
def generate_team_bookings(player_ids: list[int]) -> dict:
    """
    Returns per-team bookings for one match:
    {
      "yellow_counts": {player_id: n_yellows_this_match, ...},
      "direct_reds": [player_id, ...]
    }
    """
    if not player_ids:
        return {"yellow_counts": {}, "direct_reds": []}

    num_yellows = random.randint(YELLOW_CARDS_MIN, YELLOW_CARDS_MAX)
    yellow_counts = {}
    for _ in range(num_yellows):
        pid = random.choice(player_ids)
        yellow_counts[pid] = yellow_counts.get(pid, 0) + 1

    direct_reds = []
    if random.random() < DIRECT_RED_PROB:
        direct_reds.append(random.choice(player_ids))

    return {"yellow_counts": yellow_counts, "direct_reds": direct_reds}


# ---------------------------------------------------------
# Helper: assemble a bookings payload for API visibility
# ---------------------------------------------------------
def build_bookings_payload(home_data: dict, away_data: dict) -> dict:
    """
    Converts internal bookings into a simple API payload:
    {
      "home": [{"player_id": 1, "type": "yellow"}, ...],
      "away": [{"player_id": 9, "type": "red"}, {"player_id": 5, "type": "second_yellow_red"}]
    }
    """
    def expand(side_dict):
        events = []
        for pid, cnt in side_dict["yellow_counts"].items():
            for _ in range(min(cnt, 2)):
                events.append({"player_id": pid, "type": "yellow"})
            if cnt >= 2:
                events.append({"player_id": pid, "type": "second_yellow_red"})
        for pid in side_dict["direct_reds"]:
            events.append({"player_id": pid, "type": "red"})
        return events

    return {"home": expand(home_data), "away": expand(away_data)}


# ------------------------------------------------------------
# Helper: decrement suspensions for both clubs after the match
# ------------------------------------------------------------
def decrement_suspensions_after_match_sync(session: Session, home_club_id: int, away_club_id: int) -> None:
    """
    For all players in the two clubs with matches_remaining > 0,
    decrement by 1 (never below 0).
    """
    suspensions = session.exec(
        select(Suspension)
        .join(Player, Player.id == Suspension.player_id)
        .where(Player.club_id.in_([home_club_id, away_club_id]), Suspension.matches_remaining > 0)
    ).all()

    changed = False
    for sus in suspensions:
        sus.matches_remaining = max(0, sus.matches_remaining - 1)
        sus.updated_at = datetime.utcnow()
        session.add(sus)
        changed = True

    if changed:
        session.commit()


@router.post("/simulate")
def simulate_match(home_email: str, away_email: str, session: Session = Depends(get_session)):
    """
    Simulates a match between two clubs.
    Now includes:
    - Injury generation with reinjury risk for rehab-phase players.
    - Pitch quality effects.
    - Stat-based simulation for shots and goals.
    """

    # ---------------------------------------------
    # 🩺 Debug collector: per-player injury risk info
    # This list will collect dictionaries describing:
    # - player identity
    # - base risk before multipliers
    # - total multiplier applied
    # - final risk after multipliers
    # - reason flags (rehab / recently_healed / low_energy)
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

    # 4️⃣ Build stat dictionaries
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

    # 5️⃣ Basic match simulation (shots & goals)
    def simulate_team(attack: float, defense: float):
        value = (attack + random.uniform(0, 10)) - (defense * 0.5)
        shots = max(1, int(value / 2))
        shots_on_target = max(1, shots - random.randint(0, 3))
        goals = random.randint(0, shots_on_target)
        return shots, shots_on_target, goals

    shots_home, on_target_home, goals_home = simulate_team(
        home_stats["passing"] + home_stats["pace"],
        away_stats["defending"]
    )
    shots_away, on_target_away, goals_away = simulate_team(
        away_stats["passing"] + away_stats["pace"],
        home_stats["defending"]
    )

    # 6️⃣ Injury & Reinjury Risk
    all_players = home_players + away_players
    base_risk = 0.05
    tz = timezone(timedelta(hours=2))
    injuries = []

    for player in all_players:
        energy = 100  # placeholder until fatigue system added
        proneness = 1.0  # placeholder until hidden trait added

        # Check for active rehab injury
        rehab_injury = session.exec(
            select(Injury).where(Injury.player_id == player.id, Injury.days_remaining > 0)
        ).first()

        risk = calculate_injury_risk(base_risk, pitch_quality, energy, proneness)
            # Apply full reinjury risk multiplier system
        risk *= calculate_reinjury_risk_multiplier(player, session)
        if TEST_MODE:
            print(f"   🩺 Adjusted Injury Risk: {player.first_name} {player.last_name} (x{risk/base_risk:.2f})")

        if TEST_MODE:
            print(f"[DEBUG] Injury Roll: {player.first_name} {player.last_name} - Final Risk {risk:.2%}")

        # ---------------------------------------------
        # 🩺 Compute total reinjury multiplier & capture reasons
        # We call our helper once to get the final multiplier.
        # Then we also collect human-readable reasons to make it clear
        # why the multiplier was > 1.0
        # ---------------------------------------------
        multiplier = calculate_reinjury_risk_multiplier(player, session)
        final_risk = risk * multiplier

        # Collect reason flags (best-effort; keep it light and non-blocking)
        reason_flags = []
        try:
            # Low energy
            if hasattr(player, "energy") and player.energy < LOW_ENERGY_THRESHOLD:
                reason_flags.append("low_energy")

            # Active rehab check (days_remaining <= rehab_start)
            rehab_row = session.exec(
                select(Injury)
                .where(Injury.player_id == player.id, Injury.days_remaining > 0)
                .order_by(Injury.start_date.desc())
            ).first()
            if rehab_row and rehab_row.days_remaining <= rehab_row.rehab_start:
                reason_flags.append("rehab")

            # Recently healed check (start_date + days_total within window)
            last_row = session.exec(
                select(Injury)
                .where(Injury.player_id == player.id)
                .order_by(Injury.start_date.desc())
            ).first()
            if last_row and last_row.start_date and last_row.days_total:
                healed_date = (last_row.start_date.date()
                            if hasattr(last_row.start_date, "date")
                            else last_row.start_date) + timedelta(days=last_row.days_total)
                if healed_date < datetime.utcnow().date():
                    days_since = (datetime.utcnow().date() - healed_date).days
                    if days_since <= RECENT_HEALED_WINDOW_DAYS:
                        reason_flags.append("recently_healed")
        except Exception:
            # Debug should never break the sim
            pass
        
                # =========================================
            # 🟨🟥 Generate bookings and create suspensions
            # =========================================
            # Ensure you have the lists of Player objects for each club
            home_player_ids = [p.id for p in home_players]
            away_player_ids = [p.id for p in away_players]

            # 1) Generate bookings
            home_book = generate_team_bookings(home_player_ids)
            away_book = generate_team_bookings(away_player_ids)

            # 2) Auto-suspensions
            # Two yellows in SAME match => 1 match ban
            for pid, cnt in home_book["yellow_counts"].items():
                if cnt >= 2:
                    create_or_update_suspension_sync(session, pid, TWO_YELLOWS_SUSPENSION, reason="two_yellows")
            for pid, cnt in away_book["yellow_counts"].items():
                if cnt >= 2:
                    create_or_update_suspension_sync(session, pid, TWO_YELLOWS_SUSPENSION, reason="two_yellows")

            # Direct red => randomized suspension length
            for pid in home_book["direct_reds"]:
                red_len = random.randint(RED_SUSPENSION_MIN, RED_SUSPENSION_MAX)
                create_or_update_suspension_sync(session, pid, red_len, reason="red_card")
            for pid in away_book["direct_reds"]:
                red_len = random.randint(RED_SUSPENSION_MIN, RED_SUSPENSION_MAX)
                create_or_update_suspension_sync(session, pid, red_len, reason="red_card")

            # 3) Build bookings payload and attach to result
            bookings_payload = build_bookings_payload(home_book, away_book)

            # 4) After registering suspensions for this match, decrement all active suspensions by 1
            #    for both clubs so they tick down per match.
            decrement_suspensions_after_match_sync(session, home_club.id, away_club.id)

            # If your function builds a 'result' dict, attach it:
            # result["bookings"] = bookings_payload
            # If you return a dict inline, add `"bookings": bookings_payload` to it.


        # Store one debug entry for this player
        injury_risk_debug.append({
            "player": f"{player.first_name} {player.last_name}",
            "base_risk": round(risk, 6),
            "multiplier": round(multiplier, 6),
            "final_risk": round(final_risk, 6),
            "reasons": reason_flags,
        })

        # From here on, use final_risk for the roll
        risk = final_risk


        # Roll injury
        if random.random() < risk:
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
                    print(f"   🔁 Reinjury Event: {player.first_name} aggravated existing injury!")
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
                "reinjury": reinjury_flag,
                **injury_data
            })

            if TEST_MODE:
                print(f"🩺 Injury Logged: {player.first_name} {player.last_name} - {injury_data['name']} ({injury_data['severity']})")

    session.commit()

    # ✅ Summary calculations
    if TEST_MODE:
        total = len(injuries)
        reinjuries = sum(1 for inj in injuries if inj["reinjury"])
        new_injuries = total - reinjuries
        print(f"\n[DEBUG] Match Injury Summary: Total={total}, New={new_injuries}, Reinjuries={reinjuries}\n")

    # ✅ Split injuries by team
    home_injuries = [inj for inj in injuries if "player_id" in inj and any(p.id == inj["player_id"] for p in home_players)]
    away_injuries = [inj for inj in injuries if "player_id" in inj and any(p.id == inj["player_id"] for p in away_players)]
    
        # 🧠 ENERGY DRAIN AFTER MATCH (default: 90 mins, balanced tactics)
    def drain_energy(players: List[Player], minutes_played: int = 90, intensity_factor: float = 1.0):
        """
        Reduce energy based on minutes played and tactical intensity.
        - Default minutes: 90
        - Default intensity: 1.0 (balanced)
        """
        base_energy_loss = minutes_played * 0.2 * intensity_factor  # Full 90 mins = 18 energy loss
        for player in players:
            player.energy = max(0, player.energy - int(base_energy_loss))
            session.add(player)

    # Apply energy drain to both teams
    drain_energy(home_players)
    drain_energy(away_players)
    session.commit()


    # ✅ Return data
    return {
        "home_goals": goals_home,
        "away_goals": goals_away,
        "shots": {"home": shots_home, "away": shots_away},
        "on_target": {"home": on_target_home, "away": on_target_away},
        "injuries": injuries,
        "reinjury_count": reinjuries,            # Total aggravated injuries
        "new_injury_count": new_injuries,        # Total fresh injuries
        "home_injuries": home_injuries,          # Injuries for home team only
        "away_injuries": away_injuries,           # Injuries for away team only
        "injury_risk_debug": injury_risk_debug

    }



