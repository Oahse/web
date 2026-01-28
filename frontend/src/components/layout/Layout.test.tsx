// frontend/src/components/layout/Layout.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vitest, beforeEach, afterEach } from 'vitest';
import { Layout, AdminLayout, AuthLayout, MinimalLayout } from './Layout';
import { Header } from './Header';
import { Footer } from './Footer';
import { MobileSearch } from './MobileSearch';
import { MobileCategories } from './MobileCategories';
import { useTheme } from '../../store/ThemeContext';

// --- Mock external dependencies ---
vitest.mock('./Header', () => ({
  Header: vitest.fn((props) => (
    <div data-testid="mock-header" onClick={props.onSearchClick}>
      Mock Header {props.isScrolled ? '(Scrolled)' : ''}
      <button onClick={props.onSearchClick} data-testid="header-search-btn"></button>
      <button onClick={props.onCategoriesClick} data-testid="header-categories-btn"></button>
    </div>
  )),
}));
vitest.mock('./Footer', () => ({
  Footer: vitest.fn(() => <div data-testid="mock-footer">Mock Footer</div>),
}));
vitest.mock('./MobileSearch', () => ({
  MobileSearch: vitest.fn((props) => (
    props.isOpen ? <div data-testid="mock-mobile-search"><button onClick={props.onClose}>Close Search</button></div> : null
  )),
}));
vitest.mock('./MobileCategories', () => ({
  MobileCategories: vitest.fn((props) => (
    props.isOpen ? <div data-testid="mock-mobile-categories"><button onClick={props.onClose}>Close Categories</button></div> : null
  )),
}));
vitest.mock('../../contexts/ThemeContext', () => ({
  useTheme: vitest.fn(),
}));

const mockUseTheme = useTheme as vitest.Mock;
const mockHeader = Header as vitest.Mock;
const mockFooter = Footer as vitest.Mock;
const mockMobileSearch = MobileSearch as vitest.Mock;
const mockMobileCategories = MobileCategories as vitest.Mock;

describe('Layout Component', () => {
  beforeEach(() => {
    vitest.clearAllMocks();
    mockUseTheme.mockReturnValue({}); // Default mock return
    // Default to desktop view to avoid mobile menu rendering issues initially
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 1024 });
    window.dispatchEvent(new Event('resize'));
    // Restore body overflow after each test
    document.body.style.overflow = 'unset';
  });

  afterEach(() => {
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 1024 });
    window.dispatchEvent(new Event('resize'));
  });

  it('renders Header, Footer, and children by default', () => {
    render(<Layout><div data-testid="child-content">App Content</div></Layout>);
    expect(screen.getByTestId('mock-header')).toBeInTheDocument();
    expect(screen.getByTestId('mock-footer')).toBeInTheDocument();
    expect(screen.getByTestId('child-content')).toBeInTheDocument();
  });

  it('does not render Header when showHeader is false', () => {
    render(<Layout showHeader={false}><div data-testid="child-content">App Content</div></Layout>);
    expect(screen.queryByTestId('mock-header')).not.toBeInTheDocument();
  });

  it('does not render Footer when showFooter is false', () => {
    render(<Layout showFooter={false}><div data-testid="child-content">App Content</div></Layout>);
    expect(screen.queryByTestId('mock-footer')).not.toBeInTheDocument();
  });

  it('opens MobileSearch when Header triggers onSearchClick', async () => {
    // Simulate mobile viewport for MobileSearch to be relevant
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 500 });
    window.dispatchEvent(new Event('resize'));

    render(<Layout />);
    // Simulate the Header calling onSearchClick
    act(() => {
      mockHeader.mock.calls[0][0].onSearchClick({ preventDefault: vitest.fn() });
    });

    await waitFor(() => {
      expect(mockMobileSearch).toHaveBeenCalledWith(expect.objectContaining({ isOpen: true }), {});
      expect(document.body.style.overflow).toBe('hidden');
    });
  });

  it('closes MobileSearch when MobileSearch triggers onClose', async () => {
    // Open search first
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 500 });
    window.dispatchEvent(new Event('resize'));
    const { rerender } = render(<Layout />);
    act(() => {
      mockHeader.mock.calls[0][0].onSearchClick({ preventDefault: vitest.fn() });
    });
    
    // Simulate MobileSearch calling its onClose
    await waitFor(() => {
      act(() => {
        mockMobileSearch.mock.calls[0][0].onClose();
      });
    });

    await waitFor(() => {
      expect(mockMobileSearch).toHaveBeenCalledWith(expect.objectContaining({ isOpen: false }), {});
      expect(document.body.style.overflow).toBe('unset');
    });
  });

  it('closes mobile menus on Escape key press', async () => {
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 500 });
    window.dispatchEvent(new Event('resize'));
    render(<Layout />);
    act(() => {
      mockHeader.mock.calls[0][0].onCategoriesClick({ preventDefault: vitest.fn() });
    });
    await waitFor(() => {
      expect(mockMobileCategories).toHaveBeenCalledWith(expect.objectContaining({ isOpen: true }), {});
    });

    fireEvent.keyDown(document, { key: 'Escape' });

    await waitFor(() => {
      expect(mockMobileCategories).toHaveBeenCalledWith(expect.objectContaining({ isOpen: false }), {});
      expect(document.body.style.overflow).toBe('unset');
    });
  });

  it('closes mobile menus on backdrop click', async () => {
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 500 });
    window.dispatchEvent(new Event('resize'));
    render(<Layout />);
    act(() => {
      mockHeader.mock.calls[0][0].onSearchClick({ preventDefault: vitest.fn() });
    });
    await waitFor(() => {
      expect(mockMobileSearch).toHaveBeenCalledWith(expect.objectContaining({ isOpen: true }), {});
    });

    // Simulate click on the backdrop
    const backdrop = screen.getByTestId('mock-mobile-search').closest('div')?.nextElementSibling;
    if (backdrop) {
      fireEvent.click(backdrop);
    } else {
      fireEvent.click(document.body); // Fallback if backdrop is hard to select
    }

    await waitFor(() => {
      expect(mockMobileSearch).toHaveBeenCalledWith(expect.objectContaining({ isOpen: false }), {});
      expect(document.body.style.overflow).toBe('unset');
    });
  });
  
  it('passes isScrolled prop to Header based on scroll position', () => {
    render(<Layout />);
    
    // Initial state: not scrolled
    expect(mockHeader).toHaveBeenCalledWith(expect.objectContaining({ isScrolled: false }), {});

    // Simulate scrolling down
    Object.defineProperty(window, 'scrollY', { value: 50, writable: true });
    fireEvent.scroll(window);

    expect(mockHeader).toHaveBeenCalledWith(expect.objectContaining({ isScrolled: true }), {});
    
    // Simulate scrolling back up
    Object.defineProperty(window, 'scrollY', { value: 5, writable: true });
    fireEvent.scroll(window);
    
    expect(mockHeader).toHaveBeenCalledWith(expect.objectContaining({ isScrolled: false }), {});
  });

  // --- Test Layout Variants ---
  it('AdminLayout hides header and footer and applies custom class', () => {
    render(<AdminLayout><div data-testid="child-content">Admin Content</div></AdminLayout>);
    expect(mockHeader).toHaveBeenCalledWith(expect.objectContaining({ showHeader: false }), {});
    expect(mockFooter).toHaveBeenCalledWith(expect.objectContaining({ showFooter: false }), {});
    expect(screen.getByTestId('child-content').closest('div')).toHaveClass('bg-surface-elevated');
  });

  it('AuthLayout hides header and footer and wraps children', () => {
    render(<AuthLayout><div data-testid="child-content">Auth Content</div></AuthLayout>);
    expect(mockHeader).toHaveBeenCalledWith(expect.objectContaining({ showHeader: false }), {});
    expect(mockFooter).toHaveBeenCalledWith(expect.objectContaining({ showFooter: false }), {});
    expect(screen.getByTestId('child-content').closest('div')).toHaveClass('w-full', 'max-w-md'); // Specific wrapper
  });

  it('MinimalLayout hides footer and passes headerProps', () => {
    render(<MinimalLayout><div data-testid="child-content">Minimal Content</div></MinimalLayout>);
    expect(mockFooter).toHaveBeenCalledWith(expect.objectContaining({ showFooter: false }), {});
    expect(mockHeader).toHaveBeenCalledWith(expect.objectContaining({ minimal: true }), {});
  });
});
