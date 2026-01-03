import React, { useState, useMemo, useRef, useEffect } from 'react';
import { cn } from '../../lib/utils';
import { 
  countries, 
  getPopularCountries, 
  searchCountries, 
  continents, 
  getCurrencySymbol
} from '../../lib/countries';
import { ChevronDownIcon, SearchIcon, XIcon, GlobeIcon } from 'lucide-react';

export const CountrySelector = ({
  value,
  onChange,
  placeholder = "Select a country",
  className,
  disabled = false,
  showFlag = true,
  showCurrency = false,
  showPhoneCode = false,
  groupByContinent = false,
  showPopularFirst = true,
  searchable = true,
  clearable = false,
  size = 'md',
  variant = 'default',
  error = false,
  helperText
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const dropdownRef = useRef(null);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  const selectedCountry = useMemo(() => {
    const safeCountries = countries || [];
    const foundCountry = value ? safeCountries.find(c => c.code === value) : undefined;
    return foundCountry;
  }, [value]);

  const filteredCountries = useMemo(() => {
    let result = searchQuery ? searchCountries(searchQuery) : countries;
    
    if (showPopularFirst && !searchQuery) {
      const popular = getPopularCountries();
      const others = result.filter(c => !c.popular);
      result = [...popular, ...others];
    }
    
    return result;
  }, [searchQuery, showPopularFirst]);

  const groupedCountries = useMemo(() => {
    if (!groupByContinent) return { 'All Countries': filteredCountries };
    
    const groups = {};
    
    if (showPopularFirst && !searchQuery) {
      groups['Popular'] = getPopularCountries();
    }
    
    continents.forEach(continent => {
      const countriesInContinent = filteredCountries.filter(c => 
        c.continent === continent && (!showPopularFirst || !c.popular || searchQuery)
      );
      if (countriesInContinent.length > 0) {
        groups[continent] = countriesInContinent;
      }
    });
    
    return groups;
  }, [filteredCountries, groupByContinent, showPopularFirst, searchQuery]);

  const allOptions = useMemo(() => {
    const options = [];
    Object.entries(groupedCountries).forEach(([groupName, countries]) => {
      if (groupByContinent) {
        options.push({ type: 'group', name: groupName });
      }
      options.push(...countries);
    });
    return options;
  }, [groupedCountries, groupByContinent]);

  const handleSelect = (country) => {
    onChange(country);
    setIsOpen(false);
    setSearchQuery('');
    setHighlightedIndex(-1);
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setHighlightedIndex(prev => {
            const nextIndex = prev + 1;
            const maxIndex = allOptions.filter(option => 'code' in option).length - 1;
            return nextIndex > maxIndex ? 0 : nextIndex;
          });
          break;
        case 'ArrowUp':
          e.preventDefault();
          setHighlightedIndex(prev => {
            const prevIndex = prev - 1;
            const maxIndex = allOptions.filter(option => 'code' in option).length - 1;
            return prevIndex < 0 ? maxIndex : prevIndex;
          });
          break;
        case 'Enter': {
          e.preventDefault();
          const countryOptions = allOptions.filter(option => 'code' in option);
          if (highlightedIndex >= 0 && countryOptions[highlightedIndex]) {
            handleSelect(countryOptions[highlightedIndex]);
          }
          break;
        }
        case 'Escape':
          setIsOpen(false);
          setSearchQuery('');
          break;
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, highlightedIndex, allOptions, handleSelect]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearchQuery('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  
  const handleClear = (e) => {
    e.stopPropagation();
    onChange({ code: '', name: '', flag: '', currency: '', languages: [], continent: '', phoneCode: '' });
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-4 py-3 text-lg'
  };

  const variantClasses = {
    default: 'border border-border bg-surface shadow-sm',
    minimal: 'border-0 border-b border-border bg-transparent rounded-none'
  };

  return (
    <div className={cn('relative', className)} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          'w-full flex items-center justify-between rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-colors',
          sizeClasses[size],
          variantClasses[variant],
          error && 'border-error focus:ring-error',
          disabled && 'opacity-50 cursor-not-allowed bg-surface-disabled',
          'hover:border-border-strong'
        )}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label="Select country"
      >
        <div className="flex items-center min-w-0 flex-1">
          {selectedCountry ? (
            <>
              {showFlag && (
                <span className="mr-2 text-lg" role="img" aria-label={`${selectedCountry.name} flag`}>
                  {selectedCountry.flag}
                </span>
              )}
              <span className="truncate">{selectedCountry.name}</span>
              {showPhoneCode && (
                <span className="ml-2 text-copy-light text-sm">
                  {selectedCountry.phoneCode}
                </span>
              )}
              {showCurrency && (
                <span className="ml-2 text-copy-light text-sm">
                  {getCurrencySymbol(selectedCountry.currency)} {selectedCountry.currency}
                </span>
              )}
            </>
          ) : (
            <span className="text-copy-light flex items-center">
              <GlobeIcon size={16} className="mr-2" />
              {placeholder}
            </span>
          )}
        </div>
        
        <div className="flex items-center ml-2">
          {clearable && selectedCountry && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1 hover:bg-surface-hover rounded mr-1"
              aria-label="Clear selection"
            >
              <XIcon size={14} />
            </button>
          )}
          <ChevronDownIcon 
            size={16} 
            className={cn(
              'text-copy-muted transition-transform',
              isOpen && 'transform rotate-180'
            )} 
          />
        </div>
      </button>

      {helperText && (
        <p className={cn(
          'mt-1 text-sm',
          error ? 'text-error-600' : 'text-copy-light'
        )}>
          {helperText}
        </p>
      )}

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-surface border border-border rounded-md shadow-lg max-h-60 overflow-hidden">
          {searchable && (
            <div className="p-2 border-b border-border">
              <div className="relative">
                <SearchIcon size={16} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-copy-muted" />
                <input
                  ref={inputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search countries..."
                  className="w-full pl-9 pr-3 py-2 text-sm border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent bg-surface text-copy"
                  autoFocus
                />
              </div>
            </div>
          )}

          <div ref={listRef} className="overflow-y-auto max-h-48">
            {Object.entries(groupedCountries).map(([groupName, groupCountries]) => (
              <div key={groupName}>
                {groupByContinent && (
                  <div className="px-3 py-2 text-xs font-semibold text-copy-light bg-surface-hover border-b border-border-light">
                    {groupName}
                  </div>
                )}
                {groupCountries.map((country) => {
                  const globalIndex = allOptions.filter(option => 'code' in option).findIndex(c => c.code === country.code);
                  const isHighlighted = globalIndex === highlightedIndex;
                  const isSelected = selectedCountry?.code === country.code;
                  
                  return (
                    <button
                      key={country.code}
                      type="button"
                      onClick={() => handleSelect(country)}
                      className={cn(
                        'w-full px-3 py-2 text-left flex items-center hover:bg-surface-hover focus:outline-none focus:bg-surface-hover',
                        isHighlighted && 'bg-surface-hover',
                        isSelected && 'bg-primary text-white hover:bg-primary'
                      )}
                      role="option"
                      aria-selected={isSelected}
                    >
                      {showFlag && (
                        <span className="mr-3 text-lg" role="img" aria-label={`${country.name} flag`}>
                          {country.flag}
                        </span>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="truncate">{country.name}</div>
                        {(showPhoneCode || showCurrency) && (
                          <div className="text-xs text-copy-light mt-0.5">
                            {showPhoneCode && country.phoneCode}
                            {showPhoneCode && showCurrency && ' • '}
                            {showCurrency && `${getCurrencySymbol(country.currency)} ${country.currency}`}
                          </div>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            ))}
            
            {filteredCountries.length === 0 && (
              <div className="px-3 py-8 text-center text-copy-light">
                <GlobeIcon size={24} className="mx-auto mb-2 text-copy-muted" />
                <p>No countries found</p>
                {searchQuery && (
                  <p className="text-sm mt-1">Try a different search term</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export const SimpleCountrySelector = (props) => (
  <CountrySelector
    {...props}
    groupByContinent={false}
    showPopularFirst={true}
    showCurrency={false}
    showPhoneCode={false}
  />
);

export const PhoneCountrySelector = (props) => (
  <CountrySelector
    {...props}
    showPhoneCode={true}
    placeholder="Select country code"
  />
);