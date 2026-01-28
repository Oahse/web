// frontend/src/components/ui/ThemeToggle.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vitest } from 'vitest';
import { ThemeToggle } from './ThemeToggle';
import { useTheme } from '../../store/ThemeContext'; // Import the actual useTheme hook

// Mock the useTheme hook
vitest.mock('../../contexts/ThemeContext', () => ({
  useTheme: vitest.fn(),
}));

describe('ThemeToggle Component', () => {
  const mockSetTheme = vitest.fn();

  beforeEach(() => {
    // Reset the mock before each test
    vitest.clearAllMocks();
  });

  // Test 'buttons' variant (default)
  describe('buttons variant (default)', () => {
    it('renders three buttons for light, dark, and system themes', () => {
      (useTheme as vitest.Mock).mockReturnValue({ theme: 'light', setTheme: mockSetTheme });
      render(<ThemeToggle />);
      expect(screen.getByLabelText(/switch to light theme/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/switch to dark theme/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/switch to system theme/i)).toBeInTheDocument();
    });

    it('calls setTheme with correct value when a theme button is clicked', () => {
      (useTheme as vitest.Mock).mockReturnValue({ theme: 'light', setTheme: mockSetTheme });
      render(<ThemeToggle />);

      fireEvent.click(screen.getByLabelText(/switch to dark theme/i));
      expect(mockSetTheme).toHaveBeenCalledWith('dark');

      fireEvent.click(screen.getByLabelText(/switch to system theme/i));
      expect(mockSetTheme).toHaveBeenCalledWith('system');

      fireEvent.click(screen.getByLabelText(/switch to light theme/i));
      expect(mockSetTheme).toHaveBeenCalledWith('light');
    });

    it('displays labels when showLabels is true', () => {
      (useTheme as vitest.Mock).mockReturnValue({ theme: 'light', setTheme: mockSetTheme });
      render(<ThemeToggle showLabels />);
      expect(screen.getByText(/light/i)).toBeInTheDocument();
      expect(screen.getByText(/dark/i)).toBeInTheDocument();
      expect(screen.getByText(/system/i)).toBeInTheDocument();
    });

    it('does not display labels when showLabels is false', () => {
      (useTheme as vitest.Mock).mockReturnValue({ theme: 'light', setTheme: mockSetTheme });
      render(<ThemeToggle showLabels={false} />);
      expect(screen.queryByText(/light/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/dark/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/system/i)).not.toBeInTheDocument();
    });
  });

  // Test 'dropdown' variant
  describe('dropdown variant', () => {
    it('renders a select element with theme options', () => {
      (useTheme as vitest.Mock).mockReturnValue({ theme: 'light', setTheme: mockSetTheme });
      render(<ThemeToggle variant="dropdown" />);
      const selectElement = screen.getByRole('combobox');
      expect(selectElement).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /light/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /dark/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /system/i })).toBeInTheDocument();
    });

    it('calls setTheme with new value when dropdown selection changes', () => {
      (useTheme as vitest.Mock).mockReturnValue({ theme: 'light', setTheme: mockSetTheme });
      render(<ThemeToggle variant="dropdown" />);
      const selectElement = screen.getByRole('combobox');

      fireEvent.change(selectElement, { target: { value: 'dark' } });
      expect(mockSetTheme).toHaveBeenCalledWith('dark');
    });
  });

  // Test 'switch' variant
  describe('switch variant', () => {
    it('renders a single button to switch themes', () => {
      (useTheme as vitest.Mock).mockReturnValue({ theme: 'light', setTheme: mockSetTheme });
      render(<ThemeToggle variant="switch" />);
      expect(screen.getByRole('button', { name: /switch to dark theme/i })).toBeInTheDocument();
    });

    it('cycles through themes when the switch button is clicked', () => {
      (useTheme as vitest.Mock)
        .mockReturnValueOnce({ theme: 'light', setTheme: mockSetTheme })
        .mockReturnValueOnce({ theme: 'dark', setTheme: mockSetTheme })
        .mockReturnValueOnce({ theme: 'system', setTheme: mockSetTheme });

      const { rerender } = render(<ThemeToggle variant="switch" />);

      // Initial theme is light, click to switch to dark
      fireEvent.click(screen.getByRole('button', { name: /switch to dark theme/i }));
      expect(mockSetTheme).toHaveBeenCalledWith('dark');

      // Re-render with new theme context to simulate theme change
      (useTheme as vitest.Mock).mockReturnValue({ theme: 'dark', setTheme: mockSetTheme });
      rerender(<ThemeToggle variant="switch" />);
      fireEvent.click(screen.getByRole('button', { name: /switch to system theme/i }));
      expect(mockSetTheme).toHaveBeenCalledWith('system');

      (useTheme as vitest.Mock).mockReturnValue({ theme: 'system', setTheme: mockSetTheme });
      rerender(<ThemeToggle variant="switch" />);
      fireEvent.click(screen.getByRole('button', { name: /switch to light theme/i }));
      expect(mockSetTheme).toHaveBeenCalledWith('light');
    });

    it('displays labels when showLabels is true', () => {
      (useTheme as vitest.Mock).mockReturnValue({ theme: 'light', setTheme: mockSetTheme });
      render(<ThemeToggle variant="switch" showLabels />);
      expect(screen.getByText(/light/i)).toBeInTheDocument();
    });
  });
});
