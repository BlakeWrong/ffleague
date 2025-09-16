"use client"

import { useState, useEffect } from "react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { TrophyIcon, CalendarIcon, ExternalLinkIcon } from "lucide-react"

interface BenchPlayer {
  player_name: string
  points: number
  team_name: string
  team_id: number
  owner: string
  position: string
  pro_team: string
}

interface BenchHeroesData {
  year: number
  week: number
  bench_heroes: BenchPlayer[]
  total_bench_players: number
}

interface BenchHeroesProps {
  onDataRequest: (year: number, week: number) => void
  data: BenchHeroesData | null
  isLoading: boolean
  error?: string
}

export function BenchHeroes({ onDataRequest, data, isLoading, error }: BenchHeroesProps) {
  const [selectedYear, setSelectedYear] = useState("2025")
  const [selectedWeek, setSelectedWeek] = useState("1")
  const [leagueId, setLeagueId] = useState<number | null>(null)
  const [availableYears, setAvailableYears] = useState<number[]>([])

  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch league ID
        const healthResponse = await fetch('/api/health')
        if (healthResponse.ok) {
          const healthData = await healthResponse.json()
          setLeagueId(healthData.league_id)
        }

        // Fetch available years
        const yearsResponse = await fetch('/api/available-years')
        if (yearsResponse.ok) {
          const yearsData = await yearsResponse.json()
          const allYears = yearsData.available_years || []
          setAvailableYears(allYears)

          // Set default year to the most recent available year
          if (allYears.length > 0) {
            setSelectedYear(allYears[0].toString())
          }
        }
      } catch (error) {
        console.error('Failed to fetch data:', error)
      }
    }
    fetchData()
  }, [])

  const handleFetch = () => {
    onDataRequest(parseInt(selectedYear), parseInt(selectedWeek))
  }

  const getPointsBarWidth = (points: number, maxPoints: number) => {
    return maxPoints > 0 ? (points / maxPoints) * 100 : 0
  }

  const getPositionColor = (position: string) => {
    const colors: Record<string, string> = {
      'QB': 'bg-red-500',
      'RB': 'bg-green-500',
      'WR': 'bg-blue-500',
      'TE': 'bg-yellow-500',
      'K': 'bg-purple-500',
      'DST': 'bg-gray-500',
      'D/ST': 'bg-gray-500'
    }
    return colors[position] || 'bg-gray-400'
  }

  const generateESPNLink = (teamId: number, year: number, week: number) => {
    if (!leagueId) return null
    return `https://fantasy.espn.com/football/boxscore?leagueId=${leagueId}&matchupPeriodId=${week}&scoringPeriodId=${week}&seasonId=${year}&teamId=${teamId}&view=scoringperiod`
  }

  const maxPoints = data?.bench_heroes ? Math.max(...data.bench_heroes.map(p => p.points)) : 0

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <p className="text-center text-destructive">Error: {error}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2 text-xl">
              <TrophyIcon className="h-5 w-5 text-yellow-500" />
              fuuuuck gronk on da bench
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Top scoring bench players by week (because pain is eternal)
            </p>
            <p className="text-xs bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300 p-2 rounded mt-2">
              💡 Note: Data only available from 2019 onwards due to ESPN API limitations
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-2">
            <Select value={selectedYear} onValueChange={setSelectedYear}>
              <SelectTrigger className="w-full sm:w-24">
                <SelectValue placeholder="Year" />
              </SelectTrigger>
              <SelectContent>
                {availableYears.length > 0 ? (
                  availableYears.map((year) => (
                    <SelectItem key={year} value={year.toString()}>
                      {year}
                    </SelectItem>
                  ))
                ) : (
                  <SelectItem value="2025" disabled>No data available</SelectItem>
                )}
              </SelectContent>
            </Select>

            <Select value={selectedWeek} onValueChange={setSelectedWeek}>
              <SelectTrigger className="w-full sm:w-24">
                <SelectValue placeholder="Week" />
              </SelectTrigger>
              <SelectContent>
                {Array.from({ length: 18 }, (_, i) => (
                  <SelectItem key={i + 1} value={(i + 1).toString()}>
                    Week {i + 1}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button onClick={handleFetch} disabled={isLoading} size="sm">
              {isLoading ? "Loading..." : "Go Cry"}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Origin Story Section */}
        <div className="mb-8 p-6 bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 rounded-lg border-2 border-yellow-200 dark:border-yellow-800">
          <div className="flex flex-col lg:flex-row gap-6 items-start">
            {/* Mobile Screenshot */}
            <div className="flex-shrink-0">
              <div className="relative">
                <div className="w-64 h-96 mx-auto bg-gray-200 dark:bg-gray-700 rounded-2xl shadow-lg border-4 border-gray-300 dark:border-gray-600 flex items-center justify-center">
                  {/* Phone Frame Mockup */}
                  <div className="text-center text-gray-500 dark:text-gray-400">
                    <div className="text-sm mb-2">📱 Group Chat Screenshot</div>
                    <div className="text-xs">(Upload to /public/images/)</div>
                  </div>
                </div>
                <div className="absolute top-4 left-1/2 transform -translate-x-1/2 w-16 h-1 bg-gray-400 rounded-full"></div>
                <div className="absolute top-8 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-gray-400 rounded-full"></div>
              </div>
            </div>

            {/* Story Content */}
            <div className="flex-1">
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                📜 The Origin of "fuuuuck gronk on da bench"
              </h3>

              <div className="prose prose-sm dark:prose-invert max-w-none">
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  On <strong>September 9, 2021 - Week 1</strong>, a legend was born in the group chat.
                  Rob Gronkowski, sitting pretty on someone's bench, exploded for <strong>29.0 points</strong>
                  in his return to fantasy relevance with Tom Brady and the Tampa Bay Buccaneers.
                </p>

                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  The group chat erupted. The pain was real. The memes were born. And thus,
                  "fuuuuck gronk on da bench" became the rallying cry for every fantasy manager
                  who's ever left points on the sideline.
                </p>

                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 mb-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">📊 The Legendary Performance</h4>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    <div><strong>Player:</strong> Rob Gronkowski (TE, Tampa Bay)</div>
                    <div><strong>Date:</strong> September 9, 2021 (Week 1)</div>
                    <div><strong>Points:</strong> 29.0 (absolutely devastating on the bench)</div>
                    <div><strong>Victim:</strong> Luke Benedict ("Tyreek Hill's Daycare")</div>
                  </div>
                  <a
                    href="https://fantasy.espn.com/football/boxscore?leagueId=1729198&matchupPeriodId=1&scoringPeriodId=1&seasonId=2021&teamId=3&view=scoringperiod"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 mt-3 text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    <ExternalLinkIcon className="h-4 w-4" />
                    View the Legendary ESPN Boxscore
                  </a>
                </div>

                <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                  This section exists to honor that moment and all the bench heroes who followed.
                  Because in fantasy football, the bench is where dreams go to explode. 💥
                </p>
              </div>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-16 bg-muted rounded-lg"></div>
              </div>
            ))}
          </div>
        ) : data?.bench_heroes && data.bench_heroes.length > 0 ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
              <CalendarIcon className="h-4 w-4" />
              {data.year} • Week {data.week} • {data.total_bench_players} total bench players
            </div>

            {data.bench_heroes.map((player, index) => (
              <div key={`${player.player_name}-${index}`} className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-muted/30 to-transparent rounded-lg"
                     style={{
                       width: `${getPointsBarWidth(player.points, maxPoints)}%`
                     }}
                />

                <div className="relative p-4 border rounded-lg hover:bg-muted/20 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge
                          className={`${getPositionColor(player.position)} text-white text-xs px-2 py-0.5`}
                          variant="secondary"
                        >
                          {player.position}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {player.pro_team}
                        </span>
                      </div>

                      <h4 className="font-semibold text-lg truncate">
                        {player.player_name}
                      </h4>

                      <div className="text-sm text-muted-foreground">
                        <div className="truncate">
                          {player.team_name} • {player.owner}
                        </div>
                      </div>
                    </div>

                    <div className="text-right ml-4 flex flex-col items-end gap-2">
                      <div className="text-2xl font-bold text-primary">
                        {player.points}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        pts
                      </div>
                      {data && generateESPNLink(player.team_id, data.year, data.week) && (
                        <a
                          href={generateESPNLink(player.team_id, data.year, data.week)!}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 transition-colors"
                        >
                          <ExternalLinkIcon className="h-3 w-3" />
                          ESPN
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {data.bench_heroes.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <p>No bench players found for this week.</p>
                <p className="text-sm">Everyone started their studs! 🎉</p>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            <TrophyIcon className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
            <p>Select a year and week to see which bench players would have won you the week.</p>
            <p className="text-sm mt-1">Spoiler alert: it's always Gronk. 😭</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}