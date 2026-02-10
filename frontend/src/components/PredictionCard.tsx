import { Prediction } from '../lib/types';

interface PredictionCardProps {
  prediction: Prediction;
  onBet?: (p: Prediction) => void;
  compact?: boolean;
}

export function PredictionCard({ prediction, onBet, compact = false }: PredictionCardProps) {
  const isHighConfidence = prediction.confidence >= 0.7;
  const isMediumConfidence = prediction.confidence >= 0.6 && prediction.confidence < 0.7;
  
  const badgeColor = isHighConfidence 
    ? 'bg-green-500' 
    : isMediumConfidence 
    ? 'bg-yellow-500' 
    : 'bg-red-500';

  if (compact) {
    return (
      <div className="bg-gray-800 p-3 rounded-lg border border-gray-700 hover:border-gray-600 transition">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h4 className="font-semibold text-sm">
              {prediction.home_team} vs {prediction.away_team}
            </h4>
            <div className="flex items-center gap-2 mt-1">
              <span className={`${badgeColor} text-white px-2 py-0.5 rounded text-xs font-bold`}>
                {(prediction.confidence * 100).toFixed(0)}%
              </span>
              <span className="text-xs text-gray-400">
                {prediction.prediction}
              </span>
            </div>
          </div>
          {isHighConfidence && onBet && (
            <button
              onClick={() => onBet(prediction)}
              className="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded text-xs transition ml-2"
            >
              Bet
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h4 className="font-bold text-lg">
            {prediction.home_team} vs {prediction.away_team}
          </h4>
          <p className="text-gray-400 text-sm">Prediction: {prediction.prediction}</p>
        </div>
        <span className={`${badgeColor} text-white px-3 py-1 rounded-full text-sm font-bold`}>
          {(prediction.confidence * 100).toFixed(1)}%
        </span>
      </div>
      
      <div className="flex justify-between items-center">
        <div className="text-sm text-gray-400">
          Probability: {(prediction.proba_home_win * 100).toFixed(1)}%
        </div>
        {isHighConfidence && onBet && (
          <button
            onClick={() => onBet(prediction)}
            className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded transition"
          >
            Bet (Paper)
          </button>
        )}
      </div>
    </div>
  );
}
