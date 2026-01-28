/**
 * Locale Selector Component
 * 
 * Allows users to manually select their country/locale
 */

import React, { useState } from 'react';
import { useLocale } from '../../hooks/useLocale';
import { COUNTRY_CONFIG } from '../../utils/locale-config';
import { Globe, Check } from 'lucide-react';

export const LocaleSelector: React.FC = () => {
  const { locale, changeLocale, locationData, isDetecting } = useLocale();
  const [isOpen, setIsOpen] = useState(false);

  const handleLocaleChange = (countryCode: string) => {
    changeLocale(countryCode);
    setIsOpen(false);
  };

  if (isDetecting) {
    return (
      <div className="flex items-center gap-2 text-sm text-copy-light">
        <Globe className="w-4 h-4 animate-spin" />
        <span>Detecting location...</span>
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg hover:bg-surface-elevated transition-colors"
        aria-label="Select country"
      >
        <span className="text-xl">{locale.flag}</span>
        <span className="hidden sm:inline">{locale.name}</span>
        <span className="text-xs text-copy-light">{locale.currency}</span>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-72 bg-surface-elevated rounded-lg shadow-lg border border-border z-50 max-h-96 overflow-y-auto">
            <div className="p-3 border-b border-border">
              <h3 className="font-semibold text-sm">Select Your Country</h3>
              {locationData?.detected && (
                <p className="text-xs text-copy-light mt-1">
                  Auto-detected: {locationData.countryName}
                </p>
              )}
            </div>

            <div className="py-2">
              {Object.values(COUNTRY_CONFIG).map((country) => (
                <button
                  key={country.code}
                  onClick={() => handleLocaleChange(country.code)}
                  className={`w-full flex items-center justify-between px-4 py-2 text-sm hover:bg-surface transition-colors ${
                    locale.code === country.code ? 'bg-surface' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl">{country.flag}</span>
                    <div className="text-left">
                      <div className="font-medium">{country.name}</div>
                      <div className="text-xs text-copy-light">
                        {country.currency} • {country.language.toUpperCase()}
                      </div>
                    </div>
                  </div>
                  {locale.code === country.code && (
                    <Check className="w-4 h-4 text-primary" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
