"""
Database-backed API endpoints for fantasy football data
Replaces slow ESPN API calls with fast SQLite queries
"""

import sqlite3
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

class DatabaseAPI:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Look for database in parent directory first, then current directory
            parent_db = os.path.join(os.path.dirname(__file__), "..", "fantasy_football.db")
            current_db = "fantasy_football.db"

            if os.path.exists(parent_db):
                self.db_path = parent_db
            else:
                self.db_path = current_db
        else:
            self.db_path = db_path

    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def _execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute query and return results as list of dictionaries"""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def _execute_single(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Execute query and return single result"""
        results = self._execute_query(query, params)
        return results[0] if results else None

    def get_league_stats(self, year: int = 2025) -> Dict[str, Any]:
        """Get league statistics for a specific year"""
        try:
            # Get league info
            league_query = """
            SELECT * FROM leagues WHERE year = ?
            """
            league = self._execute_single(league_query, (year,))

            if not league:
                return {"error": f"No data found for year {year}"}

            # Get teams for that year
            teams_query = """
            SELECT * FROM teams WHERE year = ?
            ORDER BY wins DESC, points_for DESC
            """
            teams = self._execute_query(teams_query, (year,))

            if not teams:
                return {"error": f"No teams found for year {year}"}

            # Calculate stats
            total_teams = len(teams)
            league_leader = teams[0] if teams else None
            total_points = sum(team['points_for'] for team in teams)
            average_score = round(total_points / total_teams, 2) if total_teams else 0.0

            # Get recent matchups for current year
            recent_matchups = []
            if year == 2025:
                matchups_query = """
                SELECT
                    m.week,
                    ht.team_name as home_team,
                    at.team_name as away_team,
                    m.home_score,
                    m.away_score
                FROM matchups m
                JOIN teams ht ON m.home_team_id = ht.team_id AND m.year = ht.year
                JOIN teams at ON m.away_team_id = at.team_id AND m.year = at.year
                WHERE m.year = ?
                ORDER BY m.week DESC
                LIMIT 5
                """
                recent_matchups = self._execute_query(matchups_query, (year,))

            return {
                "year": year,
                "current_week": league.get('current_week', 1),
                "total_teams": total_teams,
                "league_leader": {
                    "team_name": league_leader['team_name'] if league_leader else "Unknown",
                    "record": f"{league_leader['wins']}-{league_leader['losses']}" if league_leader else "0-0",
                    "points_for": league_leader['points_for'] if league_leader else 0
                },
                "average_score": str(average_score),
                "recent_matchups": recent_matchups
            }

        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

    def get_standings(self, year: int = 2025) -> Dict[str, Any]:
        """Get current standings from database"""
        try:
            standings_query = """
            SELECT
                t.standing,
                t.team_id,
                t.team_name,
                t.owners,
                t.wins,
                t.losses,
                t.ties,
                t.points_for,
                t.points_against,
                t.streak_type,
                t.streak_length
            FROM teams t
            WHERE t.year = ?
            ORDER BY t.standing ASC
            """

            standings_raw = self._execute_query(standings_query, (year,))

            # Process standings to extract owner names from JSON
            standings = []
            for team in standings_raw:
                # Parse owners JSON to get owner name
                try:
                    owners_data = json.loads(team['owners']) if team['owners'] else []
                    if owners_data and len(owners_data) > 0:
                        owner_data = owners_data[0]
                        if 'firstName' in owner_data and 'lastName' in owner_data:
                            owner_name = f"{owner_data['firstName']} {owner_data['lastName']}".strip()
                        else:
                            owner_name = owner_data.get('displayName', 'Unknown')
                    else:
                        owner_name = "Unknown"
                except:
                    owner_name = "Unknown"

                standings.append({
                    "rank": team['standing'],
                    "team_id": team['team_id'],
                    "team_name": team['team_name'],
                    "owner": owner_name,
                    "wins": team['wins'],
                    "losses": team['losses'],
                    "ties": team['ties'],
                    "points_for": round(team['points_for'], 2),
                    "points_against": round(team['points_against'], 2),
                    "streak_type": team['streak_type'],
                    "streak_length": team['streak_length']
                })

            # Get current week from league
            league = self._execute_single("SELECT current_week FROM leagues WHERE year = ?", (year,))
            current_week = league['current_week'] if league else 1

            return {
                "year": year,
                "current_week": current_week,
                "standings": standings,
                "total_teams": len(standings)
            }

        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

    def get_teams(self, year: int = 2025) -> Dict[str, Any]:
        """Get all teams for a specific year"""
        try:
            teams_query = """
            SELECT
                team_id,
                team_name,
                owners,
                wins,
                losses,
                ties,
                points_for,
                points_against,
                standing
            FROM teams
            WHERE year = ?
            ORDER BY standing ASC
            """

            teams_raw = self._execute_query(teams_query, (year,))

            # Process teams to extract owner names from JSON
            teams = []
            for team in teams_raw:
                # Parse owners JSON to get owner name
                try:
                    owners_data = json.loads(team['owners']) if team['owners'] else []
                    if owners_data and len(owners_data) > 0:
                        owner_data = owners_data[0]
                        if 'firstName' in owner_data and 'lastName' in owner_data:
                            owner_name = f"{owner_data['firstName']} {owner_data['lastName']}".strip()
                        else:
                            owner_name = owner_data.get('displayName', 'Unknown')
                    else:
                        owner_name = "Unknown"
                except:
                    owner_name = "Unknown"

                teams.append({
                    "team_id": team['team_id'],
                    "team_name": team['team_name'],
                    "owner": owner_name,
                    "wins": team['wins'],
                    "losses": team['losses'],
                    "ties": team['ties'],
                    "points_for": team['points_for'],
                    "points_against": team['points_against'],
                    "standing": team['standing']
                })

            return {
                "year": year,
                "teams": teams,
                "total": len(teams)
            }

        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

    def get_matchups(self, year: int, week: int) -> Dict[str, Any]:
        """Get matchups for a specific week and year"""
        try:
            matchups_query = """
            SELECT
                m.week,
                m.home_score,
                m.away_score,
                ht.team_name as home_team_name,
                at.team_name as away_team_name
            FROM matchups m
            JOIN teams ht ON m.home_team_id = ht.team_id AND m.year = ht.year
            JOIN teams at ON m.away_team_id = at.team_id AND m.year = at.year
            WHERE m.year = ? AND m.week = ?
            """

            matchups_data = self._execute_query(matchups_query, (year, week))

            matchups = []
            for matchup in matchups_data:
                matchups.append({
                    "week": matchup['week'],
                    "home_team": {
                        "name": matchup['home_team_name'],
                        "score": round(matchup['home_score'], 2)
                    },
                    "away_team": {
                        "name": matchup['away_team_name'],
                        "score": round(matchup['away_score'], 2)
                    }
                })

            return {
                "week": week,
                "year": year,
                "matchups": matchups
            }

        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

    def get_bench_heroes(self, year: int, week: int) -> Dict[str, Any]:
        """Get top bench performers for a specific week"""
        try:
            bench_query = """
            SELECT
                p.name as player_name,
                pp.points,
                t.team_name,
                t.team_id,
                t.owners,
                p.position,
                p.pro_team
            FROM player_performances pp
            JOIN players p ON pp.player_id = p.player_id
            JOIN teams t ON pp.team_id = t.team_id AND pp.year = t.year
            WHERE pp.year = ? AND pp.week = ?
            AND pp.lineup_slot LIKE '%BE%'
            ORDER BY pp.points DESC
            LIMIT 5
            """

            bench_heroes = self._execute_query(bench_query, (year, week))

            # Format the response
            formatted_heroes = []
            for hero in bench_heroes:
                # Parse owners JSON to get owner name
                try:
                    owners_data = json.loads(hero['owners']) if hero['owners'] else []
                    if owners_data and len(owners_data) > 0:
                        owner_data = owners_data[0]
                        if 'firstName' in owner_data and 'lastName' in owner_data:
                            owner_name = f"{owner_data['firstName']} {owner_data['lastName']}".strip()
                        else:
                            owner_name = owner_data.get('displayName', 'Unknown')
                    else:
                        owner_name = "Unknown"
                except:
                    owner_name = "Unknown"

                formatted_heroes.append({
                    "player_name": hero['player_name'],
                    "points": round(hero['points'], 2),
                    "team_name": hero['team_name'],
                    "team_id": hero['team_id'],
                    "owner": owner_name,
                    "position": hero['position'],
                    "pro_team": hero['pro_team']
                })

            return {
                "year": year,
                "week": week,
                "bench_heroes": formatted_heroes,
                "total_bench_players": len(formatted_heroes),
                "total": len(formatted_heroes)
            }

        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

    def get_available_years(self) -> Dict[str, Any]:
        """Get list of available years in the database"""
        try:
            years_query = "SELECT DISTINCT year FROM leagues ORDER BY year DESC"
            years_data = self._execute_query(years_query)

            available_years = [row['year'] for row in years_data]
            supported_years = [year for year in available_years if year >= 2019]

            # Get current year info
            current_year = 2025
            current_league = self._execute_single("SELECT current_week FROM leagues WHERE year = ?", (current_year,))
            current_week = current_league['current_week'] if current_league else 1

            return {
                "available_years": available_years,
                "supported_years": supported_years,
                "total_years": len(available_years),
                "current_year": current_year,
                "current_week": current_week
            }

        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

    def get_available_weeks(self, year: int) -> Dict[str, Any]:
        """Get available weeks for a specific year"""
        try:
            weeks_query = """
            SELECT DISTINCT week FROM matchups
            WHERE year = ?
            ORDER BY week ASC
            """
            weeks_data = self._execute_query(weeks_query, (year,))

            available_weeks = [row['week'] for row in weeks_data]
            max_week = max(available_weeks) if available_weeks else 1

            return {
                "year": year,
                "available_weeks": available_weeks,
                "max_week": max_week,
                "is_current_year": year == 2025
            }

        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

    def get_champions(self, year: int = 2025) -> Dict[str, Any]:
        """Get championship results for a specific year"""
        try:
            champions_query = """
            SELECT
                t.team_id,
                t.team_name,
                t.owners,
                t.wins,
                t.losses,
                t.ties,
                t.points_for,
                t.points_against,
                t.final_standing,
                t.standing
            FROM teams t
            WHERE t.year = ?
            ORDER BY
                CASE WHEN t.final_standing > 0 THEN t.final_standing ELSE t.standing END ASC
            LIMIT 3
            """

            champions_data = self._execute_query(champions_query, (year,))

            champions = []
            for i, team in enumerate(champions_data):
                place = i + 1

                # Parse owners JSON to get owner name
                try:
                    owners_data = json.loads(team['owners']) if team['owners'] else []
                    if owners_data and len(owners_data) > 0:
                        owner_data = owners_data[0]
                        if 'firstName' in owner_data and 'lastName' in owner_data:
                            owner_name = f"{owner_data['firstName']} {owner_data['lastName']}".strip()
                        else:
                            owner_name = owner_data.get('displayName', 'Unknown')
                    else:
                        owner_name = "Unknown"
                except:
                    owner_name = "Unknown"

                champions.append({
                    "place": place,
                    "team_id": team['team_id'],
                    "team_name": team['team_name'],
                    "owner": owner_name,
                    "wins": team['wins'],
                    "losses": team['losses'],
                    "ties": team['ties'],
                    "points_for": team['points_for'],
                    "points_against": team['points_against'],
                    "final_standing": team['final_standing'] if team['final_standing'] > 0 else team['standing']
                })

            # Check if season is complete
            season_complete = all(team['final_standing'] > 0 for team in champions_data)

            return {
                "year": year,
                "champions": champions,
                "season_complete": season_complete
            }

        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

    def get_luck_analysis(self) -> Dict[str, Any]:
        """Get luck analysis data from database"""
        try:
            # Check if pre-calculated luck analysis exists
            luck_query = "SELECT COUNT(*) as count FROM luck_analysis_seasons"
            luck_count = self._execute_single(luck_query)

            if luck_count and luck_count['count'] > 0:
                # Return pre-calculated luck analysis
                seasons_query = """
                SELECT
                    year,
                    team_name,
                    owner_name,
                    total_luck,
                    average_luck,
                    games_played,
                    biggest_lucky_week,
                    biggest_lucky_opponent,
                    biggest_lucky_points,
                    biggest_unlucky_week,
                    biggest_unlucky_opponent,
                    biggest_unlucky_points
                FROM luck_analysis_seasons
                ORDER BY year DESC, total_luck DESC
                """
                seasons_data = self._execute_query(seasons_query)

                matchups_query = """
                SELECT
                    year,
                    week,
                    team_name,
                    opponent_name,
                    luck_score,
                    actual_score,
                    projected_score
                FROM luck_analysis_matchups
                WHERE ABS(luck_score) > 10
                ORDER BY ABS(luck_score) DESC
                LIMIT 20
                """
                top_matchups = self._execute_query(matchups_query)

                return {
                    "season_data": seasons_data,
                    "top_lucky_matchups": top_matchups,
                    "data_source": "database"
                }
            else:
                # No pre-calculated data available - return empty but properly structured data
                return {
                    "season_data": [],
                    "top_lucky_matchups": [],
                    "summary": {
                        "total_seasons": 0,
                        "total_matchups": 0,
                        "most_lucky_team": None,
                        "most_unlucky_team": None
                    },
                    "data_source": "database",
                    "message": "Luck analysis data not yet calculated"
                }

        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

    def health_check(self) -> Dict[str, Any]:
        """Health check - verify database connection and basic functionality"""
        try:
            # Test basic query
            test_query = "SELECT COUNT(*) as count FROM leagues"
            result = self._execute_single(test_query)

            if result:
                return {
                    "status": "healthy",
                    "database": "connected",
                    "total_leagues": result['count']
                }
            else:
                return {
                    "status": "unhealthy",
                    "database": "error",
                    "error": "No leagues found"
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }