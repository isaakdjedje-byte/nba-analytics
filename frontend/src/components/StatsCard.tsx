import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  trend?: number;
  trendLabel?: string;
}

export function StatsCard({ title, value, trend, trendLabel }: StatsCardProps) {
  return (
    <div className="bg-gray-800 p-6 rounded-lg">
      <h3 className="text-gray-400 text-sm uppercase">{title}</h3>
      <div className="mt-2 flex items-end justify-between">
        <span className="text-3xl font-bold">{value}</span>
        {trend !== undefined && (
          <div className={`flex items-center ${trend >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {trend >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
            <span className="ml-1 text-sm">
              {trend > 0 ? '+' : ''}{trend}%{trendLabel && ` ${trendLabel}`}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
