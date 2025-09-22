"""
Incremental Database Update System
Updates only new/changed data without full re-import
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from espn_api.football import League
from database import get_database, FFDatabase
from import_espn_data import ESPNDataImporter

# ESPN API Configuration
LEAGUE_ID = int(os.getenv('LEAGUE_ID', '0'))
ESPN_S2 = os.getenv('ESPN_S2', '')
SWID = os.getenv('SWID', '')

class DatabaseUpdater:
    def __init__(self):
        self.db = get_database()
        self.importer = ESPNDataImporter()
        self.current_year = 2025

    def daily_update(self):
        """Run daily database updates"""
        print("🔄 Starting daily database update")
        log_id = self.db.log_import_start('daily')

        try:
            updates_made = 0

            # Update current season data
            updates_made += self.update_current_season()

            # Update player performances for current week
            updates_made += self.update_current_week_performances()

            # Update team stats and standings
            updates_made += self.update_team_standings()

            # Update recent activities
            updates_made += self.update_recent_activities()

            # Recalculate analytics if significant changes
            if updates_made > 10:
                print("🧮 Recalculating analytics due to significant changes")
                self.recalculate_analytics()

            self.db.log_import_complete(log_id, updates_made)
            print(f"✅ Daily update completed - {updates_made} records updated")
            return updates_made

        except Exception as e:
            self.db.log_import_error(log_id, str(e))
            print(f"❌ Daily update failed: {e}")
            raise

    def update_current_season(self):
        """Update current season basic data"""
        print("  Updating current season data")

        try:
            league = League(league_id=LEAGUE_ID, year=self.current_year, espn_s2=ESPN_S2, swid=SWID)

            # Update league info
            league_data = {
                'year': self.current_year,
                'league_id': league.league_id if hasattr(league, 'league_id') else LEAGUE_ID,
                'name': getattr(league, 'name', None),
                'current_week': getattr(league, 'current_week', None),
                'nfl_week': getattr(league, 'nfl_week', None),
                'total_teams': len(league.teams) if hasattr(league, 'teams') else None,
                'updated_at': datetime.utcnow().isoformat()
            }

            self.db.execute_insert('leagues', league_data)
            return 1

        except Exception as e:
            print(f"    Error updating current season: {e}")
            return 0

    def update_current_week_performances(self):
        """Update player performances for the current week"""
        print("  Updating current week player performances")

        try:
            league = League(league_id=LEAGUE_ID, year=self.current_year, espn_s2=ESPN_S2, swid=SWID)
            current_week = getattr(league, 'current_week', 1)

            # Check if we already have data for this week
            existing_data = self.db.execute_query(
                "SELECT COUNT(*) FROM player_performances WHERE year = ? AND week = ?",
                (self.current_year, current_week)
            )

            if existing_data and existing_data[0][0] > 0:
                print(f"    Week {current_week} data already exists, updating...")

            # Get box scores for current week
            try:
                box_scores = league.box_scores(current_week)
                if not box_scores:
                    print(f"    No box scores available for week {current_week}")
                    return 0

                player_performances_data = []
                players_seen = set()

                for box_score in box_scores:
                    if not (hasattr(box_score, 'home_team') and hasattr(box_score, 'away_team')):
                        continue

                    # Update box score record - use UPDATE or INSERT based on existence
                    existing_box_score = self.db.execute_query(
                        "SELECT id FROM box_scores WHERE year = ? AND week = ? AND home_team_id = ? AND away_team_id = ?",
                        (self.current_year, current_week, box_score.home_team.team_id, box_score.away_team.team_id)
                    )

                    box_score_data = {
                        'year': self.current_year,
                        'week': current_week,
                        'home_team_id': box_score.home_team.team_id,
                        'away_team_id': box_score.away_team.team_id,
                        'home_score': getattr(box_score, 'home_score', 0),
                        'home_projected': getattr(box_score, 'home_projected', 0),
                        'away_score': getattr(box_score, 'away_score', 0),
                        'away_projected': getattr(box_score, 'away_projected', 0),
                        'is_playoff': getattr(box_score, 'is_playoff', False),
                        'matchup_type': getattr(box_score, 'matchup_type', 'NONE')
                    }

                    if existing_box_score and len(existing_box_score) > 0:
                        # Update existing record
                        box_score_id = existing_box_score[0][0]
                        self.db.execute_query(
                            """UPDATE box_scores SET
                               home_score = ?, home_projected = ?, away_score = ?, away_projected = ?,
                               is_playoff = ?, matchup_type = ?
                               WHERE id = ?""",
                            (box_score_data['home_score'], box_score_data['home_projected'],
                             box_score_data['away_score'], box_score_data['away_projected'],
                             box_score_data['is_playoff'], box_score_data['matchup_type'], box_score_id)
                        )
                    else:
                        # Insert new record
                        self.db.execute_insert('box_scores', box_score_data)

                    # Update player performances
                    for lineup_type, lineup in [('home', getattr(box_score, 'home_lineup', [])), ('away', getattr(box_score, 'away_lineup', []))]:
                        team_id = box_score.home_team.team_id if lineup_type == 'home' else box_score.away_team.team_id

                        for player in lineup:
                            if hasattr(player, 'playerId'):
                                # Update player info if not seen recently
                                if player.playerId not in players_seen:
                                    player_data = {
                                        'player_id': player.playerId,
                                        'name': getattr(player, 'name', ''),
                                        'position': getattr(player, 'position', None),
                                        'pro_team': getattr(player, 'proTeam', None),
                                        'injury_status': getattr(player, 'injuryStatus', None),
                                        'injured': getattr(player, 'injured', False),
                                        'updated_at': datetime.utcnow().isoformat()
                                    }
                                    self.db.execute_insert('players', player_data)
                                    players_seen.add(player.playerId)

                                # Update/insert player performance
                                performance_data = {
                                    'player_id': player.playerId,
                                    'year': self.current_year,
                                    'week': current_week,
                                    'team_id': team_id,
                                    'slot_position': getattr(player, 'slot_position', None),
                                    'points': getattr(player, 'points', 0),
                                    'projected_points': getattr(player, 'projected_points', 0),
                                    'pro_opponent': getattr(player, 'pro_opponent', None),
                                    'game_played': getattr(player, 'game_played', 0),
                                    'on_bye_week': getattr(player, 'on_bye_week', False)
                                }
                                player_performances_data.append(performance_data)

                if player_performances_data:
                    self.db.execute_many_inserts('player_performances', player_performances_data)

                return len(player_performances_data)

            except Exception as e:
                print(f"    Box scores not available for week {current_week}: {e}")
                return 0

        except Exception as e:
            print(f"    Error updating current week: {e}")
            return 0

    def update_team_standings(self):
        """Update team records and standings"""
        print("  Updating team standings and records")

        try:
            league = League(league_id=LEAGUE_ID, year=self.current_year, espn_s2=ESPN_S2, swid=SWID)

            teams_updated = 0
            for team in league.teams:
                team_data = {
                    'team_id': team.team_id,
                    'year': self.current_year,
                    'team_name': team.team_name,
                    'wins': team.wins,
                    'losses': team.losses,
                    'ties': getattr(team, 'ties', 0),
                    'points_for': team.points_for,
                    'points_against': team.points_against,
                    'standing': getattr(team, 'standing', None),
                    'streak_type': getattr(team, 'streak_type', None),
                    'streak_length': getattr(team, 'streak_length', 0),
                    'playoff_pct': getattr(team, 'playoff_pct', None)
                }

                self.db.execute_insert('teams', team_data)
                teams_updated += 1

            return teams_updated

        except Exception as e:
            print(f"    Error updating team standings: {e}")
            return 0

    def update_recent_activities(self):
        """Update recent league activities"""
        print("  Updating recent activities")

        try:
            league = League(league_id=LEAGUE_ID, year=self.current_year, espn_s2=ESPN_S2, swid=SWID)

            # Get recent activities (last 50)
            activities = league.recent_activity(size=50)
            if not activities:
                return 0

            # Get the most recent activity date from database
            last_activity = self.db.execute_query(
                "SELECT MAX(date) FROM activities WHERE year = ?",
                (self.current_year,)
            )
            last_date = last_activity[0][0] if last_activity and last_activity[0][0] else 0

            new_activities = []
            for activity in activities:
                activity_date = getattr(activity, 'date', 0)
                if activity_date > last_date:
                    # Serialize actions carefully
                    actions = getattr(activity, 'actions', [])
                    serialized_actions = []

                    for action in actions:
                        if isinstance(action, tuple) and len(action) >= 2:
                            # Extract basic info without complex objects
                            serialized_action = {
                                'team_name': str(action[0]) if action[0] else None,
                                'action': str(action[1]) if len(action) > 1 else None,
                                'player_name': str(action[2]) if len(action) > 2 and hasattr(action[2], 'name') else None,
                                'bid_amount': action[3] if len(action) > 3 and isinstance(action[3], (int, float)) else None
                            }
                            serialized_actions.append(serialized_action)

                    activity_data = {
                        'year': self.current_year,
                        'date': activity_date,
                        'actions': serialized_actions
                    }
                    new_activities.append(activity_data)

            if new_activities:
                self.db.execute_many_inserts('activities', new_activities)

            return len(new_activities)

        except Exception as e:
            print(f"    Error updating activities: {e}")
            return 0

    def weekly_update(self):
        """Run weekly updates (more comprehensive)"""
        print("🔄 Starting weekly database update")
        log_id = self.db.log_import_start('weekly')

        try:
            updates_made = 0

            # Run daily updates first
            updates_made += self.daily_update()

            # Update draft data (in case of changes)
            updates_made += self.update_draft_data()

            # Full analytics recalculation
            print("🧮 Recalculating all analytics")
            self.recalculate_analytics()

            self.db.log_import_complete(log_id, updates_made)
            print(f"✅ Weekly update completed - {updates_made} records updated")

        except Exception as e:
            self.db.log_import_error(log_id, str(e))
            print(f"❌ Weekly update failed: {e}")
            raise

    def update_draft_data(self):
        """Update draft information for current year"""
        print("  Updating draft data")

        try:
            league = League(league_id=LEAGUE_ID, year=self.current_year, espn_s2=ESPN_S2, swid=SWID)

            if not hasattr(league, 'draft') or not league.draft:
                return 0

            draft_data = []
            for pick in league.draft:
                pick_data = {
                    'year': self.current_year,
                    'team_id': pick.team.team_id if hasattr(pick, 'team') and pick.team else None,
                    'player_id': getattr(pick, 'playerId', None),
                    'player_name': getattr(pick, 'playerName', None),
                    'round_num': getattr(pick, 'round_num', None),
                    'round_pick': getattr(pick, 'round_pick', None),
                    'bid_amount': getattr(pick, 'bid_amount', 0),
                    'keeper_status': getattr(pick, 'keeper_status', False)
                }
                draft_data.append(pick_data)

            if draft_data:
                self.db.execute_many_inserts('draft_picks', draft_data)

            return len(draft_data)

        except Exception as e:
            print(f"    Error updating draft data: {e}")
            return 0

    def recalculate_analytics(self):
        """Recalculate analytics tables"""
        print("  Recalculating luck analysis")
        self.recalculate_luck_analysis()

        print("  Recalculating team legacy")
        self.recalculate_team_legacy()

    def recalculate_luck_analysis(self):
        """Recalculate luck analysis from box scores"""
        try:
            # Clear existing data
            self.db.connection.execute("DELETE FROM luck_analysis_seasons")
            self.db.connection.execute("DELETE FROM luck_analysis_matchups")

            # Recalculate from box_scores table
            box_scores = self.db.execute_query("""
                SELECT bs.*,
                       ht.owners as home_owners, ht.team_name as home_name,
                       at.owners as away_owners, at.team_name as away_name
                FROM box_scores bs
                JOIN teams ht ON bs.home_team_id = ht.team_id AND bs.year = ht.year
                JOIN teams at ON bs.away_team_id = at.team_id AND bs.year = at.year
                ORDER BY year, week
            """)

            luck_data = {}  # team_id, year -> luck stats
            matchup_luck = []

            for row in box_scores:
                year, week = row['year'], row['week']

                # Calculate luck
                home_projected_margin = row['home_projected'] - row['away_projected']
                home_actual_margin = row['home_score'] - row['away_score']
                home_luck = home_actual_margin - home_projected_margin
                away_luck = -home_luck

                # Get owner names
                try:
                    home_owners = json.loads(row['home_owners']) if row['home_owners'] else []
                    away_owners = json.loads(row['away_owners']) if row['away_owners'] else []

                    home_owner = home_owners[0].get('displayName', f"Team_{row['home_team_id']}") if home_owners else f"Team_{row['home_team_id']}"
                    away_owner = away_owners[0].get('displayName', f"Team_{row['away_team_id']}") if away_owners else f"Team_{row['away_team_id']}"
                except:
                    home_owner = f"Team_{row['home_team_id']}"
                    away_owner = f"Team_{row['away_team_id']}"

                # Store matchup luck
                matchup_luck.append({
                    'year': year, 'week': week,
                    'team_id': row['home_team_id'], 'team_name': row['home_name'], 'owner_name': home_owner,
                    'opponent_team_id': row['away_team_id'], 'opponent_name': row['away_name'],
                    'luck_points': home_luck, 'actual_score': row['home_score'], 'projected_score': row['home_projected'],
                    'opponent_actual': row['away_score'], 'opponent_projected': row['away_projected'],
                    'actual_margin': home_actual_margin, 'projected_margin': home_projected_margin
                })

                matchup_luck.append({
                    'year': year, 'week': week,
                    'team_id': row['away_team_id'], 'team_name': row['away_name'], 'owner_name': away_owner,
                    'opponent_team_id': row['home_team_id'], 'opponent_name': row['home_name'],
                    'luck_points': away_luck, 'actual_score': row['away_score'], 'projected_score': row['away_projected'],
                    'opponent_actual': row['home_score'], 'opponent_projected': row['home_projected'],
                    'actual_margin': -home_actual_margin, 'projected_margin': -home_projected_margin
                })

                # Aggregate season luck
                for team_id, luck, owner, team_name in [(row['home_team_id'], home_luck, home_owner, row['home_name']),
                                                       (row['away_team_id'], away_luck, away_owner, row['away_name'])]:
                    key = (team_id, year)
                    if key not in luck_data:
                        luck_data[key] = {
                            'year': year, 'team_id': team_id, 'owner_name': owner, 'team_name': team_name,
                            'total_luck': 0, 'games_played': 0,
                            'biggest_lucky_week': 0, 'biggest_lucky_opponent': '', 'biggest_lucky_points': 0,
                            'biggest_unlucky_week': 0, 'biggest_unlucky_opponent': '', 'biggest_unlucky_points': 0
                        }

                    luck_data[key]['total_luck'] += luck
                    luck_data[key]['games_played'] += 1

                    if luck > luck_data[key]['biggest_lucky_points']:
                        luck_data[key]['biggest_lucky_points'] = luck
                        luck_data[key]['biggest_lucky_week'] = week
                        luck_data[key]['biggest_lucky_opponent'] = row['away_name'] if team_id == row['home_team_id'] else row['home_name']

                    if luck < luck_data[key]['biggest_unlucky_points']:
                        luck_data[key]['biggest_unlucky_points'] = luck
                        luck_data[key]['biggest_unlucky_week'] = week
                        luck_data[key]['biggest_unlucky_opponent'] = row['away_name'] if team_id == row['home_team_id'] else row['home_name']

            # Insert season luck data
            season_luck_data = []
            for data in luck_data.values():
                data['average_luck'] = data['total_luck'] / data['games_played'] if data['games_played'] > 0 else 0
                season_luck_data.append(data)

            if season_luck_data:
                self.db.execute_many_inserts('luck_analysis_seasons', season_luck_data)

            if matchup_luck:
                self.db.execute_many_inserts('luck_analysis_matchups', matchup_luck)

        except Exception as e:
            print(f"    Error recalculating luck analysis: {e}")

    def recalculate_team_legacy(self):
        """Recalculate team legacy rankings"""
        try:
            # Clear existing data
            self.db.connection.execute("DELETE FROM team_legacy")

            # Aggregate team performance across years
            teams_data = self.db.execute_query("""
                SELECT team_id, year, owners, team_name, wins, losses, ties, points_for, standing, final_standing
                FROM teams
                ORDER BY year
            """)

            legacy_data = {}  # owner -> legacy stats

            for row in teams_data:
                try:
                    owners = json.loads(row['owners']) if row['owners'] else []
                    owner_name = owners[0].get('displayName', f"Team_{row['team_id']}") if owners else f"Team_{row['team_id']}"
                except:
                    owner_name = f"Team_{row['team_id']}"

                if owner_name not in legacy_data:
                    legacy_data[owner_name] = {
                        'owner_name': owner_name,
                        'team_names': set(),
                        'total_seasons': 0,
                        'championships': 0,
                        'total_wins': 0,
                        'total_losses': 0,
                        'total_ties': 0,
                        'total_points': 0,
                        'placements': [],
                        'years_participated': []
                    }

                data = legacy_data[owner_name]
                data['team_names'].add(row['team_name'])
                data['total_seasons'] += 1
                data['total_wins'] += row['wins'] or 0
                data['total_losses'] += row['losses'] or 0
                data['total_ties'] += row['ties'] or 0
                data['total_points'] += row['points_for'] or 0
                data['years_participated'].append(row['year'])

                final_standing = row['final_standing'] or row['standing']
                if final_standing:
                    data['placements'].append(final_standing)
                    if final_standing == 1:
                        data['championships'] += 1

            # Calculate averages and format for database
            final_legacy_data = []
            for owner, data in legacy_data.items():
                avg_placement = sum(data['placements']) / len(data['placements']) if data['placements'] else 0

                legacy_record = {
                    'owner_name': owner,
                    'team_names': list(data['team_names']),
                    'total_seasons': data['total_seasons'],
                    'championships': data['championships'],
                    'total_wins': data['total_wins'],
                    'total_losses': data['total_losses'],
                    'total_ties': data['total_ties'],
                    'total_points': data['total_points'],
                    'average_placement': avg_placement,
                    'best_season_placement': min(data['placements']) if data['placements'] else None,
                    'worst_season_placement': max(data['placements']) if data['placements'] else None,
                    'years_participated': data['years_participated']
                }
                final_legacy_data.append(legacy_record)

            if final_legacy_data:
                self.db.execute_many_inserts('team_legacy', final_legacy_data)

        except Exception as e:
            print(f"    Error recalculating team legacy: {e}")

def main():
    """Main update function"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'weekly':
        updater = DatabaseUpdater()
        updater.weekly_update()
    else:
        updater = DatabaseUpdater()
        updater.daily_update()

if __name__ == "__main__":
    main()