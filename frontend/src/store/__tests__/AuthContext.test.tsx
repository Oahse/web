import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { AuthProvider, useAuth } from '../AuthContext';
import { BrowserRouter } from 'react-router-dom';

// Mock the APIs
vi.mock('../../apis/auth', () => ({
  default: {
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    refreshToken: vi.fn(),
  },
}));

vi.mock('../../apis/client', () => ({
  TokenManager: {
    getToken: vi.fn(),
    setToken: vi.fn(),
    getRefreshToken: vi.fn(),
    setRefreshToken: vi.fn(),
    getUser: vi.fn(),
    setUser: vi.fn(),
    clearTokens: vi.fn(),
    isAuthenticated: vi.fn(),
  },
}));

// Test component that uses the auth context
const TestComponent = () => {
  const { user, isAuthenticated, isLoading, login, register, logout, updateUser } = useAuth();

  return (
    <div>
      <div data-testid="auth-status">
        {isLoading ? 'Loading' : isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
      </div>
      {user && <div data-testid="user-email">{user.email}</div>}
      <button onClick={() => login('test@example.com', 'password')}>Login</button>
      <button onClick={() => register({
        email: 'test@example.com',
        password: 'password',
        firstname: 'Test',
        lastname: 'User'
      })}>Register</button>
      <button onClick={logout}>Logout</button>
      <button onClick={() => updateUser({ firstname: 'Updated' })}>Update User</button>
    </div>
  );
};

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {component}
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('provides initial unauthenticated state', () => {
    const { TokenManager } = require('../../apis/client');
    TokenManager.isAuthenticated.mockReturnValue(false);
    TokenManager.getUser.mockReturnValue(null);

    renderWithProviders(<TestComponent />);

    expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');
  });

  it('provides authenticated state when user is logged in', async () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      firstname: 'Test',
      lastname: 'User',
      role: 'customer',
    };

    const { TokenManager } = require('../../apis/client');
    TokenManager.isAuthenticated.mockReturnValue(true);
    TokenManager.getUser.mockReturnValue(mockUser);

    renderWithProviders(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
      expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
    });
  });

  it('handles login successfully', async () => {
    const { AuthAPI } = await import('../../apis/auth');
    const { TokenManager } = require('../../apis/client');

    const mockLoginResponse = {
      success: true,
      data: {
        user: {
          id: '1',
          email: 'test@example.com',
          firstname: 'Test',
          lastname: 'User',
          role: 'customer',
        },
        access_token: 'mock-token',
        refresh_token: 'mock-refresh-token',
      },
    };

    (AuthAPI.login as any).mockResolvedValue(mockLoginResponse);
    TokenManager.isAuthenticated.mockReturnValue(false);
    TokenManager.getUser.mockReturnValue(null);

    renderWithProviders(<TestComponent />);

    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(AuthAPI.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password',
      });
      expect(TokenManager.setToken).toHaveBeenCalledWith('mock-token');
      expect(TokenManager.setRefreshToken).toHaveBeenCalledWith('mock-refresh-token');
      expect(TokenManager.setUser).toHaveBeenCalledWith(mockLoginResponse.data.user);
    });
  });

  it('handles login failure', async () => {
    const { AuthAPI } = await import('../../apis/auth');
    const { TokenManager } = require('../../apis/client');

    (AuthAPI.login as any).mockRejectedValue({
      message: 'Invalid credentials',
    });
    TokenManager.isAuthenticated.mockReturnValue(false);
    TokenManager.getUser.mockReturnValue(null);

    renderWithProviders(<TestComponent />);

    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(AuthAPI.login).toHaveBeenCalled();
      // Should remain unauthenticated
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');
    });
  });

  it('handles registration successfully', async () => {
    const { AuthAPI } = await import('../../apis/auth');
    const { TokenManager } = require('../../apis/client');

    const mockRegisterResponse = {
      success: true,
      data: {
        user: {
          id: '1',
          email: 'test@example.com',
          firstname: 'Test',
          lastname: 'User',
          role: 'customer',
        },
        access_token: 'mock-token',
        refresh_token: 'mock-refresh-token',
      },
    };

    (AuthAPI.register as any).mockResolvedValue(mockRegisterResponse);
    TokenManager.isAuthenticated.mockReturnValue(false);
    TokenManager.getUser.mockReturnValue(null);

    renderWithProviders(<TestComponent />);

    const registerButton = screen.getByText('Register');
    fireEvent.click(registerButton);

    await waitFor(() => {
      expect(AuthAPI.register).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password',
        firstname: 'Test',
        lastname: 'User',
      });
      expect(TokenManager.setToken).toHaveBeenCalledWith('mock-token');
      expect(TokenManager.setUser).toHaveBeenCalledWith(mockRegisterResponse.data.user);
    });
  });

  it('handles logout', async () => {
    const { AuthAPI } = await import('../../apis/auth');
    const { TokenManager } = require('../../apis/client');

    const mockUser = {
      id: '1',
      email: 'test@example.com',
      firstname: 'Test',
      lastname: 'User',
      role: 'customer',
    };

    TokenManager.isAuthenticated.mockReturnValue(true);
    TokenManager.getUser.mockReturnValue(mockUser);
    (AuthAPI.logout as any).mockResolvedValue({ success: true });

    renderWithProviders(<TestComponent />);

    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(AuthAPI.logout).toHaveBeenCalled();
      expect(TokenManager.clearTokens).toHaveBeenCalled();
    });
  });

  it('handles user update', async () => {
    const { AuthAPI } = await import('../../apis/auth');
    const { TokenManager } = require('../../apis/client');

    const mockUser = {
      id: '1',
      email: 'test@example.com',
      firstname: 'Test',
      lastname: 'User',
      role: 'customer',
    };

    const updatedUser = {
      ...mockUser,
      firstname: 'Updated',
    };

    TokenManager.isAuthenticated.mockReturnValue(true);
    TokenManager.getUser.mockReturnValue(mockUser);
    (AuthAPI.getCurrentUser as any).mockResolvedValue({
      success: true,
      data: updatedUser,
    });

    renderWithProviders(<TestComponent />);

    const updateButton = screen.getByText('Update User');
    fireEvent.click(updateButton);

    await waitFor(() => {
      expect(TokenManager.setUser).toHaveBeenCalledWith(updatedUser);
    });
  });

  it('shows loading state during authentication operations', async () => {
    const { AuthAPI } = await import('../../apis/auth');
    const { TokenManager } = require('../../apis/client');

    TokenManager.isAuthenticated.mockReturnValue(false);
    TokenManager.getUser.mockReturnValue(null);

    (AuthAPI.login as any).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    renderWithProviders(<TestComponent />);

    const loginButton = screen.getByText('Login');
    fireEvent.click(loginButton);

    expect(screen.getByTestId('auth-status')).toHaveTextContent('Loading');
  });

  it('handles token refresh on app initialization', async () => {
    const { AuthAPI } = await import('../../apis/auth');
    const { TokenManager } = require('../../apis/client');

    const mockUser = {
      id: '1',
      email: 'test@example.com',
      firstname: 'Test',
      lastname: 'User',
      role: 'customer',
    };

    TokenManager.isAuthenticated.mockReturnValue(true);
    TokenManager.getUser.mockReturnValue(mockUser);
    (AuthAPI.getCurrentUser as any).mockResolvedValue({
      success: true,
      data: mockUser,
    });

    renderWithProviders(<TestComponent />);

    await waitFor(() => {
      expect(AuthAPI.getCurrentUser).toHaveBeenCalled();
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Authenticated');
    });
  });

  it('clears auth state when token refresh fails', async () => {
    const { AuthAPI } = await import('../../apis/auth');
    const { TokenManager } = require('../../apis/client');

    TokenManager.isAuthenticated.mockReturnValue(true);
    TokenManager.getUser.mockReturnValue({ id: '1', email: 'test@example.com' });
    (AuthAPI.getCurrentUser as any).mockRejectedValue({
      message: 'Token expired',
    });

    renderWithProviders(<TestComponent />);

    await waitFor(() => {
      expect(TokenManager.clearTokens).toHaveBeenCalled();
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Not Authenticated');
    });
  });
});