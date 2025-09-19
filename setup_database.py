#!/usr/bin/env python3
"""
Database Setup Script
Run this to initialize the database and import all ESPN data
"""

import sys
import os

# Add the python_api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'python_api'))

from python_api.database import initialize_database
from python_api.import_espn_data import main as import_data

def main():
    """Setup database and import data"""
    print("🏈 Fantasy Football Database Setup")
    print("=" * 50)

    print("\n1. Initializing database schema...")
    try:
        initialize_database()
        print("✅ Database schema created successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return

    print("\n2. Importing ESPN data...")
    try:
        import_data()
        print("✅ Data import completed successfully")
    except Exception as e:
        print(f"❌ Failed to import data: {e}")
        return

    print("\n🎉 Database setup complete!")
    print("You can now run your FastAPI server with database-backed endpoints.")

if __name__ == "__main__":
    main()