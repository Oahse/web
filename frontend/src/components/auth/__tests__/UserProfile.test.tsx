import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { UserProfile } from '../UserProfile';
import { AuthContext } from '../../../contexts/AuthContext';
import { User } from '../../../types';

// Mock the APIs
vi.mock('../../../apis/users', () => ({
  default: {
    updateProfile: vi.fn(),
    uploadAvatar: vi.fn(),
  },
}));

describe('UserProfile Component', () => {
  const mockUser: User = {
    id: '1',
    email: 'test@example.com',
    firstname: 'John',
    lastname: 'Doe',
    phone: '+1234567890',
    role: 'customer',
    is_active: true,
    is_verified: true,
    created_at: '2023-01-01T00:00:00Z',
    profile_image: 'https://example.com/avatar.jpg',
    date_of_birth: '1990-01-01',
    gender: 'male',
    language_preference: 'en',
    currency_preference: 'USD',
  };

  const mockAuthContext = {
    user: mockUser,
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    updateUser: vi.fn(),
  };

  const renderWithAuth = (component: React.ReactElement) => {
    return render(
      <AuthContext.Provider value={mockAuthContext}>
        {component}
      </AuthContext.Provider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders user profile information', () => {
    renderWithAuth(<UserProfile />);

    expect(screen.getByDisplayValue('John')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Doe')).toBeInTheDocument();
    expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
    expect(screen.getByDisplayValue('+1234567890')).toBeInTheDocument();
  });

  it('allows editing profile information', async () => {
    renderWithAuth(<UserProfile />);

    const firstNameInput = screen.getByDisplayValue('John');
    fireEvent.change(firstNameInput, { target: { value: 'Jane' } });

    expect(screen.getByDisplayValue('Jane')).toBeInTheDocument();
  });

  it('saves profile changes', async () => {
    const { UsersAPI } = await import('../../../apis/users');
    (UsersAPI.updateProfile as any).mockResolvedValue({
      success: true,
      data: { ...mockUser, firstname: 'Jane' },
    });

    renderWithAuth(<UserProfile />);

    const firstNameInput = screen.getByDisplayValue('John');
    fireEvent.change(firstNameInput, { target: { value: 'Jane' } });

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(UsersAPI.updateProfile).toHaveBeenCalledWith({
        firstname: 'Jane',
        lastname: 'Doe',
        phone: '+1234567890',
        date_of_birth: '1990-01-01',
        gender: 'male',
        language_preference: 'en',
        currency_preference: 'USD',
      });
    });
  });

  it('handles profile update errors', async () => {
    const { UsersAPI } = await import('../../../apis/users');
    (UsersAPI.updateProfile as any).mockRejectedValue({
      message: 'Update failed',
    });

    renderWithAuth(<UserProfile />);

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Update failed')).toBeInTheDocument();
    });
  });

  it('validates required fields', async () => {
    renderWithAuth(<UserProfile />);

    const firstNameInput = screen.getByDisplayValue('John');
    fireEvent.change(firstNameInput, { target: { value: '' } });

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('First name is required')).toBeInTheDocument();
    });
  });

  it('validates email format', async () => {
    renderWithAuth(<UserProfile />);

    const emailInput = screen.getByDisplayValue('test@example.com');
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
    });
  });

  it('validates phone number format', async () => {
    renderWithAuth(<UserProfile />);

    const phoneInput = screen.getByDisplayValue('+1234567890');
    fireEvent.change(phoneInput, { target: { value: 'invalid-phone' } });

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Please enter a valid phone number')).toBeInTheDocument();
    });
  });

  it('handles avatar upload', async () => {
    const { UsersAPI } = await import('../../../apis/users');
    (UsersAPI.uploadAvatar as any).mockResolvedValue({
      success: true,
      data: { profile_image: 'https://example.com/new-avatar.jpg' },
    });

    renderWithAuth(<UserProfile />);

    const fileInput = screen.getByLabelText('Profile Picture');
    const file = new File(['avatar'], 'avatar.jpg', { type: 'image/jpeg' });

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(UsersAPI.uploadAvatar).toHaveBeenCalledWith(file);
    });
  });

  it('shows loading state during save', async () => {
    const { UsersAPI } = await import('../../../apis/users');
    (UsersAPI.updateProfile as any).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    renderWithAuth(<UserProfile />);

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    expect(screen.getByText('Saving...')).toBeInTheDocument();
    expect(saveButton).toBeDisabled();
  });

  it('resets form on cancel', () => {
    renderWithAuth(<UserProfile />);

    const firstNameInput = screen.getByDisplayValue('John');
    fireEvent.change(firstNameInput, { target: { value: 'Jane' } });

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(screen.getByDisplayValue('John')).toBeInTheDocument();
  });

  it('shows success message after successful update', async () => {
    const { UsersAPI } = await import('../../../apis/users');
    (UsersAPI.updateProfile as any).mockResolvedValue({
      success: true,
      data: mockUser,
    });

    renderWithAuth(<UserProfile />);

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Profile updated successfully')).toBeInTheDocument();
    });
  });
});