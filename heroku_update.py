#!/usr/bin/env python3
"""
Heroku-Compatible Database Update Script
For use with Heroku Scheduler add-on
"""

import sys
import os
import datetime

# Add the python_api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'python_api'))

def main():
    """Main function for Heroku scheduler"""
    print(f"🕐 {datetime.datetime.now()}: Heroku scheduled update starting")

    # Validate environment variables
    if not os.getenv('LEAGUE_ID'):
        print("❌ Missing required environment variable: LEAGUE_ID")
        return 1

    try:
        from update_database import DatabaseUpdater
        updater = DatabaseUpdater()

        # Determine update type based on day of week
        today = datetime.datetime.now().weekday()  # Monday = 0

        if today == 0:  # Monday - weekly update
            print("📅 Running weekly update (Monday)")
            updater.weekly_update()
        else:  # Other days - daily update
            print("📅 Running daily update")
            updater.daily_update()

        print(f"✅ {datetime.datetime.now()}: Update completed successfully")
        return 0

    except Exception as e:
        print(f"❌ {datetime.datetime.now()}: Update failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)