"""
Database connection and utility functions for Fantasy Football data
"""

import sqlite3
import json
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

class FFDatabase:
    def __init__(self, db_path: str = None):
        """Initialize database connection"""
        if db_path is None:
            # Use same logic as DatabaseAPI to ensure consistency
            parent_db = os.path.join(os.path.dirname(__file__), "..", "fantasy_football.db")
            current_db = "fantasy_football.db"

            if os.path.exists(parent_db):
                self.db_path = parent_db
            else:
                self.db_path = current_db
        else:
            self.db_path = db_path
        self.connection = None
        self.connect()

    def connect(self):
        """Create database connection"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
            print(f"Connected to database: {self.db_path}")
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()

    def execute_script(self, script_path: str):
        """Execute SQL script file"""
        try:
            with open(script_path, 'r') as file:
                script = file.read()

            cursor = self.connection.cursor()
            cursor.executescript(script)
            self.connection.commit()
            print(f"Successfully executed script: {script_path}")
        except Exception as e:
            print(f"Error executing script {script_path}: {e}")
            raise

    def initialize_schema(self):
        """Initialize database with schema"""
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'database_schema.sql')
        if os.path.exists(schema_path):
            self.execute_script(schema_path)
        else:
            print("Schema file not found - please ensure database_schema.sql exists")

    def execute_query(self, query: str, params: tuple = None) -> List[sqlite3.Row]:
        """Execute SELECT query and return results"""
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            print(f"Error executing query: {e}")
            raise

    def execute_insert(self, table: str, data: Dict[str, Any]) -> int:
        """Execute INSERT with data dictionary"""
        try:
            # Convert None values and serialize JSON fields
            processed_data = {}
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    processed_data[key] = json.dumps(value)
                elif value is None:
                    processed_data[key] = None
                else:
                    processed_data[key] = value

            columns = ', '.join(processed_data.keys())
            placeholders = ', '.join(['?' for _ in processed_data])
            query = f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})"

            cursor = self.connection.cursor()
            cursor.execute(query, tuple(processed_data.values()))
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error inserting into {table}: {e}")
            print(f"Data: {data}")
            raise

    def execute_many_inserts(self, table: str, data_list: List[Dict[str, Any]]):
        """Execute multiple INSERTs efficiently"""
        if not data_list:
            return

        try:
            # Process all records consistently
            processed_data_list = []
            for data in data_list:
                processed_data = {}
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        processed_data[key] = json.dumps(value)
                    elif value is None:
                        processed_data[key] = None
                    else:
                        processed_data[key] = value
                processed_data_list.append(processed_data)

            # Use first record to determine columns
            if processed_data_list:
                columns = ', '.join(processed_data_list[0].keys())
                placeholders = ', '.join(['?' for _ in processed_data_list[0]])
                query = f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})"

                cursor = self.connection.cursor()
                cursor.executemany(query, [tuple(data.values()) for data in processed_data_list])
                self.connection.commit()
                print(f"Inserted {len(processed_data_list)} records into {table}")
        except Exception as e:
            print(f"Error bulk inserting into {table}: {e}")
            raise

    def get_last_import_status(self, import_type: str, table_name: str = None) -> Optional[sqlite3.Row]:
        """Get status of last import for a given type"""
        query = """
        SELECT * FROM import_log
        WHERE import_type = ?
        AND (table_name = ? OR ? IS NULL)
        ORDER BY started_at DESC
        LIMIT 1
        """
        results = self.execute_query(query, (import_type, table_name, table_name))
        return results[0] if results else None

    def log_import_start(self, import_type: str, table_name: str = None, year: int = None, week: int = None) -> int:
        """Log start of import process"""
        data = {
            'import_type': import_type,
            'table_name': table_name,
            'year': year,
            'week': week,
            'status': 'running',
            'started_at': datetime.utcnow().isoformat()
        }
        return self.execute_insert('import_log', data)

    def log_import_complete(self, log_id: int, records_imported: int = 0, records_updated: int = 0, records_skipped: int = 0):
        """Log completion of import process"""
        query = """
        UPDATE import_log
        SET status = 'completed',
            records_imported = ?,
            records_updated = ?,
            records_skipped = ?,
            completed_at = ?
        WHERE id = ?
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (records_imported, records_updated, records_skipped, datetime.utcnow().isoformat(), log_id))
        self.connection.commit()

    def log_import_error(self, log_id: int, error_message: str):
        """Log import error"""
        query = """
        UPDATE import_log
        SET status = 'failed',
            error_message = ?,
            completed_at = ?
        WHERE id = ?
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (error_message, datetime.utcnow().isoformat(), log_id))
        self.connection.commit()

    def get_available_years(self) -> List[int]:
        """Get list of years with data in database"""
        query = "SELECT DISTINCT year FROM leagues ORDER BY year DESC"
        results = self.execute_query(query)
        return [row['year'] for row in results]

    def get_team_owner_mapping(self, year: int) -> Dict[int, str]:
        """Get mapping of team_id to owner name for a given year"""
        query = """
        SELECT team_id, owners FROM teams WHERE year = ?
        """
        results = self.execute_query(query, (year,))
        mapping = {}
        for row in results:
            try:
                owners_data = json.loads(row['owners']) if row['owners'] else []
                if owners_data and len(owners_data) > 0:
                    owner = owners_data[0]
                    if 'firstName' in owner and owner['firstName']:
                        owner_name = f"{owner.get('firstName', '')} {owner.get('lastName', '')}".strip()
                    else:
                        owner_name = owner.get('displayName', f"Team_{row['team_id']}")
                    mapping[row['team_id']] = owner_name
            except (json.JSONDecodeError, KeyError, IndexError):
                mapping[row['team_id']] = f"Team_{row['team_id']}"
        return mapping

# Global database instance
db = None

def get_database() -> FFDatabase:
    """Get database instance (singleton pattern)"""
    global db
    if db is None:
        db = FFDatabase()
    return db

def initialize_database():
    """Initialize database with schema"""
    database = get_database()
    database.initialize_schema()
    print("Database initialized successfully")

if __name__ == "__main__":
    # Initialize database when run directly
    initialize_database()