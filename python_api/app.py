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
from cache_setup import cached_endpoint, get_cache_stats, clear_cache

# Caching is now handled by decorators in cache_setup.py

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

@app.get("/cache-stats")
async def cache_stats():
    """Get cache statistics and status"""
    return get_cache_stats()

@app.post("/cache-clear")
async def cache_clear():
    """Clear all cache entries"""
    clear_cache()
    return {"message": "Cache cleared successfully"}

@app.get("/available-years")
@cached_endpoint("/available-years")
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

        league = League(league_id=LEAGUE_ID, year=year, espn_s2=ESPN_S2, swid=SWID, debug=False)

        # For the current year (2025), limit to current week
        if year == 2025:
            current_week = league.current_week if hasattr(league, 'current_week') else 1
            max_week = max(1, current_week)  # At least show week 1
        else:
            # For past years, check what weeks actually have data by trying a few key weeks
            max_week = 17  # Default to full season for past years

            # Try to determine actual season length by checking if week 17 has data
            try:
                box_scores_17 = league.box_scores(17)
                if box_scores_17:
                    max_week = 17
                else:
                    max_week = 16
            except:
                # If week 17 fails, try week 16
                try:
                    box_scores_16 = league.box_scores(16)
                    max_week = 16 if box_scores_16 else 15
                except:
                    max_week = 15  # Conservative fallback

        available_weeks = list(range(1, max_week + 1))

        return {
            "year": year,
            "available_weeks": available_weeks,
            "max_week": max_week,
            "is_current_year": year == 2025
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch available weeks for {year}: {str(e)}")

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

@app.get("/champions")
async def get_current_champions():
    """Get championship data for current season"""
    try:
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
@cached_endpoint("/team-legacy")
async def get_team_legacy():
    """Get comprehensive team history and legacy data across all years"""
    try:
        # Get available years first
        league = League(league_id=LEAGUE_ID, year=2025, espn_s2=ESPN_S2, swid=SWID, debug=False)
        available_years = [2025]

        if hasattr(league, 'previousSeasons') and league.previousSeasons:
            for season in league.previousSeasons:
                try:
                    year = int(season)
                    available_years.append(year)
                except ValueError:
                    continue

        available_years.sort(reverse=True)

        # Collect data for each team across all years
        team_legacy_data = {}

        for year in available_years:
            try:
                year_league = League(league_id=LEAGUE_ID, year=year, espn_s2=ESPN_S2, swid=SWID, debug=False)
                teams = year_league.teams

                for team in teams:
                    # Use owner name as the consistent identifier across years
                    owner_name = f"{team.owners[0].get('firstName', '')} {team.owners[0].get('lastName', '')}".strip() if team.owners and team.owners[0].get('firstName') else (team.owners[0]['displayName'] if team.owners else f"Team_{team.team_id}")

                    if owner_name not in team_legacy_data:
                        team_legacy_data[owner_name] = {
                            "owner": owner_name,
                            "team_names": [],  # Track all team names with years for chronological order
                            "years_active": [],
                            "placements": [],
                            "total_wins": 0,
                            "total_losses": 0,
                            "total_ties": 0,
                            "total_points_for": 0,
                            "total_points_against": 0,
                            "seasons_played": 0,
                            "championship_years": [],
                            "runner_up_years": [],
                            "third_place_years": []
                        }

                    # Add data for this year
                    team_data = team_legacy_data[owner_name]
                    team_data["team_names"].append({"name": team.team_name, "year": year})
                    team_data["years_active"].append(year)

                    # Use final_standing if available, otherwise regular standing
                    placement = team.final_standing if team.final_standing > 0 else team.standing
                    team_data["placements"].append({"year": year, "placement": placement})

                    team_data["total_wins"] += team.wins
                    team_data["total_losses"] += team.losses
                    team_data["total_ties"] += team.ties
                    team_data["total_points_for"] += team.points_for
                    team_data["total_points_against"] += team.points_against
                    team_data["seasons_played"] += 1

                    # Track championships
                    if placement == 1:
                        team_data["championship_years"].append(year)
                    elif placement == 2:
                        team_data["runner_up_years"].append(year)
                    elif placement == 3:
                        team_data["third_place_years"].append(year)

            except Exception as e:
                print(f"Error processing year {year}: {e}")
                continue

        # Calculate legacy stats and rankings
        legacy_rankings = []

        for owner, data in team_legacy_data.items():
            if data["seasons_played"] == 0:
                continue

            # Sort team names by year and get unique names
            data["team_names"].sort(key=lambda x: x["year"], reverse=True)
            unique_names = []
            seen_names = set()
            for name_entry in data["team_names"]:
                if name_entry["name"] not in seen_names:
                    unique_names.append(name_entry["name"])
                    seen_names.add(name_entry["name"])

            # Most recent team name is primary
            current_team_name = unique_names[0] if unique_names else "Unknown"
            aka_names = unique_names[1:] if len(unique_names) > 1 else []

            data["years_active"].sort(reverse=True)

            # Calculate average placement EXCLUDING current year (2025)
            completed_placements = [p for p in data["placements"] if p["year"] < 2025]

            if len(completed_placements) > 0:
                avg_placement = sum(p["placement"] for p in completed_placements) / len(completed_placements)
                has_placement_history = True
            else:
                avg_placement = None  # No completed seasons
                has_placement_history = False

            # Calculate all-time win percentage (all years including current)
            total_games = data["total_wins"] + data["total_losses"] + data["total_ties"]
            win_percentage = (data["total_wins"] / total_games * 100) if total_games > 0 else 0

            # Calculate points per game average (all years including current)
            avg_points_per_game = data["total_points_for"] / data["seasons_played"] if data["seasons_played"] > 0 else 0

            # Create gaps in participation (years not active) - exclude current year from gap calculation
            completed_years = [y for y in available_years if y < 2025]
            if completed_years:
                all_completed_years = set(range(min(completed_years), max(completed_years) + 1))
                active_completed_years = set([y for y in data["years_active"] if y < 2025])
                gap_years = sorted(list(all_completed_years - active_completed_years), reverse=True)
            else:
                gap_years = []

            # Add calculated fields
            data.update({
                "average_placement": round(avg_placement, 2) if avg_placement is not None else None,
                "has_placement_history": has_placement_history,
                "completed_seasons": len(completed_placements),
                "win_percentage": round(win_percentage, 1),
                "avg_points_per_game": round(avg_points_per_game, 1),
                "championships": len(data["championship_years"]),
                "runner_ups": len(data["runner_up_years"]),
                "third_places": len(data["third_place_years"]),
                "gap_years": gap_years,
                "current_team_name": current_team_name,
                "aka_names": aka_names,
                "years_in_league": len(data["years_active"]),
                "total_years_available": len(available_years)
            })

            legacy_rankings.append(data)

        # Sort by average placement (ascending - better placement = lower number)
        # Teams with no placement history go to the bottom
        legacy_rankings.sort(key=lambda x: (x["average_placement"] is None, x["average_placement"] or float('inf')))

        return {
            "total_teams": len(legacy_rankings),
            "years_analyzed": available_years,
            "team_legacy": legacy_rankings
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch team legacy data: {str(e)}")

@app.get("/streak-records")
@cached_endpoint("/streak-records")
async def get_streak_records(year: int = None):
    """Get winning and losing streak records, either all-time or for a specific year"""
    try:
        # Get available years first
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

        # Collect game results for streak analysis
        all_games = []

        years_to_analyze = [year] if year else available_years

        for analysis_year in years_to_analyze:
            try:
                year_league = League(league_id=LEAGUE_ID, year=analysis_year, espn_s2=ESPN_S2, swid=SWID, debug=False)

                # For current year (2025), only get completed weeks, for past years get all weeks
                max_week = 17 if analysis_year < 2025 else (year_league.current_week if hasattr(year_league, 'current_week') and year_league.current_week else 17)

                for week in range(1, max_week + 1):
                    try:
                        matchups = year_league.box_scores(week)

                        # Skip weeks with no matchups or incomplete games
                        if not matchups:
                            continue

                        # For current year, check if games are actually completed
                        if analysis_year == 2025:
                            # Check if any game has meaningful scores (both teams > 0)
                            has_completed_games = any(
                                matchup.home_score > 0 and matchup.away_score > 0
                                for matchup in matchups
                            )
                            if not has_completed_games:
                                continue

                        for matchup in matchups:
                            # Home team result
                            home_result = "W" if matchup.home_score > matchup.away_score else "L"
                            all_games.append({
                                "year": analysis_year,
                                "week": week,
                                "team_id": matchup.home_team.team_id,
                                "team_name": matchup.home_team.team_name,
                                "owner": f"{matchup.home_team.owners[0].get('firstName', '')} {matchup.home_team.owners[0].get('lastName', '')}".strip() if matchup.home_team.owners and matchup.home_team.owners[0].get('firstName') else (matchup.home_team.owners[0]['displayName'] if matchup.home_team.owners else f"Team_{matchup.home_team.team_id}"),
                                "result": home_result,
                                "score": matchup.home_score,
                                "opponent_score": matchup.away_score
                            })

                            # Away team result
                            away_result = "W" if matchup.away_score > matchup.home_score else "L"
                            all_games.append({
                                "year": analysis_year,
                                "week": week,
                                "team_id": matchup.away_team.team_id,
                                "team_name": matchup.away_team.team_name,
                                "owner": f"{matchup.away_team.owners[0].get('firstName', '')} {matchup.away_team.owners[0].get('lastName', '')}".strip() if matchup.away_team.owners and matchup.away_team.owners[0].get('firstName') else (matchup.away_team.owners[0]['displayName'] if matchup.away_team.owners else f"Team_{matchup.away_team.team_id}"),
                                "result": away_result,
                                "score": matchup.away_score,
                                "opponent_score": matchup.home_score
                            })

                    except Exception as e:
                        # Week might not exist or have data
                        continue

            except Exception as e:
                print(f"Error processing year {analysis_year}: {e}")
                continue

        # Sort games chronologically for streak analysis
        all_games.sort(key=lambda x: (x["year"], x["week"]))

        # Analyze streaks by owner (consistent across team name changes)
        owner_games = {}
        for game in all_games:
            owner = game["owner"]
            if owner not in owner_games:
                owner_games[owner] = []
            owner_games[owner].append(game)

        # Calculate streaks for each owner
        streak_records = {
            "longest_win_streaks": [],
            "longest_loss_streaks": [],
            "current_streaks": []
        }

        for owner, games in owner_games.items():
            # Calculate all streaks for this owner
            win_streaks = []
            loss_streaks = []
            current_streak = {"type": None, "length": 0, "games": []}

            for game in games:
                if current_streak["type"] == game["result"]:
                    # Continue current streak
                    current_streak["length"] += 1
                    current_streak["games"].append(game)
                else:
                    # Streak ended, record it
                    if current_streak["type"] and current_streak["length"] > 0:
                        streak_data = {
                            "owner": owner,
                            "team_names": list(set([g["team_name"] for g in current_streak["games"]])),
                            "length": current_streak["length"],
                            "start_year": current_streak["games"][0]["year"],
                            "start_week": current_streak["games"][0]["week"],
                            "end_year": current_streak["games"][-1]["year"],
                            "end_week": current_streak["games"][-1]["week"],
                            "games": current_streak["games"]
                        }

                        if current_streak["type"] == "W":
                            win_streaks.append(streak_data)
                        else:
                            loss_streaks.append(streak_data)

                    # Start new streak
                    current_streak = {
                        "type": game["result"],
                        "length": 1,
                        "games": [game]
                    }

            # Don't forget the last streak
            if current_streak["type"] and current_streak["length"] > 0:
                streak_data = {
                    "owner": owner,
                    "team_names": list(set([g["team_name"] for g in current_streak["games"]])),
                    "length": current_streak["length"],
                    "start_year": current_streak["games"][0]["year"],
                    "start_week": current_streak["games"][0]["week"],
                    "end_year": current_streak["games"][-1]["year"],
                    "end_week": current_streak["games"][-1]["week"],
                    "games": current_streak["games"],
                    "is_current": True  # Mark current streaks
                }

                if current_streak["type"] == "W":
                    win_streaks.append(streak_data)
                    streak_records["current_streaks"].append(streak_data)
                else:
                    loss_streaks.append(streak_data)
                    streak_records["current_streaks"].append(streak_data)

            # Add to overall records
            streak_records["longest_win_streaks"].extend(win_streaks)
            streak_records["longest_loss_streaks"].extend(loss_streaks)

        # Sort and get top streaks
        streak_records["longest_win_streaks"].sort(key=lambda x: x["length"], reverse=True)
        streak_records["longest_loss_streaks"].sort(key=lambda x: x["length"], reverse=True)

        # Filter current streaks to only include current season participants and 3+ streaks
        filtered_current_streaks = []
        if not year:  # Only for all-time queries
            # Get current season participants
            current_league = League(league_id=LEAGUE_ID, year=2025, espn_s2=ESPN_S2, swid=SWID, debug=False)
            current_owners = set()
            for team in current_league.teams:
                owner_name = f"{team.owners[0].get('firstName', '')} {team.owners[0].get('lastName', '')}".strip() if team.owners and team.owners[0].get('firstName') else (team.owners[0]['displayName'] if team.owners else f"Team_{team.team_id}")
                current_owners.add(owner_name)

            # Filter current streaks
            for streak in streak_records["current_streaks"]:
                if (streak.get("is_current") and
                    streak["owner"] in current_owners and
                    streak["length"] >= 3):
                    filtered_current_streaks.append(streak)

        return {
            "analysis_type": "single_season" if year else "all_time",
            "year": year,
            "years_analyzed": years_to_analyze,
            "longest_win_streaks": streak_records["longest_win_streaks"][:5],  # Top 5
            "longest_loss_streaks": streak_records["longest_loss_streaks"][:5],  # Top 5
            "current_streaks": filtered_current_streaks,
            "total_games_analyzed": len(all_games)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch streak records: {str(e)}")

@app.get("/luck-analysis")
@cached_endpoint("/luck-analysis")
async def get_luck_analysis():
    """Get luck analysis showing teams that most outperformed/underperformed projections"""
    try:
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

        # Collect luck data
        season_luck_data = []
        single_matchup_luck = []

        for analysis_year in available_years:
            try:
                year_league = League(league_id=LEAGUE_ID, year=analysis_year, espn_s2=ESPN_S2, swid=SWID, debug=False)

                # For current year (2025), only get completed weeks, for past years get all weeks
                max_week = 17 if analysis_year < 2025 else (year_league.current_week if hasattr(year_league, 'current_week') and year_league.current_week else 17)

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