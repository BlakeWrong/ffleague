from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Add the parent directory to the path so we can import our helpers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api_helpers import get_league_stats
from espn_api.football import League

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Fantasy Football League API",
    description="Advanced ESPN Fantasy Football analytics and data API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
LEAGUE_ID = int(os.getenv("LEAGUE_ID", 0))
ESPN_S2 = os.getenv("ESPN_S2")
SWID = os.getenv("SWID")

@app.get("/")
async def root():
    return {
        "message": "Fantasy Football League API",
        "version": "1.0.0",
        "endpoints": [
            "/league/stats",
            "/league/stats/{year}",
            "/teams",
            "/teams/{year}",
            "/matchups/{week}",
            "/matchups/{year}/{week}"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "league_id": LEAGUE_ID}

@app.get("/league/stats")
async def get_current_league_stats():
    """Get current season league statistics"""
    try:
        data = get_league_stats()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch league stats: {str(e)}")

@app.get("/league/stats/{year}")
async def get_league_stats_by_year(year: int):
    """Get league statistics for a specific year"""
    try:
        if not (2015 <= year <= 2024):
            raise HTTPException(status_code=400, detail="Year must be between 2015 and 2024")

        league = League(league_id=LEAGUE_ID, year=year, espn_s2=ESPN_S2, swid=SWID, debug=False)
        teams = league.teams

        # Calculate league leader for that year
        sorted_teams = sorted(teams, key=lambda t: (t.wins, t.points_for), reverse=True)
        league_leader = sorted_teams[0] if sorted_teams else None

        # Calculate average score
        total_points = sum(team.points_for for team in teams)
        average_score = round(total_points / len(teams), 1) if teams else 0.0

        return {
            "year": year,
            "total_teams": len(teams),
            "league_leader": {
                "team_name": league_leader.team_name if league_leader else "Unknown",
                "record": f"{league_leader.wins}-{league_leader.losses}" if league_leader else "0-0",
                "points_for": league_leader.points_for if league_leader else 0
            },
            "average_score": str(average_score)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch {year} league stats: {str(e)}")

@app.get("/teams")
async def get_current_teams():
    """Get all teams for current season"""
    try:
        league = League(league_id=LEAGUE_ID, year=2024, espn_s2=ESPN_S2, swid=SWID, debug=False)
        teams = league.teams

        team_data = []
        for team in teams:
            team_data.append({
                "team_id": team.team_id,
                "team_name": team.team_name,
                "owner": team.owner,
                "wins": team.wins,
                "losses": team.losses,
                "points_for": team.points_for,
                "points_against": team.points_against,
                "standing": team.standing
            })

        return {"teams": team_data, "total": len(team_data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch teams: {str(e)}")

@app.get("/teams/{year}")
async def get_teams_by_year(year: int):
    """Get all teams for a specific year"""
    try:
        if not (2015 <= year <= 2024):
            raise HTTPException(status_code=400, detail="Year must be between 2015 and 2024")

        league = League(league_id=LEAGUE_ID, year=year, espn_s2=ESPN_S2, swid=SWID, debug=False)
        teams = league.teams

        team_data = []
        for team in teams:
            team_data.append({
                "team_id": team.team_id,
                "team_name": team.team_name,
                "owner": team.owner,
                "wins": team.wins,
                "losses": team.losses,
                "points_for": team.points_for,
                "points_against": team.points_against,
                "standing": team.standing
            })

        return {"year": year, "teams": team_data, "total": len(team_data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch {year} teams: {str(e)}")

@app.get("/matchups/{week}")
async def get_current_matchups(week: int):
    """Get matchups for a specific week in current season"""
    try:
        if not (1 <= week <= 18):
            raise HTTPException(status_code=400, detail="Week must be between 1 and 18")

        league = League(league_id=LEAGUE_ID, year=2024, espn_s2=ESPN_S2, swid=SWID, debug=False)
        box_scores = league.box_scores(week)

        matchups = []
        for box_score in box_scores:
            matchups.append({
                "week": week,
                "home_team": {
                    "name": box_score.home_team.team_name,
                    "score": round(box_score.home_score, 1)
                },
                "away_team": {
                    "name": box_score.away_team.team_name,
                    "score": round(box_score.away_score, 1)
                }
            })

        return {"week": week, "year": 2024, "matchups": matchups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch week {week} matchups: {str(e)}")

@app.get("/matchups/{year}/{week}")
async def get_matchups_by_year_week(year: int, week: int):
    """Get matchups for a specific week and year"""
    try:
        if not (2015 <= year <= 2024):
            raise HTTPException(status_code=400, detail="Year must be between 2015 and 2024")
        if not (1 <= week <= 18):
            raise HTTPException(status_code=400, detail="Week must be between 1 and 18")

        league = League(league_id=LEAGUE_ID, year=year, espn_s2=ESPN_S2, swid=SWID, debug=False)
        box_scores = league.box_scores(week)

        matchups = []
        for box_score in box_scores:
            matchups.append({
                "week": week,
                "home_team": {
                    "name": box_score.home_team.team_name,
                    "score": round(box_score.home_score, 1)
                },
                "away_team": {
                    "name": box_score.away_team.team_name,
                    "score": round(box_score.away_score, 1)
                }
            })

        return {"week": week, "year": year, "matchups": matchups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch {year} week {week} matchups: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import os
    # Use PORT+1 for Python API to avoid conflict with Next.js
    heroku_port = int(os.environ.get("PORT", 3000))
    python_port = heroku_port + 1 if heroku_port != 8001 else 8001
    uvicorn.run("app:app", host="0.0.0.0", port=python_port)