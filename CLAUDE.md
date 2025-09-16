# FF League - Fantasy Football Analytics Platform

## Project Overview
A comprehensive fantasy football analytics platform that connects to ESPN Fantasy Football leagues to provide advanced statistics, historical analysis, and insights. Built with Next.js frontend and Python FastAPI backend.

## Tech Stack
- **Frontend**: Next.js 15 with shadcn/ui components, TypeScript, Tailwind CSS
- **Backend**: Python FastAPI with ESPN API integration
- **Deployment**: Heroku full-stack deployment with both frontend and backend
- **ESPN Integration**: `espn-api` Python library for real fantasy football data

## Project Structure
```
/
├── src/app/                 # Next.js App Router frontend
│   ├── api/league-stats/   # Proxy API to Python backend
│   └── page.tsx            # Main dashboard page
├── python_api/             # FastAPI Python backend
│   └── app.py              # Main API server with ESPN endpoints
├── api_helpers.py          # ESPN API integration helpers
├── package.json            # Next.js dependencies & scripts
└── requirements.txt        # Python dependencies
```

## Current Features
### Frontend (Next.js + shadcn/ui)
- Mobile-first responsive design with glassmorphism effects
- Real-time ESPN league data display
- League statistics dashboard with:
  - Current week and total teams
  - League leader with record
  - Average scoring across league
  - Recent matchups with team names and scores

### Backend (Python FastAPI)
- **Multiple ESPN API endpoints** for different data needs
- **Historical data support** (2015-2024 seasons)
- **Real ESPN integration** using `espn-api` library

#### Available API Endpoints:
- `GET /league/stats` - Current season overview
- `GET /league/stats/{year}` - Historical season data
- `GET /teams` - Current season teams with records
- `GET /teams/{year}` - Historical teams data
- `GET /matchups/{week}` - Current season week matchups
- `GET /matchups/{year}/{week}` - Historical matchups
- `GET /health` - API health check

## Development Workflow
```bash
# Run both servers concurrently
npm run dev:all

# Individual servers
npm run dev          # Next.js frontend only
npm run dev:python   # Python API only
```

## Deployment
### Heroku Full-Stack Deployment
The application is configured for Heroku deployment with both Next.js and Python API running on a single dyno:

**Setup:**
```bash
# Create Heroku app
heroku create your-ff-league-app

# Add both buildpacks
heroku buildpacks:add heroku/nodejs
heroku buildpacks:add heroku/python

# Set environment variables
heroku config:set LEAGUE_ID=your_league_id
heroku config:set ESPN_S2=your_espn_s2
heroku config:set SWID=your_swid

# Deploy
git push heroku development:main
```

**Configuration:**
- `Procfile`: Runs both Next.js and Python API concurrently using `concurrently`
- `package.json`: Contains `concurrently` in production dependencies for Heroku
- `python_api/requirements.txt`: Python dependencies for FastAPI and ESPN integration
- Dynamic port handling for Heroku's assigned PORT (Next.js on PORT, Python on PORT+1)
- Next.js API routes proxy to Python API running on same dyno
- Both buildpacks configured: `heroku/nodejs` and `heroku/python`

## Environment Variables Required
- `LEAGUE_ID` - ESPN Fantasy League ID
- `ESPN_S2` - ESPN S2 cookie for private leagues
- `SWID` - ESPN SWID cookie for private leagues

## User's Vision & Future Plans
The user wants to build a comprehensive fantasy football analytics platform with:

1. **Advanced Python Calculations**: Complex statistical analysis that requires Python's data processing capabilities
2. **Historical Comparisons**: Multi-season analysis and trends
3. **Multiple Data Views**: Different pages for different seasons/years of data
4. **In-depth Statistics**: Beyond basic ESPN data - custom metrics and insights
5. **Expandable Architecture**: Python API that can grow with multiple endpoints for different analytics

## Key Implementation Details
- **API Integration**: Next.js proxies requests to Python FastAPI to avoid CORS and provide unified interface
- **Real Data**: Uses ESPN's official fantasy API through Python library, not mock data
- **Mobile-First**: Responsive design optimized for mobile devices
- **Modular Backend**: FastAPI structure allows easy addition of new endpoints
- **Development Experience**: Concurrent development setup for full-stack development

## Recent Technical Decisions
- Moved from attempting direct ESPN API calls to using proven `espn-api` Python library
- Separated frontend and backend for better scalability and Python analytics capabilities
- Used Next.js API routes as proxy to Python backend for seamless integration
- Implemented proper error handling and validation in Python API
- Set up concurrent development environment for efficient full-stack development
- **Successfully deployed to Heroku** with full-stack configuration
- Resolved port conflicts between Next.js and Python API in production
- Moved `concurrently` to production dependencies for Heroku compatibility

## Current Status - Version 0.0.1 Production Ready
- ✅ Basic ESPN integration working with real league data
- ✅ Multiple Python API endpoints functional
- ✅ Frontend displaying real fantasy football data
- ✅ Development workflow established
- ✅ **PRODUCTION DEPLOYMENT WORKING** on Heroku
- ✅ Full-stack Next.js + Python FastAPI deployed and integrated
- ✅ Port management and buildpack configuration resolved
- 🚧 Ready for expansion with advanced analytics and additional features

## Production URL
- **Live Application**: https://ffleague-fc3c9309ff7b.herokuapp.com/
- **Status**: Fully functional with both frontend and backend APIs

## IMPORTANT: Development Workflow Rules
- **NEVER work on master branch** - Always use development branch
- **Always work on development branch** for all features and fixes
- Only merge to master for production releases

## Current Status (2025 Season)
The application is currently working with 2024 data. User wants to update to 2025 season data and add:
1. New endpoint for 2025 league standings
2. Mobile-first shadcn table component showing current standings
3. Automatically fetch most recent week's standings

## ESPN API Documentation (espn-api Python Library)

### League Class
The League Object provides access to all ESPN Fantasy data including settings, teams, roster, players, free agents, box scores/match ups, and power rankings.

**Usage:**
```python
from espn_api.football import League
league = League(league_id: int, year: int, espn_s2: str = None, swid: str = None, debug=False)
```

**Variables:**
- `league_id: int`
- `year: int`
- `settings: Settings`
- `teams: List[Team]`
- `draft: List[Pick]`
- `current_week: int` # current fantasy football week
- `nfl_week: int` # current nfl week
- `previousSeasons: List[str]` # list of leagues previous seasons

**Functions:**
- `scoreboard(week: int = None) -> List[Matchup]` - Returns basic match up info for current week
- `box_scores(week: int = None) -> List[BoxScore]` - Returns specific week match ups (current season only)
- `power_rankings(week: int=None) -> List[Tuples(str, Team)]` - Calculates power rankings using dominance
- `free_agents(week: int = None, size: int = 50, position: str = None, position_id: int=None) -> List[BoxPlayer]` - Returns free agents list
- `recent_activity(size: int = 25, msg_type: str = None, offset: int = 0) -> List[Activity]` - Returns activities (requires auth)
- `player_info(name: str = None, playerId: Union[int, list] = None) -> Union[Player, List[Player]]` - Returns player with season stats
- `refresh() -> None` - Gets latest league data

**Helper Functions:**
- `standings() -> List[Team]` - **IMPORTANT: Use this for standings table**
- `top_scorer() -> Team`
- `least_scorer() -> Team`
- `most_points_against() -> Team`
- `top_scored_week() -> Tuple(Team, int)`
- `least_scored_week() -> Tuple(Team, int)`
- `get_team_data(team_id: int) -> Team`

### Team Class
**Variables:**
- `team_id: int`
- `team_abbrev: str`
- `team_name: str`
- `division_id: str`
- `division_name: str`
- `wins: int`
- `losses: int`
- `ties: int`
- `points_for: int` # total points for through out the season
- `points_against: int` # total points against through out the season
- `waiver_rank: int` # waiver position
- `acquisitions: int` # number of acquisitions made by the team
- `acquisition_budget_spent: int` # budget spent on acquisitions
- `drops: int` # number of drops made by the team
- `trades: int` # number of trades made by the team
- `move_to_ir: int` # number of players move to ir
- `owners: List[dict]` # array of owner dict
- `stats: dict` # holds teams season long stats
- `streak_type: str` # string of either WIN or LOSS
- `streak_length: int` # how long the streak is for streak type
- `standing: int` # standing before playoffs
- `final_standing: int` # final standing at end of season
- `draft_projected_rank: int` # projected rank after draft
- `playoff_pct: int` # teams projected chance to make playoffs
- `logo_url: str`
- `roster: List[Player]`
- `schedule: List[Team]`
- `scores: List[int]`
- `outcomes: List[str]`

### Player Class
**Variables:**
- `name: str`
- `playerId: int`
- `posRank: int` # players positional rank
- `eligibleSlots: List[str]` # example ['WR', 'WR/TE/RB']
- `lineupSlot: str` # the players lineup position
- `acquisitionType: str`
- `proTeam: str` # 'PIT' or 'LAR'
- `schedule: dict` # key is scoring period
- `onTeamId: int` # id of fantasy team
- `position: str` # main position like 'TE' or 'QB'
- `injuryStatus: str`
- `injured: boolean`
- `total_points: int` # players total points during the season
- `avg_points: int` # players average points during the season
- `projected_total_points: int` # projected player points for the season
- `projected_avg_points: int` # projected players average points for the season
- `percent_owned: int` # percentage player is rostered
- `percent_started: int` # percentage player is started
- `stats: dict` # holds each week stats, actual and projected points

### Box Player Class
Inherits from Player Class with additional variables:
- `slot_position: str` # the players lineup position
- `points: int` # points scored in the current week
- `projected_points: int` # projected points for that week
- `pro_opponent: str` # the pro team the player is going against
- `pro_pos_rank: int` # the rank the pro team is against that players position
- `game_played: int` # 0 (not played/playing) or 100 (finished game)
- `game_date: datetime` # datetime object of when the pro game starts
- `on_bye_week: boolean` # whether or not the player is on a bye
- `active_status: str` # whether the player was active or not

### Box Score Class
**Variables:**
- `home_team: Team`
- `home_score: int`
- `home_projected: int`
- `away_team: Team`
- `away_score: int`
- `away_projected: int`
- `home_lineup: List[BoxPlayer]`
- `away_lineup: List[BoxPlayer]`
- `is_playoff: bool`
- `matchup_type: str` # values NONE, WINNERS_BRACKET, LOSERS_CONSOLATION_LADDER, WINNERS_CONSOLATION_LADDER

### Pick Class
**Variables:**
- `team: Team`
- `playerId: int`
- `playerName: str`
- `round_num: int`
- `round_pick: int`
- `bid_amount: int`
- `keeper_status: bool`
- `nominatingTeam: Team` # nominating team for auction drafts

### Settings Class
**Variables:**
- `reg_season_count: int`
- `veto_votes_required: int`
- `team_count: int`
- `playoff_team_count: int`
- `keeper_count: int`
- `trade_deadline: int` # epoch
- `name: str`
- `tie_rule: int`
- `playoff_tie_rule: int`
- `playoff_seed_tie_rule: int`
- `playoff_matchup_period_length: int` # Weeks Per Playoff Matchup
- `faab: bool` # Is the league using a free agent acquisition budget
- `acquisition_budget: int`
- `scoring_format: List[dict]` # example [{'abbr': 'RETD', 'label': 'TD Reception', 'id': 43, 'points': 6.0}]

### Matchup Class
**Variables:**
- `home_team: Team`
- `home_score: int`
- `away_team: Team`
- `away_score: int`
- `is_playoff: bool`
- `matchup_type: str` # values NONE, WINNERS_BRACKET, LOSERS_CONSOLATION_LADDER, WINNERS_CONSOLATION_LADDER

### Activity Class
**Variables:**
- `date: int` # Epoch time milliseconds
- `actions: List[Tuple]` # Tuple includes (team: Team Class, action: str, player: Player Class, bid_amount: int)

## Important ESPN API Notes
- Set `debug=True` in League constructor to see all ESPN API requests/responses in console
- For position inputs use: 'QB', 'RB', 'WR', 'TE', 'D/ST', 'K', 'FLEX'
- For activity msg_type inputs use: 'FA', 'WAIVER', 'TRADED'
- Owner name attributes only available for private leagues (public leagues won't show names)
- Box scores only work with current season data
- **Current year is 2025** - update all hardcoded years from 2024 to 2025
- **Key method for standings: `league.standings()`** - returns sorted List[Team] by current standings