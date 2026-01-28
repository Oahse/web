// frontend/src/components/layout/Footer.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vitest, beforeEach } from 'vitest';
import { BrowserRouter, Link } from 'react-router-dom';
import { Footer } from './Footer';
import { SOCIAL_MEDIA_LINKS } from '../../utils/social-media-config';
import {
  MapPinIcon, MailIcon, PhoneIcon, ArrowRightIcon,
  FacebookIcon, TwitterIcon, InstagramIcon, YoutubeIcon, LinkedinIcon
} from 'lucide-react'; // Mocked icons

// Mock react-router-dom Link component
vitest.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    Link: vitest.fn(({ to, children, ...props }) => (
      <a href={to} {...props}>
        {children}
      </a>
    )),
  };
});

// Mock lucide-react icons
vitest.mock('lucide-react', () => ({
  MapPinIcon: vitest.fn(() => <svg data-testid="map-pin-icon" />),
  MailIcon: vitest.fn(() => <svg data-testid="mail-icon" />),
  PhoneIcon: vitest.fn(() => <svg data-testid="phone-icon" />),
  ArrowRightIcon: vitest.fn(() => <svg data-testid="arrow-right-icon" />),
  FacebookIcon: vitest.fn(() => <svg data-testid="facebook-icon" />),
  TwitterIcon: vitest.fn(() => <svg data-testid="twitter-icon" />),
  InstagramIcon: vitest.fn(() => <svg data-testid="instagram-icon" />),
  YoutubeIcon: vitest.fn(() => <svg data-testid="youtube-icon" />),
  LinkedinIcon: vitest.fn(() => <svg data-testid="linkedin-icon" />),
}));

// Mock SOCIAL_MEDIA_LINKS
vitest.mock('../../lib/social-media-config', () => ({
  SOCIAL_MEDIA_LINKS: {
    facebook: { url: 'http://facebook.com/banwee', ariaLabel: 'Facebook', name: 'Facebook' },
    twitter: { url: 'http://twitter.com/banwee', ariaLabel: 'Twitter', name: 'Twitter' },
    instagram: { url: 'http://instagram.com/banwee', ariaLabel: 'Instagram', name: 'Instagram' },
    youtube: { url: 'http://youtube.com/banwee', ariaLabel: 'Youtube', name: 'Youtube' },
    linkedin: { url: 'http://linkedin.com/banwee', ariaLabel: 'LinkedIn', name: 'LinkedIn' },
  },
}));


describe('Footer Component', () => {
  // Helper to render with BrowserRouter context
  const renderWithRouter = (ui) => render(<BrowserRouter>{ui}</BrowserRouter>);

  beforeEach(() => {
    vitest.clearAllMocks();
  });

  it('renders newsletter subscription section', () => {
    renderWithRouter(<Footer />);
    expect(screen.getByText('Subscribe to our Newsletter')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Your email address')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Subscribe' })).toBeInTheDocument();
    expect(screen.getByTestId('arrow-right-icon')).toBeInTheDocument();
  });

  it('renders company information section', () => {
    renderWithRouter(<Footer />);
    expect(screen.getByAltText('Banwee')).toBeInTheDocument();
    expect(screen.getByText(/Banwee brings you the finest organic products from Africa/i)).toBeInTheDocument();
    
    expect(screen.getByTestId('map-pin-icon')).toBeInTheDocument();
    expect(screen.getByText('1234 Fashion Street, Suite 567, New York, NY 10001')).toBeInTheDocument();

    expect(screen.getByTestId('mail-icon')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'info@banwee.com' })).toHaveAttribute('href', 'mailto:info@banwee.com');

    expect(screen.getByTestId('phone-icon')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '(212) 555-1234' })).toHaveAttribute('href', 'tel:+12125551234');
    
    expect(screen.getByRole('link', { name: /Get direction/i })).toHaveAttribute('href', '/contact');
  });

  it('renders "Shop Categories" links', () => {
    renderWithRouter(<Footer />);
    expect(screen.getByText('Shop Categories')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Cereal Crops' })).toHaveAttribute('href', '/products?category=Cereal Crops');
    expect(screen.getByRole('link', { name: 'Legumes' })).toBeInTheDocument();
  });

  it('renders "Help" links', () => {
    renderWithRouter(<Footer />);
    expect(screen.getByText('Help')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'About Us' })).toHaveAttribute('href', '/about');
    expect(screen.getByRole('link', { name: 'Contact' })).toBeInTheDocument();
  });

  it('renders "My Account" links', () => {
    renderWithRouter(<Footer />);
    expect(screen.getByText('My Account')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'My Account' })).toHaveAttribute('href', '/account');
    expect(screen.getByRole('link', { name: 'My Orders' })).toBeInTheDocument();
  });

  it('renders social media links with correct attributes', () => {
    renderWithRouter(<Footer />);
    expect(screen.getByText(/© 2025 Banwee Store/i)).toBeInTheDocument();

    expect(screen.getByLabelText('Facebook')).toHaveAttribute('href', 'http://facebook.com/banwee');
    expect(screen.getByLabelText('Facebook')).toHaveAttribute('target', '_blank');
    expect(screen.getByLabelText('Facebook')).toHaveAttribute('rel', 'noopener noreferrer');
    expect(screen.getByTestId('facebook-icon')).toBeInTheDocument();

    expect(screen.getByLabelText('Twitter')).toHaveAttribute('href', 'http://twitter.com/banwee');
    expect(screen.getByTestId('twitter-icon')).toBeInTheDocument();

    expect(screen.getByLabelText('Instagram')).toHaveAttribute('href', 'http://instagram.com/banwee');
    expect(screen.getByTestId('instagram-icon')).toBeInTheDocument();
    
    // Check for Youtube icon (only if present in SOCIAL_MEDIA_LINKS)
    expect(screen.getByLabelText('Youtube')).toHaveAttribute('href', 'http://youtube.com/banwee');
    expect(screen.getByTestId('youtube-icon')).toBeInTheDocument();
  });
});
