import { Layout } from '../components/Layout';
import { StatsCard } from '../components/StatsCard';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { useBetsApi, useApi } from '../hooks/useApi';
import { betsApi, analysisApi } from '../lib/api';
import { PaperTradingStats, TemporalSegment } from '../lib/types';

export function Dashboard() {
  const { 
    data: stats, 
    error: statsError,
    loading: statsLoading,
    refetch: refetchStats 
  } = useBetsApi<PaperTradingStats>(() => betsApi.getStats(), []);
  
  const { 
    data: temporal,
    error: temporalError,
    loading: temporalLoading 
  } = useApi<{ segments: TemporalSegment[] }>(() => analysisApi.getTemporal());

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold">Dashboard</h2>
        <button
          onClick={refetchStats}
          disabled={statsLoading}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded transition"
        >
          {statsLoading ? 'Actualisation...' : 'Actualiser'}
        </button>
      </div>

      {/* Erreurs betting */}
      {statsError?.isBettingUnavailable && (
        <ErrorDisplay 
          error={statsError} 
          onRetry={refetchStats}
          className="mb-6"
        />
      )}
      
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatsCard 
          title="Total Bets" 
          value={stats?.total_bets || 0} 
        />
        <StatsCard 
          title="Win Rate" 
          value={`${stats?.win_rate || 0}%`} 
        />
        <StatsCard 
          title="Profit/Loss" 
          value={`${(stats?.total_profit || 0) > 0 ? '+' : ''}${(stats?.total_profit || 0).toFixed(2)} EUR`}
          trend={stats?.total_profit ? (stats.total_profit / 100) * 100 : undefined}
        />
        <StatsCard 
          title="Pending" 
          value={stats?.pending_bets || 0} 
        />
      </div>
      
      {/* Temporal Analysis */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h3 className="text-xl font-bold mb-4">Temporal Analysis</h3>
        {temporalLoading ? (
          <LoadingSpinner message="Chargement de l'analyse..." size="sm" />
        ) : temporalError ? (
          <ErrorDisplay error={temporalError} />
        ) : temporal?.segments?.length ? (
          <div className="space-y-2">
            {temporal.segments.map((seg) => (
              <div key={seg.range} className="flex items-center justify-between p-3 bg-gray-700 rounded">
                <span>Matches {seg.range}</span>
                <div className="flex items-center space-x-4">
                  <span className={`px-2 py-1 rounded text-sm ${
                    seg.accuracy > 0.65 ? 'bg-green-500' : seg.accuracy > 0.55 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}>
                    {(seg.accuracy * 100).toFixed(1)}%
                  </span>
                  <span className="text-sm text-gray-400">{seg.recommendation}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState 
            title="Analyse non disponible"
            message="Les données d'analyse temporelle ne sont pas disponibles pour le moment."
            icon="inbox"
          />
        )}
      </div>
    </Layout>
  );
}
