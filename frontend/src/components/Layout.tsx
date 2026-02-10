import { Home, DollarSign, Brain, Calendar } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  
  const navItems = [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/predictions', icon: Calendar, label: 'Prédictions Week' },
    { path: '/betting', icon: DollarSign, label: 'Paper Trading' },
    { path: '/ml-pipeline', icon: Brain, label: 'Pipeline ML' },
  ];

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      <nav className="w-64 bg-gray-800 p-4">
        <h1 className="text-2xl font-bold mb-8 text-red-600">NBA Analytics</h1>
        <div className="space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center space-x-3 p-3 rounded ${
                location.pathname === item.path 
                  ? 'bg-blue-600 text-white' 
                  : 'hover:bg-gray-700'
              }`}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </Link>
          ))}
        </div>
      </nav>
      
      <main className="flex-1 p-8 overflow-auto">
        {children}
      </main>
    </div>
  );
}
