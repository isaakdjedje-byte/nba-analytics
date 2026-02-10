import { useState, useEffect, useCallback } from 'react';

export interface ApiError {
  message: string;
  status?: number;
  isServiceUnavailable?: boolean;
}

export function useApi<T>(apiCall: () => Promise<T>, deps: any[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      const result = await apiCall();
      setData(result);
      setError(null);
    } catch (err: any) {
      // J5: Gestion améliorée des erreurs avec status code
      const status = err.response?.status;
      const isServiceUnavailable = status === 503;
      
      let message = err.message || 'Error';
      
      if (isServiceUnavailable) {
        message = 'Service temporairement indisponible';
      }
      
      setError({
        message,
        status,
        isServiceUnavailable
      });
    } finally {
      setLoading(false);
    }
  }, deps);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
}

export function useAutoRefresh<T>(apiCall: () => Promise<T>, intervalMs = 300000) {
  const result = useApi(apiCall);
  
  useEffect(() => {
    const interval = setInterval(result.refetch, intervalMs);
    return () => clearInterval(interval);
  }, [result.refetch, intervalMs]);
  
  return result;
}

// J5: Hook spécifique pour les bets avec gestion 503 (Delta A2)
export function useBetsApi<T>(apiCall: () => Promise<T>, deps: any[] = []) {
  const result = useApi<T>(apiCall, deps);
  
  // Enrichir l'erreur avec contexte betting
  const enrichedError = result.error ? {
    ...result.error,
    isBettingUnavailable: result.error.status === 503,
    userMessage: result.error.status === 503 
      ? 'Le service de paris est temporairement indisponible. Veuillez réessayer plus tard.'
      : result.error.message
  } : null;
  
  return {
    ...result,
    error: enrichedError
  };
}
