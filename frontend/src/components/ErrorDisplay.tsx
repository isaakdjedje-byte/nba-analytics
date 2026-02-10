import { AlertCircle, ServerOff, WifiOff, Loader2 } from 'lucide-react';

interface ErrorDisplayProps {
  error: {
    message: string;
    status?: number;
    isServiceUnavailable?: boolean;
    isBettingUnavailable?: boolean;
  } | null;
  onRetry?: () => void;
  className?: string;
}

export function ErrorDisplay({ error, onRetry, className = '' }: ErrorDisplayProps) {
  if (!error) return null;

  // Déterminer le type d'erreur pour l'affichage approprié
  const isServiceUnavailable = error.isServiceUnavailable || error.status === 503;
  const isBettingUnavailable = error.isBettingUnavailable;
  const isNetworkError = !error.status;

  // Message personnalisé selon le contexte
  let title = 'Erreur';
  let message = error.message;
  let icon = AlertCircle;
  let bgColor = 'bg-red-900/30';
  let borderColor = 'border-red-700';
  let textColor = 'text-red-400';

  if (isBettingUnavailable) {
    title = 'Service de paris indisponible';
    message = 'Le service de paris est temporairement indisponible. Vous pouvez toujours consulter les prédictions et le calendrier.';
    icon = ServerOff;
    bgColor = 'bg-yellow-900/30';
    borderColor = 'border-yellow-700';
    textColor = 'text-yellow-400';
  } else if (isServiceUnavailable) {
    title = 'Service temporairement indisponible';
    message = error.message || 'Le service est momentanément indisponible. Veuillez réessayer dans quelques instants.';
    icon = ServerOff;
    bgColor = 'bg-orange-900/30';
    borderColor = 'border-orange-700';
    textColor = 'text-orange-400';
  } else if (isNetworkError) {
    title = 'Problème de connexion';
    message = 'Impossible de se connecter au serveur. Vérifiez votre connexion internet.';
    icon = WifiOff;
    bgColor = 'bg-red-900/30';
    borderColor = 'border-red-700';
    textColor = 'text-red-400';
  }

  const Icon = icon;

  return (
    <div className={`rounded-lg border ${borderColor} ${bgColor} p-6 ${className}`}>
      <div className="flex items-start gap-4">
        <div className={`${textColor} flex-shrink-0`}>
          <Icon size={24} />
        </div>
        <div className="flex-1">
          <h3 className={`font-semibold ${textColor} mb-1`}>
            {title}
          </h3>
          <p className="text-gray-300 text-sm mb-3">
            {message}
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="inline-flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm transition"
            >
              <Loader2 size={16} className="animate-spin" style={{ animationDuration: '3s' }} />
              Réessayer
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
