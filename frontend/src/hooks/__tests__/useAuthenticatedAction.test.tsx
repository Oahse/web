import { renderHook } from '@testing-library/react';
import { useAuthenticatedAction } from '../useAuth';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock the dependencies
vi.mock('../../contexts/AuthContext');
vi.mock('react-router-dom');

const mockUseAuth = vi.mocked(useAuth);
const mockUseNavigate = vi.mocked(useNavigate);
const mockUseLocation = vi.mocked(useLocation);

describe('useAuthenticatedAction', () => {
  const mockNavigate = vi.fn();
  const mockSetIntendedDestination = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseNavigate.mockReturnValue(mockNavigate);
    mockUseLocation.mockReturnValue({
      pathname: '/product/123',
      search: '',
      hash: '',
      state: null,
      key: 'test'
    });
  });

  it('should execute action when user is authenticated', async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      setIntendedDestination: mockSetIntendedDestination,
    } as any);

    const { result } = renderHook(() => useAuthenticatedAction());
    const mockAction = vi.fn().mockResolvedValue(true);

    const success = await result.current.executeWithAuth(mockAction, 'cart');

    expect(mockAction).toHaveBeenCalled();
    expect(success).toBe(true);
    expect(mockNavigate).not.toHaveBeenCalled();
    expect(mockSetIntendedDestination).not.toHaveBeenCalled();
  });

  it('should redirect to login when user is not authenticated', async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      setIntendedDestination: mockSetIntendedDestination,
    } as any);

    const { result } = renderHook(() => useAuthenticatedAction());
    const mockAction = vi.fn().mockResolvedValue(true);

    const success = await result.current.executeWithAuth(mockAction, 'cart');

    expect(mockAction).not.toHaveBeenCalled();
    expect(success).toBe(false);
    expect(mockSetIntendedDestination).toHaveBeenCalledWith('/product/123', 'cart');
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('should redirect to login on authentication error', async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      setIntendedDestination: mockSetIntendedDestination,
    } as any);

    const { result } = renderHook(() => useAuthenticatedAction());
    const mockAction = vi.fn().mockRejectedValue(new Error('User must be authenticated'));

    const success = await result.current.executeWithAuth(mockAction, 'wishlist');

    expect(mockAction).toHaveBeenCalled();
    expect(success).toBe(false);
    expect(mockSetIntendedDestination).toHaveBeenCalledWith('/product/123', 'wishlist');
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('should rethrow non-authentication errors', async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      setIntendedDestination: mockSetIntendedDestination,
    } as any);

    const { result } = renderHook(() => useAuthenticatedAction());
    const mockAction = vi.fn().mockRejectedValue(new Error('Network error'));

    await expect(result.current.executeWithAuth(mockAction, 'cart')).rejects.toThrow('Network error');

    expect(mockAction).toHaveBeenCalled();
    expect(mockNavigate).not.toHaveBeenCalled();
    expect(mockSetIntendedDestination).not.toHaveBeenCalled();
  });
});