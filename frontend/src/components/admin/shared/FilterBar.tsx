import React, { useState } from 'react';
import { SearchIcon, FilterIcon, XIcon, CalendarIcon } from 'lucide-react';
import Dropdown from '../../ui/Dropdown';

export interface FilterOption {
  value: string;
  label: string;
}

export interface FilterConfig {
  key: string;
  label: string;
  type: 'select' | 'text' | 'date' | 'daterange';
  options?: FilterOption[];
  placeholder?: string;
  defaultValue?: string;
}

export interface AdminFilterBarProps {
  filters: FilterConfig[];
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
  onClear: () => void;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  searchPlaceholder?: string;
  className?: string;
}

export const AdminFilterBar: React.FC<AdminFilterBarProps> = ({
  filters,
  values,
  onChange,
  onClear,
  searchValue = '',
  onSearchChange,
  searchPlaceholder = 'Search...',
  className = ''
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const hasActiveFilters = Object.keys(values).some(key => values[key]);
  const hasActiveSearch = searchValue.trim().length > 0;

  const handleFilterChange = (key: string, value: string) => {
    onChange(key, value);
  };

  const handleClear = () => {
    onClear();
    if (onSearchChange) {
      onSearchChange('');
    }
  };

  const renderFilter = (filter: FilterConfig) => {
    const value = values[filter.key] || filter.defaultValue || '';

    switch (filter.type) {
      case 'select':
        return (
          <div key={filter.key} className="min-w-[150px]">
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {filter.label}
            </label>
            <select
              value={value}
              onChange={(e) => handleFilterChange(filter.key, e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">{filter.placeholder || `Select ${filter.label}`}</option>
              {filter.options?.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        );

      case 'text':
        return (
          <div key={filter.key} className="min-w-[150px]">
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {filter.label}
            </label>
            <input
              type="text"
              placeholder={filter.placeholder || `Filter by ${filter.label}`}
              value={value}
              onChange={(e) => handleFilterChange(filter.key, e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        );

      case 'date':
        return (
          <div key={filter.key} className="min-w-[150px]">
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {filter.label}
            </label>
            <input
              type="date"
              value={value}
              onChange={(e) => handleFilterChange(filter.key, e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        );

      case 'daterange':
        return (
          <div key={filter.key} className="min-w-[200px]">
            <label className="block text-xs font-medium text-gray-700 mb-1">
              {filter.label}
            </label>
            <div className="flex items-center space-x-2">
              <input
                type="date"
                value={value.split(',')[0] || ''}
                onChange={(e) => {
                  const endDate = value.split(',')[1] || '';
                  handleFilterChange(filter.key, `${e.target.value},${endDate}`);
                }}
                className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Start"
              />
              <span className="text-gray-500">-</span>
              <input
                type="date"
                value={value.split(',')[1] || ''}
                onChange={(e) => {
                  const startDate = value.split(',')[0] || '';
                  handleFilterChange(filter.key, `${startDate},${e.target.value}`);
                }}
                className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="End"
              />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const visibleFilters = showAdvanced ? filters : filters.slice(0, 3);

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 ${className}`}>
      <div className="flex flex-col space-y-4">
        {/* Search Bar */}
        {onSearchChange && (
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            <div className="flex-1 max-w-md">
              <div className="relative">
                <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 dark:text-gray-500" />
                <input
                  type="text"
                  placeholder={searchPlaceholder}
                  value={searchValue}
                  onChange={(e) => onSearchChange(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400"
                />
              </div>
            </div>
            
            {/* Clear Filters Button */}
            {(hasActiveFilters || hasActiveSearch) && (
              <button
                onClick={handleClear}
                className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
              >
                <XIcon className="h-4 w-4" />
                <span className="hidden sm:inline">Clear Filters</span>
                <span className="sm:hidden">Clear</span>
              </button>
            )}
            
            {/* Advanced Filters Toggle */}
            {filters.length > 3 && (
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center space-x-2 px-4 py-2 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 bg-blue-50 dark:bg-blue-900 hover:bg-blue-100 dark:hover:bg-blue-800 rounded-md transition-colors"
              >
                <FilterIcon className="h-4 w-4" />
                <span className="hidden sm:inline">{showAdvanced ? 'Show Less' : 'Show More'}</span>
                <span className="sm:hidden">{showAdvanced ? 'Less' : 'More'}</span>
              </button>
            )}
          </div>
        )}

        {/* Filters */}
        {filters.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {visibleFilters.map(renderFilter)}
          </div>
        )}

        {/* Active Filters Display */}
        {(hasActiveFilters || hasActiveSearch) && (
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-gray-200 dark:border-gray-700">
            <span className="text-sm text-gray-600 dark:text-gray-400">Active filters:</span>
            
            {hasActiveSearch && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                Search: {searchValue}
                <button
                  onClick={() => onSearchChange('')}
                  className="ml-2 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
                >
                  <XIcon className="h-3 w-3" />
                </button>
              </span>
            )}
            
            {Object.entries(values).map(([key, value]) => (
              value && (
                <span
                  key={key}
                  className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200"
                >
                  {filters.find((f) => f.key === key)?.label || key}: {value}
                  <button
                    onClick={() => handleFilterChange(key, '')}
                    className="ml-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                  >
                    <XIcon className="h-3 w-3" />
                  </button>
                </span>
              )
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminFilterBar;
