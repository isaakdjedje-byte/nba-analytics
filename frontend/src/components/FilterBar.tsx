// FilterBar component

interface FilterOption {
  value: string;
  label: string;
}

interface FilterConfig {
  key: string;
  label: string;
  options: FilterOption[];
  defaultValue?: string;
}

interface FilterBarProps {
  filters: FilterConfig[];
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
  onReset?: () => void;
}

export function FilterBar({ filters, values, onChange, onReset }: FilterBarProps) {
  const hasActiveFilters = Object.values(values).some(v => v && v !== 'all');

  return (
    <div className="flex flex-wrap items-center gap-3 bg-gray-800 p-4 rounded-lg">
      {filters.map((filter) => (
        <div key={filter.key} className="flex flex-col gap-1">
          <label className="text-xs text-gray-400 uppercase tracking-wide">
            {filter.label}
          </label>
          <select
            value={values[filter.key] || filter.defaultValue || 'all'}
            onChange={(e) => onChange(filter.key, e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm 
                       focus:outline-none focus:border-blue-500 transition-colors
                       min-w-[120px]"
          >
            {filter.options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      ))}
      
      {onReset && hasActiveFilters && (
        <button
          onClick={onReset}
          className="ml-auto text-sm text-gray-400 hover:text-white 
                     flex items-center gap-1 transition-colors"
        >
          <span>✕</span> Réinitialiser
        </button>
      )}
    </div>
  );
}

// Préréglages de filtres communs
export const confidenceFilter: FilterConfig = {
  key: 'confidence',
  label: 'Confiance',
  defaultValue: 'all',
  options: [
    { value: 'all', label: 'Tout' },
    { value: '0.6', label: '≥60%' },
    { value: '0.7', label: '≥70%' },
    { value: '0.8', label: '≥80%' },
  ],
};

export const teamFilter = (teams: string[]): FilterConfig => ({
  key: 'team',
  label: 'Équipe',
  defaultValue: 'all',
  options: [
    { value: 'all', label: 'Toutes' },
    ...teams.map(t => ({ value: t, label: t })),
  ],
});

export const typeFilter: FilterConfig = {
  key: 'type',
  label: 'Type',
  defaultValue: 'all',
  options: [
    { value: 'all', label: 'Tout' },
    { value: '1x2', label: '1X2' },
    { value: 'handicap', label: 'Handicap' },
    { value: 'total', label: 'Total' },
  ],
};
