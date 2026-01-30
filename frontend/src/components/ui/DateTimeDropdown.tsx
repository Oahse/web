import React, { useState, useRef, useEffect } from 'react';
import { CalendarIcon, ClockIcon } from 'lucide-react';
import { useTheme } from '../../store/ThemeContext';

interface DateTimeDropdownProps {
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
  showTime?: boolean;
}

export const DateTimeDropdown: React.FC<DateTimeDropdownProps> = ({
  value,
  onChange,
  placeholder = 'Select date',
  className = '',
  disabled = false,
  showTime = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [selectedTime, setSelectedTime] = useState<string>('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();

  useEffect(() => {
    if (value) {
      if (showTime) {
        const [date, time] = value.split('T');
        setSelectedDate(date || '');
        setSelectedTime(time || '');
      } else {
        setSelectedDate(value);
      }
    }
  }, [value, showTime]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleDateChange = (date: string) => {
    setSelectedDate(date);
    if (showTime && selectedTime) {
      onChange(`${date}T${selectedTime}`);
    } else if (!showTime) {
      onChange(date);
    }
  };

  const handleTimeChange = (time: string) => {
    setSelectedTime(time);
    if (selectedDate) {
      onChange(`${selectedDate}T${time}`);
    }
  };

  const formatDisplayValue = () => {
    if (!selectedDate) return placeholder;
    
    try {
      const date = new Date(selectedDate);
      if (showTime && selectedTime) {
        return date.toLocaleString() + ' ' + selectedTime;
      }
      return date.toLocaleDateString();
    } catch {
      return selectedDate;
    }
  };

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`w-full px-3 py-2 text-left border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-colors flex items-center justify-between ${
          theme === 'dark' 
            ? 'bg-gray-700 border-gray-600 text-white hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed' 
            : 'bg-white border-gray-300 text-gray-900 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed'
        }`}
      >
        <span className={selectedDate ? '' : 'text-gray-500'}>
          {formatDisplayValue()}
        </span>
        <CalendarIcon className="w-4 h-4" />
      </button>

      {isOpen && (
        <div className={`absolute z-50 w-full mt-1 rounded-lg border shadow-lg p-4 ${
          theme === 'dark' 
            ? 'bg-gray-800 border-gray-700' 
            : 'bg-white border-gray-200'
        }`}>
          <div className="space-y-3">
            <div>
              <label className={`block text-sm font-medium mb-2 ${
                theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
              }`}>
                Date
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => handleDateChange(e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent ${
                  theme === 'dark' 
                    ? 'bg-gray-700 border-gray-600 text-white' 
                    : 'bg-white border-gray-300 text-gray-900'
                }`}
              />
            </div>
            
            {showTime && (
              <div>
                <label className={`block text-sm font-medium mb-2 ${
                  theme === 'dark' ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Time
                </label>
                <div className="flex items-center space-x-2">
                  <ClockIcon className="w-4 h-4" />
                  <input
                    type="time"
                    value={selectedTime}
                    onChange={(e) => handleTimeChange(e.target.value)}
                    className={`flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent ${
                      theme === 'dark' 
                        ? 'bg-gray-700 border-gray-600 text-white' 
                        : 'bg-white border-gray-300 text-gray-900'
                    }`}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DateTimeDropdown;
