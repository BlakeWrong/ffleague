#!/usr/bin/env python3
"""
Scheduled Database Updates
Automatically keeps the database updated with new ESPN data
"""

import schedule
import time
import sys
import os
from datetime import datetime

# Add the python_api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'python_api'))

def run_daily_update():
    """Run daily database update"""
    print(f"\n🕐 {datetime.now()}: Starting scheduled daily update")
    try:
        from update_database import DatabaseUpdater
        updater = DatabaseUpdater()
        updater.daily_update()
        print(f"✅ {datetime.now()}: Daily update completed successfully")
    except Exception as e:
        print(f"❌ {datetime.now()}: Daily update failed: {e}")

def run_weekly_update():
    """Run weekly database update"""
    print(f"\n🕐 {datetime.now()}: Starting scheduled weekly update")
    try:
        from update_database import DatabaseUpdater
        updater = DatabaseUpdater()
        updater.weekly_update()
        print(f"✅ {datetime.now()}: Weekly update completed successfully")
    except Exception as e:
        print(f"❌ {datetime.now()}: Weekly update failed: {e}")

def setup_schedule():
    """Setup the update schedule"""
    # Daily updates at 6 AM and 6 PM (twice daily during season)
    schedule.every().day.at("06:00").do(run_daily_update)
    schedule.every().day.at("18:00").do(run_daily_update)

    # Weekly comprehensive update on Mondays at 3 AM
    schedule.every().monday.at("03:00").do(run_weekly_update)

    print("📅 Update schedule configured:")
    print("  - Daily updates: 6:00 AM and 6:00 PM")
    print("  - Weekly updates: Monday 3:00 AM")

def main():
    """Main scheduler function"""
    print("🤖 Fantasy Football Database Auto-Updater")
    print("=" * 50)

    # Validate environment variables
    if not all([os.getenv('LEAGUE_ID'), os.getenv('ESPN_S2'), os.getenv('SWID')]):
        print("❌ Missing required environment variables: LEAGUE_ID, ESPN_S2, SWID")
        print("   Set these in your environment or .env file")
        return

    setup_schedule()

    print(f"🚀 Scheduler started at {datetime.now()}")
    print("   Press Ctrl+C to stop")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print(f"\n⏹️  Scheduler stopped at {datetime.now()}")

if __name__ == "__main__":
    main()