import os
from espn_api.football import League
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_league_stats():
    """Get current league statistics using the ESPN API library"""
    try:
        LEAGUE_ID = int(os.getenv("LEAGUE_ID"))
        ESPN_S2 = os.getenv("ESPN_S2")
        SWID = os.getenv("SWID")

        # Load current year league
        league = League(league_id=LEAGUE_ID, year=2024, espn_s2=ESPN_S2, swid=SWID, debug=False)

        # Get teams
        teams = league.teams

        # Calculate league leader (by wins, then by points for)
        sorted_teams = sorted(teams, key=lambda t: (t.wins, t.points_for), reverse=True)
        league_leader = sorted_teams[0] if sorted_teams else None

        # Calculate average score
        total_points = sum(team.points_for for team in teams)
        average_score = round(total_points / len(teams), 1) if teams else 0.0

        # Get recent matchups (current week - 2 to current week)
        current_week = league.current_week
        recent_matchups = []

        for week in range(max(1, current_week - 2), current_week + 1):
            try:
                box_scores = league.box_scores(week)
                for box_score in box_scores:
                    if box_score.home_score > 0 or box_score.away_score > 0:  # Only completed games
                        recent_matchups.append({
                            "week": week,
                            "home_team": box_score.home_team.team_name,
                            "home_score": round(box_score.home_score, 1),
                            "away_team": box_score.away_team.team_name,
                            "away_score": round(box_score.away_score, 1)
                        })
            except Exception as e:
                print(f"Error getting week {week} matchups: {e}")
                continue

        # Take last 6 matchups
        recent_matchups = recent_matchups[-6:]

        return {
            "total_teams": len(teams),
            "current_week": current_week,
            "league_leader": {
                "team_name": league_leader.team_name if league_leader else "Unknown",
                "record": f"{league_leader.wins}-{league_leader.losses}" if league_leader else "0-0"
            },
            "average_score": str(average_score),
            "recent_matchups": recent_matchups
        }

    except Exception as e:
        print(f"Error getting league stats: {e}")
        raise e