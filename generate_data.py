#!/usr/bin/env python3
"""
Generate league data and save to JSON file
Run this script periodically to update the data
"""
import json
from api_helpers import get_league_stats

if __name__ == "__main__":
    try:
        data = get_league_stats()
        with open('league_data.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("League data updated successfully")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)