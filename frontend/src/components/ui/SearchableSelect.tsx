import React, { useState, useRef, useEffect, forwardRef } from 'react';
import { ChevronDownIcon, SearchIcon, CheckIcon } from 'lucide-react';
import { cn } from '../../lib/utils';
import './SearchableSelect.css';

interface Option {
  value: string;
  label: string;
  description?: string;
}

interface SearchableSelectProps {
  label?: React.ReactNode;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  options: Option[];
  error?: string;
  helperText?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  allowClear?: boolean;
  noOptionsMessage?: string;
}

export const SearchableSelect = forwardRef<HTMLInputElement, SearchableSelectProps>(({
  label,
  placeholder = "Search and select...",
  value = "",
  onChange,
  options = [],
  error,
  helperText,
  disabled = false,
  required = false,
  className,
  size = 'md',
  fullWidth = false,
  allowClear = false,
  noOptionsMessage = "No options found"
}, ref) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Filter options based on search term
  const filteredOptions = options.filter(option =>
    option.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
    option.value.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (option.description && option.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // Get selected option
  const selectedOption = options.find(option => option.value === value);

  // Size styles
  const sizeStyles = {
    sm: 'py-1 text-sm',
    md: 'py-2',
    lg: 'py-3 text-lg'
  };

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
        setHighlightedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isOpen) return;

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          setHighlightedIndex(prev => 
            prev < filteredOptions.length - 1 ? prev + 1 : 0
          );
          break;
        case 'ArrowUp':
          event.preventDefault();
          setHighlightedIndex(prev => 
            prev > 0 ? prev - 1 : filteredOptions.length - 1
          );
          break;
        case 'Enter':
          event.preventDefault();
          if (highlightedIndex >= 0 && filteredOptions[highlightedIndex]) {
            handleSelect(filteredOptions[highlightedIndex].value);
          }
          break;
        case 'Escape':
          setIsOpen(false);
          setSearchTerm('');
          setHighlightedIndex(-1);
          break;
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, highlightedIndex, filteredOptions]);

  // Scroll highlighted option into view
  useEffect(() => {
    if (highlightedIndex >= 0 && listRef.current) {
      const highlightedElement = listRef.current.children[highlightedIndex] as HTMLElement;
      if (highlightedElement) {
        highlightedElement.scrollIntoView({
          block: 'nearest',
          behavior: 'smooth'
        });
      }
    }
  }, [highlightedIndex]);

  const handleSelect = (optionValue: string) => {
    onChange?.(optionValue);
    setIsOpen(false);
    setSearchTerm('');
    setHighlightedIndex(-1);
  };

  const handleClear = () => {
    onChange?.('');
    setSearchTerm('');
    setIsOpen(false);
  };

  const handleInputClick = () => {
    if (!disabled) {
      setIsOpen(!isOpen);
      if (!isOpen) {
        // Focus the input when opening
        setTimeout(() => inputRef.current?.focus(), 0);
      }
    }
  };

  return (
    <div className={cn('relative', fullWidth && 'w-full')} ref={containerRef}>
      {label && (
        <label className="block text-sm font-medium text-copy mb-1">
          {label}
          {required && <span className="text-error ml-1">*</span>}
        </label>
      )}
      
      <div className="relative">
        <div
          className={cn(
            'w-full flex items-center border rounded-md cursor-pointer transition-colors',
            sizeStyles[size],
            error 
              ? 'border-error focus-within:border-error focus-within:ring-1 focus-within:ring-error/50' 
              : 'border-border focus-within:border-primary focus-within:ring-1 focus-within:ring-primary/50 hover:border-border-strong',
            disabled && 'opacity-50 cursor-not-allowed bg-surface-disabled',
            !disabled && 'bg-surface',
            className
          )}
          onClick={handleInputClick}
        >
          <div className="flex-1 flex items-center px-3">
            <SearchIcon size={16} className="text-copy-light mr-2 flex-shrink-0" />
            
            {isOpen ? (
              <input
                ref={inputRef}
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={placeholder}
                className="flex-1 bg-transparent outline-none text-copy placeholder-copy-light searchable-select-input"
                disabled={disabled}
              />
            ) : (
              <span className={cn(
                'flex-1 truncate',
                selectedOption ? 'text-copy' : 'text-copy-light'
              )}>
                {selectedOption ? selectedOption.label : placeholder}
              </span>
            )}
          </div>
          
          <div className="flex items-center px-2 space-x-1">
            {allowClear && value && !disabled && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleClear();
                }}
                className="p-1 hover:bg-surface-hover rounded text-copy-light hover:text-copy"
              >
                ×
              </button>
            )}
            <ChevronDownIcon 
              size={16} 
              className={cn(
                'text-copy-light transition-transform',
                isOpen && 'rotate-180'
              )} 
            />
          </div>
        </div>

        {/* Dropdown */}
        {isOpen && (
          <div className="absolute z-50 w-full mt-1 bg-surface border border-border rounded-md shadow-lg max-h-60 overflow-auto searchable-select-dropdown">
            {filteredOptions.length > 0 ? (
              <ul ref={listRef} className="py-1">
                {filteredOptions.map((option, index) => (
                  <li
                    key={option.value}
                    className={cn(
                      'px-3 py-2 cursor-pointer flex items-center justify-between searchable-select-option',
                      index === highlightedIndex && 'bg-primary/10',
                      option.value === value && 'bg-primary/5',
                      'hover:bg-surface-hover'
                    )}
                    onClick={() => handleSelect(option.value)}
                  >
                    <div className="flex-1">
                      <div className="text-copy">{option.label}</div>
                      {option.description && (
                        <div className="text-xs text-copy-light">{option.description}</div>
                      )}
                    </div>
                    {option.value === value && (
                      <CheckIcon size={16} className="text-primary ml-2" />
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <div className="px-3 py-2 text-copy-light text-center">
                {noOptionsMessage}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Helper text or error */}
      {(helperText || error) && (
        <p className={cn(
          'mt-1 text-xs',
          error ? 'text-error' : 'text-copy-light'
        )}>
          {error || helperText}
        </p>
      )}
    </div>
  );
});

SearchableSelect.displayName = 'SearchableSelect';