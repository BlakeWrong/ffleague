"""
Complete ESPN Fantasy Football Data Import Script
Imports ALL historical data from ESPN API into local database for fast queries
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from espn_api.football import League
from database import get_database, FFDatabase

# ESPN API Configuration
LEAGUE_ID = int(os.getenv('LEAGUE_ID', '0'))

class ESPNDataImporter:
    def __init__(self):
        self.db = get_database()
        self.stats = {
            'leagues_imported': 0,
            'teams_imported': 0,
            'players_imported': 0,
            'matchups_imported': 0,
            'box_scores_imported': 0,
            'player_performances_imported': 0,
            'draft_picks_imported': 0,
            'activities_imported': 0
        }

    def import_all_data(self, start_year: int = 2019, end_year: int = 2025):
        """Import all historical data from ESPN API"""
        print(f"Starting full import from {start_year} to {end_year}")
        log_id = self.db.log_import_start('full', 'all_tables')

        try:
            # Get available years from ESPN
            current_league = League(league_id=LEAGUE_ID, year=end_year)
            available_years = [end_year]

            if hasattr(current_league, 'previousSeasons') and current_league.previousSeasons:
                for season in current_league.previousSeasons:
                    try:
                        year = int(season)
                        if start_year <= year <= end_year:
                            available_years.append(year)
                    except ValueError:
                        continue

            available_years = sorted(set(available_years))
            print(f"Available years: {available_years}")

            # Import data for each year
            for year in available_years:
                print(f"\n=== Importing {year} Season ===")
                self.import_year_data(year)

            # Calculate analytics after all data is imported
            print(f"\n=== Calculating Analytics ===")
            self.calculate_analytics()

            # Log completion
            total_imported = sum(self.stats.values())
            self.db.log_import_complete(log_id, total_imported)
            print(f"\n✅ Import completed successfully!")
            print(f"Total records imported: {total_imported}")
            self.print_stats()

        except Exception as e:
            self.db.log_import_error(log_id, str(e))
            print(f"❌ Import failed: {e}")
            raise

    def import_year_data(self, year: int):
        """Import all data for a specific year"""
        try:
            league = League(league_id=LEAGUE_ID, year=year)

            # Import core league data
            self.import_league_data(league, year)
            self.import_league_settings(league, year)
            self.import_teams(league, year)

            # Import draft data (if available)
            self.import_draft_data(league, year)

            # Import matchup and player data
            self.import_matchups_and_players(league, year)

            # Import activities (if available)
            self.import_activities(league, year)

        except Exception as e:
            print(f"Error importing {year} data: {e}")
            raise

    def import_league_data(self, league: League, year: int):
        """Import league information"""
        print(f"  Importing league data for {year}")

        league_data = {
            'year': year,
            'league_id': league.league_id if hasattr(league, 'league_id') else LEAGUE_ID,
            'name': getattr(league, 'name', None),
            'current_week': getattr(league, 'current_week', None),
            'nfl_week': getattr(league, 'nfl_week', None),
            'total_teams': len(league.teams) if hasattr(league, 'teams') else None,
            'previousSeasons': getattr(league, 'previousSeasons', [])
        }

        self.db.execute_insert('leagues', league_data)
        self.stats['leagues_imported'] += 1

    def import_league_settings(self, league: League, year: int):
        """Import league settings"""
        if not hasattr(league, 'settings') or not league.settings:
            return

        print(f"  Importing league settings for {year}")
        settings = league.settings

        settings_data = {
            'year': year,
            'reg_season_count': getattr(settings, 'reg_season_count', None),
            'veto_votes_required': getattr(settings, 'veto_votes_required', None),
            'team_count': getattr(settings, 'team_count', None),
            'playoff_team_count': getattr(settings, 'playoff_team_count', None),
            'keeper_count': getattr(settings, 'keeper_count', None),
            'trade_deadline': getattr(settings, 'trade_deadline', None),
            'name': getattr(settings, 'name', None),
            'tie_rule': getattr(settings, 'tie_rule', None),
            'playoff_tie_rule': getattr(settings, 'playoff_tie_rule', None),
            'playoff_seed_tie_rule': getattr(settings, 'playoff_seed_tie_rule', None),
            'playoff_matchup_period_length': getattr(settings, 'playoff_matchup_period_length', None),
            'faab': getattr(settings, 'faab', None),
            'acquisition_budget': getattr(settings, 'acquisition_budget', None),
            'scoring_format': getattr(settings, 'scoring_format', [])
        }

        self.db.execute_insert('league_settings', settings_data)

    def import_teams(self, league: League, year: int):
        """Import team data"""
        print(f"  Importing teams for {year}")

        teams_data = []
        for team in league.teams:
            team_data = {
                'team_id': team.team_id,
                'year': year,
                'team_abbrev': getattr(team, 'team_abbrev', None),
                'team_name': team.team_name,
                'division_id': getattr(team, 'division_id', None),
                'division_name': getattr(team, 'division_name', None),
                'wins': team.wins,
                'losses': team.losses,
                'ties': getattr(team, 'ties', 0),
                'points_for': team.points_for,
                'points_against': team.points_against,
                'waiver_rank': getattr(team, 'waiver_rank', None),
                'acquisitions': getattr(team, 'acquisitions', 0),
                'acquisition_budget_spent': getattr(team, 'acquisition_budget_spent', 0),
                'drops': getattr(team, 'drops', 0),
                'trades': getattr(team, 'trades', 0),
                'move_to_ir': getattr(team, 'move_to_ir', 0),
                'owners': getattr(team, 'owners', []),
                'stats': getattr(team, 'stats', {}),
                'streak_type': getattr(team, 'streak_type', None),
                'streak_length': getattr(team, 'streak_length', 0),
                'standing': getattr(team, 'standing', None),
                'final_standing': getattr(team, 'final_standing', None),
                'draft_projected_rank': getattr(team, 'draft_projected_rank', None),
                'playoff_pct': getattr(team, 'playoff_pct', None),
                'logo_url': getattr(team, 'logo_url', None),
                'schedule': [t.team_id if hasattr(t, 'team_id') else str(t) for t in getattr(team, 'schedule', [])],
                'scores': getattr(team, 'scores', []),
                'outcomes': getattr(team, 'outcomes', [])
            }
            teams_data.append(team_data)

        self.db.execute_many_inserts('teams', teams_data)
        self.stats['teams_imported'] += len(teams_data)

    def import_draft_data(self, league: League, year: int):
        """Import draft picks"""
        if not hasattr(league, 'draft') or not league.draft:
            return

        print(f"  Importing draft data for {year}")

        draft_data = []
        for pick in league.draft:
            pick_data = {
                'year': year,
                'team_id': pick.team.team_id if hasattr(pick, 'team') and pick.team else None,
                'player_id': getattr(pick, 'playerId', None),
                'player_name': getattr(pick, 'playerName', None),
                'round_num': getattr(pick, 'round_num', None),
                'round_pick': getattr(pick, 'round_pick', None),
                'bid_amount': getattr(pick, 'bid_amount', 0),
                'keeper_status': getattr(pick, 'keeper_status', False),
                'nominating_team_id': pick.nominatingTeam.team_id if hasattr(pick, 'nominatingTeam') and pick.nominatingTeam else None
            }
            draft_data.append(pick_data)

        self.db.execute_many_inserts('draft_picks', draft_data)
        self.stats['draft_picks_imported'] += len(draft_data)

    def import_matchups_and_players(self, league: League, year: int):
        """Import matchups, box scores, and player performances"""
        print(f"  Importing matchups and player data for {year}")

        # Determine max week based on year
        if year < 2025:
            max_week = 17
        else:
            max_week = league.current_week if hasattr(league, 'current_week') and league.current_week else 17

        matchups_data = []
        box_scores_data = []
        player_performances_data = []
        players_seen = set()

        for week in range(1, max_week + 1):
            try:
                # Try to get box scores (more detailed)
                try:
                    box_scores = league.box_scores(week)
                    if box_scores:
                        for box_score in box_scores:
                            # Import box score
                            if hasattr(box_score, 'home_team') and hasattr(box_score, 'away_team'):
                                if hasattr(box_score.home_team, 'team_id') and hasattr(box_score.away_team, 'team_id'):
                                    box_score_data = {
                                        'year': year,
                                        'week': week,
                                        'home_team_id': box_score.home_team.team_id,
                                        'away_team_id': box_score.away_team.team_id,
                                        'home_score': getattr(box_score, 'home_score', 0),
                                        'home_projected': getattr(box_score, 'home_projected', 0),
                                        'away_score': getattr(box_score, 'away_score', 0),
                                        'away_projected': getattr(box_score, 'away_projected', 0),
                                        'is_playoff': getattr(box_score, 'is_playoff', False),
                                        'matchup_type': getattr(box_score, 'matchup_type', 'NONE')
                                    }
                                    box_scores_data.append(box_score_data)

                                    # Also create basic matchup record
                                    matchup_data = {
                                        'year': year,
                                        'week': week,
                                        'home_team_id': box_score.home_team.team_id,
                                        'away_team_id': box_score.away_team.team_id,
                                        'home_score': getattr(box_score, 'home_score', 0),
                                        'away_score': getattr(box_score, 'away_score', 0),
                                        'is_playoff': getattr(box_score, 'is_playoff', False),
                                        'matchup_type': getattr(box_score, 'matchup_type', 'NONE')
                                    }
                                    matchups_data.append(matchup_data)

                                    # Import player performances from lineups
                                    for lineup_type, lineup in [('home', getattr(box_score, 'home_lineup', [])), ('away', getattr(box_score, 'away_lineup', []))]:
                                        team_id = box_score.home_team.team_id if lineup_type == 'home' else box_score.away_team.team_id

                                        for player in lineup:
                                            if hasattr(player, 'playerId'):
                                                # Add to players table if not seen
                                                if player.playerId not in players_seen:
                                                    player_data = {
                                                        'player_id': player.playerId,
                                                        'name': getattr(player, 'name', ''),
                                                        'pos_rank': getattr(player, 'posRank', None),
                                                        'eligible_slots': getattr(player, 'eligibleSlots', []),
                                                        'acquisition_type': getattr(player, 'acquisitionType', None),
                                                        'pro_team': getattr(player, 'proTeam', None),
                                                        'position': getattr(player, 'position', None),
                                                        'injury_status': getattr(player, 'injuryStatus', None),
                                                        'injured': getattr(player, 'injured', False),
                                                        'total_points': getattr(player, 'total_points', None),
                                                        'avg_points': getattr(player, 'avg_points', None),
                                                        'projected_total_points': getattr(player, 'projected_total_points', None),
                                                        'projected_avg_points': getattr(player, 'projected_avg_points', None),
                                                        'percent_owned': getattr(player, 'percent_owned', None),
                                                        'percent_started': getattr(player, 'percent_started', None)
                                                    }
                                                    self.db.execute_insert('players', player_data)
                                                    players_seen.add(player.playerId)
                                                    self.stats['players_imported'] += 1

                                                # Add player performance
                                                performance_data = {
                                                    'player_id': player.playerId,
                                                    'year': year,
                                                    'week': week,
                                                    'team_id': team_id,
                                                    'lineup_slot': getattr(player, 'lineupSlot', None),
                                                    'slot_position': getattr(player, 'slot_position', None),
                                                    'on_team_id': getattr(player, 'onTeamId', team_id),
                                                    'schedule': getattr(player, 'schedule', {}),
                                                    'stats': getattr(player, 'stats', {}),
                                                    'points': getattr(player, 'points', 0),
                                                    'projected_points': getattr(player, 'projected_points', 0),
                                                    'pro_opponent': getattr(player, 'pro_opponent', None),
                                                    'pro_pos_rank': getattr(player, 'pro_pos_rank', None),
                                                    'game_played': getattr(player, 'game_played', 0),
                                                    'game_date': str(getattr(player, 'game_date', '')) if hasattr(player, 'game_date') else None,
                                                    'on_bye_week': getattr(player, 'on_bye_week', False),
                                                    'active_status': getattr(player, 'active_status', None)
                                                }
                                                player_performances_data.append(performance_data)

                except Exception as box_error:
                    print(f"    Box scores not available for {year} week {week}: {box_error}")

                    # Fall back to basic scoreboard if box scores fail
                    try:
                        scoreboard = league.scoreboard(week)
                        if scoreboard:
                            for matchup in scoreboard:
                                if hasattr(matchup, 'home_team') and hasattr(matchup, 'away_team'):
                                    if hasattr(matchup.home_team, 'team_id') and hasattr(matchup.away_team, 'team_id'):
                                        matchup_data = {
                                            'year': year,
                                            'week': week,
                                            'home_team_id': matchup.home_team.team_id,
                                            'away_team_id': matchup.away_team.team_id,
                                            'home_score': getattr(matchup, 'home_score', 0),
                                            'away_score': getattr(matchup, 'away_score', 0),
                                            'is_playoff': getattr(matchup, 'is_playoff', False),
                                            'matchup_type': getattr(matchup, 'matchup_type', 'NONE')
                                        }
                                        matchups_data.append(matchup_data)
                    except Exception as scoreboard_error:
                        print(f"    Scoreboard also failed for {year} week {week}: {scoreboard_error}")

            except Exception as week_error:
                print(f"    Error processing {year} week {week}: {week_error}")
                continue

        # Bulk insert all data
        if matchups_data:
            self.db.execute_many_inserts('matchups', matchups_data)
            self.stats['matchups_imported'] += len(matchups_data)

        if box_scores_data:
            self.db.execute_many_inserts('box_scores', box_scores_data)
            self.stats['box_scores_imported'] += len(box_scores_data)

        if player_performances_data:
            self.db.execute_many_inserts('player_performances', player_performances_data)
            self.stats['player_performances_imported'] += len(player_performances_data)

    def import_activities(self, league: League, year: int):
        """Import league activities (if available)"""
        try:
            activities = league.recent_activity(size=1000)  # Get lots of activities
            if activities:
                print(f"  Importing {len(activities)} activities for {year}")

                activities_data = []
                for activity in activities:
                    activity_data = {
                        'year': year,
                        'date': getattr(activity, 'date', 0),
                        'actions': getattr(activity, 'actions', [])
                    }
                    activities_data.append(activity_data)

                self.db.execute_many_inserts('activities', activities_data)
                self.stats['activities_imported'] += len(activities_data)

        except Exception as e:
            print(f"  Activities not available for {year}: {e}")

    def calculate_analytics(self):
        """Calculate and store analytics data"""
        print("Calculating streak records...")
        self.calculate_streak_records()

        print("Calculating luck analysis...")
        self.calculate_luck_analysis()

        print("Calculating team legacy...")
        self.calculate_team_legacy()

        print("Calculating championships...")
        self.calculate_championships()

    def calculate_streak_records(self):
        """Calculate winning and losing streaks"""
        # This would be a complex calculation - for now, we'll leave it to be calculated on-demand
        # or implement separately
        pass

    def calculate_luck_analysis(self):
        """Calculate luck analysis from box scores"""
        # Query box scores and calculate luck metrics
        # Store in luck_analysis_seasons and luck_analysis_matchups tables
        pass

    def calculate_team_legacy(self):
        """Calculate team legacy rankings"""
        # Aggregate team performance across all years
        # Store in team_legacy table
        pass

    def calculate_championships(self):
        """Calculate championship history"""
        # Determine champions and store in championships table
        pass

    def print_stats(self):
        """Print import statistics"""
        print("\n📊 Import Statistics:")
        for key, value in self.stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

def main():
    """Main import function"""
    print("🚀 Starting ESPN Fantasy Football Data Import")

    # Validate environment variables
    if not LEAGUE_ID:
        print("❌ Missing required environment variable: LEAGUE_ID")
        return

    # Initialize database
    db = get_database()
    db.initialize_schema()

    # Run import
    importer = ESPNDataImporter()
    importer.import_all_data()

if __name__ == "__main__":
    main()