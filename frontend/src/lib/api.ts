import axios from 'axios';

const API_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

export const predictionsApi = {
  getAll: (minConfidence = 0) => 
    api.get(`/api/v1/predictions?min_confidence=${minConfidence}`).then(res => res.data),
  getWeek: (minConfidence = 0.6) => 
    api.get(`/api/v1/predictions?view=week&min_confidence=${minConfidence}`).then(res => res.data),
  getByDate: (date: string, view: string = 'day', _includeHistory = true) =>
    api.get(`/api/v1/calendar/date/${date}?view_mode=${view}`).then(res => res.data),
};

// API Calendrier Pro
export const calendarApi = {
  getToday: (viewMode = 'day') =>
    api.get(`/api/v1/calendar/today?view_mode=${viewMode}`).then(res => res.data),
  
  getByDate: (date: string, viewMode = 'day', season = '2025-26') =>
    api.get(`/api/v1/calendar/date/${date}?view_mode=${viewMode}&season=${season}`).then(res => res.data),
  
  getWeek: (date: string, season = '2025-26') =>
    api.get(`/api/v1/calendar/week/${date}?season=${season}`).then(res => res.data),
  
  getMonth: (year: number, month: number, season = '2025-26') =>
    api.get(`/api/v1/calendar/month/${year}/${month}?season=${season}`).then(res => res.data),
  
  getRange: (start: string, end: string, season = '2025-26') =>
    api.get(`/api/v1/calendar/range?start=${start}&end=${end}&season=${season}`).then(res => res.data),
  
  getSeasonStats: (season = '2025-26') =>
    api.get(`/api/v1/calendar/stats/${season}`).then(res => res.data),
    
  refresh: () =>
    api.post('/api/v1/calendar/refresh').then(res => res.data),
};

export const betsApi = {
  place: (bet: any) => api.post('/api/v1/bets', bet).then(res => res.data),
  update: (betId: string, result: string) => 
    api.post('/api/v1/bets/update', { bet_id: betId, result }).then(res => res.data),
  getAll: (status = 'all', limit = 50) => 
    api.get(`/api/v1/bets?status=${status}&limit=${limit}`).then(res => res.data),
  getStats: () => api.get('/api/v1/bets/stats').then(res => res.data),
};

export const analysisApi = {
  getTemporal: () => api.get('/api/v1/analysis/temporal').then(res => res.data),
};

export default api;
