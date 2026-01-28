// frontend/src/components/ui/CountrySelector.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vitest } from 'vitest';
import { CountrySelector } from './CountrySelector';
import * as countriesLib from '../../utils/countries';

// Mock the countries data and utility functions
const mockCountries = [
  { code: 'US', name: 'United States', flag: '🇺🇸', currency: 'USD', languages: ['en'], continent: 'North America', phoneCode: '+1', popular: true },
  { code: 'CA', name: 'Canada', flag: '🇨🇦', currency: 'CAD', languages: ['en', 'fr'], continent: 'North America', phoneCode: '+1', popular: true },
  { code: 'GB', name: 'United Kingdom', flag: '🇬🇧', currency: 'GBP', languages: ['en'], continent: 'Europe', phoneCode: '+44', popular: true },
  { code: 'FR', name: 'France', flag: '🇫🇷', currency: 'EUR', languages: ['fr'], continent: 'Europe', phoneCode: '+33', popular: false },
  { code: 'JP', name: 'Japan', flag: '🇯🇵', currency: 'JPY', languages: ['ja'], continent: 'Asia', phoneCode: '+81', popular: false },
];

vitest.mock('../../lib/countries', () => ({
  countries: mockCountries,
  getPopularCountries: vitest.fn(() => mockCountries.filter(c => c.popular)),
  searchCountries: vitest.fn((query) =>
    mockCountries.filter(c => c.name.toLowerCase().includes(query.toLowerCase()))
  ),
  continents: ['North America', 'Europe', 'Asia'],
  getCurrencySymbol: vitest.fn((currencyCode) => {
    if (currencyCode === 'USD') return '$';
    if (currencyCode === 'CAD') return '$';
    if (currencyCode === 'GBP') return '£';
    if (currencyCode === 'EUR') return '€';
    if (currencyCode === 'JPY') return '¥';
    return '';
  }),
}));

describe('CountrySelector Component', () => {
  const mockOnChange = vitest.fn();

  beforeEach(() => {
    vitest.clearAllMocks();
    // Reset mock implementation for searchCountries and getPopularCountries
    (countriesLib.searchCountries as vitest.Mock).mockImplementation((query) =>
      mockCountries.filter(c => c.name.toLowerCase().includes(query.toLowerCase()))
    );
    (countriesLib.getPopularCountries as vitest.Mock).mockImplementation(() =>
      mockCountries.filter(c => c.popular)
    );
  });

  it('renders with placeholder when no country is selected', () => {
    render(<CountrySelector value="" onChange={mockOnChange} placeholder="Select a country" />);
    expect(screen.getByText('Select a country')).toBeInTheDocument();
    expect(screen.queryByRole('img', { name: /flag/i })).not.toBeInTheDocument();
  });

  it('renders selected country with flag', () => {
    render(<CountrySelector value="US" onChange={mockOnChange} showFlag />);
    expect(screen.getByText('United States')).toBeInTheDocument();
    expect(screen.getByLabelText('United States flag')).toBeInTheDocument();
  });

  it('opens dropdown on click', () => {
    render(<CountrySelector value="" onChange={mockOnChange} />);
    fireEvent.click(screen.getByRole('button', { name: /select country/i }));
    expect(screen.getByPlaceholderText('Search countries...')).toBeInTheDocument();
    expect(screen.getByText('United States')).toBeInTheDocument(); // First country in mock
  });

  it('closes dropdown on clicking outside', () => {
    render(<CountrySelector value="" onChange={mockOnChange} />);
    fireEvent.click(screen.getByRole('button', { name: /select country/i })); // Open
    expect(screen.getByPlaceholderText('Search countries...')).toBeInTheDocument();
    fireEvent.mouseDown(document.body); // Click outside
    expect(screen.queryByPlaceholderText('Search countries...')).not.toBeInTheDocument();
  });

  it('selects a country from the dropdown', () => {
    render(<CountrySelector value="" onChange={mockOnChange} />);
    fireEvent.click(screen.getByRole('button', { name: /select country/i })); // Open
    fireEvent.click(screen.getByRole('button', { name: /canada/i })); // Select Canada
    expect(mockOnChange).toHaveBeenCalledWith(mockCountries[1]);
    expect(screen.queryByPlaceholderText('Search countries...')).not.toBeInTheDocument(); // Dropdown closes
  });

  it('filters countries based on search query', async () => {
    render(<CountrySelector value="" onChange={mockOnChange} searchable />);
    fireEvent.click(screen.getByRole('button', { name: /select country/i })); // Open

    const searchInput = screen.getByPlaceholderText('Search countries...');
    fireEvent.change(searchInput, { target: { value: 'france' } });

    await waitFor(() => {
      expect(countriesLib.searchCountries).toHaveBeenCalledWith('france');
      expect(screen.getByText('France')).toBeInTheDocument();
      expect(screen.queryByText('United States')).not.toBeInTheDocument();
    });
  });

  it('displays "No countries found" when search yields no results', async () => {
    (countriesLib.searchCountries as vitest.Mock).mockReturnValue([]);
    render(<CountrySelector value="" onChange={mockOnChange} searchable />);
    fireEvent.click(screen.getByRole('button', { name: /select country/i })); // Open

    const searchInput = screen.getByPlaceholderText('Search countries...');
    fireEvent.change(searchInput, { target: { value: 'xyz' } });

    await waitFor(() => {
      expect(screen.getByText('No countries found')).toBeInTheDocument();
      expect(screen.getByText('Try a different search term')).toBeInTheDocument();
    });
  });

  it('displays country code when showPhoneCode is true', () => {
    render(<CountrySelector value="US" onChange={mockOnChange} showPhoneCode />);
    expect(screen.getByText('+1')).toBeInTheDocument();
  });

  it('displays currency when showCurrency is true', () => {
    render(<CountrySelector value="US" onChange={mockOnChange} showCurrency />);
    expect(screen.getByText('$ USD')).toBeInTheDocument();
  });

  it('groups countries by continent', () => {
    render(<CountrySelector value="" onChange={mockOnChange} groupByContinent />);
    fireEvent.click(screen.getByRole('button', { name: /select country/i })); // Open

    expect(screen.getByText('Popular')).toBeInTheDocument();
    expect(screen.getByText('North America')).toBeInTheDocument();
    expect(screen.getByText('Europe')).toBeInTheDocument();
    expect(screen.getByText('Asia')).toBeInTheDocument();
  });

  it('clears selection when clearable is true and clear button is clicked', () => {
    render(<CountrySelector value="US" onChange={mockOnChange} clearable />);
    expect(screen.getByLabelText('Clear selection')).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('Clear selection'));
    expect(mockOnChange).toHaveBeenCalledWith({ code: '', name: '', flag: '', currency: '', languages: [], continent: '', phoneCode: '' });
  });

  it('navigates options with arrow keys and selects with Enter', () => {
    render(<CountrySelector value="" onChange={mockOnChange} />);
    fireEvent.click(screen.getByRole('button', { name: /select country/i })); // Open

    fireEvent.keyDown(screen.getByPlaceholderText('Search countries...'), { key: 'ArrowDown' }); // US
    fireEvent.keyDown(screen.getByPlaceholderText('Search countries...'), { key: 'ArrowDown' }); // CA
    fireEvent.keyDown(screen.getByPlaceholderText('Search countries...'), { key: 'Enter' });

    expect(mockOnChange).toHaveBeenCalledWith(mockCountries[1]); // Canada
  });
});
