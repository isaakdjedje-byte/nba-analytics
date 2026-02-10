import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LoadingSpinner({ 
  message = 'Chargement...', 
  size = 'md',
  className = '' 
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-16 h-16'
  };

  const textSizes = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  };

  return (
    <div className={`flex flex-col items-center justify-center p-8 ${className}`}>
      <Loader2 
        className={`${sizeClasses[size]} text-blue-500 animate-spin mb-4`} 
      />
      <p className={`text-gray-400 ${textSizes[size]}`}>
        {message}
      </p>
    </div>
  );
}

// Variante pour carte/section
export function LoadingCard({ message = 'Chargement...' }: { message?: string }) {
  return (
    <div className="bg-gray-800 rounded-lg p-8 text-center">
      <LoadingSpinner message={message} size="md" />
    </div>
  );
}
