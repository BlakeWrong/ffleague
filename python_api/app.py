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
            "/standings",
            "/teams",
            "/teams/{year}",
            "/matchups/{week}",
            "/matchups/{year}/{week}",
            "/bench-heroes/{year}/{week}"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "league_id": LEAGUE_ID}

@app.get("/available-years")
async def get_available_years():
    """Get list of available years for the league"""
    try:
        league = League(league_id=LEAGUE_ID, year=2025, espn_s2=ESPN_S2, swid=SWID, debug=False)

        # Get current year and previous seasons
        available_years = [2025]  # Current year

        # Add previous seasons if available
        if hasattr(league, 'previousSeasons') and league.previousSeasons:
            for season in league.previousSeasons:
                try:
                    year = int(season)
                    available_years.append(year)
                except ValueError:
                    continue

        # Sort years in descending order (newest first)
        available_years.sort(reverse=True)

        # Filter to only include years 2019 and later for bench heroes compatibility
        bench_heroes_years = [year for year in available_years if year >= 2019]

        return {
            "available_years": available_years,  # All years for other endpoints
            "bench_heroes_years": bench_heroes_years,  # Only 2019+ for bench heroes
            "total_years": len(available_years)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch available years: {str(e)}")

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
        average_score = round(total_points / len(teams), 2) if teams else 0.0

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

@app.get("/standings")
async def get_current_standings():
    """Get current season standings sorted by league position"""
    try:
        league = League(league_id=LEAGUE_ID, year=2025, espn_s2=ESPN_S2, swid=SWID, debug=False)
        standings = league.standings()  # Returns teams sorted by current standings

        standings_data = []
        for team in standings:
            standings_data.append({
                "rank": team.standing,
                "team_id": team.team_id,
                "team_name": team.team_name,
                "owner": f"{team.owners[0].get('firstName', '')} {team.owners[0].get('lastName', '')}".strip() if team.owners and team.owners[0].get('firstName') else (team.owners[0]['displayName'] if team.owners else "Unknown"),
                "wins": team.wins,
                "losses": team.losses,
                "ties": team.ties,
                "points_for": round(team.points_for, 2),
                "points_against": round(team.points_against, 2),
                "streak_type": team.streak_type,
                "streak_length": team.streak_length
            })

        return {
            "year": 2025,
            "current_week": league.current_week,
            "standings": standings_data,
            "total_teams": len(standings_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch standings: {str(e)}")

@app.get("/teams")
async def get_current_teams():
    """Get all teams for current season"""
    try:
        league = League(league_id=LEAGUE_ID, year=2025, espn_s2=ESPN_S2, swid=SWID, debug=False)
        teams = league.teams

        team_data = []
        for team in teams:
            team_data.append({
                "team_id": team.team_id,
                "team_name": team.team_name,
                "owner": f"{team.owners[0].get('firstName', '')} {team.owners[0].get('lastName', '')}".strip() if team.owners and team.owners[0].get('firstName') else (team.owners[0]['displayName'] if team.owners else "Unknown"),
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
        if not (2015 <= year <= 2025):
            raise HTTPException(status_code=400, detail="Year must be between 2015 and 2025")

        league = League(league_id=LEAGUE_ID, year=year, espn_s2=ESPN_S2, swid=SWID, debug=False)
        teams = league.teams

        team_data = []
        for team in teams:
            team_data.append({
                "team_id": team.team_id,
                "team_name": team.team_name,
                "owner": f"{team.owners[0].get('firstName', '')} {team.owners[0].get('lastName', '')}".strip() if team.owners and team.owners[0].get('firstName') else (team.owners[0]['displayName'] if team.owners else "Unknown"),
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

        league = League(league_id=LEAGUE_ID, year=2025, espn_s2=ESPN_S2, swid=SWID, debug=False)
        box_scores = league.box_scores(week)

        matchups = []
        for box_score in box_scores:
            matchups.append({
                "week": week,
                "home_team": {
                    "name": box_score.home_team.team_name,
                    "score": round(box_score.home_score, 2)
                },
                "away_team": {
                    "name": box_score.away_team.team_name,
                    "score": round(box_score.away_score, 2)
                }
            })

        return {"week": week, "year": 2025, "matchups": matchups}
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
                    "score": round(box_score.home_score, 2)
                },
                "away_team": {
                    "name": box_score.away_team.team_name,
                    "score": round(box_score.away_score, 2)
                }
            })

        return {"week": week, "year": year, "matchups": matchups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch {year} week {week} matchups: {str(e)}")

@app.get("/bench-heroes/{year}/{week}")
async def get_bench_heroes(year: int, week: int):
    """Get top scoring bench players for a specific week and year"""
    try:
        if not (2019 <= year <= 2025):
            raise HTTPException(status_code=400, detail="Bench heroes data is only available from 2019 onwards due to ESPN API limitations")
        if not (1 <= week <= 18):
            raise HTTPException(status_code=400, detail="Week must be between 1 and 18")

        print(f"Fetching bench heroes for year={year}, week={week}", flush=True)

        league = League(league_id=LEAGUE_ID, year=year, espn_s2=ESPN_S2, swid=SWID, debug=False)
        print(f"League created successfully for {year}", flush=True)

        box_scores = league.box_scores(week)
        print(f"Retrieved {len(box_scores) if box_scores else 0} box scores for week {week}", flush=True)

        bench_players = []

        for i, box_score in enumerate(box_scores):
            try:
                print(f"Processing box score {i+1}/{len(box_scores)}", flush=True)

                # Process home team lineup
                if hasattr(box_score, 'home_lineup') and box_score.home_lineup:
                    for j, player in enumerate(box_score.home_lineup):
                        try:
                            # Check if player is on bench (slot_position contains "BE" or "Bench")
                            if player.slot_position and ("BE" in player.slot_position.upper() or "BENCH" in player.slot_position.upper()):
                                bench_players.append({
                                    "player_name": player.name,
                                    "points": round(player.points, 2),
                                    "team_name": box_score.home_team.team_name,
                                    "team_id": box_score.home_team.team_id,
                                    "owner": f"{box_score.home_team.owners[0].get('firstName', '')} {box_score.home_team.owners[0].get('lastName', '')}".strip() if box_score.home_team.owners and box_score.home_team.owners[0].get('firstName') else (box_score.home_team.owners[0]['displayName'] if box_score.home_team.owners else "Unknown"),
                                    "position": player.position,
                                    "pro_team": player.proTeam if hasattr(player, 'proTeam') else "N/A"
                                })
                        except Exception as player_error:
                            print(f"Error processing home player {j}: {str(player_error)}", flush=True)
                            continue

                # Process away team lineup
                if hasattr(box_score, 'away_lineup') and box_score.away_lineup:
                    for j, player in enumerate(box_score.away_lineup):
                        try:
                            # Check if player is on bench
                            if player.slot_position and ("BE" in player.slot_position.upper() or "BENCH" in player.slot_position.upper()):
                                bench_players.append({
                                    "player_name": player.name,
                                    "points": round(player.points, 2),
                                    "team_name": box_score.away_team.team_name,
                                    "team_id": box_score.away_team.team_id,
                                    "owner": f"{box_score.away_team.owners[0].get('firstName', '')} {box_score.away_team.owners[0].get('lastName', '')}".strip() if box_score.away_team.owners and box_score.away_team.owners[0].get('firstName') else (box_score.away_team.owners[0]['displayName'] if box_score.away_team.owners else "Unknown"),
                                    "position": player.position,
                                    "pro_team": player.proTeam if hasattr(player, 'proTeam') else "N/A"
                                })
                        except Exception as player_error:
                            print(f"Error processing away player {j}: {str(player_error)}", flush=True)
                            continue

            except Exception as box_score_error:
                print(f"Error processing box score {i}: {str(box_score_error)}", flush=True)
                continue

        # Sort by points (highest first) and take top 5
        bench_players.sort(key=lambda x: x['points'], reverse=True)
        top_bench_players = bench_players[:5]

        print(f"Successfully processed {len(bench_players)} total bench players", flush=True)

        return {
            "year": year,
            "week": week,
            "bench_heroes": top_bench_players,
            "total_bench_players": len(bench_players)
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in bench heroes endpoint: {error_details}", flush=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch bench heroes for {year} week {week}: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import os

    # In development, use port 8001. In production (Heroku), use PORT+1
    if os.environ.get("NODE_ENV") == "production" or os.environ.get("PORT"):
        # Production: use PORT+1 to avoid conflict with Next.js
        heroku_port = int(os.environ.get("PORT", 3000))
        python_port = heroku_port + 1
    else:
        # Development: use fixed port 8001
        python_port = 8001

    uvicorn.run("app:app", host="0.0.0.0", port=python_port)