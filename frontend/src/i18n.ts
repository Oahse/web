/**
 * i18n Utilities
 * 
 * Provides internationalization utilities for formatting dates, numbers, and currencies
 * using the Intl API and date-fns.
 */

import { format, formatDistance, formatRelative } from 'date-fns';
import { enUS, fr, ar, nl, sv, nb } from 'date-fns/locale';

// Map language codes to date-fns locales
const localeMap: Record<string, Locale> = {
  en: enUS,
  fr: fr,
  ar: ar,
  nl: nl,
  sv: sv,
  no: nb,
};

/**
 * Get date-fns locale for a language code
 */
export function getDateLocale(languageCode: string): Locale {
  return localeMap[languageCode] || enUS;
}

/**
 * Format date with locale support
 */
export function formatDate(
  date: Date | number,
  formatStr: string = 'PPP',
  locale?: string
): string {
  const dateLocale = locale ? getDateLocale(locale) : enUS;
  return format(date, formatStr, { locale: dateLocale });
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(
  date: Date | number,
  baseDate: Date | number = new Date(),
  locale?: string
): string {
  const dateLocale = locale ? getDateLocale(locale) : enUS;
  return formatDistance(date, baseDate, { addSuffix: true, locale: dateLocale });
}

/**
 * Format date relative to now (e.g., "today at 3:00 PM")
 */
export function formatRelativeDate(
  date: Date | number,
  baseDate: Date | number = new Date(),
  locale?: string
): string {
  const dateLocale = locale ? getDateLocale(locale) : enUS;
  return formatRelative(date, baseDate, { locale: dateLocale });
}

/**
 * Format number with locale support
 */
export function formatNumber(
  num: number,
  locale: string = 'en-US',
  options?: Intl.NumberFormatOptions
): string {
  return new Intl.NumberFormat(locale, options).format(num);
}

/**
 * Format currency with locale support
 */
export function formatCurrency(
  amount: number,
  currency: string = 'USD',
  locale: string = 'en-US'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency,
  }).format(amount);
}

/**
 * Format percentage with locale support
 */
export function formatPercentage(
  value: number,
  locale: string = 'en-US',
  decimals: number = 0
): string {
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Get language direction (LTR or RTL)
 */
export function getLanguageDirection(languageCode: string): 'ltr' | 'rtl' {
  const rtlLanguages = ['ar', 'he', 'fa', 'ur'];
  return rtlLanguages.includes(languageCode) ? 'rtl' : 'ltr';
}

// Re-export locale utilities
export { useLocale } from './hooks/useLocale';
export { LocaleProvider } from './contexts/LocaleContext';
