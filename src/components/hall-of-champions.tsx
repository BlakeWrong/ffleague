'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Trophy, Medal, Award, Crown } from "lucide-react"

interface Champion {
  place: number
  team_id: number
  team_name: string
  owner: string
  wins: number
  losses: number
  ties: number
  points_for: number
  points_against: number
  final_standing: number
  logo_url?: string | null
}

interface ChampionsData {
  year: number
  champions: Champion[]
  season_complete: boolean
}

interface HallOfChampionsProps {
  currentYear?: number
}

export function HallOfChampions({ currentYear = 2025 }: HallOfChampionsProps) {
  const [championsData, setChampionsData] = useState<ChampionsData | null>(null)
  const [availableYears, setAvailableYears] = useState<number[]>([])
  const [selectedYear, setSelectedYear] = useState<string>(currentYear.toString())
  const [loading, setLoading] = useState(false)

  const fetchChampions = useCallback(async (year: number) => {
    setLoading(true)
    try {
      console.log('Fetching champions for year:', year)
      const response = await fetch(`/api/champions?year=${year}`)
      console.log('Champions response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('Champions data:', data)
        setChampionsData(data)
      } else {
        console.error('Failed to fetch champions data')
        setChampionsData(null)
      }
    } catch (error) {
      console.error('Error fetching champions:', error)
      setChampionsData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const fetchAvailableYears = async () => {
      try {
        console.log('Fetching available years for champions')
        const response = await fetch('/api/available-years')
        console.log('Available years response status:', response.status)
        if (response.ok) {
          const data = await response.json()
          console.log('Available years data:', data)
          const allYears = data.available_years || []
          setAvailableYears(allYears)

          // Set default year to the most recent available year
          if (allYears.length > 0) {
            const defaultYear = allYears[0]
            setSelectedYear(defaultYear.toString())
          }
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
    if (selectedYear) {
      fetchChampions(parseInt(selectedYear))
    }
  }, [selectedYear, fetchChampions])

  const getTrophyIcon = (place: number) => {
    switch (place) {
      case 1:
        return <Crown className="h-8 w-8 text-yellow-500" />
      case 2:
        return <Medal className="h-8 w-8 text-gray-400" />
      case 3:
        return <Award className="h-8 w-8 text-amber-600" />
      default:
        return <Trophy className="h-8 w-8 text-gray-600" />
    }
  }

  const getPlaceStyle = (place: number) => {
    switch (place) {
      case 1:
        return "bg-gradient-to-br from-yellow-100 to-yellow-200 dark:from-yellow-900/20 dark:to-yellow-800/20 border-yellow-300 dark:border-yellow-700"
      case 2:
        return "bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800/20 dark:to-gray-700/20 border-gray-300 dark:border-gray-600"
      case 3:
        return "bg-gradient-to-br from-amber-100 to-amber-200 dark:from-amber-900/20 dark:to-amber-800/20 border-amber-300 dark:border-amber-700"
      default:
        return "bg-background border-border"
    }
  }

  const getPlaceText = (place: number) => {
    switch (place) {
      case 1:
        return "🏆 CHAMPION"
      case 2:
        return "🥈 RUNNER-UP"
      case 3:
        return "🥉 THIRD PLACE"
      default:
        return `#${place}`
    }
  }

  const getPlaceTextStyle = (place: number) => {
    switch (place) {
      case 1:
        return "text-yellow-700 dark:text-yellow-300 font-bold text-lg"
      case 2:
        return "text-gray-700 dark:text-gray-300 font-semibold text-base"
      case 3:
        return "text-amber-700 dark:text-amber-300 font-semibold text-base"
      default:
        return "text-foreground"
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Trophy className="h-6 w-6 text-yellow-500" />
              <h2 className="text-xl font-semibold">Hall of Champions</h2>
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              League champions and top finishers by season
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
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
            <p className="text-sm text-muted-foreground">Loading champions...</p>
          </div>
        ) : championsData ? (
          <div className="space-y-4">
            {!championsData.season_complete && (
              <div className="text-center py-2 px-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  ⚡ Season in progress - showing current standings
                </p>
              </div>
            )}

            <div className="grid gap-4">
              {championsData.champions.map((champion) => (
                <Card
                  key={champion.team_id}
                  className={`${getPlaceStyle(champion.place)} transition-all duration-200 hover:shadow-lg`}
                >
                  <CardContent className="p-4 sm:p-6">
                    {/* Mobile Layout */}
                    <div className="block sm:hidden">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          {getTrophyIcon(champion.place)}
                          <div>
                            <div className={getPlaceTextStyle(champion.place)}>
                              {getPlaceText(champion.place)}
                            </div>
                            <p className="text-xs text-muted-foreground">
                              Final Standing: #{champion.final_standing}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="mb-4">
                        <h3 className="font-semibold text-lg">{champion.team_name}</h3>
                        <p className="text-sm text-muted-foreground">{champion.owner}</p>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-center p-3 bg-muted/30 rounded-lg">
                          <p className="text-xl font-bold text-green-600 dark:text-green-400">
                            {champion.wins}
                          </p>
                          <p className="text-xs text-muted-foreground">WINS</p>
                        </div>
                        <div className="text-center p-3 bg-muted/30 rounded-lg">
                          <p className="text-xl font-bold text-red-600 dark:text-red-400">
                            {champion.losses}
                          </p>
                          <p className="text-xs text-muted-foreground">LOSSES</p>
                        </div>
                        {champion.ties > 0 && (
                          <div className="text-center p-3 bg-muted/30 rounded-lg">
                            <p className="text-xl font-bold text-yellow-600 dark:text-yellow-400">
                              {champion.ties}
                            </p>
                            <p className="text-xs text-muted-foreground">TIES</p>
                          </div>
                        )}
                        <div className="text-center p-3 bg-muted/30 rounded-lg">
                          <p className="text-lg font-semibold">
                            {champion.points_for.toFixed(1)}
                          </p>
                          <p className="text-xs text-muted-foreground">POINTS</p>
                        </div>
                      </div>
                    </div>

                    {/* Desktop Layout */}
                    <div className="hidden sm:flex sm:items-center sm:justify-between">
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-3">
                          {getTrophyIcon(champion.place)}
                          <div>
                            <div className={getPlaceTextStyle(champion.place)}>
                              {getPlaceText(champion.place)}
                            </div>
                            <p className="text-xs text-muted-foreground">
                              Final Standing: #{champion.final_standing}
                            </p>
                          </div>
                        </div>

                        <div className="ml-4">
                          <h3 className="font-semibold text-lg">{champion.team_name}</h3>
                          <p className="text-sm text-muted-foreground">{champion.owner}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-6">
                        <div className="text-center">
                          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                            {champion.wins}
                          </p>
                          <p className="text-xs text-muted-foreground">WINS</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                            {champion.losses}
                          </p>
                          <p className="text-xs text-muted-foreground">LOSSES</p>
                        </div>
                        {champion.ties > 0 && (
                          <div className="text-center">
                            <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                              {champion.ties}
                            </p>
                            <p className="text-xs text-muted-foreground">TIES</p>
                          </div>
                        )}
                        <div className="text-center">
                          <p className="text-lg font-semibold">
                            {champion.points_for.toFixed(1)}
                          </p>
                          <p className="text-xs text-muted-foreground">POINTS</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <Trophy className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
            <p className="text-muted-foreground">No champions data available</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}