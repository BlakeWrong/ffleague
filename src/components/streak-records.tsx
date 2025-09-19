'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Zap, TrendingUp, TrendingDown, Calendar, Target } from "lucide-react"
import { queuedFetch } from "@/lib/api-queue"

interface StreakGame {
  year: number
  week: number
  team_id: number
  team_name: string
  owner: string
  result: string
  score: number
  opponent_score: number
}

interface Streak {
  owner: string
  team_names: string[]
  length: number
  start_year: number
  start_week: number
  end_year: number
  end_week: number
  games: StreakGame[]
  is_current?: boolean
}

interface StreakRecordsData {
  analysis_type: string
  year?: number
  years_analyzed: number[]
  longest_win_streaks: Streak[]
  longest_loss_streaks: Streak[]
  current_streaks: Streak[]
  total_games_analyzed: number
}

export function StreakRecords() {
  const [streakData, setStreakData] = useState<StreakRecordsData | null>(null)
  const [availableYears, setAvailableYears] = useState<number[]>([])
  const [selectedYear, setSelectedYear] = useState<string>('all-time')
  const [loading, setLoading] = useState(false)

  const fetchStreakRecords = useCallback(async (year?: string) => {
    setLoading(true)
    try {
      console.log('Fetching streak records for:', year)
      const yearParam = year === 'all-time' ? '' : `?year=${year}`
      const response = await queuedFetch(`/api/streak-records${yearParam}`)
      console.log('Streak records response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('Streak records data:', data)
        setStreakData(data)
      } else {
        console.error('Failed to fetch streak records')
        setStreakData(null)
      }
    } catch (error) {
      console.error('Error fetching streak records:', error)
      setStreakData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const fetchAvailableYears = async () => {
      try {
        console.log('Fetching available years for streak records')
        const response = await queuedFetch('/api/available-years')
        console.log('Available years response status:', response.status)
        if (response.ok) {
          const data = await response.json()
          console.log('Available years data:', data)
          const allYears = data.available_years || []
          setAvailableYears(allYears)
        } else {
          const errorText = await response.text()
          console.error('Failed to fetch available years:', response.status, errorText)
        }
      } catch (error) {
        console.error('Error fetching available years:', error)
      }
    }

    fetchAvailableYears()
  }, [])

  useEffect(() => {
    fetchStreakRecords(selectedYear)
  }, [selectedYear, fetchStreakRecords])

  const formatStreakPeriod = (streak: Streak) => {
    if (streak.start_year === streak.end_year) {
      return `${streak.start_year} (Weeks ${streak.start_week}-${streak.end_week})`
    } else {
      return `${streak.start_year} Week ${streak.start_week} - ${streak.end_year} Week ${streak.end_week}`
    }
  }

  const getStreakBadgeVariant = (length: number, isWin: boolean) => {
    if (length >= 5) return isWin ? "default" : "destructive"
    if (length >= 3) return isWin ? "secondary" : "outline"
    return "outline"
  }

  const renderStreakCard = (streak: Streak, index: number, isWinStreak: boolean) => (
    <Card key={`${streak.owner}-${streak.start_year}-${streak.start_week}`} className="relative">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1">
              <span className="text-lg font-bold">#{index + 1}</span>
              {isWinStreak ? (
                <TrendingUp className="h-4 w-4 text-green-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600" />
              )}
            </div>
            <Badge
              variant={getStreakBadgeVariant(streak.length, isWinStreak)}
              className={`text-sm font-bold ${
                isWinStreak && streak.length >= 3
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : ''
              }`}
            >
              {streak.length} {isWinStreak ? 'Wins' : 'Losses'}
            </Badge>
            {streak.is_current && (
              <Badge variant="outline" className="text-xs">
                <Zap className="h-3 w-3 mr-1" />
                Current
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-2">
          <div>
            <p className="font-semibold text-sm">{streak.owner}</p>
            <p className="text-xs text-muted-foreground">
              {streak.team_names.join(', ')}
            </p>
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Calendar className="h-3 w-3" />
            <span>{formatStreakPeriod(streak)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <Target className="h-8 w-8 mx-auto mb-2 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Loading streak records...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!streakData) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8">
            <Target className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Failed to load streak records</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="h-6 w-6 text-blue-500" />
            <h2 className="text-xl font-semibold">League Streak Records</h2>
          </div>
          <Select value={selectedYear} onValueChange={setSelectedYear}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select year" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all-time">All-Time Records</SelectItem>
              {availableYears.map((year) => (
                <SelectItem key={year} value={year.toString()}>
                  {year} Season
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <p className="text-sm text-muted-foreground">
          Longest winning and losing streaks in league history
        </p>
      </CardHeader>

      <CardContent>
        <div className="space-y-6">
          <div className="text-center py-2 px-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              🎯 Analyzing {streakData.total_games_analyzed} games across {streakData.years_analyzed.length} seasons ({streakData.years_analyzed[0]} - {streakData.years_analyzed[streakData.years_analyzed.length - 1]})
            </p>
          </div>

          <Tabs defaultValue="wins" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="wins" className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Winning Streaks
              </TabsTrigger>
              <TabsTrigger value="losses" className="flex items-center gap-2">
                <TrendingDown className="h-4 w-4" />
                Losing Streaks
              </TabsTrigger>
            </TabsList>

            <TabsContent value="wins" className="space-y-4">
              {streakData.longest_win_streaks.length > 0 ? (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {streakData.longest_win_streaks.map((streak, index) =>
                    renderStreakCard(streak, index, true)
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <TrendingUp className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">No winning streaks found</p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="losses" className="space-y-4">
              {streakData.longest_loss_streaks.length > 0 ? (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {streakData.longest_loss_streaks.map((streak, index) =>
                    renderStreakCard(streak, index, false)
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <TrendingDown className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">No losing streaks found</p>
                </div>
              )}
            </TabsContent>
          </Tabs>

          {streakData.current_streaks.length > 0 && selectedYear === 'all-time' && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 pt-4 border-t border-border">
                <Zap className="h-5 w-5 text-yellow-500" />
                <h3 className="text-lg font-semibold">Current Active Streaks</h3>
              </div>
              <Tabs defaultValue="active-wins" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="active-wins" className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" />
                    Active Winning Streaks
                  </TabsTrigger>
                  <TabsTrigger value="active-losses" className="flex items-center gap-2">
                    <TrendingDown className="h-4 w-4" />
                    Active Losing Streaks
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="active-wins" className="space-y-4">
                  {streakData.current_streaks.filter(streak =>
                    streak.games[0]?.result === 'W' && streak.length >= 3
                  ).length > 0 ? (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                      {streakData.current_streaks
                        .filter(streak => streak.games[0]?.result === 'W' && streak.length >= 3)
                        .map((streak, index) =>
                          renderStreakCard(streak, index, true)
                        )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <TrendingUp className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                      <p className="text-sm text-muted-foreground">No active winning streaks of 3+ games</p>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="active-losses" className="space-y-4">
                  {streakData.current_streaks.filter(streak =>
                    streak.games[0]?.result === 'L' && streak.length >= 3
                  ).length > 0 ? (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                      {streakData.current_streaks
                        .filter(streak => streak.games[0]?.result === 'L' && streak.length >= 3)
                        .map((streak, index) =>
                          renderStreakCard(streak, index, false)
                        )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <TrendingDown className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                      <p className="text-sm text-muted-foreground">No active losing streaks of 3+ games</p>
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}