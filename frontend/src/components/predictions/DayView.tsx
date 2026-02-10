import { useState } from 'react';
import { 
  Trophy, AlertCircle, Clock, 
  ChevronLeft, ChevronRight, CheckCircle2, XCircle,
  Calendar, Activity
} from 'lucide-react';
import { CalendarDay, CalendarMatch } from '../../lib/types';
import { format, parseISO } from 'date-fns';
import { fr } from 'date-fns/locale';

interface DayViewProps {
  day: CalendarDay;
  timeFormat: 'fr' | 'us';
  onToggleTimeFormat: () => void;
  onPreviousDay?: () => void;
  onNextDay?: () => void;
  hasPrevious?: boolean;
  hasNext?: boolean;
}

export function DayView({ 
  day, 
  timeFormat, 
  onToggleTimeFormat,
  onPreviousDay,
  onNextDay,
  hasPrevious,
  hasNext
}: DayViewProps) {
  const [expandedMatch, setExpandedMatch] = useState<string | null>(null);

  // Formater la date
  const formattedDate = format(parseISO(day.date), 'EEEE d MMMM yyyy', { locale: fr });
  const formattedDateShort = format(parseISO(day.date), 'dd/MM/yyyy');

  // Trier les matchs par heure
  const sortedMatches = [...day.matches].sort((a, b) => {
    return (a.game_time_us || '').localeCompare(b.game_time_us || '');
  });

  // Calculer stats
  const pastMatches = sortedMatches.filter(m => !m.is_future && m.status === 'finished');
  const correctPredictions = pastMatches.filter(m => m.was_correct);
  const accuracy = pastMatches.length > 0 
    ? (correctPredictions.length / pastMatches.length) * 100 
    : null;

  // Déterminer couleur accuracy
  const getAccuracyColor = (acc: number | null) => {
    if (acc === null) return 'text-gray-400';
    if (acc >= 70) return 'text-green-400';
    if (acc >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getAccuracyBg = (acc: number | null) => {
    if (acc === null) return 'bg-gray-700';
    if (acc >= 70) return 'bg-green-600';
    if (acc >= 50) return 'bg-yellow-600';
    return 'bg-red-600';
  };

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gray-900/50 p-6 border-b border-gray-700">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-2xl font-bold capitalize">{formattedDate}</h2>
              {day.is_today && (
                <span className="px-2 py-1 bg-blue-600 text-xs font-bold rounded-full">
                  AUJOURD'HUI
                </span>
              )}
              {day.is_past && !day.is_today && (
                <span className="px-2 py-1 bg-gray-600 text-xs rounded-full">
                  PASSÉ
                </span>
              )}
            </div>
            
            {/* Stats rapides */}
            <div className="flex items-center gap-4 text-sm">
              <span className="text-gray-400">
                <Calendar size={14} className="inline mr-1" />
                {day.match_count} match{day.match_count > 1 ? 's' : ''}
              </span>
              
              {day.completed_matches > 0 && (
                <span className="text-gray-400">
                  <Activity size={14} className="inline mr-1" />
                  {day.completed_matches} terminé{day.completed_matches > 1 ? 's' : ''}
                </span>
              )}
              
              {accuracy !== null && (
                <span className={`font-bold ${getAccuracyColor(accuracy)}`}>
                  <Trophy size={14} className="inline mr-1" />
                  {accuracy.toFixed(0)}% accuracy
                </span>
              )}
            </div>
          </div>

          {/* Navigation et controls */}
          <div className="flex items-center gap-2">
            {/* Navigation jour */}
            <div className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
              <button
                onClick={onPreviousDay}
                disabled={!hasPrevious}
                className="p-2 hover:bg-gray-700 rounded disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ChevronLeft size={18} />
              </button>
              <span className="px-2 text-sm text-gray-400 min-w-[80px] text-center">
                {formattedDateShort}
              </span>
              <button
                onClick={onNextDay}
                disabled={!hasNext}
                className="p-2 hover:bg-gray-700 rounded disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ChevronRight size={18} />
              </button>
            </div>

            {/* Toggle heure */}
            <button
              onClick={onToggleTimeFormat}
              className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition"
            >
              <Clock size={16} />
              {timeFormat === 'fr' ? '🇫🇷 FR' : '🇺🇸 US'}
            </button>
          </div>
        </div>
      </div>

      {/* Liste des matchs */}
      <div className="divide-y divide-gray-700">
        {sortedMatches.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            <AlertCircle size={48} className="mx-auto mb-4 opacity-50" />
            <p className="text-lg">Aucun match programmé ce jour</p>
            <p className="text-sm mt-2">Sélectionnez une autre date dans le calendrier</p>
          </div>
        ) : (
          sortedMatches.map((match) => (
            <MatchCard
              key={match.game_id}
              match={match}
              timeFormat={timeFormat}
              isExpanded={expandedMatch === match.game_id}
              onToggle={() => setExpandedMatch(
                expandedMatch === match.game_id ? null : match.game_id
              )}
            />
          ))
        )}
      </div>

      {/* Footer avec stats */}
      {sortedMatches.length > 0 && (
        <div className="bg-gray-900/30 p-4 border-t border-gray-700">
          <div className="flex items-center justify-between text-sm">
            <div className="text-gray-400">
              {day.has_predictions 
                ? `${day.matches.filter(m => m.prediction).length} prédiction(s) disponible(s)`
                : 'Aucune prédiction pour ce jour'
              }
            </div>
            
            {accuracy !== null && (
              <div className={`px-3 py-1 rounded-full text-sm font-bold ${getAccuracyBg(accuracy)} text-white`}>
                {correctPredictions.length}/{pastMatches.length} correct
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Composant carte match
interface MatchCardProps {
  match: CalendarMatch;
  timeFormat: 'fr' | 'us';
  isExpanded: boolean;
  onToggle: () => void;
}

function MatchCard({ match, timeFormat, isExpanded, onToggle }: MatchCardProps) {
  const displayTime = timeFormat === 'fr' 
    ? match.game_time_fr 
    : match.game_time_us;

  const isPast = !match.is_future || match.status === 'finished';
  const hasResult = match.actual_result !== undefined;
  const isCorrect = match.was_correct;

  // Couleurs selon statut
  const getStatusColor = () => {
    if (!isPast) return 'border-l-blue-500';
    if (isCorrect === true) return 'border-l-green-500';
    if (isCorrect === false) return 'border-l-red-500';
    return 'border-l-gray-500';
  };

  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.75) return 'text-green-400';
    if (conf >= 0.60) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div 
      className={`p-4 hover:bg-gray-700/30 transition cursor-pointer border-l-4 ${getStatusColor()}`}
      onClick={onToggle}
    >
      <div className="flex items-center gap-4">
        {/* Heure */}
        <div className="w-20 text-center">
          <div className="text-xl font-bold text-blue-400">{displayTime}</div>
          {isPast && (
            <div className="text-xs text-gray-500 mt-1">
              {match.status === 'finished' ? 'Terminé' : 'En cours'}
            </div>
          )}
        </div>

        {/* Équipes et score */}
        <div className="flex-1">
          <div className="flex items-center justify-between gap-4">
            {/* Home Team */}
            <div className={`flex-1 text-right ${
              match.prediction === 'Home Win' && !isPast ? 'font-bold text-green-400' : ''
            }`}>
              <div className="text-lg">{match.home_team}</div>
              {match.home_score !== undefined && (
                <div className="text-2xl font-bold">{match.home_score}</div>
              )}
            </div>

            {/* VS */}
            <div className="text-gray-500 font-bold px-2">VS</div>

            {/* Away Team */}
            <div className={`flex-1 ${
              match.prediction === 'Away Win' && !isPast ? 'font-bold text-green-400' : ''
            }`}>
              <div className="text-lg">{match.away_team}</div>
              {match.away_score !== undefined && (
                <div className="text-2xl font-bold">{match.away_score}</div>
              )}
            </div>
          </div>
        </div>

        {/* Prédiction et résultat */}
        <div className="w-48 text-right">
          {!isPast ? (
            // Match futur
            <div>
              {match.confidence ? (
                <>
                  <div className="text-sm text-gray-400">
                    Prédiction: <span className="font-semibold">{match.prediction}</span>
                  </div>
                  <div className={`text-2xl font-bold ${getConfidenceColor(match.confidence)}`}>
                    {(match.confidence * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-500">
                    {match.recommendation}
                  </div>
                </>
              ) : (
                <span className="text-gray-500">Pas de prédiction</span>
              )}
            </div>
          ) : hasResult ? (
            // Match passé avec résultat
            <div>
              <div className={`text-lg font-bold ${
                isCorrect ? 'text-green-400' : 'text-red-400'
              }`}>
                {isCorrect ? (
                  <><CheckCircle2 className="inline mr-1" size={18} /> Correct</>
                ) : (
                  <><XCircle className="inline mr-1" size={18} /> Incorrect</>
                )}
              </div>
              <div className="text-xs text-gray-400">
                Prédiction: {match.prediction || 'N/A'}
              </div>
              {match.confidence && (
                <div className="text-xs text-gray-500">
                  Confiance: {(match.confidence * 100).toFixed(0)}%
                </div>
              )}
            </div>
          ) : (
            // Match passé sans résultat
            <div className="text-gray-500">Résultat inconnu</div>
          )}
        </div>

        {/* Expand icon */}
        <div className="text-gray-500">
          {isExpanded ? <ChevronRight className="rotate-90" /> : <ChevronRight />}
        </div>
      </div>

      {/* Détails expandables */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-700/50 grid grid-cols-3 gap-4 text-sm">
          {/* Détails prédiction */}
          <div>
            <h4 className="text-gray-500 mb-2 font-semibold">Prédiction ML</h4>
            {match.prediction ? (
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-400">Résultat:</span>
                  <span className={match.prediction === 'Home Win' ? 'text-green-400' : 'text-yellow-400'}>
                    {match.prediction}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Confiance:</span>
                  <span>{(match.confidence! * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Proba domicile:</span>
                  <span>{(match.proba_home_win! * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Recommandation:</span>
                  <span className="text-xs">{match.recommendation}</span>
                </div>
              </div>
            ) : (
              <span className="text-gray-500">Aucune prédiction</span>
            )}
          </div>

          {/* Résultat réel */}
          <div>
            <h4 className="text-gray-500 mb-2 font-semibold">Résultat Réel</h4>
            {hasResult ? (
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-gray-400">Vainqueur:</span>
                  <span className={isCorrect ? 'text-green-400' : 'text-red-400'}>
                    {match.actual_result === 'home_win' ? match.home_team : match.away_team}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Score:</span>
                  <span>{match.home_score} - {match.away_score}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Status:</span>
                  <span className="capitalize">{match.status}</span>
                </div>
              </div>
            ) : (
              <span className="text-gray-500">Match à venir ou résultat non disponible</span>
            )}
          </div>

          {/* Métadonnées */}
          <div>
            <h4 className="text-gray-500 mb-2 font-semibold">Informations</h4>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-400">ID:</span>
                <span className="font-mono">{match.game_id.slice(0, 20)}...</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Date:</span>
                <span>{match.game_date}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Heure US:</span>
                <span>{match.game_time_us}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Heure FR:</span>
                <span>{match.game_time_fr}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Source:</span>
                <span className="capitalize">{match.data_source}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
