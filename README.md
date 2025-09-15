# Fantasy Football League Dashboard

A modern web application to display your ESPN Fantasy Football league information with a beautiful UI built on Next.js, shadcn/ui, and Tailwind CSS.

## Features

- 📊 **League Overview**: Display team standings, records, and points
- 🏆 **Matchup Results**: View weekly matchups and scores
- 📈 **Historical Data**: Support for multiple seasons
- 🎨 **Modern UI**: Built with shadcn/ui components and Tailwind CSS
- ⚡ **Fast Performance**: Next.js with TypeScript
- 🚀 **Vercel Deployment**: Serverless Python API endpoints

## Project Structure

```
ffleague/
├── frontend/           # Next.js frontend application
│   ├── src/
│   │   ├── app/       # Next.js app router
│   │   ├── components/ # React components (including shadcn/ui)
│   │   └── lib/       # Utility functions
│   ├── package.json
│   └── tsconfig.json
├── api/               # Python serverless functions
│   ├── league.py      # League data endpoint
│   └── matchups.py    # Matchup data endpoint
├── main.py            # Core ESPN API logic
├── requirements.txt   # Python dependencies
├── vercel.json        # Vercel deployment config
└── .env.example       # Environment variables template
```

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone <your-repo-url>
cd ffleague

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Environment Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Get your ESPN credentials:
   - Go to ESPN Fantasy Football in your browser
   - Open Developer Tools (F12)
   - Go to Application/Storage > Cookies
   - Find your `ESPN_S2` and `SWID` values
   - Get your `LEAGUE_ID` from the URL

3. Fill in your `.env` file:
   ```
   LEAGUE_ID=123456789
   ESPN_S2=your_espn_s2_cookie_here
   SWID=your_swid_here
   ```

### 3. Local Development

```bash
# Start the frontend development server
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 4. API Endpoints

Once deployed, your API will have these endpoints:

- `GET /api/league?year=2024` - Get league info and standings
- `GET /api/matchups?year=2024` - Get all matchups for the season
- `GET /api/matchups?year=2024&week=1` - Get matchups for a specific week

## Vercel Deployment

### 1. Connect to Vercel

1. Push your code to GitHub
2. Import your repository in [Vercel Dashboard](https://vercel.com)
3. Vercel will automatically detect it's a Next.js project

### 2. Environment Variables

In your Vercel project dashboard, add these environment variables:

```
LEAGUE_ID=your_league_id
ESPN_S2=your_espn_s2_cookie
SWID=your_swid_value
```

### 3. Deploy

Vercel will automatically deploy on every push to your main branch.

## Technology Stack

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - High-quality UI components
- **Lucide React** - Icons

### Backend
- **Python 3.9** - Serverless functions
- **espn-api** - ESPN Fantasy Football API client
- **pandas** - Data manipulation
- **Vercel** - Serverless deployment

## Development

### Adding New Components

```bash
cd frontend
npx shadcn@latest add <component-name>
```

### Extending the API

Add new Python files to the `api/` directory. Each file should export a `handler` function for Vercel serverless functions.

### Local Testing

For local API testing, you can run your Python scripts directly:

```bash
python main.py
```

## Troubleshooting

### ESPN API Issues
- Make sure your `ESPN_S2` and `SWID` cookies are current
- Private leagues require authentication
- Check that your `LEAGUE_ID` is correct

### Vercel Deployment Issues
- Ensure all environment variables are set in Vercel dashboard
- Check Vercel function logs for Python errors
- Verify `requirements.txt` includes all dependencies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

MIT License - see LICENSE file for details