'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Clover, Zap, TrendingUp, Target, Calendar } from "lucide-react"
import { queuedFetch, PRIORITY } from "@/lib/api-queue"

interface LuckyGame {
  luck: number
  week: number
  opponent: string
  margin: number
}

interface SeasonLuck {
  year: number
  team_name: string
  owner: string
  total_luck: number
  average_luck: number
  games_played: number
  biggest_lucky_game: LuckyGame
  biggest_unlucky_game: LuckyGame
}

interface SingleMatchupLuck {
  year: number
  week: number
  team_name: string
  owner: string
  opponent: string
  luck: number
  actual_score: number
  projected_score: number
  opponent_actual: number
  opponent_projected: number
  actual_margin: number
  projected_margin: number
}

interface LuckAnalysisData {
  luckiest_seasons: SeasonLuck[]
  unluckiest_seasons: SeasonLuck[]
  luckiest_single_matchups: SingleMatchupLuck[]
  unluckiest_single_matchups: SingleMatchupLuck[]
  total_seasons_analyzed: number
  total_matchups_analyzed: number
}

export function LuckAnalysis() {
  const [luckData, setLuckData] = useState<LuckAnalysisData | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const fetchLuckAnalysis = async () => {
      setLoading(true)
      try {
        console.log('Fetching luck analysis data')
        const response = await queuedFetch('/api/luck-analysis', {
          cache: 'no-store',
        }, {
          priority: PRIORITY.HIGH,
          component: 'LuckAnalysis'
        })
        console.log('Luck analysis response status:', response.status)

        if (response.ok) {
          const data = await response.json()
          console.log('Luck analysis data:', data)
          setLuckData(data)
        } else {
          console.error('Failed to fetch luck analysis')
          setLuckData(null)
        }
      } catch (error) {
        console.error('Error fetching luck analysis:', error)
        setLuckData(null)
      } finally {
        setLoading(false)
      }
    }

    fetchLuckAnalysis()
  }, [])

  const getLuckBadgeColor = (luck: number) => {
    if (luck >= 20) return "bg-green-600 text-white border-green-700"
    if (luck >= 10) return "bg-green-500 text-white border-green-600"
    if (luck >= 5) return "bg-green-100 text-green-800 border-green-300"
    if (luck >= -5) return "bg-gray-100 text-gray-800 border-gray-300"
    if (luck >= -10) return "bg-red-100 text-red-800 border-red-300"
    if (luck >= -20) return "bg-red-500 text-white border-red-600"
    return "bg-red-600 text-white border-red-700"
  }

  const formatLuck = (luck: number) => {
    const sign = luck >= 0 ? '+' : ''
    return `${sign}${luck.toFixed(1)}`
  }

  const renderSeasonCard = (season: SeasonLuck, index: number, isLucky: boolean) => (
    <Card key={`${season.owner}-${season.year}`} className="transition-all duration-200 hover:shadow-lg">
      <CardContent className="p-4 sm:p-6">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold">#{index + 1}</span>
              {isLucky ? (
                <Clover className="h-4 w-4 text-green-600" />
              ) : (
                <Zap className="h-4 w-4 text-red-600" />
              )}
            </div>
            <Badge
              className={`text-sm font-bold border ${getLuckBadgeColor(season.total_luck)}`}
            >
              {formatLuck(season.total_luck)} pts
            </Badge>
          </div>

          <div>
            <p className="font-semibold text-sm">{season.owner}</p>
            <p className="text-xs text-muted-foreground">{season.team_name} • {season.year}</p>
          </div>

          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <p className="text-muted-foreground">Average per game</p>
              <p className="font-semibold">{formatLuck(season.average_luck)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Games played</p>
              <p className="font-semibold">{season.games_played}</p>
            </div>
          </div>

          <div className="space-y-2 text-xs">
            <div className="p-2 bg-green-50 rounded border border-green-200">
              <p className="text-green-700 font-medium">Luckiest Game</p>
              <p className="text-green-600">
                Week {season.biggest_lucky_game.week} vs {season.biggest_lucky_game.opponent}
              </p>
              <p className="text-green-800 font-semibold">
                {formatLuck(season.biggest_lucky_game.luck)} pts
              </p>
            </div>
            <div className="p-2 bg-red-50 rounded border border-red-200">
              <p className="text-red-700 font-medium">Unluckiest Game</p>
              <p className="text-red-600">
                Week {season.biggest_unlucky_game.week} vs {season.biggest_unlucky_game.opponent}
              </p>
              <p className="text-red-800 font-semibold">
                {formatLuck(season.biggest_unlucky_game.luck)} pts
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  const renderMatchupCard = (matchup: SingleMatchupLuck, index: number, isLucky: boolean) => (
    <Card key={`${matchup.owner}-${matchup.year}-${matchup.week}`} className="transition-all duration-200 hover:shadow-lg">
      <CardContent className="p-4 sm:p-6">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold">#{index + 1}</span>
              {isLucky ? (
                <Clover className="h-4 w-4 text-green-600" />
              ) : (
                <Zap className="h-4 w-4 text-red-600" />
              )}
            </div>
            <Badge
              className={`text-sm font-bold border ${getLuckBadgeColor(matchup.luck)}`}
            >
              {formatLuck(matchup.luck)} pts
            </Badge>
          </div>

          <div>
            <p className="font-semibold text-sm">{matchup.owner}</p>
            <p className="text-xs text-muted-foreground">{matchup.team_name}</p>
          </div>

          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Calendar className="h-3 w-3" />
            <span>{matchup.year} Week {matchup.week} vs {matchup.opponent}</span>
          </div>

          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <p className="text-muted-foreground">Actual Score</p>
              <p className="font-semibold">{matchup.actual_score.toFixed(1)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Projected Score</p>
              <p className="font-semibold">{matchup.projected_score.toFixed(1)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Actual Margin</p>
              <p className="font-semibold">{formatLuck(matchup.actual_margin)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Projected Margin</p>
              <p className="font-semibold">{formatLuck(matchup.projected_margin)}</p>
            </div>
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
              <Clover className="h-8 w-8 mx-auto mb-2 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Analyzing luck factors...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!luckData) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8">
            <Clover className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Failed to load luck analysis</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Defensive checks for data structure
  const safeData = {
    luckiest_seasons: luckData.luckiest_seasons || [],
    unluckiest_seasons: luckData.unluckiest_seasons || [],
    luckiest_single_matchups: luckData.luckiest_single_matchups || [],
    unluckiest_single_matchups: luckData.unluckiest_single_matchups || [],
    total_seasons_analyzed: luckData.total_seasons_analyzed || 0,
    total_matchups_analyzed: luckData.total_matchups_analyzed || 0
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Clover className="h-6 w-6 text-green-500" />
          <h2 className="text-xl font-semibold">Luck Analysis</h2>
        </div>
        <p className="text-sm text-muted-foreground">
          Teams that most outperformed or underperformed their projections
        </p>
      </CardHeader>

      <CardContent>
        <div className="space-y-6">
          <div className="text-center py-2 px-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              🍀 Analyzing {safeData.total_matchups_analyzed} matchups across {safeData.total_seasons_analyzed} seasons
            </p>
          </div>

          <Tabs defaultValue="seasons" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="seasons" className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Season Analysis
              </TabsTrigger>
              <TabsTrigger value="matchups" className="flex items-center gap-2">
                <Target className="h-4 w-4" />
                Single Matchups
              </TabsTrigger>
            </TabsList>

            <TabsContent value="seasons" className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Clover className="h-5 w-5 text-green-500" />
                  Luckiest Seasons (Top 3)
                </h3>
                {safeData.luckiest_seasons.length > 0 ? (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {safeData.luckiest_seasons.map((season, index) =>
                      renderSeasonCard(season, index, true)
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Clover className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">No lucky seasons found</p>
                  </div>
                )}
              </div>

              <div className="space-y-4 pt-4 border-t border-border">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Zap className="h-5 w-5 text-red-500" />
                  Unluckiest Seasons (Top 3)
                </h3>
                {safeData.unluckiest_seasons.length > 0 ? (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {safeData.unluckiest_seasons.map((season, index) =>
                      renderSeasonCard(season, index, false)
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Zap className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">No unlucky seasons found</p>
                  </div>
                )}
              </div>
            </TabsContent>

            <TabsContent value="matchups" className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Clover className="h-5 w-5 text-green-500" />
                  Luckiest Single Matchups (Top 5)
                </h3>
                {safeData.luckiest_single_matchups.length > 0 ? (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {safeData.luckiest_single_matchups.map((matchup, index) =>
                      renderMatchupCard(matchup, index, true)
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Clover className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">No lucky matchups found</p>
                  </div>
                )}
              </div>

              <div className="space-y-4 pt-4 border-t border-border">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Zap className="h-5 w-5 text-red-500" />
                  Unluckiest Single Matchups (Top 5)
                </h3>
                {safeData.unluckiest_single_matchups.length > 0 ? (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {safeData.unluckiest_single_matchups.map((matchup, index) =>
                      renderMatchupCard(matchup, index, false)
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Zap className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">No unlucky matchups found</p>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </CardContent>
    </Card>
  )
}