import { useState, useCallback } from 'react';
import { Layout } from '../components/Layout';
import { CalendarView } from '../components/calendar/CalendarView';
import { DayView } from '../components/predictions/DayView';
import { useApi } from '../hooks/useApi';
import { calendarApi } from '../lib/api';
import { CalendarResponse, CalendarDay } from '../lib/types';
import { Calendar, RefreshCw, Loader2 } from 'lucide-react';
import { subDays, addDays, format } from 'date-fns';

export function Predictions() {
  // Date du jour par défaut
  const today = new Date().toISOString().split('T')[0];
  
  // États
  const [selectedDate, setSelectedDate] = useState<string>(today);
  const [viewMode, setViewMode] = useState<'day' | 'week' | 'month'>('month');
  const [timeFormat, setTimeFormat] = useState<'fr' | 'us'>('fr');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Charger le calendrier
  const { 
    data: calendar, 
    loading: calendarLoading, 
    error: calendarError,
    refetch: refetchCalendar
  } = useApi<CalendarResponse>(() => 
    calendarApi.getByDate(selectedDate, viewMode)
  );

  // Charger le jour sélectionné spécifiquement
  const {
    data: dayData,
    loading: dayLoading,
    error: dayError,
    refetch: refetchDay
  } = useApi<CalendarDay>(() =>
    calendarApi.getByDate(selectedDate, 'day')
  );

  // Jour à afficher (priorité au jour spécifique)
  const displayDay = dayData || calendar?.current_day || calendar?.days.find(d => d.date === selectedDate);

  // Navigation jour
  const goToPreviousDay = useCallback(() => {
    const prev = subDays(new Date(selectedDate), 1);
    setSelectedDate(prev.toISOString().split('T')[0]);
  }, [selectedDate]);

  const goToNextDay = useCallback(() => {
    const next = addDays(new Date(selectedDate), 1);
    setSelectedDate(next.toISOString().split('T')[0]);
  }, [selectedDate]);

  // Rafraîchir les données
  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([refetchCalendar(), refetchDay()]);
    setIsRefreshing(false);
  };

  // Toggle format heure
  const toggleTimeFormat = () => {
    setTimeFormat(prev => prev === 'fr' ? 'us' : 'fr');
  };

  // Gérer changement de vue
  const handleViewModeChange = (mode: 'day' | 'week' | 'month') => {
    setViewMode(mode);
  };

  // Réinitialiser à aujourd'hui
  const goToToday = () => {
    setSelectedDate(today);
  };

  // Erreur
  if (calendarError || dayError) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
          <div className="text-red-400 mb-4">
            <Calendar size={48} />
          </div>
          <h2 className="text-xl font-bold mb-2">Erreur de chargement</h2>
          <p className="text-gray-400 mb-4">
            {calendarError || dayError}
          </p>
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition"
          >
            <RefreshCw size={18} />
            Réessayer
          </button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-3xl font-bold flex items-center gap-3">
              <Calendar className="text-blue-500" size={32} />
              Calendrier NBA 2025-26
            </h2>
            <p className="text-gray-400 mt-1">
              {calendar?.total_matches || 0} matchs • 
              Saison {calendar?.season || '2025-26'} • 
              {calendar?.overall_accuracy !== undefined 
                ? ` ${(calendar.overall_accuracy * 100).toFixed(1)}% accuracy`
                : ' Accuracy en cours de calcul'
              }
            </p>
          </div>

          <div className="flex items-center gap-2">
            {/* Bouton refresh */}
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded transition"
            >
              {isRefreshing ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <RefreshCw size={18} />
              )}
              <span className="hidden sm:inline">Actualiser</span>
            </button>

            {/* Bouton aujourd'hui */}
            <button
              onClick={goToToday}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded transition"
            >
              Aujourd'hui
            </button>
          </div>
        </div>

        {/* Layout principal: Calendrier + Détail */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Colonne gauche: Calendrier (4 colonnes) */}
          <div className="lg:col-span-4">
            {calendarLoading ? (
              <div className="bg-gray-800 rounded-lg p-8 text-center">
                <Loader2 size={32} className="animate-spin mx-auto mb-4 text-blue-500" />
                <p className="text-gray-400">Chargement du calendrier...</p>
              </div>
            ) : calendar ? (
              <CalendarView
                calendar={calendar}
                selectedDate={selectedDate}
                onSelectDate={setSelectedDate}
                onViewModeChange={handleViewModeChange}
              />
            ) : null}
          </div>

          {/* Colonne droite: Détail du jour (8 colonnes) */}
          <div className="lg:col-span-8">
            {dayLoading ? (
              <div className="bg-gray-800 rounded-lg p-8 text-center">
                <Loader2 size={32} className="animate-spin mx-auto mb-4 text-blue-500" />
                <p className="text-gray-400">Chargement des matchs...</p>
              </div>
            ) : displayDay ? (
              <DayView
                day={displayDay}
                timeFormat={timeFormat}
                onToggleTimeFormat={toggleTimeFormat}
                onPreviousDay={goToPreviousDay}
                onNextDay={goToNextDay}
                hasPrevious={true}
                hasNext={true}
              />
            ) : (
              <div className="bg-gray-800 rounded-lg p-8 text-center">
                <Calendar size={48} className="mx-auto mb-4 text-gray-600" />
                <h3 className="text-xl font-bold mb-2">Aucun match ce jour</h3>
                <p className="text-gray-400 mb-4">
                  Sélectionnez une autre date dans le calendrier
                </p>
                <button
                  onClick={goToToday}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition"
                >
                  Aller à aujourd'hui
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Footer avec info */}
        {calendar && (
          <div className="bg-gray-800 rounded-lg p-4 text-sm text-gray-400">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                Données chargées depuis: {calendar.data_sources.join(', ')}
              </div>
              <div>
                Généré le: {format(new Date(calendar.generated_at), 'dd/MM/yyyy HH:mm')}
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
