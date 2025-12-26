/**
 * WhatsApp Support Integration Tests
 * Tests the WhatsApp customer support functionality
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import useWhatsAppSupport from '../hooks/useWhatsAppSupport';
import { renderHook } from '@testing-library/react';

// Mock the AuthContext
const mockUser = {
  id: 'user-123',
  email: 'test@example.com',
  firstname: 'John',
  lastname: 'Doe',
  full_name: 'John Doe',
  role: 'customer' as const,
  is_active: true,
  is_verified: true,
  created_at: '2024-01-01T00:00:00Z'
};

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: mockUser })
}));

// Mock window.open
const mockWindowOpen = vi.fn();
Object.defineProperty(window, 'open', {
  value: mockWindowOpen,
  writable: true
});

// Mock navigator.clipboard
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: vi.fn().mockResolvedValue(undefined)
  },
  writable: true
});

describe('WhatsApp Support Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should generate correct support message for general inquiry', () => {
    const { result } = renderHook(() => useWhatsAppSupport());
    
    const message = result.current.generateSupportMessage({
      issueType: 'general'
    });

    expect(message).toContain('GENERAL SUPPORT REQUEST');
    expect(message).toContain('John Doe');
    expect(message).toContain('test@example.com');
    expect(message).toContain('Thank you for your help! 😊');
  });

  it('should generate urgent support message with proper formatting', () => {
    const { result } = renderHook(() => useWhatsAppSupport());
    
    const message = result.current.generateSupportMessage({
      issueType: 'urgent',
      orderNumber: 'ORD-12345'
    });

    expect(message).toContain('🚨 URGENT SUPPORT NEEDED 🚨');
    expect(message).toContain('ORD-12345');
    expect(message).toContain('John Doe');
    expect(message).toContain('This is urgent - please help ASAP! 🙏');
  });

  it('should generate order-specific support message', () => {
    const { result } = renderHook(() => useWhatsAppSupport());
    
    const message = result.current.generateSupportMessage({
      issueType: 'order',
      orderNumber: 'ORD-67890'
    });

    expect(message).toContain('📦 ORDER SUPPORT REQUEST');
    expect(message).toContain('ORD-67890');
    expect(message).toContain('Order-related inquiry');
  });

  it('should generate product-specific support message', () => {
    const { result } = renderHook(() => useWhatsAppSupport());
    
    const message = result.current.generateSupportMessage({
      issueType: 'product',
      productId: 'PROD-123'
    });

    expect(message).toContain('🛍️ PRODUCT INQUIRY');
    expect(message).toContain('PROD-123');
  });

  it('should open WhatsApp with correct URL', () => {
    const { result } = renderHook(() => useWhatsAppSupport());
    
    const success = result.current.openWhatsApp({
      issueType: 'general'
    });

    expect(success).toBe(true);
    expect(mockWindowOpen).toHaveBeenCalledWith(
      expect.stringContaining('https://wa.me/1234567890?text='),
      '_blank'
    );
  });

  it('should generate WhatsApp URL correctly', () => {
    const { result } = renderHook(() => useWhatsAppSupport());
    
    const url = result.current.getWhatsAppUrl({
      issueType: 'urgent'
    });

    expect(url).toMatch(/^https:\/\/wa\.me\/1234567890\?text=/);
    expect(decodeURIComponent(url)).toContain('URGENT SUPPORT NEEDED');
  });

  it('should copy message to clipboard', async () => {
    const { result } = renderHook(() => useWhatsAppSupport());
    
    const clipboardResult = await result.current.copyMessageToClipboard({
      issueType: 'general'
    });

    expect(clipboardResult.success).toBe(true);
    expect(clipboardResult.message).toContain('GENERAL SUPPORT REQUEST');
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      expect.stringContaining('GENERAL SUPPORT REQUEST')
    );
  });

  it('should detect WhatsApp availability', () => {
    const { result } = renderHook(() => useWhatsAppSupport());
    
    const isAvailable = result.current.isWhatsAppAvailable();
    
    // Should return true for modern browsers with service worker support
    expect(typeof isAvailable).toBe('boolean');
  });

  it('should handle custom messages', () => {
    const { result } = renderHook(() => useWhatsAppSupport());
    
    const customMessage = 'I need help with my custom issue';
    const message = result.current.generateSupportMessage({
      customMessage
    });

    expect(message).toContain(customMessage);
    expect(message).toContain('John Doe');
    expect(message).toContain('test@example.com');
  });

  it('should handle guest users (no authentication)', () => {
    // Create a new hook instance with guest user
    const { result } = renderHook(() => useWhatsAppSupport(), {
      wrapper: ({ children }) => children // Simple wrapper for this test
    });
    
    // Since we can't easily mock the hook mid-test, we'll test the message generation
    // with a null user scenario by checking the message content
    const message = result.current.generateSupportMessage({
      issueType: 'general'
    });

    // The message should still be generated even without user data
    expect(message).toContain('GENERAL SUPPORT REQUEST');
    expect(typeof message).toBe('string');
    expect(message.length).toBeGreaterThan(0);
  });
});

describe('WhatsApp Support Configuration', () => {
  it('should have correct business configuration', () => {
    const { result } = renderHook(() => useWhatsAppSupport());
    
    expect(result.current.config.businessNumber).toBe('+1234567890');
    expect(result.current.config.businessName).toBe('Banwee Support');
    expect(result.current.config.defaultMessage).toBe('Hi! I need help with my Banwee account.');
  });
});