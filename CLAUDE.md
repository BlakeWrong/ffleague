# FF League - Fantasy Football Analytics Platform

## Project Overview
A comprehensive fantasy football analytics platform that connects to ESPN Fantasy Football leagues to provide advanced statistics, historical analysis, and insights. Built with Next.js frontend and Python FastAPI backend.

## Tech Stack
- **Frontend**: Next.js 15 with shadcn/ui components, TypeScript, Tailwind CSS
- **Backend**: Python FastAPI with ESPN API integration
- **Deployment**: Vercel for frontend, Python API for backend
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

## Current Status
- ✅ Basic ESPN integration working with real league data
- ✅ Multiple Python API endpoints functional
- ✅ Frontend displaying real fantasy football data
- ✅ Development workflow established
- 🚧 Ready for expansion with advanced analytics and additional features