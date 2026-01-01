import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SessionManager } from '../SessionManager';
import { AuthContext } from '../../../contexts/AuthContext';
import { getSessionConfig } from '../../../config/session';

// Mock the session config
vi.mock('../../../config/session', () => ({
  getSessionConfig: vi.fn(() => ({
    warningThreshold: 5 * 60 * 1000, // 5 minutes
    criticalThreshold: 2 * 60 * 1000, // 2 minutes
    sessionStatusCheckInterval: 1000,
  })),
  formatTimeRemaining: vi.fn((ms) => {
    const minutes = Math.floor(ms / (1000 * 60));
    const seconds = Math.floor((ms % (1000 * 60)) / 1000);
    return minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
  }),
  getSessionStatus: vi.fn((timeRemaining, config) => {
    if (timeRemaining <= 0) return 'expired';
    if (timeRemaining <= config.criticalThreshold) return 'critical';
    if (timeRemaining <= config.warningThreshold) return 'warning';
    return 'active';
  }),
}));

const mockAuthContext = {
  isAuthenticated: true,
  getSessionInfo: vi.fn(),
  extendSession: vi.fn(),
  user: { id: '1', email: 'test@example.com' },
  isLoading: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  verifyEmail: vi.fn(),
  isAdmin: false,
  isSupplier: false,
  isCustomer: true,
  redirectPath: null,
  setRedirectPath: vi.fn(),
  intendedDestination: null,
  setIntendedDestination: vi.fn(),
  updateUserPreferences: vi.fn(),
  updateUser: vi.fn(),
  sessionWarningShown: false,
};

const renderWithAuth = (component: React.ReactElement, authValue = mockAuthContext) => {
  return render(
    <AuthContext.Provider value={authValue}>
      {component}
    </AuthContext.Provider>
  );
};

describe('SessionManager', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should not render when user is not authenticated', () => {
    const unauthenticatedContext = {
      ...mockAuthContext,
      isAuthenticated: false,
    };

    renderWithAuth(<SessionManager />, unauthenticatedContext);
    
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('should not render when session info is null', () => {
    const contextWithNullSession = {
      ...mockAuthContext,
      getSessionInfo: vi.fn(() => null),
    };

    renderWithAuth(<SessionManager />, contextWithNullSession);
    
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('should display session time remaining in compact mode', () => {
    mockAuthContext.getSessionInfo.mockReturnValue({
      timeUntilExpiry: 10 * 60 * 1000, // 10 minutes
      rememberMe: false,
      lastActivity: Date.now(),
      isValid: true,
    });

    renderWithAuth(<SessionManager />);
    
    expect(screen.getByText('10m 0s')).toBeInTheDocument();
  });

  it('should show extend button when session is expiring soon', () => {
    mockAuthContext.getSessionInfo.mockReturnValue({
      timeUntilExpiry: 3 * 60 * 1000, // 3 minutes (within warning threshold)
      rememberMe: false,
      lastActivity: Date.now(),
      isValid: true,
    });

    renderWithAuth(<SessionManager />);
    
    expect(screen.getByText('Extend')).toBeInTheDocument();
  });

  it('should call extendSession when extend button is clicked', async () => {
    mockAuthContext.getSessionInfo.mockReturnValue({
      timeUntilExpiry: 3 * 60 * 1000, // 3 minutes
      rememberMe: false,
      lastActivity: Date.now(),
      isValid: true,
    });

    renderWithAuth(<SessionManager />);
    
    const extendButton = screen.getByText('Extend');
    fireEvent.click(extendButton);
    
    expect(mockAuthContext.extendSession).toHaveBeenCalledTimes(1);
  });

  it('should display detailed session info when showDetails is true', () => {
    const lastActivity = Date.now() - 5000; // 5 seconds ago
    mockAuthContext.getSessionInfo.mockReturnValue({
      timeUntilExpiry: 15 * 60 * 1000, // 15 minutes
      rememberMe: true,
      lastActivity,
      isValid: true,
    });

    renderWithAuth(<SessionManager showDetails={true} />);
    
    expect(screen.getByText('Session Status')).toBeInTheDocument();
    expect(screen.getByText('Time Remaining:')).toBeInTheDocument();
    expect(screen.getByText('Remember Me:')).toBeInTheDocument();
    expect(screen.getByText('Yes (30 days)')).toBeInTheDocument();
    expect(screen.getByText('Extend Session')).toBeInTheDocument();
  });

  it('should show "No (30 min)" when remember me is false', () => {
    mockAuthContext.getSessionInfo.mockReturnValue({
      timeUntilExpiry: 15 * 60 * 1000,
      rememberMe: false,
      lastActivity: Date.now(),
      isValid: true,
    });

    renderWithAuth(<SessionManager showDetails={true} />);
    
    expect(screen.getByText('No (30 min)')).toBeInTheDocument();
  });

  it('should update time display every second', async () => {
    let timeRemaining = 65000; // 1 minute 5 seconds
    
    mockAuthContext.getSessionInfo.mockImplementation(() => ({
      timeUntilExpiry: timeRemaining,
      rememberMe: false,
      lastActivity: Date.now(),
      isValid: true,
    }));

    renderWithAuth(<SessionManager />);
    
    // Initial display
    expect(screen.getByText('1m 5s')).toBeInTheDocument();
    
    // Simulate time passing
    timeRemaining = 64000; // 1 minute 4 seconds
    vi.advanceTimersByTime(1000);
    
    await waitFor(() => {
      expect(screen.getByText('1m 4s')).toBeInTheDocument();
    });
  });

  it('should show critical styling when time is very low', () => {
    mockAuthContext.getSessionInfo.mockReturnValue({
      timeUntilExpiry: 60000, // 1 minute (critical)
      rememberMe: false,
      lastActivity: Date.now(),
      isValid: true,
    });

    renderWithAuth(<SessionManager />);
    
    const timeElement = screen.getByText('1m 0s');
    expect(timeElement).toHaveClass('text-red-600');
  });

  it('should show warning styling when time is low but not critical', () => {
    mockAuthContext.getSessionInfo.mockReturnValue({
      timeUntilExpiry: 4 * 60 * 1000, // 4 minutes (warning)
      rememberMe: false,
      lastActivity: Date.now(),
      isValid: true,
    });

    renderWithAuth(<SessionManager />);
    
    const timeElement = screen.getByText('4m 0s');
    expect(timeElement).toHaveClass('text-orange-600');
  });

  it('should show normal styling when time is sufficient', () => {
    mockAuthContext.getSessionInfo.mockReturnValue({
      timeUntilExpiry: 10 * 60 * 1000, // 10 minutes (normal)
      rememberMe: false,
      lastActivity: Date.now(),
      isValid: true,
    });

    renderWithAuth(<SessionManager />);
    
    const timeElement = screen.getByText('10m 0s');
    expect(timeElement).toHaveClass('text-gray-600');
  });

  it('should display "Expired" when session has expired', () => {
    mockAuthContext.getSessionInfo.mockReturnValue({
      timeUntilExpiry: 0,
      rememberMe: false,
      lastActivity: Date.now() - 1000000,
      isValid: false,
    });

    renderWithAuth(<SessionManager />);
    
    expect(screen.getByText('Expired')).toBeInTheDocument();
  });
});