import { Inbox, Calendar, Search } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  message?: string;
  icon?: 'inbox' | 'calendar' | 'search';
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({ 
  title = 'Aucune donnée', 
  message = 'Il n\'y a rien à afficher pour le moment.',
  icon = 'inbox',
  action,
  className = '' 
}: EmptyStateProps) {
  const icons = {
    inbox: Inbox,
    calendar: Calendar,
    search: Search
  };

  const Icon = icons[icon];

  return (
    <div className={`bg-gray-800 rounded-lg p-8 text-center ${className}`}>
      <Icon size={48} className="mx-auto mb-4 text-gray-600" />
      <h3 className="text-xl font-bold mb-2">{title}</h3>
      <p className="text-gray-400 mb-4">{message}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
