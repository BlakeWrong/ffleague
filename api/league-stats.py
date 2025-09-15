from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Mock data for testing frontend
        data = {
            "total_teams": 12,
            "current_week": 3,
            "league_leader": {
                "team_name": "The Gronk Squad",
                "record": "3-0"
            },
            "average_score": "118.5",
            "recent_matchups": [
                {
                    "week": 3,
                    "home_team": "The Gronk Squad",
                    "home_score": 142.3,
                    "away_team": "Fantasy Footballers",
                    "away_score": 98.7
                },
                {
                    "week": 3,
                    "home_team": "Touchdown Titans",
                    "home_score": 125.1,
                    "away_team": "Gridiron Glory",
                    "away_score": 108.4
                },
                {
                    "week": 3,
                    "home_team": "End Zone Elite",
                    "home_score": 89.6,
                    "away_team": "Pigskin Pirates",
                    "away_score": 134.8
                }
            ]
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        self.wfile.write(json.dumps(data).encode('utf-8'))
        return