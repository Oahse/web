/**
 * Locale Context
 * 
 * Manages user's locale preferences including country, language, and currency.
 * Provides methods to change locale and format data according to user's location.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
  type LocaleConfig,
  getLocaleConfig,
  DEFAULT_LOCALE,
  convertCurrency,
  formatCurrency as formatCurrencyUtil,
  getSupportedCountries,
} from '../lib/locale-config';
import {
  detectUserLocation,
  saveLocationPreference,
  clearLocationPreference,
  getCurrentLocation,
  type LocationData,
} from '../lib/location-detection';

interface LocaleContextType {
  // Current locale configuration
  locale: LocaleConfig;
  countryCode: string;
  language: string;
  currency: string;
  flag: string;
  
  // Location data
  locationData: LocationData | null;
  isDetecting: boolean;
  
  // Methods
  changeLocale: (countryCode: string) => void;
  resetToAutoDetect: () => void;
  
  // Formatting utilities
  formatCurrency: (amount: number, sourceCurrency?: string) => string;
  convertPrice: (amountInUSD: number) => number;
  formatDate: (date: Date) => string;
  formatNumber: (num: number) => string;
  
  // Supported countries
  supportedCountries: string[];
}

const LocaleContext = createContext<LocaleContextType | undefined>(undefined);

interface LocaleProviderProps {
  children: ReactNode;
}

export function LocaleProvider({ children }: LocaleProviderProps) {
  const [locale, setLocale] = useState<LocaleConfig>(DEFAULT_LOCALE);
  const [locationData, setLocationData] = useState<LocationData | null>(null);
  const [isDetecting, setIsDetecting] = useState(true);

  // Detect user's location on mount
  useEffect(() => {
    const initializeLocale = async () => {
      setIsDetecting(true);
      
      try {
        // Check if we have a current location
        const currentLocation = getCurrentLocation();
        
        if (currentLocation) {
          // Use cached/saved location
          const config = getLocaleConfig(currentLocation.countryCode);
          setLocale(config);
          setLocationData(currentLocation);
          setIsDetecting(false);
        } else {
          // Detect location
          const detected = await detectUserLocation();
          const config = getLocaleConfig(detected.countryCode);
          setLocale(config);
          setLocationData(detected);
          setIsDetecting(false);
        }
      } catch (error) {
        console.error('Error initializing locale:', error);
        setLocale(DEFAULT_LOCALE);
        setLocationData({
          countryCode: DEFAULT_LOCALE.code,
          countryName: DEFAULT_LOCALE.name,
          detected: false,
        });
        setIsDetecting(false);
      }
    };

    initializeLocale();
  }, []);

  // Change locale manually
  const changeLocale = (countryCode: string) => {
    const config = getLocaleConfig(countryCode);
    setLocale(config);
    
    // Save preference
    saveLocationPreference(countryCode);
    
    // Update location data
    setLocationData({
      countryCode: config.code,
      countryName: config.name,
      detected: false,
    });
  };

  // Reset to auto-detect
  const resetToAutoDetect = async () => {
    clearLocationPreference();
    setIsDetecting(true);
    
    try {
      const detected = await detectUserLocation();
      const config = getLocaleConfig(detected.countryCode);
      setLocale(config);
      setLocationData(detected);
    } catch (error) {
      console.error('Error resetting to auto-detect:', error);
      setLocale(DEFAULT_LOCALE);
      setLocationData({
        countryCode: DEFAULT_LOCALE.code,
        countryName: DEFAULT_LOCALE.name,
        detected: false,
      });
    } finally {
      setIsDetecting(false);
    }
  };

  // Format currency with conversion
  const formatCurrency = (amount: number, sourceCurrency: string = 'USD'): string => {
    let finalAmount = amount;
    
    // Convert if source currency is different from user's currency
    if (sourceCurrency !== locale.currency) {
      // If source is USD, convert directly
      if (sourceCurrency === 'USD') {
        finalAmount = convertCurrency(amount, locale.currency);
      } else {
        // For other currencies, we'd need to convert through USD
        // For now, we'll just use the amount as-is
        // In a real app, you'd want a more sophisticated conversion system
        finalAmount = amount;
      }
    }
    
    return formatCurrencyUtil(finalAmount, locale.currency, locale.language);
  };

  // Convert price from USD to user's currency
  const convertPrice = (amountInUSD: number): number => {
    return convertCurrency(amountInUSD, locale.currency);
  };

  // Format date according to locale
  const formatDate = (date: Date): string => {
    try {
      return new Intl.DateTimeFormat(locale.language, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      }).format(date);
    } catch (error) {
      console.error('Error formatting date:', error);
      return date.toLocaleDateString();
    }
  };

  // Format number according to locale
  const formatNumber = (num: number): string => {
    try {
      return new Intl.NumberFormat(locale.language).format(num);
    } catch (error) {
      console.error('Error formatting number:', error);
      return num.toString();
    }
  };

  const value: LocaleContextType = {
    locale,
    countryCode: locale.code,
    language: locale.language,
    currency: locale.currency,
    flag: locale.flag,
    locationData,
    isDetecting,
    changeLocale,
    resetToAutoDetect,
    formatCurrency,
    convertPrice,
    formatDate,
    formatNumber,
    supportedCountries: getSupportedCountries(),
  };

  return (
    <LocaleContext.Provider value={value}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale() {
  const context = useContext(LocaleContext);
  if (context === undefined) {
    throw new Error('useLocale must be used within a LocaleProvider');
  }
  return context;
}
