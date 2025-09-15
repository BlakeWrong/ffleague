import math
import os
from typing import List, Dict, Any, Tuple
import pandas as pd
from espn_api.football import League
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------- CONFIG ----------------
LEAGUE_ID = int(os.getenv("LEAGUE_ID"))
ESPN_S2 = os.getenv("ESPN_S2")
SWID = os.getenv("SWID")
YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
YEARS = [2018, 2019, 2020]

# ---------- lineup rules (strict starters + dedup) ----------
STARTER_SLOTS = {
    "QB","RB","WR","TE","FLEX","WR/RB","WR/TE","RB/WR","RB/WR/TE",
    "OP","SUPER_FLEX","D/ST","DST","K"
}
EXCLUDE_SLOTS = {"BE","BN","IR","NA","RES","TAXI","UTIL_BENCH"}

def _sum_starters_strict(lineup) -> float:
    total = 0.0
    seen = set()
    for bp in (lineup or []):
        slot = getattr(bp, "slot_position", getattr(bp, "lineupSlot", "UNK")) or "UNK"
        pid  = getattr(bp, "playerId", getattr(bp, "player_id", None))
        pts  = getattr(bp, "points", None)

        slot_norm = slot.replace("D/ST", "DST").replace("WR/TE/RB", "RB/WR/TE")
        if slot_norm in EXCLUDE_SLOTS or slot_norm not in STARTER_SLOTS or pts is None:
            continue

        key = (pid, slot_norm)
        if key in seen:
            continue
        seen.add(key)

        try:
            total += float(pts)
        except Exception:
            pass
    return total

# ------------------ HELPERS ------------------

def load_league(year: int) -> League:
    return League(league_id=LEAGUE_ID, year=year, espn_s2=ESPN_S2, swid=SWID, debug=False)

def weeks_for_year(lg: League) -> List[int]:
    reg = getattr(lg.settings, "reg_season_count", None) or 14
    playoff_teams = getattr(lg.settings, "playoff_team_count", None) or 0
    matchup_len = getattr(lg.settings, "playoff_matchup_period_length", 1) or 1
    rounds = math.ceil(math.log2(playoff_teams)) if playoff_teams and playoff_teams > 1 else 0
    total = reg + rounds * matchup_len
    weeks = list(range(1, total + 1))

    actual_weeks = []
    for wk in weeks:
        try:
            if (lg.box_scores(week=wk) or []):
                actual_weeks.append(wk)
        except Exception:
            pass
    if not actual_weeks:
        for wk in range(1, 30):
            try:
                sb = lg.scoreboard(week=wk) or []
                if not sb:
                    break
                actual_weeks.append(wk)
            except Exception:
                break
    return actual_weeks