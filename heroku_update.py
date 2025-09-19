#!/usr/bin/env python3
"""
Heroku-Compatible Database Update Script
For use with Heroku Scheduler add-on
"""

import sys
import os
import datetime as dt

# Add the python_api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'python_api'))

def main():
    """Main function for Heroku scheduler"""
    print(f"🕐 {dt.datetime.now()}: Heroku scheduled update starting")

    # Validate environment variables
    if not all([os.getenv('LEAGUE_ID'), os.getenv('ESPN_S2'), os.getenv('SWID')]):
        print("❌ Missing required environment variables")
        return 1

    try:
        from update_database import DatabaseUpdater
        updater = DatabaseUpdater()

        # Determine update type based on day of week
        import datetime as dt
        today = dt.datetime.now().weekday()  # Monday = 0

        if today == 0:  # Monday - weekly update
            print("📅 Running weekly update (Monday)")
            updater.weekly_update()
        else:  # Other days - daily update
            print("📅 Running daily update")
            updater.daily_update()

        print(f"✅ {dt.datetime.now()}: Update completed successfully")
        return 0

    except Exception as e:
        print(f"❌ {dt.datetime.now()}: Update failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)