from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import math
from typing import List, Dict, Any, Tuple
import pandas as pd
from espn_api.football import League
from urllib.parse import urlparse, parse_qs

# Add the root directory to the path to import from main.py
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import functions from main.py
try:
    from main import load_league, weeks_for_year, _sum_starters_strict
except ImportError:
    # Fallback definitions if import fails
    def load_league(year: int) -> League:
        league_id = int(os.getenv("LEAGUE_ID"))
        espn_s2 = os.getenv("ESPN_S2")
        swid = os.getenv("SWID")
        return League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid, debug=False)

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

    def _sum_starters_strict(lineup) -> float:
        STARTER_SLOTS = {
            "QB","RB","WR","TE","FLEX","WR/RB","WR/TE","RB/WR","RB/WR/TE",
            "OP","SUPER_FLEX","D/ST","DST","K"
        }
        EXCLUDE_SLOTS = {"BE","BN","IR","NA","RES","TAXI","UTIL_BENCH"}

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


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse the URL and query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)

            # Set CORS headers
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

            # Get year parameter (default to 2024)
            year = int(query_params.get('year', ['2024'])[0])

            # Load league data
            league = load_league(year)
            weeks = weeks_for_year(league)

            # Get basic league info
            league_info = {
                'name': league.settings.name,
                'year': year,
                'size': league.settings.team_count,
                'weeks': weeks,
                'teams': [
                    {
                        'id': team.team_id,
                        'name': team.team_name,
                        'owner': team.owner,
                        'wins': team.wins,
                        'losses': team.losses,
                        'points_for': team.points_for,
                        'points_against': team.points_against
                    }
                    for team in league.teams
                ]
            }

            # Add standings
            standings = sorted(league.teams, key=lambda t: (t.wins, t.points_for), reverse=True)
            league_info['standings'] = [
                {
                    'rank': i + 1,
                    'team_id': team.team_id,
                    'team_name': team.team_name,
                    'owner': team.owner,
                    'wins': team.wins,
                    'losses': team.losses,
                    'points_for': round(team.points_for, 2),
                    'points_against': round(team.points_against, 2)
                }
                for i, team in enumerate(standings)
            ]

            response = json.dumps(league_info, indent=2)
            self.wfile.write(response.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            error_response = json.dumps({'error': str(e)})
            self.wfile.write(error_response.encode())

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()