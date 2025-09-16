"use client"

import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

interface StandingsData {
  rank: number
  team_id: number
  team_name: string
  owner: string
  wins: number
  losses: number
  ties: number
  points_for: number
  points_against: number
  streak_type: string
  streak_length: number
}

interface StandingsTableProps {
  standings: StandingsData[]
  currentWeek: number
  isLoading?: boolean
}

export function StandingsTable({ standings, currentWeek, isLoading = false }: StandingsTableProps) {
  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-muted rounded w-1/4"></div>
          <div className="space-y-2">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-12 bg-muted rounded"></div>
            ))}
          </div>
        </div>
      </Card>
    )
  }

  const getStreakBadgeVariant = (streakType: string) => {
    return streakType === "WIN" ? "default" : "destructive"
  }

  const getStreakText = (streakType: string, streakLength: number) => {
    const letter = streakType === "WIN" ? "W" : "L"
    return `${letter}${streakLength}`
  }

  return (
    <Card className="overflow-hidden">
      <div className="p-4 border-b bg-muted/50">
        <h2 className="text-lg font-semibold">League Standings</h2>
        <p className="text-sm text-muted-foreground">Week {currentWeek} • 2025 Season</p>
      </div>

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">#</TableHead>
              <TableHead className="w-32">Team</TableHead>
              <TableHead className="hidden sm:table-cell">Owner</TableHead>
              <TableHead className="text-center w-20">Record</TableHead>
              <TableHead className="text-right hidden md:table-cell w-20">PF</TableHead>
              <TableHead className="text-right hidden md:table-cell w-20">PA</TableHead>
              <TableHead className="text-center w-16">Streak</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {standings.map((team) => (
              <TableRow key={team.team_id} className="hover:bg-muted/50">
                <TableCell className="font-medium text-center">
                  {team.rank}
                </TableCell>
                <TableCell className="font-medium">
                  <div className="truncate">
                    {team.team_name}
                  </div>
                </TableCell>
                <TableCell className="hidden sm:table-cell text-muted-foreground">
                  <div className="truncate">
                    {team.owner}
                  </div>
                </TableCell>
                <TableCell className="text-center font-mono text-sm">
                  {team.wins}-{team.losses}
                  {team.ties > 0 && `-${team.ties}`}
                </TableCell>
                <TableCell className="text-right font-mono text-sm hidden md:table-cell">
                  {team.points_for.toFixed(2)}
                </TableCell>
                <TableCell className="text-right font-mono text-sm hidden md:table-cell">
                  {team.points_against.toFixed(2)}
                </TableCell>
                <TableCell className="text-center">
                  <Badge
                    variant={getStreakBadgeVariant(team.streak_type)}
                    className="text-xs font-mono"
                  >
                    {getStreakText(team.streak_type, team.streak_length)}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Mobile-only summary cards for key stats */}
      <div className="p-4 border-t bg-muted/30 md:hidden">
        <div className="text-xs text-muted-foreground mb-2">Points For/Against (Top 3)</div>
        <div className="grid grid-cols-3 gap-2 text-xs">
          {standings.slice(0, 3).map((team) => (
            <div key={team.team_id} className="text-center">
              <div className="font-medium truncate">{team.team_name}</div>
              <div className="text-muted-foreground">{team.points_for.toFixed(2)}/{team.points_against.toFixed(2)}</div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}