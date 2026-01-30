import React from 'react';
import { LucideIcon } from 'lucide-react';
import { useTheme } from '../../../store/ThemeContext';

export interface AdminStatsCardProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: 'increase' | 'decrease' | 'neutral';
    period?: string;
  };
  icon?: LucideIcon;
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple' | 'indigo' | 'pink' | 'gray';
  loading?: boolean;
  error?: string;
  className?: string;
  onClick?: () => void;
}

export const AdminStatsCard: React.FC<AdminStatsCardProps> = ({
  title,
  value,
  change,
  icon: Icon,
  color = 'blue',
  loading = false,
  error,
  className = '',
  onClick
}) => {
  const { theme } = useTheme();

  const colorClasses = {
    blue: 'bg-blue-500 text-white',
    green: 'bg-green-500 text-white',
    red: 'bg-red-500 text-white',
    yellow: 'bg-yellow-500 text-white',
    purple: 'bg-purple-500 text-white',
    indigo: 'bg-indigo-500 text-white',
    pink: 'bg-pink-500 text-white',
    gray: 'bg-gray-500 text-white'
  };

  const changeColorClasses = {
    increase: 'text-green-600 bg-green-100',
    decrease: 'text-red-600 bg-red-100',
    neutral: 'text-gray-600 bg-gray-100'
  };

  const changeIcons = {
    increase: '↗',
    decrease: '↘',
    neutral: '→'
  };

  if (loading) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4"></div>
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
          <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/4"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-red-200 dark:border-red-700 p-6 ${className}`}>
        <div className="text-red-600 dark:text-red-400 text-sm">{error}</div>
      </div>
    );
  }

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow ${
        onClick ? 'cursor-pointer' : ''
      } ${className}`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
          
          {change && (
            <div className="flex items-center mt-2">
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${changeColorClasses[change.type]}`}>
                <span className="mr-1">{changeIcons[change.type]}</span>
                {Math.abs(change.value)}%
                {change.period && ` ${change.period}`}
              </span>
            </div>
          )}
        </div>
        
        {Icon && (
          <div className={`ml-4 p-3 rounded-lg ${colorClasses[color]}`}>
            <Icon className="h-6 w-6" />
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminStatsCard;
