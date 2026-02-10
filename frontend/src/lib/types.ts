// Auto-generated from Pydantic models
// Do not edit manually - run: python scripts/generate_types.py

export interface Prediction {
  home_team: string;
  away_team: string;
  prediction: string;
  proba_home_win: number;
  confidence: number;
  recommendation: string;
  // Champs calendrier
  game_date?: string;
  game_time_us?: string;
  game_time_fr?: string;
  // Pour matchs passés
  actual_result?: 'home_win' | 'away_win';
  home_score?: number;
  away_score?: number;
  was_correct?: boolean;
  is_future?: boolean;
  status?: 'scheduled' | 'live' | 'finished' | 'postponed';
}

export interface Bet {
  id: string;
  date: string;
  match: string;
  prediction: string;
  stake: number;
  odds: number;
  result?: 'win' | 'loss' | 'pending';
  profit?: number;
}

export interface BetRequest {
  date: string;
  match: string;
  prediction: string;
  stake: number;
  odds: number;
}

export interface PaperTradingStats {
  total_bets: number;
  won_bets: number;
  lost_bets: number;
  pending_bets: number;
  total_profit: number;
  avg_profit: number;
  win_rate: number;
}

export interface TemporalSegment {
  range: string;
  matches_count: number;
  accuracy: number;
  recommendation: string;
}

export interface TemporalAnalysisResponse {
  segments: TemporalSegment[];
  optimal_threshold: number;
  current_season_progress: string;
  overall_accuracy: number;
}

export interface PredictionsResponse {
  predictions: Prediction[];
  count: number;
  date?: string;
}

export interface BetsResponse {
  bets: Bet[];
}

export interface WeekData {
  date: string;
  day_name: string;
  match_count: number;
  avg_confidence: number;
  matches: Prediction[];
}

// Types Calendrier Pro
export interface CalendarMatch extends Prediction {
  game_id: string;
  game_date: string;
  game_time_us: string;
  game_time_fr: string;
  data_source: 'api' | 'backtest' | 'prediction';
}

export interface CalendarDay {
  date: string;
  day_name: string;
  day_number: number;
  month: number;
  year: number;
  match_count: number;
  matches: CalendarMatch[];
  has_predictions: boolean;
  completed_matches: number;
  correct_predictions?: number;
  accuracy?: number;
  avg_confidence?: number;
  is_today: boolean;
  is_weekend: boolean;
  is_past: boolean;
}

export interface CalendarWeek {
  week_number: number;
  start_date: string;
  end_date: string;
  days: CalendarDay[];
  total_matches: number;
  has_predictions_count: number;
  completed_count: number;
  week_accuracy?: number;
}

export interface CalendarMonth {
  year: number;
  month: number;
  month_name: string;
  weeks: CalendarWeek[];
  total_matches: number;
  days_with_matches: number;
  month_accuracy?: number;
}

export interface CalendarResponse {
  season: string;
  view_mode: 'day' | 'week' | 'month';
  start_date: string;
  end_date: string;
  today: string;
  days: CalendarDay[];
  weeks?: CalendarWeek[];
  current_day?: CalendarDay;
  total_matches: number;
  matches_with_predictions: number;
  matches_completed: number;
  overall_accuracy?: number;
  has_previous: boolean;
  has_next: boolean;
  previous_date?: string;
  next_date?: string;
  generated_at: string;
  data_sources: string[];
}
