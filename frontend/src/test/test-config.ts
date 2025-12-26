/**
 * Enhanced Test Configuration
 * Comprehensive testing configuration for frontend test coverage
 */

export interface TestConfig {
  coverage: {
    components: number;
    hooks: number;
    contexts: number;
    apis: number;
    pages: number;
  };
  propertyTests: {
    iterations: number;
    timeout: number;
  };
  performance: {
    maxExecutionTime: number;
  };
}

export const TEST_CONFIG: TestConfig = {
  coverage: {
    components: 90, // 90% coverage for components
    hooks: 95,      // 95% coverage for hooks
    contexts: 90,   // 90% coverage for contexts
    apis: 85,       // 85% coverage for APIs
    pages: 80,      // 80% coverage for pages
  },
  propertyTests: {
    iterations: 100,    // Minimum 100 iterations per property test
    timeout: 30000,     // 30 seconds timeout
  },
  performance: {
    maxExecutionTime: 300000, // 5 minutes max execution time
  },
};

export const PROPERTY_TEST_CONFIG = {
  numRuns: TEST_CONFIG.propertyTests.iterations,
  timeout: TEST_CONFIG.propertyTests.timeout,
  verbose: false,
};

// Test environment validation
export function validateTestEnvironment(): void {
  // Validate fast-check is available
  try {
    require('fast-check');
  } catch (error) {
    throw new Error('fast-check is not installed. Run: npm install fast-check');
  }

  // Validate React Testing Library is available
  try {
    require('@testing-library/react');
  } catch (error) {
    throw new Error('@testing-library/react is not installed');
  }

  // Validate MSW is available
  try {
    require('msw');
  } catch (error) {
    throw new Error('MSW is not installed for API mocking');
  }

  // Validate Vitest is available
  try {
    require('vitest');
  } catch (error) {
    throw new Error('Vitest is not installed');
  }
}

// Coverage thresholds for different file types
export const COVERAGE_THRESHOLDS = {
  'src/components/**/*.{ts,tsx}': {
    branches: TEST_CONFIG.coverage.components,
    functions: TEST_CONFIG.coverage.components,
    lines: TEST_CONFIG.coverage.components,
    statements: TEST_CONFIG.coverage.components,
  },
  'src/hooks/**/*.{ts,tsx}': {
    branches: TEST_CONFIG.coverage.hooks,
    functions: TEST_CONFIG.coverage.hooks,
    lines: TEST_CONFIG.coverage.hooks,
    statements: TEST_CONFIG.coverage.hooks,
  },
  'src/contexts/**/*.{ts,tsx}': {
    branches: TEST_CONFIG.coverage.contexts,
    functions: TEST_CONFIG.coverage.contexts,
    lines: TEST_CONFIG.coverage.contexts,
    statements: TEST_CONFIG.coverage.contexts,
  },
  'src/apis/**/*.{ts,tsx}': {
    branches: TEST_CONFIG.coverage.apis,
    functions: TEST_CONFIG.coverage.apis,
    lines: TEST_CONFIG.coverage.apis,
    statements: TEST_CONFIG.coverage.apis,
  },
  'src/pages/**/*.{ts,tsx}': {
    branches: TEST_CONFIG.coverage.pages,
    functions: TEST_CONFIG.coverage.pages,
    lines: TEST_CONFIG.coverage.pages,
    statements: TEST_CONFIG.coverage.pages,
  },
};

// Test utilities configuration
export const TEST_UTILITIES_CONFIG = {
  // Mock data configuration
  mockData: {
    userCount: 10,
    productCount: 20,
    categoryCount: 5,
  },
  
  // API mocking configuration
  apiMocking: {
    baseUrl: 'http://localhost:8000/v1',
    timeout: 5000,
    retries: 3,
  },
  
  // Component testing configuration
  componentTesting: {
    renderTimeout: 5000,
    interactionTimeout: 3000,
    accessibilityTimeout: 2000,
  },
};

export default TEST_CONFIG;