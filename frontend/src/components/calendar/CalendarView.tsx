import { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight, Calendar } from 'lucide-react';
import { CalendarResponse, CalendarDay } from '../../lib/types';
import { addMonths, subMonths, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isToday, isWeekend } from 'date-fns';

interface CalendarViewProps {
  calendar: CalendarResponse;
  selectedDate: string;
  onSelectDate: (date: string) => void;
  onViewModeChange?: (mode: 'day' | 'week' | 'month') => void;
}

const MONTHS_FR = [
  'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
  'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
];

const WEEKDAYS_SHORT = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];

export function CalendarView({ 
  calendar, 
  selectedDate, 
  onSelectDate,
  onViewModeChange 
}: CalendarViewProps) {
  const [currentMonth, setCurrentMonth] = useState(() => new Date(selectedDate));
  const [viewMode, setViewMode] = useState<'day' | 'week' | 'month'>('month');

  // Créer un map des jours avec matchs pour accès rapide
  const daysMap = useMemo(() => {
    const map = new Map<string, CalendarDay>();
    calendar.days.forEach(day => {
      map.set(day.date, day);
    });
    return map;
  }, [calendar.days]);

  // Navigation mois
  const goToPreviousMonth = () => setCurrentMonth(subMonths(currentMonth, 1));
  const goToNextMonth = () => setCurrentMonth(addMonths(currentMonth, 1));
  const goToToday = () => {
    const today = new Date();
    setCurrentMonth(today);
    onSelectDate(today.toISOString().split('T')[0]);
  };

  // Générer les jours du mois
  const monthDays = useMemo(() => {
    const start = startOfMonth(currentMonth);
    const end = endOfMonth(currentMonth);
    return eachDayOfInterval({ start, end });
  }, [currentMonth]);

  // Obtenir les infos d'un jour
  const getDayInfo = (date: Date): CalendarDay | undefined => {
    const dateStr = date.toISOString().split('T')[0];
    return daysMap.get(dateStr);
  };

  const handleViewModeChange = (mode: 'day' | 'week' | 'month') => {
    setViewMode(mode);
    onViewModeChange?.(mode);
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4 space-y-4">
      {/* Header avec navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Calendar className="text-blue-500" size={24} />
          <h3 className="text-xl font-bold">
            {MONTHS_FR[currentMonth.getMonth()]} {currentMonth.getFullYear()}
          </h3>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Bouton Aujourd'hui */}
          <button
            onClick={goToToday}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition"
          >
            Aujourd'hui
          </button>
          
          {/* Navigation mois */}
          <button
            onClick={goToPreviousMonth}
            className="p-2 hover:bg-gray-700 rounded transition"
            title="Mois précédent"
          >
            <ChevronLeft size={20} />
          </button>
          <button
            onClick={goToNextMonth}
            className="p-2 hover:bg-gray-700 rounded transition"
            title="Mois suivant"
          >
            <ChevronRight size={20} />
          </button>
        </div>
      </div>

      {/* Sélecteur de vue */}
      <div className="flex gap-1 bg-gray-900 p-1 rounded-lg">
        {(['day', 'week', 'month'] as const).map((mode) => (
          <button
            key={mode}
            onClick={() => handleViewModeChange(mode)}
            className={`flex-1 py-1.5 px-3 rounded text-sm font-medium transition ${
              viewMode === mode
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            {mode === 'day' ? 'Jour' : mode === 'week' ? 'Semaine' : 'Mois'}
          </button>
        ))}
      </div>

      {/* Grille calendrier */}
      <div className="space-y-2">
        {/* Jours de la semaine */}
        <div className="grid grid-cols-7 gap-1">
          {WEEKDAYS_SHORT.map((day) => (
            <div
              key={day}
              className="text-center text-xs font-medium text-gray-500 py-2"
            >
              {day}
            </div>
          ))}
        </div>

        {/* Jours du mois */}
        <div className="grid grid-cols-7 gap-1">
          {monthDays.map((date) => {
            const dateStr = date.toISOString().split('T')[0];
            const dayInfo = getDayInfo(date);
            const isSelected = dateStr === selectedDate;
            const isCurrentMonth = isSameMonth(date, currentMonth);
            const isTodayDate = isToday(date);
            const isWeekendDate = isWeekend(date);
            const hasMatches = dayInfo && dayInfo.match_count > 0;

            return (
              <button
                key={dateStr}
                onClick={() => onSelectDate(dateStr)}
                className={`
                  relative p-2 rounded-lg transition min-h-[70px] flex flex-col items-center justify-center
                  ${isSelected 
                    ? 'bg-blue-600 text-white ring-2 ring-blue-400' 
                    : isTodayDate 
                      ? 'bg-blue-900/30 border border-blue-500/50'
                      : hasMatches 
                        ? 'bg-gray-700 hover:bg-gray-600'
                        : 'bg-gray-800/50 hover:bg-gray-700/50'
                  }
                  ${!isCurrentMonth && 'opacity-40'}
                  ${isWeekendDate && !isSelected && 'bg-gray-800/30'}
                `}
              >
                {/* Numéro du jour */}
                <span className={`text-sm font-semibold ${
                  isSelected ? 'text-white' : isTodayDate ? 'text-blue-400' : 'text-gray-300'
                }`}>
                  {date.getDate()}
                </span>

                {/* Indicateur matchs */}
                {hasMatches && (
                  <div className="mt-1 flex flex-col items-center gap-0.5">
                    <span className={`text-xs font-medium ${
                      isSelected ? 'text-blue-200' : 'text-green-400'
                    }`}>
                      {dayInfo!.match_count} match{dayInfo!.match_count > 1 ? 's' : ''}
                    </span>
                    
                    {/* Indicateur accuracy pour matchs passés */}
                    {dayInfo!.accuracy !== undefined && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        dayInfo!.accuracy >= 0.7 
                          ? 'bg-green-500/20 text-green-400'
                          : dayInfo!.accuracy >= 0.5
                            ? 'bg-yellow-500/20 text-yellow-400'
                            : 'bg-red-500/20 text-red-400'
                      }`}>
                        {(dayInfo!.accuracy * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                )}

                {/* Point pour aujourd'hui */}
                {isTodayDate && !isSelected && (
                  <div className="absolute top-1 right-1 w-2 h-2 bg-blue-500 rounded-full" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Légende */}
      <div className="flex flex-wrap gap-3 text-xs text-gray-400 pt-2 border-t border-gray-700">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 bg-blue-600 rounded" />
          <span>Sélectionné</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 bg-blue-500/30 border border-blue-500 rounded" />
          <span>Aujourd'hui</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 bg-gray-700 rounded" />
          <span>Avec matchs</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 bg-green-500/20 rounded" />
          <span>+70% accuracy</span>
        </div>
      </div>

      {/* Stats rapides */}
      {calendar.total_matches > 0 && (
        <div className="grid grid-cols-3 gap-2 pt-2 border-t border-gray-700">
          <div className="text-center">
            <p className="text-lg font-bold text-blue-400">{calendar.total_matches}</p>
            <p className="text-xs text-gray-500">Total matchs</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-bold text-green-400">
              {calendar.overall_accuracy ? `${(calendar.overall_accuracy * 100).toFixed(1)}%` : '-'}
            </p>
            <p className="text-xs text-gray-500">Accuracy</p>
          </div>
          <div className="text-center">
            <p className="text-lg font-bold text-purple-400">{calendar.matches_completed}</p>
            <p className="text-xs text-gray-500">Terminés</p>
          </div>
        </div>
      )}
    </div>
  );
}
