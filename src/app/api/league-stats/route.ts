import { NextRequest, NextResponse } from 'next/server'

interface ESPNTeam {
  id: number;
  location: string;
  nickname: string;
  owners: Array<{ firstName: string; lastName: string }>;
  record: {
    overall: {
      wins: number;
      losses: number;
      ties: number;
    }
  };
  points: number;
  pointsFor: number;
}

interface ESPNMatchup {
  id: number;
  matchupPeriodId: number;
  home: {
    teamId: number;
    totalPoints: number;
  };
  away: {
    teamId: number;
    totalPoints: number;
  };
}

export async function GET(request: NextRequest) {
  try {
    const LEAGUE_ID = process.env.LEAGUE_ID;
    const ESPN_S2 = process.env.ESPN_S2;
    const SWID = process.env.SWID;

    if (!LEAGUE_ID) {
      throw new Error('LEAGUE_ID environment variable is required');
    }

    // Get league info and teams
    const leagueUrl = `https://fantasy.espn.com/apis/v3/games/ffl/seasons/2024/segments/0/leagues/${LEAGUE_ID}?view=mTeam&view=mRoster&view=mMatchup&view=mSettings`;

    const headers: HeadersInit = {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    };

    // Add authentication headers if available
    if (ESPN_S2 && SWID) {
      headers['Cookie'] = `espn_s2=${ESPN_S2}; SWID=${SWID}`;
    }

    const response = await fetch(leagueUrl, { headers });

    if (!response.ok) {
      throw new Error(`ESPN API returned ${response.status}: ${response.statusText}`);
    }

    const leagueData = await response.json();

    // Extract teams data
    const teams: ESPNTeam[] = leagueData.teams || [];
    const schedule: ESPNMatchup[] = leagueData.schedule || [];
    const currentWeek = leagueData.scoringPeriodId || leagueData.status?.currentMatchupPeriod || 1;

    // Calculate league leader
    const sortedTeams = teams
      .filter(team => team.record?.overall)
      .sort((a, b) => {
        // Sort by wins first, then by points for
        const aWins = a.record.overall.wins;
        const bWins = b.record.overall.wins;
        if (aWins !== bWins) return bWins - aWins;
        return (b.pointsFor || 0) - (a.pointsFor || 0);
      });

    const leagueLeader = sortedTeams[0];
    const leaderName = leagueLeader
      ? `${leagueLeader.location} ${leagueLeader.nickname}`
      : "Unknown";
    const leaderRecord = leagueLeader?.record?.overall
      ? `${leagueLeader.record.overall.wins}-${leagueLeader.record.overall.losses}`
      : "0-0";

    // Calculate average score
    const totalPoints = teams.reduce((sum, team) => sum + (team.pointsFor || 0), 0);
    const averageScore = teams.length > 0 ? (totalPoints / teams.length).toFixed(1) : "0.0";

    // Get recent matchups (last few weeks)
    const recentMatchups = schedule
      .filter(matchup => matchup.matchupPeriodId >= Math.max(1, currentWeek - 2))
      .slice(-6)
      .map(matchup => {
        const homeTeam = teams.find(t => t.id === matchup.home?.teamId);
        const awayTeam = teams.find(t => t.id === matchup.away?.teamId);

        return {
          week: matchup.matchupPeriodId,
          home_team: homeTeam ? `${homeTeam.location} ${homeTeam.nickname}` : "Unknown",
          home_score: matchup.home?.totalPoints || 0,
          away_team: awayTeam ? `${awayTeam.location} ${awayTeam.nickname}` : "Unknown",
          away_score: matchup.away?.totalPoints || 0
        };
      })
      .filter(matchup => matchup.home_score > 0 || matchup.away_score > 0); // Filter out incomplete games

    const data = {
      total_teams: teams.length,
      current_week: currentWeek,
      league_leader: {
        team_name: leaderName,
        record: leaderRecord
      },
      average_score: averageScore,
      recent_matchups: recentMatchups
    };

    return NextResponse.json(data);
  } catch (error) {
    console.error('ESPN API Error:', error);
    return NextResponse.json(
      {
        error: 'Failed to fetch league data',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}