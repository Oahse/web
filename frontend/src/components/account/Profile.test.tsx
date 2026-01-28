// frontend/src/components/account/Profile.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vitest, beforeEach } from 'vitest';
import { Profile } from './Profile';
import { useAuth } from '../../store/AuthContext';
import { AuthAPI } from '../../apis';
import { toast } from 'react-hot-toast';

// --- Mock external dependencies ---
vitest.mock('../../contexts/AuthContext', () => ({
  useAuth: vitest.fn(),
}));

vitest.mock('../../apis', () => ({
  AuthAPI: {
    updateProfile: vitest.fn(),
  },
}));

vitest.mock('react-hot-toast', () => ({
  toast: {
    success: vitest.fn(),
    error: vitest.fn(),
  },
}));

// Mock lucide-react icons
vitest.mock('lucide-react', () => ({
  UserIcon: vitest.fn(() => <svg data-testid="icon-user" />),
  MailIcon: vitest.fn(() => <svg data-testid="icon-mail" />),
  PhoneIcon: vitest.fn(() => <svg data-testid="icon-phone" />),
  MapPinIcon: vitest.fn(() => <svg data-testid="icon-map-pin" />),
  CalendarIcon: vitest.fn(() => <svg data-testid="icon-calendar" />),
  GlobeIcon: vitest.fn(() => <svg data-testid="icon-globe" />),
  SaveIcon: vitest.fn(() => <svg data-testid="icon-save" />),
}));

describe('Profile Component', () => {
  const mockUser = {
    firstname: 'John',
    lastname: 'Doe',
    full_name: 'John Doe',
    email: 'john.doe@example.com',
    phone: '+1234567890',
    age: 30,
    gender: 'Male',
    country: 'United States',
    language: 'en',
    timezone: 'America/New_York',
    verified: true,
    role: 'customer',
    active: true,
    created_at: new Date('2023-01-01').toISOString(),
  };

  const mockUpdateUser = vitest.fn();
  const mockUseAuth = useAuth as vitest.Mock;
  const mockUpdateProfile = AuthAPI.updateProfile as vitest.Mock;

  beforeEach(() => {
    vitest.clearAllMocks();
    mockUseAuth.mockReturnValue({ user: mockUser, updateUser: mockUpdateUser });
  });

  it('renders "Loading profile..." when user is null', () => {
    mockUseAuth.mockReturnValue({ user: null, updateUser: mockUpdateUser });
    render(<Profile />);
    expect(screen.getByText('Loading profile...')).toBeInTheDocument();
  });

  it('renders user profile information in view mode', () => {
    render(<Profile />);
    expect(screen.getByText('My Profile')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john.doe@example.com')).toBeInTheDocument();
    expect(screen.getByText('+1234567890')).toBeInTheDocument();
    expect(screen.getByText('Verified')).toBeInTheDocument();
    expect(screen.getByText('customer')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Edit Profile' })).toBeInTheDocument();
    
    // Check account information
    expect(screen.getByText('Account Status')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Email Verification')).toBeInTheDocument();
    expect(screen.getByText('Verified', { selector: 'span.px-2' })).toBeInTheDocument();
    expect(screen.getByText('Member Since')).toBeInTheDocument();
    expect(screen.getByText(new Date(mockUser.created_at).toLocaleDateString())).toBeInTheDocument();
  });

  it('enters edit mode when "Edit Profile" button is clicked', () => {
    render(<Profile />);
    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));
    expect(screen.getByLabelText('First Name *').closest('div')?.querySelector('input')).not.toBeDisabled();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Save Changes' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Edit Profile' })).not.toBeInTheDocument();
  });

  it('updates form data on input change', () => {
    render(<Profile />);
    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));
    const firstNameInput = screen.getByLabelText('First Name *').closest('div')?.querySelector('input')!;
    fireEvent.change(firstNameInput, { target: { name: 'firstname', value: 'Jane' } });
    expect(firstNameInput).toHaveValue('Jane');
  });

  it('calls AuthAPI.updateProfile and updateUser on successful form submission', async () => {
    mockUpdateProfile.mockResolvedValueOnce({
      ...mockUser,
      firstname: 'Jane',
      full_name: 'Jane Doe',
    });
    render(<Profile />);
    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));
    fireEvent.change(screen.getByLabelText('First Name *').closest('div')?.querySelector('input')!, { target: { name: 'firstname', value: 'Jane' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));

    await waitFor(() => {
      expect(mockUpdateProfile).toHaveBeenCalledWith(expect.objectContaining({ firstname: 'Jane' }));
      expect(mockUpdateUser).toHaveBeenCalledWith(expect.objectContaining({ firstname: 'Jane' }));
      expect(toast.success).toHaveBeenCalledWith('Profile updated successfully');
      expect(screen.queryByRole('button', { name: 'Save Changes' })).not.toBeInTheDocument(); // Exits edit mode
    });
  });

  it('shows error toast on failed form submission', async () => {
    mockUpdateProfile.mockRejectedValueOnce(new Error('Update failed'));
    render(<Profile />);
    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));
    fireEvent.change(screen.getByLabelText('First Name *').closest('div')?.querySelector('input')!, { target: { name: 'firstname', value: 'Jane' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to update profile');
      expect(screen.getByRole('button', { name: 'Save Changes' })).toBeInTheDocument(); // Stays in edit mode
    });
  });

  it('resets form data and exits edit mode on cancel', () => {
    render(<Profile />);
    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));
    fireEvent.change(screen.getByLabelText('First Name *').closest('div')?.querySelector('input')!, { target: { name: 'firstname', value: 'Jane' } });
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    
    expect(screen.getByText('John Doe')).toBeInTheDocument(); // Original name displayed
    expect(screen.queryByRole('button', { name: 'Cancel' })).not.toBeInTheDocument(); // Exits edit mode
  });

  it('disables buttons and shows loading text during form submission', () => {
    mockUpdateProfile.mockImplementationOnce(() => new Promise(() => {})); // Never resolve
    render(<Profile />);
    fireEvent.click(screen.getByRole('button', { name: 'Edit Profile' }));
    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }));
    expect(screen.getByRole('button', { name: 'Saving...' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled();
  });
});
