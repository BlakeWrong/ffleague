#!/usr/bin/env python3
"""
Production database initialization script for Heroku
"""
import sys
import os

# Add python_api to path for imports
sys.path.append('python_api')

from import_espn_data import ESPNDataImporter

def main():
    print("🚀 Production database import starting...")

    try:
        importer = ESPNDataImporter()
        importer.import_all_data()
        print("✅ Production database import completed successfully!")
        return 0
    except Exception as e:
        print(f"❌ Production database import failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())