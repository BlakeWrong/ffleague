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

# Import database API
from db_api import DatabaseAPI


# Initialize database API
db_api = DatabaseAPI()

def use_database() -> bool:
    """Check if database exists and should be used instead of ESPN API"""
    # Check both current directory and parent directory
    current_db = "fantasy_football.db"
    parent_db = os.path.join(os.path.dirname(__file__), "..", "fantasy_football.db")
    return os.path.exists(current_db) or os.path.exists(parent_db)

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
    if use_database():
        db_health = db_api.health_check()
        return {
            "status": "healthy",
            "league_id": LEAGUE_ID,
            "data_source": "database",
            "database_status": db_health
        }
    else:
        return {
            "status": "healthy",
            "league_id": LEAGUE_ID,
            "data_source": "espn_api"
        }


@app.get("/available-years")
async def get_available_years():
    """Get list of available years for the league"""
    try:
        if use_database():
            return db_api.get_available_years()
        else:
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

            # Filter to only include years 2019 and later due to ESPN API limitations
            supported_years = [year for year in available_years if year >= 2019]

            return {
                "available_years": available_years,  # All years for other endpoints
                "supported_years": supported_years,  # Only 2019+ due to ESPN API limitations
                "total_years": len(available_years),
                "current_year": 2025,
                "current_week": league.current_week if hasattr(league, 'current_week') else 18
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch available years: {str(e)}")

@app.get("/available-weeks/{year}")
async def get_available_weeks(year: int):
    """Get list of available weeks for a specific year"""
    try:
        if not (2019 <= year <= 2025):
            raise HTTPException(status_code=400, detail="Year must be between 2019 and 2025")

        return db_api.get_available_weeks(year)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch available weeks for {year}: {str(e)}")

@app.get("/league/stats")
async def get_current_league_stats():
    """Get current season league statistics"""
    try:
        if use_database():
            return db_api.get_league_stats(2025)
        else:
            data = get_league_stats()
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch league stats: {str(e)}")

@app.get("/league/stats/{year}")
async def get_league_stats_by_year(year: int):
    """Get league statistics for a specific year"""
    try:
        if not (2015 <= year <= 2025):
            raise HTTPException(status_code=400, detail="Year must be between 2015 and 2025")

        if use_database():
            return db_api.get_league_stats(year)
        else:
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
        if use_database():
            return db_api.get_standings(2025)
        else:
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
        if use_database():
            return db_api.get_teams(2025)
        else:
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

@app.get("/champions")
async def get_current_champions():
    """Get championship data for current season"""
    try:
        if use_database():
            return db_api.get_champions(2025)

        league = League(league_id=LEAGUE_ID, year=2025, espn_s2=ESPN_S2, swid=SWID, debug=False)
        teams = league.teams

        # Sort teams by final_standing (1st, 2nd, 3rd, etc.)
        # Note: final_standing might be 0 if season isn't complete, fall back to regular standing
        sorted_teams = sorted(teams, key=lambda x: x.final_standing if x.final_standing > 0 else x.standing)

        champions_data = []
        for i, team in enumerate(sorted_teams[:3]):  # Top 3 only
            place = i + 1
            champions_data.append({
                "place": place,
                "team_id": team.team_id,
                "team_name": team.team_name,
                "owner": f"{team.owners[0].get('firstName', '')} {team.owners[0].get('lastName', '')}".strip() if team.owners and team.owners[0].get('firstName') else (team.owners[0]['displayName'] if team.owners else "Unknown"),
                "wins": team.wins,
                "losses": team.losses,
                "ties": team.ties,
                "points_for": team.points_for,
                "points_against": team.points_against,
                "final_standing": team.final_standing if team.final_standing > 0 else team.standing,
                "logo_url": team.logo_url if hasattr(team, 'logo_url') else None
            })

        return {
            "year": 2025,
            "champions": champions_data,
            "season_complete": all(team.final_standing > 0 for team in teams)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch champions: {str(e)}")

@app.get("/champions/{year}")
async def get_champions_by_year(year: int):
    """Get championship data for a specific year"""
    try:
        if not (2015 <= year <= 2025):
            raise HTTPException(status_code=400, detail="Year must be between 2015 and 2025")

        if use_database():
            return db_api.get_champions(year)

        league = League(league_id=LEAGUE_ID, year=year, espn_s2=ESPN_S2, swid=SWID, debug=False)
        teams = league.teams

        # Sort teams by final_standing (1st, 2nd, 3rd, etc.)
        # Note: final_standing might be 0 if season isn't complete, fall back to regular standing
        sorted_teams = sorted(teams, key=lambda x: x.final_standing if x.final_standing > 0 else x.standing)

        champions_data = []
        for i, team in enumerate(sorted_teams[:3]):  # Top 3 only
            place = i + 1
            champions_data.append({
                "place": place,
                "team_id": team.team_id,
                "team_name": team.team_name,
                "owner": f"{team.owners[0].get('firstName', '')} {team.owners[0].get('lastName', '')}".strip() if team.owners and team.owners[0].get('firstName') else (team.owners[0]['displayName'] if team.owners else "Unknown"),
                "wins": team.wins,
                "losses": team.losses,
                "ties": team.ties,
                "points_for": team.points_for,
                "points_against": team.points_against,
                "final_standing": team.final_standing if team.final_standing > 0 else team.standing,
                "logo_url": team.logo_url if hasattr(team, 'logo_url') else None
            })

        return {
            "year": year,
            "champions": champions_data,
            "season_complete": all(team.final_standing > 0 for team in teams)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch champions for {year}: {str(e)}")

@app.get("/team-legacy")
async def get_team_legacy():
    """Get comprehensive team history and legacy data across all years"""
    try:
        return db_api.get_team_legacy()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch team legacy data: {str(e)}")

@app.get("/streak-records")
async def get_streak_records(year: int = None):
    """Get winning and losing streak records from database"""
    try:
        db = DatabaseAPI()
        result = db.get_streak_records(year)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch streak records: {str(e)}")

@app.get("/luck-analysis")
async def get_luck_analysis():
    """Get luck analysis showing teams that most outperformed/underperformed projections"""
    try:
        # Use database
        if use_database():
            return db_api.get_luck_analysis()

        # Fallback to ESPN API (original logic)
        # Get available years
        league = League(league_id=LEAGUE_ID, year=2025, espn_s2=ESPN_S2, swid=SWID, debug=False)
        available_years = [2025]

        if hasattr(league, 'previousSeasons') and league.previousSeasons:
            for season in league.previousSeasons:
                try:
                    season_year = int(season)
                    available_years.append(season_year)
                except ValueError:
                    continue

        available_years.sort(reverse=True)

        # Limit to recent years for performance (last 5 years including current)
        recent_years = [year for year in available_years if year >= 2019][:5]
        print(f"Processing luck analysis for years: {recent_years}", flush=True)

        # Collect luck data
        season_luck_data = []
        single_matchup_luck = []

        for year_index, analysis_year in enumerate(recent_years):
            print(f"Processing year {analysis_year} ({year_index + 1}/{len(recent_years)})", flush=True)

            try:
                year_league = League(league_id=LEAGUE_ID, year=analysis_year, espn_s2=ESPN_S2, swid=SWID, debug=False)

                # For current year (2025), only get completed weeks, for past years get all weeks
                max_week = 17 if analysis_year < 2025 else (year_league.current_week if hasattr(year_league, 'current_week') and year_league.current_week else 17)
                print(f"Processing weeks 1-{max_week} for {analysis_year}", flush=True)

                season_team_luck = {}  # team_id -> luck stats for the season

                for week in range(1, max_week + 1):
                    try:
                        matchups = year_league.box_scores(week)

                        # Skip weeks with no matchups or incomplete games
                        if not matchups:
                            continue

                        # For current year, check if games are actually completed
                        if analysis_year == 2025:
                            has_completed_games = any(
                                matchup.home_score > 0 and matchup.away_score > 0
                                for matchup in matchups
                            )
                            if not has_completed_games:
                                continue

                        for matchup in matchups:
                            # Validate matchup data structure
                            if not hasattr(matchup, 'home_team') or not hasattr(matchup, 'away_team'):
                                continue

                            # Check if team objects are valid (sometimes they can be integers)
                            if not hasattr(matchup.home_team, 'team_id') or not hasattr(matchup.away_team, 'team_id'):
                                print(f"Skipping invalid matchup in {analysis_year} week {week}: team objects are not properly formed", flush=True)
                                continue

                            # Check if required attributes exist
                            if not hasattr(matchup, 'home_projected') or not hasattr(matchup, 'away_projected'):
                                print(f"Skipping matchup in {analysis_year} week {week}: missing projected scores", flush=True)
                                continue

                            # Calculate luck for home team
                            home_projected_margin = matchup.home_projected - matchup.away_projected
                            home_actual_margin = matchup.home_score - matchup.away_score
                            home_luck = home_actual_margin - home_projected_margin

                            # Calculate luck for away team (opposite of home)
                            away_luck = -home_luck

                            # Track season totals
                            home_id = matchup.home_team.team_id
                            away_id = matchup.away_team.team_id

                            if home_id not in season_team_luck:
                                season_team_luck[home_id] = {
                                    "team_name": matchup.home_team.team_name,
                                    "owner": f"{matchup.home_team.owners[0].get('firstName', '')} {matchup.home_team.owners[0].get('lastName', '')}".strip() if matchup.home_team.owners and matchup.home_team.owners[0].get('firstName') else (matchup.home_team.owners[0]['displayName'] if matchup.home_team.owners else f"Team_{matchup.home_team.team_id}"),
                                    "total_luck": 0,
                                    "games_played": 0,
                                    "biggest_lucky_game": {"luck": 0, "week": 0, "opponent": "", "margin": 0},
                                    "biggest_unlucky_game": {"luck": 0, "week": 0, "opponent": "", "margin": 0}
                                }

                            if away_id not in season_team_luck:
                                season_team_luck[away_id] = {
                                    "team_name": matchup.away_team.team_name,
                                    "owner": f"{matchup.away_team.owners[0].get('firstName', '')} {matchup.away_team.owners[0].get('lastName', '')}".strip() if matchup.away_team.owners and matchup.away_team.owners[0].get('firstName') else (matchup.away_team.owners[0]['displayName'] if matchup.away_team.owners else f"Team_{matchup.away_team.team_id}"),
                                    "total_luck": 0,
                                    "games_played": 0,
                                    "biggest_lucky_game": {"luck": 0, "week": 0, "opponent": "", "margin": 0},
                                    "biggest_unlucky_game": {"luck": 0, "week": 0, "opponent": "", "margin": 0}
                                }

                            # Update season totals
                            season_team_luck[home_id]["total_luck"] += home_luck
                            season_team_luck[home_id]["games_played"] += 1
                            season_team_luck[away_id]["total_luck"] += away_luck
                            season_team_luck[away_id]["games_played"] += 1

                            # Track biggest lucky/unlucky games for the season
                            if home_luck > season_team_luck[home_id]["biggest_lucky_game"]["luck"]:
                                season_team_luck[home_id]["biggest_lucky_game"] = {
                                    "luck": home_luck,
                                    "week": week,
                                    "opponent": matchup.away_team.team_name,
                                    "margin": home_actual_margin
                                }
                            if home_luck < season_team_luck[home_id]["biggest_unlucky_game"]["luck"]:
                                season_team_luck[home_id]["biggest_unlucky_game"] = {
                                    "luck": home_luck,
                                    "week": week,
                                    "opponent": matchup.away_team.team_name,
                                    "margin": home_actual_margin
                                }

                            if away_luck > season_team_luck[away_id]["biggest_lucky_game"]["luck"]:
                                season_team_luck[away_id]["biggest_lucky_game"] = {
                                    "luck": away_luck,
                                    "week": week,
                                    "opponent": matchup.home_team.team_name,
                                    "margin": -home_actual_margin
                                }
                            if away_luck < season_team_luck[away_id]["biggest_unlucky_game"]["luck"]:
                                season_team_luck[away_id]["biggest_unlucky_game"] = {
                                    "luck": away_luck,
                                    "week": week,
                                    "opponent": matchup.home_team.team_name,
                                    "margin": -home_actual_margin
                                }

                            # Track single matchups for overall analysis
                            single_matchup_luck.append({
                                "year": analysis_year,
                                "week": week,
                                "team_name": matchup.home_team.team_name,
                                "owner": f"{matchup.home_team.owners[0].get('firstName', '')} {matchup.home_team.owners[0].get('lastName', '')}".strip() if matchup.home_team.owners and matchup.home_team.owners[0].get('firstName') else (matchup.home_team.owners[0]['displayName'] if matchup.home_team.owners else f"Team_{matchup.home_team.team_id}"),
                                "opponent": matchup.away_team.team_name,
                                "luck": home_luck,
                                "actual_score": matchup.home_score,
                                "projected_score": matchup.home_projected,
                                "opponent_actual": matchup.away_score,
                                "opponent_projected": matchup.away_projected,
                                "actual_margin": home_actual_margin,
                                "projected_margin": home_projected_margin
                            })

                            single_matchup_luck.append({
                                "year": analysis_year,
                                "week": week,
                                "team_name": matchup.away_team.team_name,
                                "owner": f"{matchup.away_team.owners[0].get('firstName', '')} {matchup.away_team.owners[0].get('lastName', '')}".strip() if matchup.away_team.owners and matchup.away_team.owners[0].get('firstName') else (matchup.away_team.owners[0]['displayName'] if matchup.away_team.owners else f"Team_{matchup.away_team.team_id}"),
                                "opponent": matchup.home_team.team_name,
                                "luck": away_luck,
                                "actual_score": matchup.away_score,
                                "projected_score": matchup.away_projected,
                                "opponent_actual": matchup.home_score,
                                "opponent_projected": matchup.home_projected,
                                "actual_margin": -home_actual_margin,
                                "projected_margin": -home_projected_margin
                            })

                    except Exception as week_error:
                        print(f"Error processing {analysis_year} week {week}: {str(week_error)}", flush=True)
                        continue

                # Add season data with averages
                for team_id, data in season_team_luck.items():
                    if data["games_played"] > 0:
                        season_luck_data.append({
                            "year": analysis_year,
                            "team_name": data["team_name"],
                            "owner": data["owner"],
                            "total_luck": round(data["total_luck"], 2),
                            "average_luck": round(data["total_luck"] / data["games_played"], 2),
                            "games_played": data["games_played"],
                            "biggest_lucky_game": data["biggest_lucky_game"],
                            "biggest_unlucky_game": data["biggest_unlucky_game"]
                        })

            except Exception as year_error:
                print(f"Error processing {analysis_year}: {str(year_error)}", flush=True)
                continue

        # Sort and get top results
        luckiest_seasons = sorted(season_luck_data, key=lambda x: x["total_luck"], reverse=True)[:3]
        unluckiest_seasons = sorted(season_luck_data, key=lambda x: x["total_luck"])[:3]
        luckiest_single_matchups = sorted(single_matchup_luck, key=lambda x: x["luck"], reverse=True)[:5]
        unluckiest_single_matchups = sorted(single_matchup_luck, key=lambda x: x["luck"])[:5]

        return {
            "luckiest_seasons": luckiest_seasons,
            "unluckiest_seasons": unluckiest_seasons,
            "luckiest_single_matchups": luckiest_single_matchups,
            "unluckiest_single_matchups": unluckiest_single_matchups,
            "total_seasons_analyzed": len(available_years),
            "total_matchups_analyzed": len(single_matchup_luck)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch luck analysis: {str(e)}")

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

        if use_database():
            return db_api.get_matchups(2025, week)

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
        if not (2015 <= year <= 2025):
            raise HTTPException(status_code=400, detail="Year must be between 2015 and 2025")
        if not (1 <= week <= 18):
            raise HTTPException(status_code=400, detail="Week must be between 1 and 18")

        if use_database():
            return db_api.get_matchups(year, week)

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

@app.get("/bench-heroes")
async def get_bench_heroes_query(year: int, week: int):
    """Get top scoring bench players for a specific week and year (query params)"""
    try:
        if not (2019 <= year <= 2025):
            raise HTTPException(status_code=400, detail="Bench heroes data is only available from 2019 onwards due to ESPN API limitations")
        if not (1 <= week <= 18):
            raise HTTPException(status_code=400, detail="Week must be between 1 and 18")

        if use_database():
            return db_api.get_bench_heroes(year, week)

        print(f"Fetching bench heroes for year={year}, week={week}", flush=True)

        league = League(league_id=LEAGUE_ID, year=year, espn_s2=ESPN_S2, swid=SWID, debug=False)
        print(f"League created successfully for {year}", flush=True)

        box_scores = league.box_scores(week)
        print(f"Retrieved {len(box_scores) if box_scores else 0} box scores for week {week}", flush=True)

        if not box_scores:
            print(f"No box scores available for year={year}, week={week}", flush=True)
            return {
                "year": year,
                "week": week,
                "bench_heroes": [],
                "total_bench_players": 0,
                "message": f"No games found for week {week} of {year}"
            }

        bench_heroes = []

        for box_score in box_scores:
            print(f"Processing matchup: {box_score.home_team.team_name} vs {box_score.away_team.team_name}", flush=True)

            # Process home team bench
            for player in box_score.home_lineup:
                if hasattr(player, 'slot_position') and player.slot_position == 'BE' and hasattr(player, 'points') and player.points > 0:
                    bench_heroes.append({
                        "player_name": player.name,
                        "points": round(player.points, 2),
                        "team_name": box_score.home_team.team_name,
                        "team_id": box_score.home_team.team_id,
                        "owner": f"{box_score.home_team.owners[0].get('firstName', '')} {box_score.home_team.owners[0].get('lastName', '')}".strip() if box_score.home_team.owners and box_score.home_team.owners[0].get('firstName') else (box_score.home_team.owners[0]['displayName'] if box_score.home_team.owners else f"Team_{box_score.home_team.team_id}"),
                        "position": player.position,
                        "pro_team": player.proTeam if hasattr(player, 'proTeam') else 'N/A'
                    })

            # Process away team bench
            for player in box_score.away_lineup:
                if hasattr(player, 'slot_position') and player.slot_position == 'BE' and hasattr(player, 'points') and player.points > 0:
                    bench_heroes.append({
                        "player_name": player.name,
                        "points": round(player.points, 2),
                        "team_name": box_score.away_team.team_name,
                        "team_id": box_score.away_team.team_id,
                        "owner": f"{box_score.away_team.owners[0].get('firstName', '')} {box_score.away_team.owners[0].get('lastName', '')}".strip() if box_score.away_team.owners and box_score.away_team.owners[0].get('firstName') else (box_score.away_team.owners[0]['displayName'] if box_score.away_team.owners else f"Team_{box_score.away_team.team_id}"),
                        "position": player.position,
                        "pro_team": player.proTeam if hasattr(player, 'proTeam') else 'N/A'
                    })

        # Sort by points and get top performers
        bench_heroes.sort(key=lambda x: x["points"], reverse=True)
        top_bench_heroes = bench_heroes[:10]  # Top 10

        print(f"Found {len(bench_heroes)} total bench players, returning top {len(top_bench_heroes)}", flush=True)

        return {
            "year": year,
            "week": week,
            "bench_heroes": top_bench_heroes,
            "total_bench_players": len(bench_heroes),
            "total": len(top_bench_heroes)
        }

    except Exception as e:
        print(f"Error in get_bench_heroes: {str(e)}", flush=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch bench heroes: {str(e)}")

@app.get("/bench-heroes/{year}/{week}")
async def get_bench_heroes(year: int, week: int):
    """Get top scoring bench players for a specific week and year"""
    try:
        if not (2019 <= year <= 2025):
            raise HTTPException(status_code=400, detail="Bench heroes data is only available from 2019 onwards due to ESPN API limitations")
        if not (1 <= week <= 18):
            raise HTTPException(status_code=400, detail="Week must be between 1 and 18")

        if use_database():
            return db_api.get_bench_heroes(year, week)

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