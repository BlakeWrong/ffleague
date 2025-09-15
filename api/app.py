from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI(title="FF League API")

# Add CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "FF League API"}

@app.get("/api/league-stats")
async def get_league_stats():
    # Mock data for testing frontend
    return {
        "total_teams": 12,
        "current_week": 3,
        "league_leader": {
            "team_name": "The Gronk Squad",
            "record": "3-0"
        },
        "average_score": "118.5",
        "recent_matchups": [
            {
                "week": 3,
                "home_team": "The Gronk Squad",
                "home_score": 142.3,
                "away_team": "Fantasy Footballers",
                "away_score": 98.7
            },
            {
                "week": 3,
                "home_team": "Touchdown Titans",
                "home_score": 125.1,
                "away_team": "Gridiron Glory",
                "away_score": 108.4
            },
            {
                "week": 3,
                "home_team": "End Zone Elite",
                "home_score": 89.6,
                "away_team": "Pigskin Pirates",
                "away_score": 134.8
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)