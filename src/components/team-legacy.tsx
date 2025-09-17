'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { BarChart3, Trophy, Medal, Award, TrendingUp, TrendingDown, Minus, History } from "lucide-react"

interface TeamPlacement {
  year: number
  placement: number
}

interface TeamLegacy {
  owner: string
  years_active: number[]
  placements: TeamPlacement[]
  total_wins: number
  total_losses: number
  total_ties: number
  total_points_for: number
  total_points_against: number
  seasons_played: number
  championship_years: number[]
  runner_up_years: number[]
  third_place_years: number[]
  average_placement: number | null
  has_placement_history: boolean
  completed_seasons: number
  win_percentage: number
  avg_points_per_game: number
  championships: number
  runner_ups: number
  third_places: number
  gap_years: number[]
  current_team_name: string
  aka_names: string[]
  years_in_league: number
  total_years_available: number
}

interface TeamLegacyData {
  total_teams: number
  years_analyzed: number[]
  team_legacy: TeamLegacy[]
}

export function TeamLegacy() {
  const [legacyData, setLegacyData] = useState<TeamLegacyData | null>(null)
  const [loading, setLoading] = useState(false)

  const fetchTeamLegacy = useCallback(async () => {
    setLoading(true)
    try {
      console.log('Fetching team legacy data')
      const response = await fetch('/api/team-legacy')
      console.log('Team legacy response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('Team legacy data:', data)
        setLegacyData(data)
      } else {
        console.error('Failed to fetch team legacy data')
        setLegacyData(null)
      }
    } catch (error) {
      console.error('Error fetching team legacy:', error)
      setLegacyData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTeamLegacy()
  }, [fetchTeamLegacy])


  const getPlacementTrend = (placements: TeamPlacement[]) => {
    if (placements.length < 2) return <Minus className="h-4 w-4 text-gray-400" />

    // Sort by year to get chronological order
    const sorted = [...placements].sort((a, b) => a.year - b.year)
    const recent = sorted.slice(-3) // Last 3 years

    if (recent.length < 2) return <Minus className="h-4 w-4 text-gray-400" />

    const trend = recent[recent.length - 1].placement - recent[0].placement

    if (trend < 0) return <TrendingUp className="h-4 w-4 text-green-500" /> // Getting better (lower placement)
    if (trend > 0) return <TrendingDown className="h-4 w-4 text-red-500" /> // Getting worse (higher placement)
    return <Minus className="h-4 w-4 text-gray-400" />
  }

  const PlacementHistory = ({ placements }: { placements: TeamPlacement[] }) => {
    // Prepare data - exclude current year (2025)
    const completedPlacements = placements
      .filter(p => p.year < 2025)
      .sort((a, b) => b.year - a.year) // Most recent first

    if (completedPlacements.length === 0) {
      return (
        <div className="h-16 flex items-center justify-center text-sm text-muted-foreground">
          No completed seasons yet
        </div>
      )
    }

    const getPlacementColor = (placement: number) => {
      if (placement === 1) return "bg-yellow-400 text-yellow-900 border-yellow-500"
      if (placement === 2) return "bg-gray-300 text-gray-900 border-gray-400"
      if (placement === 3) return "bg-amber-400 text-amber-900 border-amber-500"
      if (placement <= 4) return "bg-green-200 text-green-800 border-green-300"
      if (placement <= 6) return "bg-blue-200 text-blue-800 border-blue-300"
      if (placement <= 8) return "bg-orange-200 text-orange-800 border-orange-300"
      return "bg-red-200 text-red-800 border-red-300"
    }

    const getPlacementIcon = (placement: number) => {
      if (placement === 1) return "🏆"
      if (placement === 2) return "🥈"
      if (placement === 3) return "🥉"
      return `#${placement}`
    }

    return (
      <div className="space-y-3">
        {/* Recent years timeline */}
        <div className="flex items-center gap-2 flex-wrap">
          {completedPlacements.slice(0, 8).map((p) => (
            <div
              key={p.year}
              className={`px-3 py-2 rounded-lg border text-sm font-semibold transition-all hover:scale-105 ${getPlacementColor(p.placement)}`}
              title={`${p.year}: ${getPlacementIcon(p.placement)} place`}
            >
              <div className="text-xs opacity-75">{p.year}</div>
              <div className="text-sm font-bold">{getPlacementIcon(p.placement)}</div>
            </div>
          ))}
          {completedPlacements.length > 8 && (
            <div className="text-xs text-muted-foreground px-2">
              +{completedPlacements.length - 8} more
            </div>
          )}
        </div>

        {/* Summary stats */}
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span>Best: {getPlacementIcon(Math.min(...completedPlacements.map(p => p.placement)))}</span>
          <span>Worst: #{Math.max(...completedPlacements.map(p => p.placement))}</span>
          <span>Recent: {getPlacementIcon(completedPlacements[0]?.placement)} ({completedPlacements[0]?.year})</span>
        </div>
      </div>
    )
  }

  const AKANamesButton = ({ akaNames }: { akaNames: string[] }) => {
    if (akaNames.length === 0) return null

    return (
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline" size="sm" className="h-6 px-2 py-0 text-xs">
            <History className="h-3 w-3 mr-1" />
            {akaNames.length} AKA
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-72 sm:w-80" align="start" side="bottom" sideOffset={4}>
          <div className="space-y-2">
            <h4 className="font-semibold text-sm">Previous Team Names</h4>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {akaNames.map((name, index) => (
                <div key={index} className="text-sm py-1 px-2 bg-muted rounded text-muted-foreground">
                  {name}
                </div>
              ))}
            </div>
          </div>
        </PopoverContent>
      </Popover>
    )
  }

  const getRankBadgeColor = (rank: number) => {
    if (rank === 1) return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 border-yellow-300"
    if (rank === 2) return "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200 border-gray-300"
    if (rank === 3) return "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 border-amber-300"
    if (rank <= 5) return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 border-green-300"
    if (rank <= 8) return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 border-blue-300"
    return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 border-red-300"
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <BarChart3 className="h-6 w-6 text-blue-500" />
          <h2 className="text-xl font-semibold">Team Legacy Rankings</h2>
        </div>
        <p className="text-sm text-muted-foreground">
          All-time performance ranked by average placement across league history
        </p>
      </CardHeader>

      <CardContent>
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
            <p className="text-sm text-muted-foreground">Analyzing team legacies...</p>
          </div>
        ) : legacyData ? (
          <div className="space-y-4">
            <div className="text-center py-2 px-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <p className="text-sm text-blue-700 dark:text-blue-300">
                📊 Analyzing {legacyData.total_teams} teams across {legacyData.years_analyzed.length} seasons ({legacyData.years_analyzed[legacyData.years_analyzed.length - 1]} - {legacyData.years_analyzed[0]})
              </p>
            </div>

            <div className="grid gap-4">
              {legacyData.team_legacy.map((team, index) => {
                const rank = index + 1
                return (
                  <Card
                    key={team.owner}
                    className="transition-all duration-200 hover:shadow-lg"
                  >
                    <CardContent className="p-6">
                      <div className="flex flex-col gap-4">
                        {/* Header Row */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <Badge className={`${getRankBadgeColor(rank)} font-bold text-lg px-3 py-1 border`}>
                              {team.has_placement_history ? `#${rank}` : 'NEW'}
                            </Badge>
                            <div>
                              <div className="flex items-center gap-2">
                                <h3 className="font-semibold text-lg">{team.current_team_name}</h3>
                                <AKANamesButton akaNames={team.aka_names} />
                              </div>
                              <p className="text-sm text-muted-foreground">{team.owner}</p>
                            </div>
                          </div>

                          <div className="flex items-center gap-4">
                            <div className="text-center">
                              <p className="text-2xl font-bold text-primary">
                                {team.has_placement_history ? team.average_placement : '–'}
                              </p>
                              <p className="text-xs text-muted-foreground">AVG RANK</p>
                              {!team.has_placement_history && (
                                <p className="text-xs text-yellow-600 dark:text-yellow-400">First Season</p>
                              )}
                            </div>
                            {team.has_placement_history && getPlacementTrend(team.placements)}
                          </div>
                        </div>

                        {/* Stats Row */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4 py-2 border-t border-border">
                          <div className="text-center">
                            <p className="text-lg font-semibold text-green-600 dark:text-green-400">
                              {team.completed_seasons}/{legacyData.years_analyzed.filter(y => y < 2025).length}
                            </p>
                            <p className="text-xs text-muted-foreground">SEASONS</p>
                          </div>
                          <div className="text-center">
                            <p className="text-lg font-semibold">
                              {team.win_percentage}%
                            </p>
                            <p className="text-xs text-muted-foreground">WIN RATE</p>
                          </div>
                          <div className="text-center">
                            <p className="text-lg font-semibold text-blue-600 dark:text-blue-400">
                              {team.avg_points_per_game}
                            </p>
                            <p className="text-xs text-muted-foreground">PPG</p>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-semibold flex items-center justify-center gap-1">
                              {team.championships > 0 && <><Trophy className="h-4 w-4 text-yellow-500" /><span>{team.championships}</span></>}
                              {team.runner_ups > 0 && <><Medal className="h-4 w-4 text-gray-400" /><span>{team.runner_ups}</span></>}
                              {team.third_places > 0 && <><Award className="h-4 w-4 text-amber-600" /><span>{team.third_places}</span></>}
                              {team.championships === 0 && team.runner_ups === 0 && team.third_places === 0 && <span className="text-muted-foreground">-</span>}
                            </div>
                            <p className="text-xs text-muted-foreground">PODIUM</p>
                          </div>
                          <div className="text-center">
                            <p className="text-lg font-semibold">
                              {team.total_wins}-{team.total_losses}
                              {team.total_ties > 0 && `-${team.total_ties}`}
                            </p>
                            <p className="text-xs text-muted-foreground">RECORD</p>
                          </div>
                          <div className="text-center">
                            <p className="text-lg font-semibold">
                              {team.gap_years.length}
                            </p>
                            <p className="text-xs text-muted-foreground">GAPS</p>
                          </div>
                        </div>

                        {/* Chart Row */}
                        <div className="flex flex-col gap-2 pt-2 border-t border-border">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">Placement History (Recent Seasons)</span>
                            <span className="text-xs text-muted-foreground">
                              🏆 1st • 🥈 2nd • 🥉 3rd
                            </span>
                          </div>
                          <PlacementHistory placements={team.placements} />
                          {team.gap_years.length > 0 && (
                            <p className="text-xs text-yellow-700 dark:text-yellow-300">
                              ⚠️ Missed seasons: {team.gap_years.join(', ')}
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
            <p className="text-muted-foreground">No team legacy data available</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}