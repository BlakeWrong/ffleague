-- Fantasy Football League Database Schema
-- Captures ALL ESPN API data points for local storage and fast queries

-- =====================================================================================
-- CORE LEAGUE DATA
-- =====================================================================================

-- League Information (from League Class)
CREATE TABLE leagues (
    id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL UNIQUE,
    league_id INTEGER NOT NULL,  -- ESPN league ID
    name TEXT,
    current_week INTEGER,
    nfl_week INTEGER,
    total_teams INTEGER,
    previousSeasons TEXT,  -- JSON array of previous season years
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- League Settings (from Settings Class)
CREATE TABLE league_settings (
    id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL,
    reg_season_count INTEGER,
    veto_votes_required INTEGER,
    team_count INTEGER,
    playoff_team_count INTEGER,
    keeper_count INTEGER,
    trade_deadline INTEGER,  -- epoch timestamp
    name TEXT,
    tie_rule INTEGER,
    playoff_tie_rule INTEGER,
    playoff_seed_tie_rule INTEGER,
    playoff_matchup_period_length INTEGER,
    faab BOOLEAN,  -- free agent acquisition budget
    acquisition_budget INTEGER,
    scoring_format TEXT,  -- JSON array of scoring rules
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (year) REFERENCES leagues(year),
    UNIQUE(year)
);

-- =====================================================================================
-- TEAM DATA
-- =====================================================================================

-- Teams (from Team Class - ALL attributes)
CREATE TABLE teams (
    id INTEGER PRIMARY KEY,
    team_id INTEGER NOT NULL,  -- ESPN team ID
    year INTEGER NOT NULL,
    team_abbrev TEXT,
    team_name TEXT NOT NULL,
    division_id TEXT,
    division_name TEXT,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    ties INTEGER DEFAULT 0,
    points_for REAL DEFAULT 0,
    points_against REAL DEFAULT 0,
    waiver_rank INTEGER,
    acquisitions INTEGER DEFAULT 0,
    acquisition_budget_spent INTEGER DEFAULT 0,
    drops INTEGER DEFAULT 0,
    trades INTEGER DEFAULT 0,
    move_to_ir INTEGER DEFAULT 0,
    owners TEXT,  -- JSON array of owner objects
    stats TEXT,  -- JSON object of team season stats
    streak_type TEXT,  -- 'WIN' or 'LOSS'
    streak_length INTEGER DEFAULT 0,
    standing INTEGER,  -- standing before playoffs
    final_standing INTEGER,  -- final standing at end of season
    draft_projected_rank INTEGER,
    playoff_pct INTEGER,  -- projected chance to make playoffs
    logo_url TEXT,
    schedule TEXT,  -- JSON array of opponent team IDs
    scores TEXT,  -- JSON array of weekly scores
    outcomes TEXT,  -- JSON array of weekly outcomes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (year) REFERENCES leagues(year),
    UNIQUE(team_id, year)
);

-- =====================================================================================
-- PLAYER DATA
-- =====================================================================================

-- Players (from Player Class - ALL attributes)
CREATE TABLE players (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL UNIQUE,  -- ESPN player ID
    name TEXT NOT NULL,
    pos_rank INTEGER,  -- positional rank
    eligible_slots TEXT,  -- JSON array like ['WR', 'WR/TE/RB']
    acquisition_type TEXT,
    pro_team TEXT,  -- NFL team like 'PIT', 'LAR'
    position TEXT,  -- main position like 'TE', 'QB'
    injury_status TEXT,
    injured BOOLEAN DEFAULT FALSE,
    total_points REAL,  -- season total
    avg_points REAL,  -- season average
    projected_total_points REAL,
    projected_avg_points REAL,
    percent_owned REAL,
    percent_started REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Player Weekly Performance (from Player/BoxPlayer Classes)
CREATE TABLE player_performances (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    week INTEGER NOT NULL,
    team_id INTEGER,  -- fantasy team that owned them
    lineup_slot TEXT,  -- lineup position
    slot_position TEXT,  -- BE for bench, QB, RB, etc.
    on_team_id INTEGER,  -- fantasy team ID
    schedule TEXT,  -- JSON object with scheduling info
    stats TEXT,  -- JSON object with week stats

    -- BoxPlayer specific attributes
    points REAL,  -- points scored this week
    projected_points REAL,  -- projected points for this week
    pro_opponent TEXT,  -- opponent NFL team
    pro_pos_rank INTEGER,  -- rank against position
    game_played INTEGER DEFAULT 0,  -- 0 or 100
    game_date TEXT,  -- ISO datetime string
    on_bye_week BOOLEAN DEFAULT FALSE,
    active_status TEXT,  -- active status

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (year) REFERENCES leagues(year),
    FOREIGN KEY (team_id, year) REFERENCES teams(team_id, year),
    UNIQUE(player_id, year, week, team_id)
);

-- =====================================================================================
-- MATCHUP DATA
-- =====================================================================================

-- Matchups (from Matchup Class)
CREATE TABLE matchups (
    id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL,
    week INTEGER NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    home_score REAL,
    away_score REAL,
    is_playoff BOOLEAN DEFAULT FALSE,
    matchup_type TEXT,  -- NONE, WINNERS_BRACKET, LOSERS_CONSOLATION_LADDER, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (year) REFERENCES leagues(year),
    FOREIGN KEY (home_team_id, year) REFERENCES teams(team_id, year),
    FOREIGN KEY (away_team_id, year) REFERENCES teams(team_id, year),
    UNIQUE(year, week, home_team_id, away_team_id)
);

-- Box Scores (from BoxScore Class - ALL attributes)
CREATE TABLE box_scores (
    id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL,
    week INTEGER NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    home_score REAL,
    home_projected REAL,
    away_score REAL,
    away_projected REAL,
    is_playoff BOOLEAN DEFAULT FALSE,
    matchup_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (year) REFERENCES leagues(year),
    FOREIGN KEY (home_team_id, year) REFERENCES teams(team_id, year),
    FOREIGN KEY (away_team_id, year) REFERENCES teams(team_id, year),
    UNIQUE(year, week, home_team_id, away_team_id)
);

-- =====================================================================================
-- DRAFT DATA
-- =====================================================================================

-- Draft Picks (from Pick Class - ALL attributes)
CREATE TABLE draft_picks (
    id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    player_name TEXT NOT NULL,
    round_num INTEGER NOT NULL,
    round_pick INTEGER NOT NULL,
    bid_amount INTEGER DEFAULT 0,
    keeper_status BOOLEAN DEFAULT FALSE,
    nominating_team_id INTEGER,  -- for auction drafts
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (year) REFERENCES leagues(year),
    FOREIGN KEY (team_id, year) REFERENCES teams(team_id, year),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (nominating_team_id, year) REFERENCES teams(team_id, year),
    UNIQUE(year, round_num, round_pick)
);

-- =====================================================================================
-- ACTIVITY DATA
-- =====================================================================================

-- League Activities (from Activity Class - ALL attributes)
CREATE TABLE activities (
    id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL,
    date INTEGER NOT NULL,  -- epoch timestamp in milliseconds
    actions TEXT NOT NULL,  -- JSON array of action tuples
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (year) REFERENCES leagues(year)
);

-- =====================================================================================
-- ADVANCED ANALYTICS (Pre-calculated for performance)
-- =====================================================================================

-- Streak Records
CREATE TABLE streak_records (
    id INTEGER PRIMARY KEY,
    owner_name TEXT NOT NULL,
    streak_type TEXT NOT NULL,  -- 'W' or 'L'
    length INTEGER NOT NULL,
    start_year INTEGER NOT NULL,
    start_week INTEGER NOT NULL,
    end_year INTEGER NOT NULL,
    end_week INTEGER NOT NULL,
    is_current BOOLEAN DEFAULT FALSE,
    team_names TEXT,  -- JSON array of team names during streak
    games TEXT,  -- JSON array of game details
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Luck Analysis - Season Level
CREATE TABLE luck_analysis_seasons (
    id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    owner_name TEXT NOT NULL,
    team_name TEXT NOT NULL,
    total_luck REAL NOT NULL,
    average_luck REAL NOT NULL,
    games_played INTEGER NOT NULL,
    biggest_lucky_week INTEGER,
    biggest_lucky_opponent TEXT,
    biggest_lucky_points REAL,
    biggest_lucky_margin REAL,
    biggest_unlucky_week INTEGER,
    biggest_unlucky_opponent TEXT,
    biggest_unlucky_points REAL,
    biggest_unlucky_margin REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (year) REFERENCES leagues(year),
    FOREIGN KEY (team_id, year) REFERENCES teams(team_id, year),
    UNIQUE(year, team_id)
);

-- Luck Analysis - Individual Matchups
CREATE TABLE luck_analysis_matchups (
    id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL,
    week INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    team_name TEXT NOT NULL,
    owner_name TEXT NOT NULL,
    opponent_team_id INTEGER NOT NULL,
    opponent_name TEXT NOT NULL,
    luck_points REAL NOT NULL,
    actual_score REAL NOT NULL,
    projected_score REAL NOT NULL,
    opponent_actual REAL NOT NULL,
    opponent_projected REAL NOT NULL,
    actual_margin REAL NOT NULL,
    projected_margin REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (year) REFERENCES leagues(year),
    FOREIGN KEY (team_id, year) REFERENCES teams(team_id, year),
    FOREIGN KEY (opponent_team_id, year) REFERENCES teams(team_id, year),
    UNIQUE(year, week, team_id)
);

-- Team Legacy Rankings
CREATE TABLE team_legacy (
    id INTEGER PRIMARY KEY,
    owner_name TEXT NOT NULL UNIQUE,
    team_names TEXT,  -- JSON array of all team names used
    total_seasons INTEGER NOT NULL,
    championships INTEGER DEFAULT 0,
    playoff_appearances INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    total_losses INTEGER DEFAULT 0,
    total_ties INTEGER DEFAULT 0,
    total_points REAL DEFAULT 0,
    average_placement REAL NOT NULL,
    best_season_year INTEGER,
    best_season_placement INTEGER,
    best_season_record TEXT,
    worst_season_year INTEGER,
    worst_season_placement INTEGER,
    worst_season_record TEXT,
    years_participated TEXT,  -- JSON array of years
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Championship History
CREATE TABLE championships (
    id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL,
    champion_team_id INTEGER NOT NULL,
    champion_name TEXT NOT NULL,
    champion_owner TEXT NOT NULL,
    runner_up_team_id INTEGER,
    runner_up_name TEXT,
    runner_up_owner TEXT,
    championship_score REAL,
    runner_up_score REAL,
    playoff_bracket TEXT,  -- JSON representation of playoff bracket
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (year) REFERENCES leagues(year),
    FOREIGN KEY (champion_team_id, year) REFERENCES teams(team_id, year),
    FOREIGN KEY (runner_up_team_id, year) REFERENCES teams(team_id, year),
    UNIQUE(year)
);

-- =====================================================================================
-- IMPORT TRACKING
-- =====================================================================================

-- Data Import Log
CREATE TABLE import_log (
    id INTEGER PRIMARY KEY,
    import_type TEXT NOT NULL,  -- 'full', 'incremental', 'weekly', 'analytics'
    table_name TEXT,  -- which table was imported
    year INTEGER,
    week INTEGER,
    status TEXT NOT NULL,  -- 'running', 'completed', 'failed'
    records_imported INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- =====================================================================================
-- PERFORMANCE INDEXES
-- =====================================================================================

-- League indexes
CREATE INDEX idx_leagues_year ON leagues(year);

-- Team indexes
CREATE INDEX idx_teams_year ON teams(year);
CREATE INDEX idx_teams_owner ON teams(owners);
CREATE INDEX idx_teams_standing ON teams(standing);
CREATE INDEX idx_teams_points ON teams(points_for DESC);

-- Player indexes
CREATE INDEX idx_players_name ON players(name);
CREATE INDEX idx_players_position ON players(position);
CREATE INDEX idx_players_pro_team ON players(pro_team);

-- Performance indexes
CREATE INDEX idx_player_performances_year_week ON player_performances(year, week);
CREATE INDEX idx_player_performances_team ON player_performances(team_id, year);
CREATE INDEX idx_player_performances_slot ON player_performances(slot_position);
CREATE INDEX idx_player_performances_points ON player_performances(points DESC);

-- Matchup indexes
CREATE INDEX idx_matchups_year_week ON matchups(year, week);
CREATE INDEX idx_matchups_teams ON matchups(home_team_id, away_team_id);
CREATE INDEX idx_matchups_playoff ON matchups(is_playoff);

-- Box score indexes
CREATE INDEX idx_box_scores_year_week ON box_scores(year, week);
CREATE INDEX idx_box_scores_teams ON box_scores(home_team_id, away_team_id);

-- Analytics indexes
CREATE INDEX idx_streak_records_type ON streak_records(streak_type);
CREATE INDEX idx_streak_records_length ON streak_records(length DESC);
CREATE INDEX idx_luck_seasons_year ON luck_analysis_seasons(year);
CREATE INDEX idx_luck_seasons_luck ON luck_analysis_seasons(total_luck DESC);
CREATE INDEX idx_luck_matchups_luck ON luck_analysis_matchups(luck_points DESC);
CREATE INDEX idx_team_legacy_placement ON team_legacy(average_placement);

-- Activity indexes
CREATE INDEX idx_activities_year ON activities(year);
CREATE INDEX idx_activities_date ON activities(date DESC);

-- Draft indexes
CREATE INDEX idx_draft_picks_year ON draft_picks(year);
CREATE INDEX idx_draft_picks_round ON draft_picks(round_num, round_pick);