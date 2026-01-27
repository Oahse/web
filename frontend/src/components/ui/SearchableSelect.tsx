import React, { useState, useRef, useEffect, forwardRef } from 'react';
import { ChevronDownIcon, SearchIcon, CheckIcon, XIcon } from 'lucide-react';
import { cn } from '../../lib/utils';
import { themeClasses, combineThemeClasses, getInputClasses } from '../../lib/themeClasses';

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
  variant?: 'default' | 'outline' | 'filled';
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
  noOptionsMessage = "No options found",
  variant = 'default'
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
    sm: 'py-1.5 text-sm',
    md: 'py-2.5 text-sm sm:text-base',
    lg: 'py-3 text-lg'
  };

  const variantStyles = {
    default: getInputClasses(error ? 'error' : 'default'),
    outline: combineThemeClasses(
      'border-2 bg-transparent',
      error ? themeClasses.border.error : themeClasses.border.default,
      'focus-within:border-primary focus-within:ring-primary/20'
    ),
    filled: combineThemeClasses(
      themeClasses.background.elevated,
      'border-transparent focus-within:border-primary focus-within:ring-primary/20'
    )
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
    <div className={combineThemeClasses('relative', fullWidth && 'w-full')} ref={containerRef}>
      {label && (
        <label className={combineThemeClasses(themeClasses.text.primary, 'block text-sm font-medium mb-2')}>
          {label}
          {required && <span className={combineThemeClasses(themeClasses.text.error, 'ml-1')}>*</span>}
        </label>
      )}
      
      <div className="relative">
        <div
          className={combineThemeClasses(
            'w-full flex items-center rounded-lg cursor-pointer transition-all duration-200',
            sizeStyles[size],
            variantStyles[variant],
            disabled && themeClasses.input.disabled,
            !disabled && themeClasses.interactive.hover,
            className
          )}
          onClick={handleInputClick}
        >
          <div className="flex-1 flex items-center px-3">
            <SearchIcon size={size === 'sm' ? 14 : size === 'lg' ? 18 : 16} className={combineThemeClasses(themeClasses.text.muted, 'mr-2 flex-shrink-0')} />
            
            {isOpen ? (
              <input
                ref={inputRef}
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={placeholder}
                className={combineThemeClasses(
                  'flex-1 bg-transparent outline-none',
                  themeClasses.text.primary,
                  'placeholder:' + themeClasses.text.muted
                )}
                disabled={disabled}
              />
            ) : (
              <span className={combineThemeClasses(
                'flex-1 truncate',
                selectedOption ? themeClasses.text.primary : themeClasses.text.muted
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
                className={combineThemeClasses(
                  'p-1 rounded transition-colors',
                  themeClasses.text.muted,
                  themeClasses.interactive.hover
                )}
              >
                <XIcon size={14} />
              </button>
            )}
            <ChevronDownIcon 
              size={size === 'sm' ? 14 : size === 'lg' ? 18 : 16} 
              className={combineThemeClasses(
                themeClasses.text.muted,
                'transition-transform duration-200',
                isOpen && 'rotate-180'
              )} 
            />
          </div>
        </div>

        {/* Dropdown */}
        {isOpen && (
          <div className={combineThemeClasses(
            themeClasses.card.elevated,
            'absolute z-50 w-full mt-1 max-h-60 overflow-auto'
          )}>
            {filteredOptions.length > 0 ? (
              <ul ref={listRef} className="py-1">
                {filteredOptions.map((option, index) => (
                  <li
                    key={option.value}
                    className={combineThemeClasses(
                      'px-3 py-2 cursor-pointer flex items-center justify-between transition-colors',
                      index === highlightedIndex && 'bg-primary/10',
                      option.value === value && 'bg-primary/5',
                      themeClasses.interactive.hover
                    )}
                    onClick={() => handleSelect(option.value)}
                  >
                    <div className="flex-1">
                      <div className={themeClasses.text.primary}>{option.label}</div>
                      {option.description && (
                        <div className={combineThemeClasses(themeClasses.text.muted, 'text-xs')}>{option.description}</div>
                      )}
                    </div>
                    {option.value === value && (
                      <CheckIcon size={16} className={combineThemeClasses(themeClasses.text.success, 'ml-2')} />
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <div className={combineThemeClasses(themeClasses.text.muted, 'px-3 py-2 text-center')}>
                {noOptionsMessage}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Helper text or error */}
      {(helperText || error) && (
        <p className={combineThemeClasses(
          'mt-2 text-xs',
          error ? themeClasses.text.error : themeClasses.text.muted
        )}>
          {error || helperText}
        </p>
      )}
    </div>
  );
});

SearchableSelect.displayName = 'SearchableSelect';