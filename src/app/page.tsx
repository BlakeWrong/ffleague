"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { StandingsTable } from "@/components/standings-table";
import { BenchHeroes } from "@/components/bench-heroes";
import { MatchupsSection } from "@/components/matchups-section";
import { Trophy, Users, TrendingUp, Calendar } from "lucide-react";
import { useEffect, useState } from "react";

interface LeagueData {
  total_teams: number;
  current_week: number;
  league_leader: {
    team_name: string;
    record: string;
  };
  average_score: string;
  recent_matchups: Array<{
    week: number;
    home_team: string;
    home_score: number;
    away_team: string;
    away_score: number;
  }>;
}

interface StandingsData {
  rank: number;
  team_id: number;
  team_name: string;
  owner: string;
  wins: number;
  losses: number;
  ties: number;
  points_for: number;
  points_against: number;
  streak_type: string;
  streak_length: number;
}

interface StandingsResponse {
  year: number;
  current_week: number;
  standings: StandingsData[];
  total_teams: number;
}


export default function Home() {
  const [leagueData, setLeagueData] = useState<LeagueData | null>(null);
  const [standingsData, setStandingsData] = useState<StandingsResponse | null>(null);
  const [standingsLoading, setStandingsLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        console.log('Fetching from:', '/api/league-stats');

        const response = await fetch('/api/league-stats', {
          cache: 'no-store',
        });

        console.log('Response status:', response.status);

        if (!response.ok) {
          console.log('Response not OK:', response.status, response.statusText);
          return;
        }

        const data = await response.json();
        console.log('API data:', data);
        setLeagueData(data);
      } catch (error) {
        console.error('Fetch error:', error);
      }
    }

    async function fetchStandings() {
      try {
        console.log('Fetching standings from:', '/api/standings');

        const response = await fetch('/api/standings', {
          cache: 'no-store',
        });

        console.log('Standings response status:', response.status);

        if (!response.ok) {
          console.log('Standings response not OK:', response.status, response.statusText);
          return;
        }

        const data = await response.json();
        console.log('Standings data:', data);
        setStandingsData(data);
      } catch (error) {
        console.error('Standings fetch error:', error);
      } finally {
        setStandingsLoading(false);
      }
    }

    fetchData();
    fetchStandings();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <header className="bg-white/80 backdrop-blur-sm shadow-sm dark:bg-gray-900/80">
        <div className="container mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Trophy className="h-8 w-8 text-blue-600" />
              <h1 className="text-xl font-bold text-gray-900 dark:text-white sm:text-2xl">
                Show Me Your TDs
              </h1>
            </div>
            <Badge variant="outline" className="text-xs sm:text-sm">
              2025 Season
            </Badge>
          </div>
        </div>
      </header>

      <main className="container mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="space-y-8">
          <section className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-4xl">
              Welcome to Your Fantasy Football League
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
              Track your team&apos;s performance, analyze matchups, and dominate your league
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
              Weekly Matchups
            </h2>
            <MatchupsSection
              currentWeek={leagueData?.current_week}
              currentYear={2025}
            />
          </section>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Teams</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {leagueData?.total_teams || "Loading..."}
                </div>
                <p className="text-xs text-muted-foreground">
                  Active in league
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Current Week</CardTitle>
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {leagueData?.current_week || "Loading..."}
                </div>
                <p className="text-xs text-muted-foreground">
                  Regular season
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">League Leader</CardTitle>
                <Trophy className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {leagueData?.league_leader?.team_name || "Loading..."}
                </div>
                <p className="text-xs text-muted-foreground">
                  {leagueData?.league_leader?.record || ""}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Score</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {leagueData?.average_score || "Loading..."}
                </div>
                <p className="text-xs text-muted-foreground">
                  Points per game
                </p>
              </CardContent>
            </Card>
          </div>

          <Separator />

          <section>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
              League Standings
            </h3>
            <StandingsTable
              standings={standingsData?.standings || []}
              currentWeek={standingsData?.current_week || 0}
              isLoading={standingsLoading}
            />
          </section>

          <Separator />

          <section>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
              <em>Fuccck gronk on the bench</em>
            </h2>
            <BenchHeroes
              currentWeek={leagueData?.current_week}
              currentYear={2025}
            />
          </section>

          <Separator />

          <section>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
              Recent Matchups
            </h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {leagueData?.recent_matchups ? (
                leagueData.recent_matchups.map((matchup, index) => (
                  <Card key={index}>
                    <CardHeader>
                      <CardTitle className="text-lg">
                        Week {matchup.week}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="font-medium">{matchup.home_team}</span>
                          <Badge variant={matchup.home_score > matchup.away_score ? "default" : "secondary"}>
                            {matchup.home_score.toFixed(2)}
                          </Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="font-medium">{matchup.away_team}</span>
                          <Badge variant={matchup.away_score > matchup.home_score ? "default" : "secondary"}>
                            {matchup.away_score.toFixed(2)}
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <Card className="col-span-full">
                  <CardContent className="pt-6">
                    <p className="text-center text-muted-foreground">
                      Loading matchup data...
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </section>

          <section className="text-center">
            <Card className="mx-auto max-w-md">
              <CardHeader>
                <CardTitle>Get Started</CardTitle>
                <CardDescription>
                  Connect to your ESPN Fantasy Football league
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full">
                  View League Dashboard
                </Button>
              </CardContent>
            </Card>
          </section>
        </div>
      </main>

      <footer className="mt-16 bg-white/80 backdrop-blur-sm dark:bg-gray-900/80">
        <div className="container mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="text-center text-sm text-gray-600 dark:text-gray-300">
            <p>&copy; 2025 FF League. Built with Next.js and shadcn/ui.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
