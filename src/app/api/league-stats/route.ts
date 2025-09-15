import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    // Mock data for testing frontend
    const data = {
      total_teams: 12,
      current_week: 3,
      league_leader: {
        team_name: "The Gronk Squad",
        record: "3-0"
      },
      average_score: "118.5",
      recent_matchups: [
        {
          week: 3,
          home_team: "The Gronk Squad",
          home_score: 142.3,
          away_team: "Fantasy Footballers",
          away_score: 98.7
        },
        {
          week: 3,
          home_team: "Touchdown Titans",
          home_score: 125.1,
          away_team: "Gridiron Glory",
          away_score: 108.4
        },
        {
          week: 3,
          home_team: "End Zone Elite",
          home_score: 89.6,
          away_team: "Pigskin Pirates",
          away_score: 134.8
        }
      ]
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    )
  }
}