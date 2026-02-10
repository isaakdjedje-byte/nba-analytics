import { useState } from 'react';
import { Prediction } from '../lib/types';
import { PredictionCard } from './PredictionCard';
import { FilterBar, confidenceFilter, teamFilter, typeFilter } from './FilterBar';

interface PredictionsListProps {
  predictions: Prediction[];
  mode: 'compact' | 'detailed' | 'betting';
  groupBy?: 'day' | null;
  onBet?: (prediction: Prediction) => void;
  showFilters?: boolean;
  availableTeams?: string[];
}

interface DayGroup {
  date: string;
  dayName: string;
  matches: Prediction[];
}

export function PredictionsList({
  predictions,
  mode,
  groupBy = null,
  onBet,
  showFilters = true,
  availableTeams = [],
}: PredictionsListProps) {
  const [filters, setFilters] = useState<Record<string, string>>({
    confidence: 'all',
    team: 'all',
    type: 'all',
  });

  // Filter predictions
  const filteredPredictions = predictions.filter((p) => {
    // Confidence filter
    if (filters.confidence !== 'all') {
      const minConf = parseFloat(filters.confidence);
      if (p.confidence < minConf) return false;
    }

    // Team filter
    if (filters.team !== 'all') {
      const teamLower = filters.team.toLowerCase();
      if (
        !p.home_team.toLowerCase().includes(teamLower) &&
        !p.away_team.toLowerCase().includes(teamLower)
      ) {
        return false;
      }
    }

    return true;
  });

  // Group by day if needed
  const groupedPredictions = (): DayGroup[] => {
    if (!groupBy) {
      return [
        {
          date: new Date().toISOString().split('T')[0],
          dayName: 'Aujourd\'hui',
          matches: filteredPredictions,
        },
      ];
    }

    // Simulate grouping by day for demo
    const days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];
    const groups: DayGroup[] = [];

    days.forEach((dayName, index) => {
      const dayMatches = filteredPredictions.filter((_, i) => i % 7 === index);
      if (dayMatches.length > 0) {
        groups.push({
          date: `2025-02-${10 + index}`,
          dayName,
          matches: dayMatches,
        });
      }
    });

    return groups;
  };

  const filterConfigs = [
    confidenceFilter,
    ...(availableTeams.length > 0 ? [teamFilter(availableTeams)] : []),
    ...(mode !== 'compact' ? [typeFilter] : []),
  ];

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const handleResetFilters = () => {
    setFilters({
      confidence: 'all',
      team: 'all',
      type: 'all',
    });
  };

  const groups = groupedPredictions();

  return (
    <div className="space-y-4">
      {showFilters && mode !== 'compact' && (
        <FilterBar
          filters={filterConfigs}
          values={filters}
          onChange={handleFilterChange}
          onReset={handleResetFilters}
        />
      )}

      <div className="text-sm text-gray-400">
        {filteredPredictions.length} prédiction
        {filteredPredictions.length > 1 ? 's' : ''} trouvée
        {filteredPredictions.length > 1 ? 's' : ''}
      </div>

      {groups.map((group) => (
        <div key={group.date} className="space-y-3">
          {groupBy && (
            <div className="flex items-center gap-2 border-b border-gray-700 pb-2">
              <span className="text-lg font-semibold">{group.dayName}</span>
              <span className="text-sm text-gray-400">{group.date}</span>
              <span className="text-sm text-gray-500 ml-auto">
                {group.matches.length} match
                {group.matches.length > 1 ? 's' : ''}
              </span>
            </div>
          )}

          <div
            className={`grid gap-3 ${
              mode === 'compact'
                ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
                : 'grid-cols-1'
            }`}
          >
            {group.matches.map((prediction, index) => (
              <PredictionCard
                key={`${prediction.home_team}-${prediction.away_team}-${index}`}
                prediction={prediction}
                onBet={mode === 'betting' ? onBet : undefined}
                compact={mode === 'compact'}
              />
            ))}
          </div>
        </div>
      ))}

      {filteredPredictions.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg">Aucune prédiction trouvée</p>
          <p className="text-sm">Essayez de modifier vos filtres</p>
        </div>
      )}
    </div>
  );
}
