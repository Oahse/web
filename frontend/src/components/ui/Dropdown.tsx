import React, { useState, useRef, useEffect } from 'react';
import { ChevronDownIcon, CheckIcon } from 'lucide-react';
import { cn } from '../../utils/utils';

interface DropdownOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface DropdownProps {
  options: DropdownOption[];
  value?: string;
  placeholder?: string;
  onChange: (value: string) => void;
  className?: string;
  disabled?: boolean;
}

export const Dropdown: React.FC<DropdownProps> = ({
  options,
  value,
  placeholder = 'Select an option',
  onChange,
  className = '',
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedOption, setSelectedOption] = useState<DropdownOption | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const option = options.find(opt => opt.value === value);
    setSelectedOption(option || null);
  }, [value, options]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (option: DropdownOption) => {
    if (option.disabled) return;
    setSelectedOption(option);
    onChange(option.value);
    setIsOpen(false);
  };

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          'w-full px-3 py-2 text-left border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors flex items-center justify-between',
          'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white',
          'hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed'
        )}
      >
        <span className={cn(
          selectedOption ? 'text-gray-900 dark:text-white' : 'text-gray-500 dark:text-gray-400'
        )}>
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronDownIcon 
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} 
        />
      </button>

      {isOpen && (
        <div className={cn(
          'absolute z-50 w-full mt-1 rounded-lg border shadow-lg max-h-60 overflow-auto',
          'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
        )}>
          {options.map((option, index) => (
            <button
              key={index}
              type="button"
              onClick={() => handleSelect(option)}
              disabled={option.disabled}
              className={cn(
                'w-full text-left px-3 py-2 text-sm transition-colors',
                option.disabled
                  ? 'text-gray-400 dark:text-gray-500 cursor-not-allowed'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700',
                value === option.value && 'bg-primary/10 text-primary dark:bg-primary/20'
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default Dropdown;
