from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs

# Add the root directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from main import load_league, weeks_for_year, _sum_starters_strict
except ImportError:
    # Fallback - same as in league.py
    pass


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

            # Get parameters
            year = int(query_params.get('year', ['2024'])[0])
            week = query_params.get('week', [None])[0]

            # Load league data
            league = load_league(year)
            weeks = weeks_for_year(league)

            if week:
                week = int(week)
                if week not in weeks:
                    raise ValueError(f"Week {week} not available for year {year}")

                # Get matchups for specific week
                box_scores = league.box_scores(week=week)
                matchups = []

                for matchup in box_scores:
                    home_team = matchup.home_team
                    away_team = matchup.away_team

                    matchup_data = {
                        'week': week,
                        'home_team': {
                            'id': home_team.team_id,
                            'name': home_team.team_name,
                            'owner': home_team.owner,
                            'score': round(matchup.home_score, 2)
                        },
                        'away_team': {
                            'id': away_team.team_id,
                            'name': away_team.team_name,
                            'owner': away_team.owner,
                            'score': round(matchup.away_score, 2)
                        }
                    }
                    matchups.append(matchup_data)

                response = json.dumps({
                    'year': year,
                    'week': week,
                    'matchups': matchups
                }, indent=2)

            else:
                # Get all matchups for the season
                all_matchups = []

                for wk in weeks:
                    try:
                        box_scores = league.box_scores(week=wk)
                        week_matchups = []

                        for matchup in box_scores:
                            home_team = matchup.home_team
                            away_team = matchup.away_team

                            matchup_data = {
                                'week': wk,
                                'home_team': {
                                    'id': home_team.team_id,
                                    'name': home_team.team_name,
                                    'owner': home_team.owner,
                                    'score': round(matchup.home_score, 2)
                                },
                                'away_team': {
                                    'id': away_team.team_id,
                                    'name': away_team.team_name,
                                    'owner': away_team.owner,
                                    'score': round(matchup.away_score, 2)
                                }
                            }
                            week_matchups.append(matchup_data)

                        all_matchups.extend(week_matchups)
                    except Exception as e:
                        continue

                response = json.dumps({
                    'year': year,
                    'total_weeks': len(weeks),
                    'matchups': all_matchups
                }, indent=2)

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