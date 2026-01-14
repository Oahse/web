/**
 * Property-Based Testing Utilities
 * Provides generators and utilities for property-based testing with fast-check
 * Feature: frontend-test-coverage, Property 24: Data Transformation Integrity
 * Validates: Requirements 7.1
 */

import * as fc from 'fast-check';
import { expect } from 'vitest';
import { PropertyTestConfig, DEFAULT_PROPERTY_CONFIG } from './utils';

// ==================== GENERATORS ====================

// User data generators
export const userArbitrary = fc.record({
  id: fc.string({ minLength: 1, maxLength: 50 }),
  email: fc.emailAddress(),
  firstname: fc.string({ minLength: 1, maxLength: 50 }),
  lastname: fc.string({ minLength: 1, maxLength: 50 }),
  role: fc.constantFrom('Admin', 'Customer', 'Supplier'),
  verified: fc.boolean(),
  phone: fc.option(fc.string({ minLength: 10, maxLength: 15 })),
  created_at: fc.date().map(d => d.toISOString()),
});

// Product data generators
export const productVariantArbitrary = fc.record({
  id: fc.string({ minLength: 1, maxLength: 50 }),
  name: fc.string({ minLength: 1, maxLength: 100 }),
  price: fc.float({ min: 0.01, max: 10000, noNaN: true }),
  sku: fc.string({ minLength: 1, maxLength: 50 }),
  stock_quantity: fc.integer({ min: 0, max: 1000 }),
  attributes: fc.record({
    size: fc.option(fc.constantFrom('XS', 'S', 'M', 'L', 'XL', 'XXL')),
    color: fc.option(fc.constantFrom('Red', 'Blue', 'Green', 'Black', 'White')),
  }),
});

export const productArbitrary = fc.record({
  id: fc.string({ minLength: 1, maxLength: 50 }),
  name: fc.string({ minLength: 1, maxLength: 200 }),
  description: fc.string({ minLength: 10, maxLength: 1000 }),
  price: fc.float({ min: 0.01, max: 10000, noNaN: true }),
  category: fc.constantFrom('Electronics', 'Clothing', 'Books', 'Home', 'Sports'),
  brand: fc.string({ minLength: 1, maxLength: 50 }),
  sku: fc.string({ minLength: 1, maxLength: 50 }),
  stock_quantity: fc.integer({ min: 0, max: 1000 }),
  is_active: fc.boolean(),
  images: fc.array(fc.webUrl(), { minLength: 0, maxLength: 5 }),
  variants: fc.array(productVariantArbitrary, { minLength: 0, maxLength: 10 }),
  created_at: fc.date().map(d => d.toISOString()),
});

// Cart data generators
export const cartItemArbitrary = fc.record({
  id: fc.string({ minLength: 1, maxLength: 50 }),
  product: productArbitrary,
  variant_id: fc.option(fc.string({ minLength: 1, maxLength: 50 })),
  quantity: fc.integer({ min: 1, max: 100 }),
  price: fc.float({ min: 0.01, max: 10000, noNaN: true }),
  total: fc.float({ min: 0.01, max: 100000, noNaN: true }),
});

export const cartArbitrary = fc.record({
  id: fc.string({ minLength: 1, maxLength: 50 }),
  items: fc.array(cartItemArbitrary, { minLength: 0, maxLength: 20 }),
  total_items: fc.integer({ min: 0, max: 100 }),
  total_price: fc.float({ min: 0, max: 100000, noNaN: true }),
  created_at: fc.date().map(d => d.toISOString()),
  updated_at: fc.date().map(d => d.toISOString()),
});

// Form data generators
export const loginFormArbitrary = fc.record({
  email: fc.emailAddress(),
  password: fc.string({ minLength: 8, maxLength: 128 }),
});

export const registerFormArbitrary = fc.record({
  email: fc.emailAddress(),
  password: fc.string({ minLength: 8, maxLength: 128 }),
  firstname: fc.string({ minLength: 1, maxLength: 50 }),
  lastname: fc.string({ minLength: 1, maxLength: 50 }),
  phone: fc.option(fc.string({ minLength: 10, maxLength: 15 })),
});

// API response generators
export const apiResponseArbitrary = <T>(dataArbitrary: fc.Arbitrary<T>) =>
  fc.record({
    data: dataArbitrary,
    status: fc.constantFrom(200, 201, 204),
    headers: fc.record({
      'content-type': fc.constant('application/json'),
      'x-request-id': fc.string({ minLength: 10, maxLength: 50 }),
    }),
  });

export const apiErrorArbitrary = fc.record({
  message: fc.string({ minLength: 1, maxLength: 200 }),
  code: fc.constantFrom('400', '401', '403', '404', '422', '500'),
  statusCode: fc.constantFrom(400, 401, 403, 404, 422, 500),
  details: fc.option(fc.record({
    field: fc.array(fc.string({ minLength: 1, maxLength: 100 })),
  })),
});

// Component prop generators
export const buttonPropsArbitrary = fc.record({
  children: fc.string({ minLength: 1, maxLength: 50 }),
  variant: fc.constantFrom('primary', 'secondary', 'outline', 'ghost', 'destructive'),
  size: fc.constantFrom('sm', 'md', 'lg'),
  disabled: fc.boolean(),
  loading: fc.boolean(),
  onClick: fc.constant(() => {}),
});

export const inputPropsArbitrary = fc.record({
  type: fc.constantFrom('text', 'email', 'password', 'number', 'tel'),
  placeholder: fc.option(fc.string({ minLength: 1, maxLength: 100 })),
  value: fc.string({ minLength: 0, maxLength: 200 }),
  disabled: fc.boolean(),
  required: fc.boolean(),
  onChange: fc.constant(() => {}),
});

// Navigation and routing generators
export const routeParamsArbitrary = fc.record({
  id: fc.option(fc.string({ minLength: 1, maxLength: 50 })),
  slug: fc.option(fc.string({ minLength: 1, maxLength: 100 })),
  page: fc.option(fc.integer({ min: 1, max: 100 }).map(String)),
  category: fc.option(fc.string({ minLength: 1, maxLength: 50 })),
});

export const searchParamsArbitrary = fc.record({
  q: fc.option(fc.string({ minLength: 1, maxLength: 100 })),
  category: fc.option(fc.string({ minLength: 1, maxLength: 50 })),
  sort: fc.option(fc.constantFrom('name', 'price', 'created_at')),
  order: fc.option(fc.constantFrom('asc', 'desc')),
  page: fc.option(fc.integer({ min: 1, max: 100 }).map(String)),
  limit: fc.option(fc.integer({ min: 1, max: 100 }).map(String)),
});

// ==================== PROPERTY TEST HELPERS ====================

/**
 * Run a property test with default configuration
 */
export function runPropertyTest<T>(
  name: string,
  arbitrary: fc.Arbitrary<T>,
  predicate: (value: T) => boolean | void,
  config: Partial<PropertyTestConfig> = {}
): void {
  const testConfig = { ...DEFAULT_PROPERTY_CONFIG, ...config };
  
  fc.assert(
    fc.property(arbitrary, predicate),
    {
      numRuns: testConfig.iterations,
      timeout: testConfig.timeout,
      seed: testConfig.seed,
      verbose: testConfig.verbose,
    }
  );
}

/**
 * Run an async property test
 */
export function runAsyncPropertyTest<T>(
  name: string,
  arbitrary: fc.Arbitrary<T>,
  predicate: (value: T) => Promise<boolean | void>,
  config: Partial<PropertyTestConfig> = {}
): Promise<void> {
  const testConfig = { ...DEFAULT_PROPERTY_CONFIG, ...config };
  
  return fc.assert(
    fc.asyncProperty(arbitrary, predicate),
    {
      numRuns: testConfig.iterations,
      timeout: testConfig.timeout,
      seed: testConfig.seed,
      verbose: testConfig.verbose,
    }
  );
}

/**
 * Create a property test for component rendering stability
 */
export function createRenderingStabilityTest<T>(
  componentName: string,
  propsArbitrary: fc.Arbitrary<T>,
  renderComponent: (props: T) => void
): void {
  runPropertyTest(
    `${componentName} rendering stability`,
    propsArbitrary,
    (props) => {
      // Should not throw when rendering with valid props
      expect(() => renderComponent(props)).not.toThrow();
    }
  );
}

/**
 * Create a property test for data transformation integrity
 */
export function createDataTransformationTest<T, U>(
  transformationName: string,
  inputArbitrary: fc.Arbitrary<T>,
  transform: (input: T) => U,
  invariant: (input: T, output: U) => boolean
): void {
  runPropertyTest(
    `${transformationName} data integrity`,
    inputArbitrary,
    (input) => {
      const output = transform(input);
      expect(invariant(input, output)).toBe(true);
    }
  );
}

/**
 * Create a property test for round-trip operations
 */
export function createRoundTripTest<T>(
  operationName: string,
  dataArbitrary: fc.Arbitrary<T>,
  serialize: (data: T) => string,
  deserialize: (serialized: string) => T,
  equals: (a: T, b: T) => boolean = (a, b) => JSON.stringify(a) === JSON.stringify(b)
): void {
  runPropertyTest(
    `${operationName} round trip`,
    dataArbitrary,
    (data) => {
      const serialized = serialize(data);
      const deserialized = deserialize(serialized);
      expect(equals(data, deserialized)).toBe(true);
    }
  );
}

/**
 * Create a property test for idempotent operations
 */
export function createIdempotencyTest<T>(
  operationName: string,
  dataArbitrary: fc.Arbitrary<T>,
  operation: (data: T) => T,
  equals: (a: T, b: T) => boolean = (a, b) => JSON.stringify(a) === JSON.stringify(b)
): void {
  runPropertyTest(
    `${operationName} idempotency`,
    dataArbitrary,
    (data) => {
      const result1 = operation(data);
      const result2 = operation(result1);
      expect(equals(result1, result2)).toBe(true);
    }
  );
}

/**
 * Create a property test for invariant preservation
 */
export function createInvariantTest<T>(
  operationName: string,
  dataArbitrary: fc.Arbitrary<T>,
  operation: (data: T) => T,
  invariant: (data: T) => boolean
): void {
  runPropertyTest(
    `${operationName} invariant preservation`,
    dataArbitrary,
    (data) => {
      // Skip if initial data doesn't satisfy invariant
      if (!invariant(data)) return;
      
      const result = operation(data);
      expect(invariant(result)).toBe(true);
    }
  );
}

/**
 * Create a property test for error handling robustness
 */
export function createErrorHandlingTest<T>(
  operationName: string,
  invalidDataArbitrary: fc.Arbitrary<T>,
  operation: (data: T) => any,
  shouldThrow: boolean = true
): void {
  runPropertyTest(
    `${operationName} error handling`,
    invalidDataArbitrary,
    (invalidData) => {
      if (shouldThrow) {
        expect(() => operation(invalidData)).toThrow();
      } else {
        // Should not throw, but may return error result
        expect(() => operation(invalidData)).not.toThrow();
      }
    }
  );
}

// ==================== SPECIALIZED GENERATORS ====================

/**
 * Generate invalid/edge case data for error testing
 */
export const invalidStringArbitrary = fc.oneof(
  fc.constant(''),
  fc.constant('   '), // whitespace only
  fc.string({ minLength: 1000, maxLength: 2000 }), // too long
  fc.constant(null as any),
  fc.constant(undefined as any),
);

export const invalidEmailArbitrary = fc.oneof(
  fc.constant(''),
  fc.constant('invalid-email'),
  fc.constant('@domain.com'),
  fc.constant('user@'),
  fc.constant('user@domain'),
  fc.string({ minLength: 1, maxLength: 10 }), // random string
);

export const invalidNumberArbitrary = fc.oneof(
  fc.constant(NaN),
  fc.constant(Infinity),
  fc.constant(-Infinity),
  fc.constant(null as any),
  fc.constant(undefined as any),
  fc.constant('not-a-number' as any),
);

/**
 * Generate realistic but diverse test data
 */
export const realisticUserArbitrary = fc.record({
  id: fc.uuid(),
  email: fc.emailAddress(),
  firstname: fc.constantFrom('John', 'Jane', 'Alice', 'Bob', 'Charlie', 'Diana'),
  lastname: fc.constantFrom('Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia'),
  role: fc.constantFrom('Customer', 'Admin', 'Supplier'),
  verified: fc.boolean(),
  phone: fc.option(fc.constantFrom('+1234567890', '+9876543210', '+5555555555')),
  created_at: fc.date({ min: new Date('2020-01-01'), max: new Date() }).map(d => d.toISOString()),
});

// Export fast-check for direct use
export { fc };