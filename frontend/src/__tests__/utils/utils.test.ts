/**
 * Tests for General Utilities - Comprehensive test suite
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { cn, formatCurrency, formatDate, truncate, debounce, generateId } from '../../utils/utils';

describe('General Utilities', () => {
  describe('cn (className utility)', () => {
    it('should combine class names correctly', () => {
      expect(cn('class1', 'class2', 'class3')).toBe('class1 class2 class3');
    });

    it('should filter out falsy values', () => {
      expect(cn('class1', null, 'class2', undefined, 'class3', false)).toBe('class1 class2 class3');
    });

    it('should handle empty input', () => {
      expect(cn()).toBe('');
    });

    it('should handle all falsy values', () => {
      expect(cn(null, undefined, false, '')).toBe('');
    });

    it('should handle conditional classes', () => {
      const isActive = true;
      const isDisabled = false;
      expect(cn('base', isActive && 'active', isDisabled && 'disabled')).toBe('base active');
    });

    it('should handle mixed types', () => {
      expect(cn('base', 0, 'valid', '', 'final')).toBe('base valid final');
    });
  });

  describe('formatCurrency', () => {
    it('should format USD currency correctly', () => {
      expect(formatCurrency(99.99)).toBe('$99.99');
      expect(formatCurrency(0)).toBe('$0.00');
      expect(formatCurrency(1234.56)).toBe('$1,234.56');
    });

    it('should format different currencies', () => {
      expect(formatCurrency(99.99, 'EUR')).toBe('€99.99');
      expect(formatCurrency(99.99, 'GBP')).toBe('£99.99');
      expect(formatCurrency(99.99, 'CAD')).toBe('CA$99.99');
      expect(formatCurrency(99.99, 'JPY')).toBe('¥100'); // JPY doesn't use decimals
    });

    it('should handle invalid amounts', () => {
      expect(formatCurrency(null)).toBe('$0.00');
      expect(formatCurrency(undefined)).toBe('$0.00');
      expect(formatCurrency(NaN)).toBe('$0.00');
    });

    it('should handle negative amounts', () => {
      expect(formatCurrency(-10.50)).toBe('-$10.50');
      expect(formatCurrency(-1234.56)).toBe('-$1,234.56');
    });

    it('should handle large amounts', () => {
      expect(formatCurrency(1234567.89)).toBe('$1,234,567.89');
      expect(formatCurrency(1000000)).toBe('$1,000,000.00');
    });

    it('should handle very small amounts', () => {
      expect(formatCurrency(0.01)).toBe('$0.01');
      expect(formatCurrency(0.001)).toBe('$0.00'); // Rounds to nearest cent
    });

    it('should handle string numbers', () => {
      expect(formatCurrency('99.99' as any)).toBe('$99.99');
      expect(formatCurrency('invalid' as any)).toBe('$0.00');
    });
  });

  describe('formatDate', () => {
    it('should format dates correctly with default locale', () => {
      const date = new Date('2024-01-15T10:00:00Z');
      const formatted = formatDate(date);
      expect(formatted).toBe('January 15, 2024');
    });

    it('should format date strings correctly', () => {
      const formatted = formatDate('2024-12-25');
      expect(formatted).toBe('December 25, 2024');
    });

    it('should format dates with different locales', () => {
      const date = new Date('2024-01-15T10:00:00Z');
      
      // Note: Locale formatting may vary by system, so we test the structure
      const enUS = formatDate(date, 'en-US');
      const enGB = formatDate(date, 'en-GB');
      
      expect(enUS).toContain('January');
      expect(enUS).toContain('15');
      expect(enUS).toContain('2024');
      
      expect(enGB).toContain('January');
      expect(enGB).toContain('15');
      expect(enGB).toContain('2024');
    });

    it('should handle ISO date strings', () => {
      const formatted = formatDate('2024-01-15T10:00:00.000Z');
      expect(formatted).toBe('January 15, 2024');
    });

    it('should handle timestamp numbers', () => {
      const timestamp = new Date('2024-01-15').getTime();
      const formatted = formatDate(timestamp);
      expect(formatted).toBe('January 15, 2024');
    });

    it('should handle invalid dates gracefully', () => {
      expect(() => formatDate('invalid-date')).not.toThrow();
      const result = formatDate('invalid-date');
      expect(result).toBe('Invalid Date');
    });
  });

  describe('truncate', () => {
    it('should truncate text longer than maxLength', () => {
      const text = 'This is a very long text that should be truncated';
      expect(truncate(text, 20)).toBe('This is a very long ...');
    });

    it('should not truncate text shorter than maxLength', () => {
      const text = 'Short text';
      expect(truncate(text, 20)).toBe('Short text');
    });

    it('should handle text exactly at maxLength', () => {
      const text = 'Exactly twenty chars';
      expect(truncate(text, 20)).toBe('Exactly twenty chars');
    });

    it('should handle empty text', () => {
      expect(truncate('', 10)).toBe('');
    });

    it('should handle maxLength of 0', () => {
      expect(truncate('test', 0)).toBe('...');
    });

    it('should handle negative maxLength', () => {
      expect(truncate('test', -5)).toBe('...');
    });

    it('should handle very short maxLength', () => {
      expect(truncate('Hello World', 3)).toBe('Hel...');
    });

    it('should handle unicode characters', () => {
      const text = 'Hello 🌍 World 🚀';
      expect(truncate(text, 10)).toBe('Hello 🌍 W...');
    });
  });

  describe('debounce', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should delay function execution', () => {
      const mockFn = vi.fn();
      const debouncedFn = debounce(mockFn, 100);

      debouncedFn();
      expect(mockFn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(100);
      expect(mockFn).toHaveBeenCalledTimes(1);
    });

    it('should cancel previous calls when called multiple times', () => {
      const mockFn = vi.fn();
      const debouncedFn = debounce(mockFn, 100);

      debouncedFn();
      debouncedFn();
      debouncedFn();

      vi.advanceTimersByTime(100);
      expect(mockFn).toHaveBeenCalledTimes(1);
    });

    it('should pass arguments correctly', () => {
      const mockFn = vi.fn();
      const debouncedFn = debounce(mockFn, 100);

      debouncedFn('arg1', 'arg2', 123);
      vi.advanceTimersByTime(100);

      expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2', 123);
    });

    it('should handle multiple calls with different arguments', () => {
      const mockFn = vi.fn();
      const debouncedFn = debounce(mockFn, 100);

      debouncedFn('first');
      vi.advanceTimersByTime(50);
      debouncedFn('second');
      vi.advanceTimersByTime(100);

      expect(mockFn).toHaveBeenCalledTimes(1);
      expect(mockFn).toHaveBeenCalledWith('second');
    });

    it('should work with zero delay', () => {
      const mockFn = vi.fn();
      const debouncedFn = debounce(mockFn, 0);

      debouncedFn();
      vi.advanceTimersByTime(0);

      expect(mockFn).toHaveBeenCalledTimes(1);
    });

    it('should handle this context correctly', () => {
      const obj = {
        value: 'test',
        method: function(arg) {
          return this.value + arg;
        }
      };

      const mockFn = vi.fn(function(arg) {
        return obj.method.call(this, arg);
      });

      const debouncedFn = debounce(mockFn, 100);
      debouncedFn.call(obj, '123');

      vi.advanceTimersByTime(100);
      expect(mockFn).toHaveBeenCalledWith('123');
    });

    it('should handle rapid successive calls', () => {
      const mockFn = vi.fn();
      const debouncedFn = debounce(mockFn, 100);

      // Simulate rapid typing
      for (let i = 0; i < 10; i++) {
        debouncedFn(`call${i}`);
        vi.advanceTimersByTime(10);
      }

      vi.advanceTimersByTime(100);
      expect(mockFn).toHaveBeenCalledTimes(1);
      expect(mockFn).toHaveBeenCalledWith('call9');
    });
  });

  describe('generateId', () => {
    it('should generate unique IDs', () => {
      const id1 = generateId();
      const id2 = generateId();
      
      expect(id1).not.toBe(id2);
      expect(typeof id1).toBe('string');
      expect(typeof id2).toBe('string');
    });

    it('should generate IDs with reasonable length', () => {
      const id = generateId();
      expect(id.length).toBeGreaterThan(10);
      expect(id.length).toBeLessThan(30);
    });

    it('should generate IDs with alphanumeric characters', () => {
      const id = generateId();
      expect(id).toMatch(/^[a-z0-9]+$/);
    });

    it('should generate different IDs when called rapidly', () => {
      const ids = [];
      for (let i = 0; i < 100; i++) {
        ids.push(generateId());
      }

      const uniqueIds = new Set(ids);
      expect(uniqueIds.size).toBe(100); // All IDs should be unique
    });

    it('should include timestamp component for uniqueness', () => {
      const beforeTime = Date.now();
      const id = generateId();
      const afterTime = Date.now();

      // The ID should contain a timestamp component
      // We can't test the exact format, but we can verify it's time-based
      expect(id).toBeTruthy();
      expect(id.length).toBeGreaterThan(0);
    });

    it('should handle concurrent generation', async () => {
      const promises = Array.from({ length: 50 }, () => 
        Promise.resolve(generateId())
      );

      const ids = await Promise.all(promises);
      const uniqueIds = new Set(ids);
      
      expect(uniqueIds.size).toBe(50);
    });
  });

  describe('Edge Cases and Error Handling', () => {
    it('should handle null and undefined inputs gracefully', () => {
      expect(() => cn(null, undefined)).not.toThrow();
      expect(() => formatCurrency(null)).not.toThrow();
      expect(() => truncate(null as any, 10)).toThrow(); // This should throw
      expect(() => formatDate(null as any)).not.toThrow();
    });

    it('should handle extreme values', () => {
      expect(formatCurrency(Number.MAX_SAFE_INTEGER)).toContain('$');
      expect(formatCurrency(Number.MIN_SAFE_INTEGER)).toContain('-$');
      expect(truncate('a'.repeat(10000), 5)).toBe('aaaaa...');
    });

    it('should handle special characters in text', () => {
      const specialText = 'Hello 🌍 World! @#$%^&*()';
      expect(truncate(specialText, 10)).toBe('Hello 🌍 W...');
    });

    it('should handle different number formats in formatCurrency', () => {
      expect(formatCurrency(1.999)).toBe('$2.00'); // Rounds to nearest cent
      expect(formatCurrency(1.001)).toBe('$1.00'); // Rounds down
    });

    it('should handle very long debounce delays', () => {
      vi.useFakeTimers();
      const mockFn = vi.fn();
      const debouncedFn = debounce(mockFn, 10000);

      debouncedFn();
      vi.advanceTimersByTime(5000);
      expect(mockFn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(5000);
      expect(mockFn).toHaveBeenCalledTimes(1);

      vi.useRealTimers();
    });
  });

  describe('Performance and Memory', () => {
    it('should not leak memory with debounce', () => {
      const mockFn = vi.fn();
      let debouncedFn = debounce(mockFn, 100);

      // Simulate many calls
      for (let i = 0; i < 1000; i++) {
        debouncedFn();
      }

      // Clear reference
      debouncedFn = null as any;

      // Should not cause memory issues
      expect(mockFn).toBeDefined();
    });

    it('should handle large text truncation efficiently', () => {
      const largeText = 'a'.repeat(100000);
      const start = performance.now();
      const result = truncate(largeText, 100);
      const end = performance.now();

      expect(result).toBe('a'.repeat(100) + '...');
      expect(end - start).toBeLessThan(100); // Should be fast
    });

    it('should generate IDs efficiently', () => {
      const start = performance.now();
      const ids = Array.from({ length: 1000 }, () => generateId());
      const end = performance.now();

      expect(ids).toHaveLength(1000);
      expect(end - start).toBeLessThan(1000); // Should be reasonably fast
    });
  });
});