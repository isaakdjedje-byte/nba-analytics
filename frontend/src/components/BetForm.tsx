import { useState } from 'react';
import { Prediction } from '../lib/types';
import { betsApi } from '../lib/api';
import { AlertCircle, ServerOff } from 'lucide-react';

interface BetFormProps {
  prediction: Prediction;
  onSuccess: () => void;
  onCancel: () => void;
}

interface BetError {
  message: string;
  isServiceUnavailable?: boolean;
  isValidationError?: boolean;
}

export function BetForm({ prediction, onSuccess, onCancel }: BetFormProps) {
  const [stake, setStake] = useState(2);
  const [odds, setOdds] = useState(1.85);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<BetError | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      await betsApi.place({
        date: new Date().toISOString().split('T')[0],
        match: `${prediction.home_team} vs ${prediction.away_team}`,
        prediction: prediction.prediction,
        stake,
        odds,
      });
      onSuccess();
    } catch (err: any) {
      const status = err.response?.status;
      
      if (status === 503) {
        setError({
          message: 'Le service de paris est temporairement indisponible. Veuillez réessayer dans quelques instants.',
          isServiceUnavailable: true
        });
      } else if (status === 422) {
        setError({
          message: err.response?.data?.detail || 'Données invalides. Vérifiez le montant et les cotes.',
          isValidationError: true
        });
      } else {
        setError({
          message: 'Une erreur est survenue lors du placement du pari. Veuillez réessayer.'
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 p-6 rounded-lg w-96">
        <h3 className="text-xl font-bold mb-4">Place Paper Bet</h3>
        
        {/* Affichage erreur */}
        {error && (
          <div className={`mb-4 p-3 rounded flex items-start gap-3 ${
            error.isServiceUnavailable 
              ? 'bg-yellow-900/30 border border-yellow-700 text-yellow-400' 
              : 'bg-red-900/30 border border-red-700 text-red-400'
          }`}>
            {error.isServiceUnavailable ? <ServerOff size={20} /> : <AlertCircle size={20} />}
            <div className="flex-1 text-sm">{error.message}</div>
          </div>
        )}
        
        <div className="mb-4 p-3 bg-gray-700 rounded">
          <p className="font-semibold">{prediction.home_team} vs {prediction.away_team}</p>
          <p className="text-sm text-gray-400">Prediction: {prediction.prediction}</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Stake (EUR)</label>
            <input
              type="number"
              value={stake}
              onChange={(e) => setStake(Number(e.target.value))}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              min="0.5"
              step="0.5"
            />
          </div>
          
          <div>
            <label className="block text-sm text-gray-400 mb-1">Odds</label>
            <input
              type="number"
              value={odds}
              onChange={(e) => setOdds(Number(e.target.value))}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              min="1.01"
              step="0.01"
            />
          </div>
          
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 bg-gray-600 hover:bg-gray-500 py-2 rounded"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-blue-600 hover:bg-blue-500 py-2 rounded disabled:opacity-50"
            >
              {loading ? '...' : 'Confirm'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
