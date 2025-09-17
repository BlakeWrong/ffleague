"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { CalendarIcon, TrophyIcon } from "lucide-react"
import { queuedFetch } from "@/lib/api-queue"

interface Team {
  name: string
  score: number
}

interface Matchup {
  week: number
  home_team: Team
  away_team: Team
}

interface MatchupsData {
  week: number
  year: number
  matchups: Matchup[]
}

interface MatchupsSectionProps {
  currentWeek?: number
  currentYear?: number
}

export function MatchupsSection({ currentWeek = 1, currentYear = 2025 }: MatchupsSectionProps) {
  const [selectedYear, setSelectedYear] = useState(currentYear.toString())
  const [selectedWeek, setSelectedWeek] = useState(currentWeek.toString())
  const [matchupsData, setMatchupsData] = useState<MatchupsData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | undefined>()
  const [availableYears, setAvailableYears] = useState<number[]>([])
  const [availableWeeks, setAvailableWeeks] = useState<number[]>([])
  const [weeksLoading, setWeeksLoading] = useState(false)

  // Initialize with current week/year
  useEffect(() => {
    setSelectedYear(currentYear.toString())
    setSelectedWeek(currentWeek.toString())
  }, [currentYear, currentWeek])

  // Fetch available years
  useEffect(() => {
    async function fetchAvailableYears() {
      try {
        console.log('Fetching available years...')
        const response = await queuedFetch('/api/available-years')
        console.log('Available years response status:', response.status)
        if (response.ok) {
          const data = await response.json()
          console.log('Available years data:', data)
          const allYears = data.supported_years || data.available_years || []
          setAvailableYears(allYears)
        } else {
          const errorText = await response.text()
          console.error('Failed to fetch available years:', response.status, errorText)
        }
      } catch (error) {
        console.error('Failed to fetch available years:', error)
      }
    }
    fetchAvailableYears()
  }, [])

  // Fetch available weeks when year changes
  useEffect(() => {
    if (!selectedYear) return
    async function fetchAvailableWeeks() {
      setWeeksLoading(true)
      try {
        console.log('Fetching available weeks for year:', selectedYear)
        const response = await queuedFetch(`/api/available-weeks/${selectedYear}`)
        console.log('Available weeks response status:', response.status)
        if (response.ok) {
          const data = await response.json()
          console.log('Available weeks data:', data)
          const allWeeks = data.available_weeks || []
          setAvailableWeeks(allWeeks)
        } else {
          const errorText = await response.text()
          console.error('Failed to fetch available weeks:', response.status, errorText)
        }
      } catch (error) {
        console.error('Failed to fetch available weeks:', error)
      } finally {
        setWeeksLoading(false)
      }
    }
    fetchAvailableWeeks()
  }, [selectedYear])

  const fetchMatchups = useCallback(async (year: number, week: number) => {
    setIsLoading(true)
    setError(undefined)
    try {
      let url: string
      if (year === currentYear) {
        url = `/api/matchups?week=${week}`
      } else {
        url = `/api/matchups?year=${year}&week=${week}`
      }

      const response = await fetch(url)
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || `Request failed with status ${response.status}`)
      }

      const data = await response.json()
      setMatchupsData(data)
    } catch (error) {
      console.error('Matchups fetch error:', error)
      setError(error instanceof Error ? error.message : 'Unknown error')
    } finally {
      setIsLoading(false)
    }
  }, [currentYear])

  // Auto-fetch matchups when component mounts or selections change
  useEffect(() => {
    if (selectedYear && selectedWeek) {
      fetchMatchups(parseInt(selectedYear), parseInt(selectedWeek))
    }
  }, [selectedYear, selectedWeek, fetchMatchups])

  const getWinner = (matchup: Matchup) => {
    if (matchup.home_team.score > matchup.away_team.score) return 'home'
    if (matchup.away_team.score > matchup.home_team.score) return 'away'
    return 'tie'
  }

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
            <p className="text-sm text-muted-foreground">
              Head-to-head matchups and scores for any week
            </p>
            <p className="text-xs text-yellow-700 dark:text-yellow-300">
              💡 Note: Data only available from 2019 onwards due to ESPN API limitations
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-2">
            <Select value={selectedYear} onValueChange={setSelectedYear}>
              <SelectTrigger className="w-full sm:w-32">
                <SelectValue placeholder="Year" />
              </SelectTrigger>
              <SelectContent>
                {availableYears.map((year) => (
                  <SelectItem key={year} value={year.toString()}>
                    {year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={selectedWeek}
              onValueChange={setSelectedWeek}
              disabled={weeksLoading || availableWeeks.length === 0}
            >
              <SelectTrigger className="w-full sm:w-32">
                <SelectValue placeholder={weeksLoading ? "Loading..." : "Week"} />
              </SelectTrigger>
              <SelectContent>
                {availableWeeks.map((week) => (
                  <SelectItem key={week} value={week.toString()}>
                    Week {week}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="text-center py-8">
            <p className="text-muted-foreground">Loading matchups...</p>
          </div>
        ) : matchupsData?.matchups ? (
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-4">
              <CalendarIcon className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">
                {matchupsData.year} Season - Week {matchupsData.week}
              </span>
              <Badge variant="outline" className="text-xs">
                {matchupsData.matchups.length} matchups
              </Badge>
            </div>

            <div className="grid gap-3">
              {matchupsData.matchups.map((matchup, index) => {
                const winner = getWinner(matchup)
                return (
                  <div
                    key={index}
                    className="bg-muted/30 rounded-lg p-4 border border-border/50"
                  >
                    <div className="flex items-center justify-between">
                      {/* Away Team */}
                      <div className={`flex-1 text-left ${
                        winner === 'away' ? 'font-semibold text-foreground' : 'text-muted-foreground'
                      }`}>
                        <div className="text-sm sm:text-base">
                          {matchup.away_team.name}
                        </div>
                        <div className="text-lg font-bold">
                          {matchup.away_team.score}
                        </div>
                      </div>

                      {/* VS Separator */}
                      <div className="px-4">
                        <div className="flex flex-col items-center">
                          <span className="text-xs text-muted-foreground font-medium">VS</span>
                          {winner === 'tie' && (
                            <span className="text-xs text-yellow-600 font-medium">TIE</span>
                          )}
                          {winner !== 'tie' && (
                            <TrophyIcon className="h-3 w-3 text-yellow-500 mt-1" />
                          )}
                        </div>
                      </div>

                      {/* Home Team */}
                      <div className={`flex-1 text-right ${
                        winner === 'home' ? 'font-semibold text-foreground' : 'text-muted-foreground'
                      }`}>
                        <div className="text-sm sm:text-base">
                          {matchup.home_team.name}
                        </div>
                        <div className="text-lg font-bold">
                          {matchup.home_team.score}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-muted-foreground">No matchups available for this week</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}