// frontend/src/components/common/LocaleSelector.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vitest, beforeEach } from 'vitest';
import { LocaleSelector } from './LocaleSelector';
import { useLocale } from '../../hooks/useLocale';
import { COUNTRY_CONFIG } from '../../utils/locale-config';
import { Globe, Check } from 'lucide-react'; // Mocked icons

// Mock the useLocale hook
vitest.mock('../../hooks/useLocale', () => ({
  useLocale: vitest.fn(),
}));

// Mock COUNTRY_CONFIG with a simplified set of countries for testing
const mockCountryConfig = {
  US: { code: 'US', name: 'United States', flag: '🇺🇸', currency: 'USD', language: 'en' },
  CA: { code: 'CA', name: 'Canada', flag: '🇨🇦', currency: 'CAD', language: 'en' },
  GB: { code: 'GB', name: 'United Kingdom', flag: '🇬🇧', currency: 'GBP', language: 'en' },
};
vitest.mock('../../lib/locale-config', () => ({
  COUNTRY_CONFIG: mockCountryConfig,
}));

// Mock lucide-react icons to avoid SVG rendering issues
vitest.mock('lucide-react', () => ({
  Globe: vitest.fn(() => <svg data-testid="globe-icon" />),
  Check: vitest.fn(() => <svg data-testid="check-icon" />),
}));

describe('LocaleSelector Component', () => {
  const mockChangeLocale = vitest.fn();

  beforeEach(() => {
    vitest.clearAllMocks();
    // Default mock for useLocale
    (useLocale as vitest.Mock).mockReturnValue({
      locale: mockCountryConfig.US,
      changeLocale: mockChangeLocale,
      locationData: null,
      isDetecting: false,
    });
  });

  it('renders "Detecting location..." when isDetecting is true', () => {
    (useLocale as vitest.Mock).mockReturnValue({
      locale: mockCountryConfig.US,
      changeLocale: mockChangeLocale,
      locationData: null,
      isDetecting: true,
    });
    render(<LocaleSelector />);
    expect(screen.getByText('Detecting location...')).toBeInTheDocument();
    expect(screen.getByTestId('globe-icon')).toBeInTheDocument();
  });

  it('renders current locale info when not detecting', () => {
    render(<LocaleSelector />);
    expect(screen.getByLabelText('Select country')).toBeInTheDocument();
    expect(screen.getByText('🇺🇸')).toBeInTheDocument(); // Flag
    expect(screen.getByText('United States')).toBeInTheDocument(); // Name
    expect(screen.getByText('USD')).toBeInTheDocument(); // Currency
  });

  it('opens and closes the dropdown', () => {
    render(<LocaleSelector />);
    const selectButton = screen.getByLabelText('Select country');

    // Open dropdown
    fireEvent.click(selectButton);
    expect(screen.getByText('Select Your Country')).toBeInTheDocument();
    expect(screen.getByText('Canada')).toBeInTheDocument();

    // Close dropdown by clicking button again
    fireEvent.click(selectButton);
    expect(screen.queryByText('Select Your Country')).not.toBeInTheDocument();

    // Re-open and close by clicking backdrop
    fireEvent.click(selectButton);
    expect(screen.getByText('Select Your Country')).toBeInTheDocument();
    fireEvent.click(document.querySelector('.fixed.inset-0.z-40')!); // Click backdrop
    expect(screen.queryByText('Select Your Country')).not.toBeInTheDocument();
  });

  it('calls changeLocale with correct country code when an option is clicked', () => {
    render(<LocaleSelector />);
    fireEvent.click(screen.getByLabelText('Select country')); // Open dropdown

    fireEvent.click(screen.getByText('Canada')); // Click Canada option
    expect(mockChangeLocale).toHaveBeenCalledWith('CA');
    expect(screen.queryByText('Select Your Country')).not.toBeInTheDocument(); // Dropdown closes
  });

  it('displays auto-detected location data if available', () => {
    (useLocale as vitest.Mock).mockReturnValue({
      locale: mockCountryConfig.US,
      changeLocale: mockChangeLocale,
      locationData: { detected: true, countryName: 'Detected Country' },
      isDetecting: false,
    });
    render(<LocaleSelector />);
    fireEvent.click(screen.getByLabelText('Select country')); // Open dropdown
    expect(screen.getByText('Auto-detected: Detected Country')).toBeInTheDocument();
  });

  it('shows check icon next to the currently selected locale in dropdown', () => {
    (useLocale as vitest.Mock).mockReturnValue({
      locale: mockCountryConfig.CA, // Canada is selected
      changeLocale: mockChangeLocale,
      locationData: null,
      isDetecting: false,
    });
    render(<LocaleSelector />);
    fireEvent.click(screen.getByLabelText('Select country')); // Open dropdown
    
    const canadaOption = screen.getByText('Canada').closest('button')!;
    expect(canadaOption).toBeInTheDocument();
    expect(canadaOption).toContainElement(screen.getByTestId('check-icon')); // Check icon should be next to Canada
  });

  it('has correct button styling for selected option', () => {
    (useLocale as vitest.Mock).mockReturnValue({
      locale: mockCountryConfig.GB, // UK is selected
      changeLocale: mockChangeLocale,
      locationData: null,
      isDetecting: false,
    });
    render(<LocaleSelector />);
    fireEvent.click(screen.getByLabelText('Select country')); // Open dropdown

    const ukOption = screen.getByText('United Kingdom').closest('button')!;
    expect(ukOption).toHaveClass('bg-surface'); // Selected option should have 'bg-surface' class
  });
});
