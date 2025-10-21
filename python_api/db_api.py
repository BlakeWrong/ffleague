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
                owner_name = self._get_owner_name(team)

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
                owner_name = self._get_owner_name(team)

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
            AND pp.slot_position LIKE '%BE%'
            ORDER BY pp.points DESC
            LIMIT 5
            """

            bench_heroes = self._execute_query(bench_query, (year, week))

            # Format the response
            formatted_heroes = []
            for hero in bench_heroes:
                owner_name = self._get_owner_name(hero)

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

    def _get_espn_owner_id_mapping(self) -> Dict[str, str]:
        """Create mapping of ESPN owner IDs to owner names - THE AUTHORITATIVE SOURCE"""
        return {
            # Current known ESPN owner IDs mapped to names
            "{B5FBB7B7-C134-4B6B-BBB7-B7C1343B6BCF}": "D'Anthony",  # team_1
            "{247150F3-5E23-403B-B150-F35E23603B86}": "Robert",      # team_2
            "{B67B55F7-CBF5-4789-BB55-F7CBF5A78967}": "Luke",        # team_3
            "{604BB883-79E2-4222-8BB8-8379E2922282}": "Dylan",       # team_4
            "{E2A887FA-CFF4-4F06-A887-FACFF40F0667}": "Derek",       # team_6
            "{7B4DE853-00A2-41CA-8494-216DEAD703FA}": "Zach",        # team_8 historical owner
            "{AC97CE73-BCAB-4F60-AF01-A4E51D98145A}": "Cody",        # team_9
            "{BC146B65-4056-4B5A-946B-6540566B5ABF}": "Alec",        # team_10
            "{E3298BFC-6D98-4852-AD4A-E1E138A72791}": "Andre",       # team_11
            "{8AA29716-021A-4CB9-8306-8ABC5E14D5BD}": "Sam",         # team_12
            "{B461B1C8-244E-4927-BFD1-FC980E492516}": "Blake",       # Historical team_9, now team_13?
            "{2EC18A2F-6C3B-41FF-9B3D-1305343ACF66}": "Brett",       # team_8 in 2018
            "{EB9FA5E5-2DF6-48AC-9FA5-E52DF688AC5F}": "Shane",       # team_6 in 2018-2019
            "{49B96E8E-113F-4403-8AD7-D7E785D16975}": "Julian",      # team_12 in 2020-2021
            # Note: Charlie (team_14) ESPN ID not yet captured
            # Note: Nick (current team_8 in 2025) ESPN ID not yet captured
        }

    def _get_team_id_owner_mapping(self) -> Dict[int, str]:
        """Create mapping of team_id to owner names - THE SINGLE SOURCE OF TRUTH"""
        return {
            1: "D'Anthony",     # The Two-Two Train / Soldier Fields / etc.
            2: "Robert",        # Doug Dimmadome / Milds n' Yak / etc.
            3: "Luke",          # American Eagle Jeans / Sock Stiffener / etc.
            4: "Dylan",         # Andy Reid's Mustache / Patty ICE / etc.
            6: "Derek",         # Kansas City Arrestables / Got the Rugg Pulled / etc.
            8: "Nick",          # John's Scary Team / Here 4 the Beer / etc.
            9: "Cody",          # Ten inch Penix / You got a Purdy mouth / KC Bacardi / etc.
            10: "Alec",         # Tit$burg feelers / Team oberzan / etc.
            11: "Andre",        # Damardiac Arrest / Hawk Tua / Mojo Dojo Casa House / etc.
            12: "Sam",          # Clark County Body Kamara / Winston's Crab Shack / etc.
            13: "Blake",        # Faded off that Josh (new in 2025)
            14: "Charlie",      # Chucktown Chuggers (new in 2025)
        }

    def _get_owner_name(self, team_data) -> str:
        """Extract owner name using ESPN owner ID as primary, team_id as fallback"""
        # First, try to extract ESPN owner ID from the owners JSON
        owners_json = team_data.get('owners')
        if owners_json:
            try:
                import json
                owners = json.loads(owners_json) if isinstance(owners_json, str) else owners_json

                # Get the first owner's ESPN ID
                if owners and isinstance(owners, list) and len(owners) > 0:
                    owner = owners[0]
                    espn_id = owner.get('id')

                    if espn_id:
                        espn_mapping = self._get_espn_owner_id_mapping()
                        if espn_id in espn_mapping:
                            return espn_mapping[espn_id]
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass

        # Fallback to team_id mapping for current season data
        team_id_mapping = self._get_team_id_owner_mapping()
        team_id = team_data.get('team_id')

        if team_id in team_id_mapping:
            return team_id_mapping[team_id]

        return "Unknown"

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
                CASE WHEN t.final_standing IS NOT NULL AND t.final_standing > 0 THEN t.final_standing ELSE t.standing END ASC
            LIMIT 3
            """

            champions_data = self._execute_query(champions_query, (year,))

            champions = []
            for i, team in enumerate(champions_data):
                place = i + 1
                owner_name = self._get_owner_name(team)

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
                    "final_standing": team['final_standing'] if team['final_standing'] is not None and team['final_standing'] > 0 else team['standing']
                })

            # Check if season is complete
            season_complete = all(team['final_standing'] is not None and team['final_standing'] > 0 for team in champions_data)

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
                    owner_name,
                    opponent_name,
                    luck_points as luck_score,
                    actual_score,
                    projected_score,
                    opponent_actual,
                    opponent_projected,
                    actual_margin,
                    projected_margin
                FROM luck_analysis_matchups
                WHERE ABS(luck_points) > 10
                ORDER BY ABS(luck_points) DESC
                LIMIT 20
                """
                top_matchups = self._execute_query(matchups_query)

                # Transform seasons data to match React component expectations
                def transform_season_data(season):
                    return {
                        "year": season['year'],
                        "team_name": season['team_name'],
                        "owner": season['owner_name'],
                        "total_luck": season['total_luck'],
                        "average_luck": season['average_luck'],
                        "games_played": season['games_played'],
                        "biggest_lucky_game": {
                            "week": season['biggest_lucky_week'],
                            "opponent": season['biggest_lucky_opponent'],
                            "luck": season['biggest_lucky_points']
                        } if season['biggest_lucky_week'] else None,
                        "biggest_unlucky_game": {
                            "week": season['biggest_unlucky_week'],
                            "opponent": season['biggest_unlucky_opponent'],
                            "luck": season['biggest_unlucky_points']
                        } if season['biggest_unlucky_week'] else None
                    }

                # Transform matchup data to match React component expectations
                def transform_matchup_data(matchup):
                    return {
                        "year": matchup['year'],
                        "week": matchup['week'],
                        "team_name": matchup['team_name'],
                        "owner": matchup['owner_name'] if matchup['owner_name'] else 'Unknown',
                        "opponent": matchup['opponent_name'],
                        "luck": matchup['luck_score'],
                        "actual_score": matchup['actual_score'],
                        "projected_score": matchup['projected_score'],
                        "opponent_actual": matchup['opponent_actual'],
                        "opponent_projected": matchup['opponent_projected'],
                        "actual_margin": matchup['actual_margin'],
                        "projected_margin": matchup['projected_margin']
                    }

                # Process seasons data to separate lucky vs unlucky
                all_seasons_transformed = [transform_season_data(s) for s in seasons_data]
                luckiest_seasons = [s for s in all_seasons_transformed if s['total_luck'] > 0][:3]
                unluckiest_seasons = sorted([s for s in all_seasons_transformed if s['total_luck'] < 0], key=lambda x: x['total_luck'])[:3]

                # Process matchups to separate lucky vs unlucky
                all_matchups_transformed = [transform_matchup_data(m) for m in top_matchups]
                luckiest_matchups = [m for m in all_matchups_transformed if m['luck'] > 0][:5]
                unluckiest_matchups = sorted([m for m in all_matchups_transformed if m['luck'] < 0], key=lambda x: x['luck'])[:5]

                # Count unique games analyzed (divide by 2 since each game has 2 records)
                unique_games_query = "SELECT COUNT(DISTINCT year || '-' || week || '-' || team_id || '-' || opponent_team_id) / 2 as count FROM luck_analysis_matchups"
                unique_games_count = self._execute_single(unique_games_query)
                total_games = int(unique_games_count['count']) if unique_games_count else 0

                # Get years analyzed from both tables (seasons and matchups)
                years_query = """
                SELECT DISTINCT year FROM (
                    SELECT year FROM luck_analysis_seasons
                    UNION
                    SELECT year FROM luck_analysis_matchups
                ) ORDER BY year
                """
                years_data = self._execute_query(years_query)
                years_analyzed = [row['year'] for row in years_data]

                return {
                    "luckiest_seasons": luckiest_seasons,
                    "unluckiest_seasons": unluckiest_seasons,
                    "luckiest_single_matchups": luckiest_matchups,
                    "unluckiest_single_matchups": unluckiest_matchups,
                    "total_seasons_analyzed": len(years_analyzed),
                    "total_games_analyzed": total_games,
                    "years_analyzed": years_analyzed,
                    "data_source": "database"
                }
            else:
                # No pre-calculated data available - return empty but properly structured data
                return {
                    "luckiest_seasons": [],
                    "unluckiest_seasons": [],
                    "luckiest_single_matchups": [],
                    "unluckiest_single_matchups": [],
                    "total_seasons_analyzed": 0,
                    "total_matchups_analyzed": 0,
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

    def get_streak_records(self, year: int = None) -> Dict[str, Any]:
        """Get winning and losing streak records from database"""
        try:
            # Base query to get all matchups with outcomes
            if year:
                years_filter = "WHERE m.year = ?"
                params = (year,)
                years_analyzed = [year]
            else:
                years_filter = ""
                params = ()
                # Get available years for streak analysis
                years_query = "SELECT DISTINCT year FROM matchups ORDER BY year"
                years_data = self._execute_query(years_query)
                years_analyzed = [row['year'] for row in years_data]

            # Respect the current_week for each season (championship week varies by year)
            if year:
                # Single year analysis - use that year's current_week
                current_week_query = "SELECT current_week FROM leagues WHERE year = ?"
                current_week_data = self._execute_single(current_week_query, (year,))
                if current_week_data and year == 2025:
                    # For current year (2025), only count completed weeks
                    current_week = current_week_data['current_week']
                    week_filter = f"AND m.week < {current_week}"
                elif current_week_data:
                    # For past years, include all weeks up to the season's final week
                    current_week = current_week_data['current_week']
                    week_filter = f"AND m.week <= {current_week}"
                else:
                    week_filter = ""
            else:
                # All-time analysis - respect each year's current_week
                week_filter = """AND EXISTS (
                    SELECT 1 FROM leagues l
                    WHERE l.year = m.year
                    AND (
                        (m.year = 2025 AND m.week < l.current_week) OR
                        (m.year < 2025 AND m.week <= l.current_week)
                    )
                )"""

            matchups_query = f"""
            SELECT
                m.year,
                m.week,
                m.home_team_id,
                m.away_team_id,
                m.home_score,
                m.away_score,
                ht.team_name as home_team_name,
                ht.owners as home_owners,
                at.team_name as away_team_name,
                at.owners as away_owners
            FROM matchups m
            JOIN teams ht ON m.home_team_id = ht.team_id AND m.year = ht.year
            JOIN teams at ON m.away_team_id = at.team_id AND m.year = at.year
            {years_filter}
            {week_filter}
            ORDER BY m.year, m.week
            """

            matchups_data = self._execute_query(matchups_query, params)

            # Process matchups into game results per owner
            owner_games = {}

            for matchup in matchups_data:
                # Parse owner names using hybrid ESPN ID / team_id resolution
                # Get team data for home and away teams to use with owner resolution
                home_team_data = {'team_id': matchup['home_team_id'], 'owners': None}
                away_team_data = {'team_id': matchup['away_team_id'], 'owners': None}

                # Try to get owners data for these teams from the same year
                owners_query = """
                SELECT team_id, owners FROM teams
                WHERE year = ? AND (team_id = ? OR team_id = ?)
                """
                owners_data = self._execute_query(owners_query, (matchup['year'], matchup['home_team_id'], matchup['away_team_id']))

                for team_data in owners_data:
                    if team_data['team_id'] == matchup['home_team_id']:
                        home_team_data['owners'] = team_data['owners']
                    elif team_data['team_id'] == matchup['away_team_id']:
                        away_team_data['owners'] = team_data['owners']

                home_owner = self._get_owner_name(home_team_data)
                away_owner = self._get_owner_name(away_team_data)

                # Determine winner/loser
                home_score = float(matchup['home_score'])
                away_score = float(matchup['away_score'])

                # Create game records
                home_game = {
                    'year': matchup['year'],
                    'week': matchup['week'],
                    'owner': home_owner,
                    'team_name': matchup['home_team_name'],
                    'opponent': away_owner,
                    'score': home_score,
                    'opponent_score': away_score,
                    'result': 'W' if home_score > away_score else 'L' if home_score < away_score else 'T'
                }

                away_game = {
                    'year': matchup['year'],
                    'week': matchup['week'],
                    'owner': away_owner,
                    'team_name': matchup['away_team_name'],
                    'opponent': home_owner,
                    'score': away_score,
                    'opponent_score': home_score,
                    'result': 'W' if away_score > home_score else 'L' if away_score < home_score else 'T'
                }

                # Add to owner games
                if home_owner not in owner_games:
                    owner_games[home_owner] = []
                if away_owner not in owner_games:
                    owner_games[away_owner] = []

                owner_games[home_owner].append(home_game)
                owner_games[away_owner].append(away_game)

            # Calculate streaks for each owner
            win_streaks = []
            loss_streaks = []
            current_streaks = []

            for owner, games in owner_games.items():
                # Sort games chronologically
                games.sort(key=lambda x: (x['year'], x['week']))

                # Calculate all streaks for this owner
                owner_win_streaks = []
                owner_loss_streaks = []

                current_streak_type = None
                current_streak_length = 0
                current_streak_start_idx = 0

                for i, game in enumerate(games):
                    if game['result'] in ['W', 'L']:  # Skip ties
                        if current_streak_type == game['result']:
                            # Continue current streak
                            current_streak_length += 1
                        else:
                            # End previous streak if it existed
                            if current_streak_type and current_streak_length > 0:
                                # Get streak games and team names
                                streak_games = games[current_streak_start_idx:current_streak_start_idx + current_streak_length]
                                team_names = list(set([g['team_name'] for g in streak_games]))

                                streak_record = {
                                    'owner': owner,
                                    'type': current_streak_type,
                                    'length': current_streak_length,
                                    'start_year': streak_games[0]['year'],
                                    'start_week': streak_games[0]['week'],
                                    'end_year': streak_games[-1]['year'],
                                    'end_week': streak_games[-1]['week'],
                                    'team_names': team_names,
                                    'games': streak_games,
                                    'is_current': False  # Not current unless it's the final streak
                                }

                                if current_streak_type == 'W':
                                    owner_win_streaks.append(streak_record)
                                else:
                                    owner_loss_streaks.append(streak_record)

                            # Start new streak
                            current_streak_type = game['result']
                            current_streak_length = 1
                            current_streak_start_idx = i

                # Handle final streak (this is the current streak)
                if current_streak_type and current_streak_length > 0:
                    # Get streak games and team names
                    streak_games = games[current_streak_start_idx:current_streak_start_idx + current_streak_length]
                    team_names = list(set([g['team_name'] for g in streak_games]))

                    streak_record = {
                        'owner': owner,
                        'type': current_streak_type,
                        'length': current_streak_length,
                        'start_year': streak_games[0]['year'],
                        'start_week': streak_games[0]['week'],
                        'end_year': streak_games[-1]['year'],
                        'end_week': streak_games[-1]['week'],
                        'team_names': team_names,
                        'games': streak_games,
                        'is_current': True  # Final streak is always current
                    }

                    if current_streak_type == 'W':
                        owner_win_streaks.append(streak_record)
                    else:
                        owner_loss_streaks.append(streak_record)

                    # Add to current streaks if 3+ games, only for all-time analysis, and owner is active
                    if not year and current_streak_length >= 3:
                        current_streaks.append(streak_record)

                # Add all streaks to main lists
                win_streaks.extend(owner_win_streaks)
                loss_streaks.extend(owner_loss_streaks)

            # Sort streaks by length
            win_streaks.sort(key=lambda x: x['length'], reverse=True)
            loss_streaks.sort(key=lambda x: x['length'], reverse=True)

            # Filter current streaks to only include active league participants (2025 season)
            if not year:  # Only for all-time analysis
                # Get current season participants from database
                active_owners_query = """
                SELECT DISTINCT owners
                FROM teams
                WHERE year = 2025
                """
                active_teams_data = self._execute_query(active_owners_query)

                active_owners = set()
                for team in active_teams_data:
                    owner_name = self._get_owner_name(team)
                    active_owners.add(owner_name)

                # Filter current streaks to only include active owners
                filtered_current_streaks = [
                    streak for streak in current_streaks
                    if streak['owner'] in active_owners
                ]
                current_streaks = filtered_current_streaks

            current_streaks.sort(key=lambda x: x['length'], reverse=True)

            return {
                "analysis_type": "single_season" if year else "all_time",
                "year": year,
                "years_analyzed": years_analyzed,
                "longest_win_streaks": win_streaks[:5],  # Top 5
                "longest_loss_streaks": loss_streaks[:5],  # Top 5
                "current_streaks": current_streaks,
                "total_games_analyzed": len(matchups_data)
            }

        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

    def get_team_legacy(self) -> Dict[str, Any]:
        """Get comprehensive team legacy data across all years"""
        try:
            # Get all team data across years
            teams_query = """
            SELECT
                t.year,
                t.team_id,
                t.team_name,
                t.owners,
                t.wins,
                t.losses,
                t.ties,
                t.points_for,
                t.points_against,
                t.standing,
                t.final_standing
            FROM teams t
            ORDER BY t.year, t.team_id
            """
            teams_data = self._execute_query(teams_query)

            # Get available years
            years_query = "SELECT DISTINCT year FROM teams ORDER BY year DESC"
            years_data = self._execute_query(years_query)
            available_years = [row['year'] for row in years_data]

            # Process team legacy data by owner
            team_legacy_data = {}

            for team in teams_data:
                # Extract owner name
                owner_name = self._get_owner_name(team)

                # Initialize owner data if not exists
                if owner_name not in team_legacy_data:
                    team_legacy_data[owner_name] = {
                        "owner": owner_name,
                        "team_names": [],
                        "years_active": [],
                        "placements": [],
                        "championship_years": [],
                        "runner_up_years": [],
                        "third_place_years": [],
                        "total_wins": 0,
                        "total_losses": 0,
                        "total_ties": 0,
                        "total_points_for": 0,
                        "total_points_against": 0,
                        "seasons_played": 0,
                        "completed_seasons": 0
                    }

                # Add data for this year
                team_data = team_legacy_data[owner_name]
                team_data["team_names"].append({"name": team['team_name'], "year": team['year']})
                team_data["years_active"].append(team['year'])

                # Use final_standing if available, otherwise regular standing
                placement = team['final_standing'] if team['final_standing'] and team['final_standing'] > 0 else team['standing']
                team_data["placements"].append({"year": team['year'], "placement": placement})

                team_data["total_wins"] += team['wins']
                team_data["total_losses"] += team['losses']
                team_data["total_ties"] += team['ties']
                team_data["total_points_for"] += team['points_for']
                team_data["total_points_against"] += team['points_against']
                team_data["seasons_played"] += 1

                # Track championships
                if placement == 1:
                    team_data["championship_years"].append(team['year'])
                elif placement == 2:
                    team_data["runner_up_years"].append(team['year'])
                elif placement == 3:
                    team_data["third_place_years"].append(team['year'])

                # Count completed seasons (not current year)
                if team['year'] < 2025:
                    team_data["completed_seasons"] += 1

            # Calculate legacy rankings and additional stats
            legacy_rankings = []
            for owner_name, data in team_legacy_data.items():
                # Calculate additional metrics
                championships = len(data["championship_years"])
                runner_ups = len(data["runner_up_years"])
                third_places = len(data["third_place_years"])

                # Legacy score calculation
                legacy_score = (championships * 50) + (runner_ups * 30) + (third_places * 15) + data["total_wins"]

                # Win percentage
                total_games = data["total_wins"] + data["total_losses"] + data["total_ties"]
                win_percentage = (data["total_wins"] / total_games * 100) if total_games > 0 else 0

                # Points per game
                points_per_game = (data["total_points_for"] / total_games) if total_games > 0 else 0

                # Calculate current_team_name and aka_names
                data["team_names"].sort(key=lambda x: x["year"], reverse=True)
                unique_names = []
                seen_names = set()
                for name_entry in data["team_names"]:
                    if name_entry["name"] not in seen_names:
                        unique_names.append(name_entry["name"])
                        seen_names.add(name_entry["name"])

                current_team_name = unique_names[0] if unique_names else "Unknown"
                aka_names = unique_names[1:] if len(unique_names) > 1 else []

                # Calculate average placement and has_placement_history
                completed_placements = [p for p in data["placements"] if p["year"] < 2025]
                if len(completed_placements) > 0:
                    average_placement = sum(p["placement"] for p in completed_placements) / len(completed_placements)
                    has_placement_history = True
                else:
                    average_placement = None
                    has_placement_history = False

                # Calculate gap years (years not active) - include current year
                if available_years:
                    min_year = min(available_years)
                    max_year = max(available_years)
                    all_years = set(range(min_year, max_year + 1))
                    active_years = set(data["years_active"])
                    gap_years = sorted(list(all_years - active_years), reverse=True)
                else:
                    gap_years = []

                legacy_rankings.append({
                    **data,
                    "championships": championships,
                    "runner_ups": runner_ups,
                    "third_places": third_places,
                    "legacy_score": legacy_score,
                    "win_percentage": round(win_percentage, 1),
                    "avg_points_per_game": round(points_per_game, 2),
                    "total_games": total_games,
                    "current_team_name": current_team_name,
                    "aka_names": aka_names,
                    "has_placement_history": has_placement_history,
                    "average_placement": round(average_placement, 2) if average_placement is not None else None,
                    "gap_years": gap_years
                })

            # Sort by placement history first (teams with history come first), then by average placement
            # Teams with no placement history go to the bottom regardless of average placement
            legacy_rankings.sort(key=lambda x: (not x["has_placement_history"], x["average_placement"] or float('inf')))

            return {
                "total_teams": len(legacy_rankings),
                "years_analyzed": available_years,
                "team_legacy": legacy_rankings
            }

        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

    def _extract_owner_name(self, owners_data):
        """Helper method to extract owner name from JSON data"""
        if owners_data and len(owners_data) > 0:
            owner_data = owners_data[0]
            if 'firstName' in owner_data and 'lastName' in owner_data:
                return f"{owner_data['firstName']} {owner_data['lastName']}".strip()
            else:
                return owner_data.get('displayName', 'Unknown')
        return "Unknown"