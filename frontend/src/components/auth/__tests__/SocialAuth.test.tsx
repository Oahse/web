import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { SocialAuth } from '../SocialAuth';
import { AuthContext } from '../../../contexts/AuthContext';
import { BrowserRouter } from 'react-router-dom';

// Mock the Google OAuth provider
vi.mock('@react-oauth/google', () => ({
  GoogleLogin: vi.fn(({ onSuccess, onError }) => (
    <button
      data-testid="google-login"
      onClick={() => {
        const mockCredentialResponse = {
          credential: 'mock-jwt-token',
          select_by: 'btn',
        };
        onSuccess(mockCredentialResponse);
      }}
    >
      Sign in with Google
    </button>
  )),
}));

// Mock the auth API
vi.mock('../../../apis/auth', () => ({
  default: {
    googleLogin: vi.fn(),
    facebookLogin: vi.fn(),
  },
}));

describe('SocialAuth Component', () => {
  const mockAuthContext = {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    updateUser: vi.fn(),
  };

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <BrowserRouter>
        <AuthContext.Provider value={mockAuthContext}>
          {component}
        </AuthContext.Provider>
      </BrowserRouter>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders social login buttons', () => {
    renderWithProviders(<SocialAuth />);

    expect(screen.getByTestId('google-login')).toBeInTheDocument();
    expect(screen.getByText('Sign in with Google')).toBeInTheDocument();
  });

  it('handles Google login success', async () => {
    const { AuthAPI } = await import('../../../apis/auth');
    (AuthAPI.googleLogin as any).mockResolvedValue({
      success: true,
      data: {
        user: { id: '1', email: 'test@example.com' },
        access_token: 'mock-token',
      },
    });

    renderWithProviders(<SocialAuth />);

    const googleButton = screen.getByTestId('google-login');
    fireEvent.click(googleButton);

    await waitFor(() => {
      expect(AuthAPI.googleLogin).toHaveBeenCalledWith('mock-jwt-token');
    });
  });

  it('handles Google login error', async () => {
    const { AuthAPI } = await import('../../../apis/auth');
    (AuthAPI.googleLogin as any).mockRejectedValue(new Error('Login failed'));

    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    renderWithProviders(<SocialAuth />);

    const googleButton = screen.getByTestId('google-login');
    fireEvent.click(googleButton);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith('Google login error:', expect.any(Error));
    });

    consoleErrorSpy.mockRestore();
  });

  it('shows loading state during authentication', async () => {
    const { AuthAPI } = await import('../../../apis/auth');
    (AuthAPI.googleLogin as any).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    renderWithProviders(<SocialAuth />);

    const googleButton = screen.getByTestId('google-login');
    fireEvent.click(googleButton);

    // Should show loading state
    expect(screen.getByTestId('google-login')).toBeDisabled();
  });

  it('displays error message on authentication failure', async () => {
    const { AuthAPI } = await import('../../../apis/auth');
    (AuthAPI.googleLogin as any).mockRejectedValue({
      message: 'Authentication failed',
    });

    renderWithProviders(<SocialAuth />);

    const googleButton = screen.getByTestId('google-login');
    fireEvent.click(googleButton);

    await waitFor(() => {
      expect(screen.getByText('Authentication failed')).toBeInTheDocument();
    });
  });

  it('redirects after successful login', async () => {
    const { AuthAPI } = await import('../../../apis/auth');
    (AuthAPI.googleLogin as any).mockResolvedValue({
      success: true,
      data: {
        user: { id: '1', email: 'test@example.com' },
        access_token: 'mock-token',
      },
    });

    const mockNavigate = vi.fn();
    vi.mock('react-router-dom', async () => {
      const actual = await vi.importActual('react-router-dom');
      return {
        ...actual,
        useNavigate: () => mockNavigate,
      };
    });

    renderWithProviders(<SocialAuth />);

    const googleButton = screen.getByTestId('google-login');
    fireEvent.click(googleButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });
  });
});