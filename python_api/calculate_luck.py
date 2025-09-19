#!/usr/bin/env python3
"""
Luck Analysis Calculator
Calculates luck scores for all matchups and populates luck analysis tables
"""

import sqlite3
import json
from typing import Dict, List, Any

def get_connection():
    """Get database connection"""
    import os
    # Check for database in parent directory first, then current directory
    parent_db = os.path.join(os.path.dirname(__file__), "..", "fantasy_football.db")
    current_db = "fantasy_football.db"

    if os.path.exists(parent_db):
        return sqlite3.connect(parent_db)
    else:
        return sqlite3.connect(current_db)

def calculate_luck_for_matchup(actual_score: float, projected_score: float,
                              opponent_actual: float, opponent_projected: float) -> float:
    """
    Calculate luck score for a single matchup
    Positive = lucky, Negative = unlucky
    """
    # How much better/worse you did vs projection
    your_variance = actual_score - projected_score

    # How much better/worse opponent did vs projection
    opponent_variance = opponent_actual - opponent_projected

    # Your luck is your outperformance minus opponent's outperformance
    luck_score = your_variance - opponent_variance

    return luck_score

def populate_luck_analysis():
    """Calculate and populate luck analysis tables"""
    with get_connection() as conn:
        cursor = conn.cursor()

        print("🍀 Starting luck analysis calculation...")

        # Clear existing luck analysis data
        cursor.execute("DELETE FROM luck_analysis_matchups")
        cursor.execute("DELETE FROM luck_analysis_seasons")

        # Get all matchups with scores and projections
        matchups_query = """
        SELECT
            m.year,
            m.week,
            m.home_team_id,
            m.away_team_id,
            m.home_score,
            m.away_score,
            ht.team_name as home_team_name,
            at.team_name as away_team_name,
            ht.owners as home_owners,
            at.owners as away_owners,
            bs.home_projected,
            bs.away_projected
        FROM matchups m
        JOIN teams ht ON m.home_team_id = ht.team_id AND m.year = ht.year
        JOIN teams at ON m.away_team_id = at.team_id AND m.year = at.year
        JOIN box_scores bs ON m.year = bs.year AND m.week = bs.week
            AND m.home_team_id = bs.home_team_id AND m.away_team_id = bs.away_team_id
        WHERE bs.home_projected > 0 AND bs.away_projected > 0
        ORDER BY m.year, m.week
        """

        matchups = cursor.execute(matchups_query).fetchall()

        luck_matchups = []

        for matchup in matchups:
            (year, week, home_team_id, away_team_id, home_score, away_score,
             home_team_name, away_team_name, home_owners, away_owners,
             home_projected, away_projected) = matchup

            # Parse owner names
            def get_owner_name(owners_json):
                try:
                    owners = json.loads(owners_json) if owners_json else []
                    if owners and len(owners) > 0:
                        owner = owners[0]
                        if 'firstName' in owner and 'lastName' in owner:
                            return f"{owner['firstName']} {owner['lastName']}".strip()
                        else:
                            return owner.get('displayName', 'Unknown')
                    return 'Unknown'
                except:
                    return 'Unknown'

            home_owner = get_owner_name(home_owners)
            away_owner = get_owner_name(away_owners)

            # Calculate luck for home team
            home_luck = calculate_luck_for_matchup(
                home_score, home_projected, away_score, away_projected
            )

            # Calculate luck for away team (inverse)
            away_luck = calculate_luck_for_matchup(
                away_score, away_projected, home_score, home_projected
            )

            # Store both perspectives with all required fields
            luck_matchups.extend([
                (year, week, home_team_id, home_team_name, home_owner, away_team_id, away_team_name,
                 home_luck, home_score, home_projected, away_score, away_projected,
                 home_score - away_score, home_projected - away_projected),
                (year, week, away_team_id, away_team_name, away_owner, home_team_id, home_team_name,
                 away_luck, away_score, away_projected, home_score, home_projected,
                 away_score - home_score, away_projected - home_projected)
            ])

        # Insert matchup luck data
        cursor.executemany("""
            INSERT INTO luck_analysis_matchups
            (year, week, team_id, team_name, owner_name, opponent_team_id, opponent_name,
             luck_points, actual_score, projected_score, opponent_actual, opponent_projected,
             actual_margin, projected_margin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, luck_matchups)

        print(f"✅ Inserted {len(luck_matchups)} luck matchup records")

        # Calculate season aggregates
        season_query = """
        SELECT
            year,
            team_name,
            owner_name,
            COUNT(*) as games_played,
            SUM(luck_points) as total_luck,
            AVG(luck_points) as average_luck,
            MAX(luck_points) as biggest_lucky_points,
            MIN(luck_points) as biggest_unlucky_points
        FROM luck_analysis_matchups
        GROUP BY year, team_name, owner_name
        HAVING games_played >= 5
        ORDER BY year, total_luck DESC
        """

        seasons = cursor.execute(season_query).fetchall()

        season_records = []
        for season in seasons:
            (year, team_name, owner_name, games_played, total_luck,
             average_luck, biggest_lucky_points, biggest_unlucky_points) = season

            # Get team_id for this team
            team_id = cursor.execute("""
                SELECT team_id FROM luck_analysis_matchups
                WHERE year = ? AND team_name = ? LIMIT 1
            """, (year, team_name)).fetchone()[0]

            # Find biggest lucky game details
            lucky_game = cursor.execute("""
                SELECT week, opponent_name, luck_points, actual_margin
                FROM luck_analysis_matchups
                WHERE year = ? AND team_name = ? AND luck_points = ?
                LIMIT 1
            """, (year, team_name, biggest_lucky_points)).fetchone()

            # Find biggest unlucky game details
            unlucky_game = cursor.execute("""
                SELECT week, opponent_name, luck_points, actual_margin
                FROM luck_analysis_matchups
                WHERE year = ? AND team_name = ? AND luck_points = ?
                LIMIT 1
            """, (year, team_name, biggest_unlucky_points)).fetchone()

            season_records.append((
                year, team_id, owner_name, team_name, total_luck, average_luck, games_played,
                lucky_game[0] if lucky_game else None,    # biggest_lucky_week
                lucky_game[1] if lucky_game else None,    # biggest_lucky_opponent
                biggest_lucky_points,
                lucky_game[3] if lucky_game else None,    # biggest_lucky_margin
                unlucky_game[0] if unlucky_game else None,  # biggest_unlucky_week
                unlucky_game[1] if unlucky_game else None,  # biggest_unlucky_opponent
                biggest_unlucky_points,
                unlucky_game[3] if unlucky_game else None   # biggest_unlucky_margin
            ))

        # Insert season luck data
        cursor.executemany("""
            INSERT INTO luck_analysis_seasons
            (year, team_id, owner_name, team_name, total_luck, average_luck, games_played,
             biggest_lucky_week, biggest_lucky_opponent, biggest_lucky_points, biggest_lucky_margin,
             biggest_unlucky_week, biggest_unlucky_opponent, biggest_unlucky_points, biggest_unlucky_margin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, season_records)

        print(f"✅ Inserted {len(season_records)} luck season records")

        # Show some stats
        total_matchups = cursor.execute("SELECT COUNT(*) FROM luck_analysis_matchups").fetchone()[0]
        total_seasons = cursor.execute("SELECT COUNT(*) FROM luck_analysis_seasons").fetchone()[0]

        print(f"📊 Luck Analysis Complete:")
        print(f"   Total matchups analyzed: {total_matchups}")
        print(f"   Total seasons analyzed: {total_seasons}")

        luckiest = cursor.execute("""
            SELECT team_name, owner_name, year, total_luck
            FROM luck_analysis_seasons
            ORDER BY total_luck DESC LIMIT 1
        """).fetchone()

        unluckiest = cursor.execute("""
            SELECT team_name, owner_name, year, total_luck
            FROM luck_analysis_seasons
            ORDER BY total_luck ASC LIMIT 1
        """).fetchone()

        if luckiest:
            print(f"🍀 Luckiest season: {luckiest[1]} ({luckiest[0]}) in {luckiest[2]} with +{luckiest[3]:.1f} points")

        if unluckiest:
            print(f"💔 Unluckiest season: {unluckiest[1]} ({unluckiest[0]}) in {unluckiest[2]} with {unluckiest[3]:.1f} points")

if __name__ == "__main__":
    populate_luck_analysis()