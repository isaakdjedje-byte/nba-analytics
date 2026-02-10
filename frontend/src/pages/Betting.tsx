import { useState } from 'react';
import { Layout } from '../components/Layout';
import { StatsCard } from '../components/StatsCard';
import { PredictionCard } from '../components/PredictionCard';
import { BetForm } from '../components/BetForm';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { useBetsApi, useAutoRefresh } from '../hooks/useApi';
import { useApi } from '../hooks/useApi';
import { betsApi, predictionsApi } from '../lib/api';
import { PaperTradingStats, Bet, Prediction } from '../lib/types';

export function Betting() {
  // Utiliser useBetsApi pour les appels betting (gestion 503 intégrée)
  const { 
    data: stats, 
    error: statsError,
    refetch: refetchStats 
  } = useBetsApi<PaperTradingStats>(() => betsApi.getStats(), []);
  
  const { 
    data: bets, 
    error: betsError,
    loading: betsLoading,
    refetch: refetchBets 
  } = useBetsApi<{ bets: Bet[] }>(() => betsApi.getAll(), []);
  
  const { 
    data: predictions,
    error: predictionsError,
    loading: predictionsLoading 
  } = useApi<{ predictions: Prediction[] }>(() => 
    predictionsApi.getAll(0.7)
  );
  
  const [selectedPrediction, setSelectedPrediction] = useState<Prediction | null>(null);
  
  // Gestionnaire de refresh global
  const handleRefresh = () => {
    refetchStats();
    refetchBets();
  };

  const handleUpdateResult = async (betId: string, result: string) => {
    await betsApi.update(betId, result);
    refetchBets();
  };

  // Affichage erreur globale (503 betting)
  if (statsError?.isBettingUnavailable || betsError?.isBettingUnavailable) {
    return (
      <Layout>
        <h2 className="text-3xl font-bold mb-6">Paper Trading</h2>
        <ErrorDisplay 
          error={statsError || betsError} 
          onRetry={handleRefresh}
          className="mb-6"
        />
        <div className="grid grid-cols-2 gap-8">
          <div>
            <h3 className="text-xl font-bold mb-4">High Confidence Predictions (≥70%)</h3>
            {predictionsLoading ? (
              <LoadingSpinner message="Chargement des prédictions..." />
            ) : predictions?.predictions?.length ? (
              <div className="space-y-3">
                {predictions.predictions.map((pred) => (
                  <PredictionCard 
                    key={`${pred.home_team}-${pred.away_team}`}
                    prediction={pred}
                    onBet={setSelectedPrediction}
                  />
                ))}
              </div>
            ) : (
              <EmptyState 
                title="Aucune prédiction"
                message="Aucune prédiction disponible pour le moment."
              />
            )}
          </div>
          <div>
            <EmptyState
              title="Paris indisponibles"
              message="Le service de paris est temporairement indisponible. Vous pouvez consulter les prédictions mais pas placer de paris."
              icon="inbox"
            />
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold">Paper Trading</h2>
        <button
          onClick={handleRefresh}
          disabled={betsLoading}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 rounded transition"
        >
          {betsLoading ? 'Actualisation...' : 'Actualiser'}
        </button>
      </div>

      {/* Erreurs partielles */}
      {(statsError || betsError) && (
        <ErrorDisplay 
          error={statsError || betsError} 
          onRetry={handleRefresh}
          className="mb-6"
        />
      )}
      
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatsCard title="Current Bankroll" value={`${100 + (stats?.total_profit || 0)} EUR`} />
        <StatsCard title="Win Rate" value={`${stats?.win_rate || 0}%`} />
        <StatsCard title="Total Profit" value={`${stats?.total_profit?.toFixed(2) || 0} EUR`} />
        <StatsCard title="Active Bets" value={stats?.pending_bets || 0} />
      </div>

      <div className="grid grid-cols-2 gap-8">
        <div>
          <h3 className="text-xl font-bold mb-4">High Confidence Predictions (≥70%)</h3>
          {predictionsLoading ? (
            <LoadingSpinner message="Chargement des prédictions..." />
          ) : predictionsError ? (
            <ErrorDisplay error={predictionsError} />
          ) : predictions?.predictions?.length ? (
            <div className="space-y-3">
              {predictions.predictions.map((pred) => (
                <PredictionCard 
                  key={`${pred.home_team}-${pred.away_team}`}
                  prediction={pred}
                  onBet={setSelectedPrediction}
                />
              ))}
            </div>
          ) : (
            <EmptyState 
              title="Aucune prédiction"
              message="Aucune prédiction à haute confiance disponible pour le moment."
            />
          )}
        </div>
        
        <div>
          <h3 className="text-xl font-bold mb-4">Active Bets</h3>
          {betsLoading ? (
            <LoadingSpinner message="Chargement des paris..." />
          ) : bets?.bets?.filter(b => b.result === 'pending').length === 0 ? (
            <EmptyState 
              title="Aucun pari actif"
              message="Vous n'avez pas de paris en cours. Sélectionnez une prédiction pour placer un pari."
              icon="inbox"
            />
          ) : (
            <div className="space-y-2 mb-6">
              {bets?.bets?.filter(b => b.result === 'pending').map((bet) => (
                <div key={bet.id} className="flex items-center justify-between p-3 bg-gray-700 rounded">
                  <div>
                    <p className="font-semibold">{bet.match}</p>
                    <p className="text-sm text-gray-400">{bet.prediction} • {bet.stake} EUR @ {bet.odds}</p>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleUpdateResult(bet.id, 'win')}
                      className="bg-green-600 hover:bg-green-500 px-3 py-1 rounded text-sm"
                    >
                      Win
                    </button>
                    <button
                      onClick={() => handleUpdateResult(bet.id, 'loss')}
                      className="bg-red-600 hover:bg-red-500 px-3 py-1 rounded text-sm"
                    >
                      Loss
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          <h3 className="text-xl font-bold mb-4">History</h3>
          <div className="space-y-2">
            {bets?.bets?.filter(b => b.result !== 'pending').slice(0, 10).map((bet) => (
              <div key={bet.id} className="flex items-center justify-between p-3 bg-gray-700 rounded">
                <div>
                  <p className="font-semibold">{bet.match}</p>
                  <p className="text-sm text-gray-400">{bet.date}</p>
                </div>
                <div className={`font-bold ${bet.profit && bet.profit > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {bet.profit && bet.profit > 0 ? '+' : ''}{bet.profit?.toFixed(2)} EUR
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {selectedPrediction && (
        <BetForm
          prediction={selectedPrediction}
          onSuccess={() => {
            setSelectedPrediction(null);
            refetchBets();
          }}
          onCancel={() => setSelectedPrediction(null)}
        />
      )}
    </Layout>
  );
}
