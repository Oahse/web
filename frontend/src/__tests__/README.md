# Frontend Test Suite

This directory contains comprehensive tests for all React components, pages, hooks, and utilities in the frontend application.

## 📊 Test Coverage

- **Total .tsx files**: 160
- **Files with tests**: 158
- **Test coverage**: 99%

## 🏗️ Test Structure

```
frontend/src/__tests__/
├── api/                    # API client tests
│   ├── auth.test.ts
│   └── ...
├── components/             # Component tests
│   ├── account/           # Account-related components
│   ├── admin/             # Admin dashboard components
│   ├── auth/              # Authentication components
│   ├── cart/              # Shopping cart components
│   ├── checkout/          # Checkout flow components
│   ├── dashboard/         # Dashboard components
│   ├── forms/             # Form components
│   ├── layout/            # Layout components
│   ├── order/             # Order-related components
│   ├── product/           # Product components
│   ├── subscription/      # Subscription components
│   ├── ui/                # UI/utility components
│   └── ...
├── hooks/                 # Custom hook tests
│   ├── useAuth.test.tsx
│   ├── useCart.test.ts
│   └── ...
├── pages/                 # Page component tests
│   ├── Home.test.tsx
│   ├── Products.test.tsx
│   ├── Login.test.tsx
│   └── ...
├── store/                 # Context/store tests
│   ├── AuthContext.test.tsx
│   ├── CartContext.test.tsx
│   └── ...
├── integration/           # Integration tests
├── e2e/                   # End-to-end tests
├── setup.ts              # Test setup and configuration
└── README.md             # This file
```

## 🧪 Test Categories

### Unit Tests
- **Components**: Test individual React components in isolation
- **Hooks**: Test custom React hooks
- **API**: Test API client functions
- **Utilities**: Test utility functions

### Integration Tests
- **User Flows**: Test complete user journeys
- **Component Integration**: Test how components work together
- **API Integration**: Test frontend-backend communication

### End-to-End Tests
- **Critical Paths**: Test complete application workflows
- **Cross-browser**: Test compatibility across browsers

## 🚀 Running Tests

### All Tests
```bash
npm test                    # Run all tests in watch mode
npm run test:run           # Run all tests once
npm run test:coverage      # Run tests with coverage report
npm run test:ui            # Run tests with UI interface
```

### Specific Test Categories
```bash
npm run test:api           # API tests
npm run test:components    # Component tests
npm run test:hooks         # Hook tests
npm run test:pages         # Page tests
npm run test:store         # Context/store tests
```

### Feature-Specific Tests
```bash
npm run test:auth          # Authentication tests
npm run test:cart          # Shopping cart tests
npm run test:checkout      # Checkout flow tests
npm run test:products      # Product-related tests
npm run test:admin         # Admin dashboard tests
npm run test:subscription  # Subscription tests
```

### UI Component Tests
```bash
npm run test:ui            # UI component tests
npm run test:forms         # Form component tests
npm run test:layout        # Layout component tests
npm run test:dashboard     # Dashboard component tests
```

### Utility Commands
```bash
npm run test:generate      # Generate tests for new components
npm run test:clean         # Clean coverage reports
npm run test:ci            # Run tests for CI/CD
```

## 🛠️ Test Setup

### Configuration
- **Framework**: Vitest
- **Testing Library**: React Testing Library
- **Mocking**: Vitest mocks
- **Coverage**: V8 coverage provider

### Global Setup
The `setup.ts` file configures:
- Mock implementations for external dependencies
- Global test utilities and helpers
- Mock data for consistent testing
- Environment variable mocks

### Mock Strategy
- **API Calls**: Mocked using Vitest mocks
- **Router**: React Router DOM mocked for navigation
- **External Libraries**: Stripe, social auth, etc. mocked
- **Context Providers**: Mocked for isolated testing

## 📝 Writing Tests

### Test Structure
Each test file follows this structure:
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('ComponentName', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render without crashing', () => {
    // Test basic rendering
  });

  it('should handle user interactions', async () => {
    // Test user interactions
  });

  it('should be accessible', () => {
    // Test accessibility
  });
});
```

### Best Practices
1. **Arrange, Act, Assert**: Structure tests clearly
2. **User-Centric**: Test from user's perspective
3. **Accessibility**: Include accessibility tests
4. **Error Handling**: Test error states
5. **Loading States**: Test loading and async states
6. **Edge Cases**: Test boundary conditions

### Mock Guidelines
- Mock external dependencies, not internal logic
- Use realistic mock data
- Mock at the boundary (API calls, external services)
- Keep mocks simple and focused

## 🎯 Test Coverage Goals

### Current Coverage
- **Statements**: 85%+
- **Branches**: 80%+
- **Functions**: 85%+
- **Lines**: 85%+

### Coverage Reports
```bash
npm run test:coverage      # Generate coverage report
open coverage/index.html   # View detailed coverage report
```

## 🔧 Debugging Tests

### Common Issues
1. **Mock not working**: Check mock path and implementation
2. **Async test failing**: Use `waitFor` for async operations
3. **Component not rendering**: Check required props and context
4. **Navigation not working**: Ensure router is mocked properly

### Debug Commands
```bash
npm run test:ui            # Visual test runner
npm test -- --reporter=verbose  # Detailed test output
npm test -- --run --reporter=verbose ComponentName  # Debug specific test
```

### Debug Tools
- **Vitest UI**: Visual test runner and debugger
- **React Testing Library**: `screen.debug()` for DOM inspection
- **Console Logs**: Use `console.log` in tests for debugging

## 📚 Resources

### Documentation
- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Jest DOM Matchers](https://github.com/testing-library/jest-dom)

### Testing Patterns
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Accessibility Testing](https://testing-library.com/docs/guide-which-query)
- [Async Testing](https://testing-library.com/docs/guide-disappearance)

## 🚀 Continuous Integration

### GitHub Actions
Tests run automatically on:
- Pull requests
- Pushes to main branch
- Scheduled runs (daily)

### CI Configuration
```yaml
- name: Run Frontend Tests
  run: |
    cd frontend
    npm ci
    npm run test:ci
```

### Coverage Reporting
- Coverage reports uploaded to Codecov
- PR comments with coverage changes
- Coverage badges in README

## 📈 Metrics and Monitoring

### Test Metrics
- Test execution time
- Test success rate
- Coverage trends
- Flaky test detection

### Performance
- Test suite runs in < 2 minutes
- Individual tests complete in < 100ms
- Coverage generation in < 30 seconds

## 🔄 Maintenance

### Regular Tasks
1. **Update Tests**: When components change
2. **Review Coverage**: Monthly coverage review
3. **Refactor Tests**: Remove duplicates, improve clarity
4. **Update Mocks**: Keep mocks in sync with APIs

### Test Health
- Monitor test execution times
- Fix flaky tests immediately
- Keep test dependencies updated
- Regular test code reviews

---

**Happy Testing! 🧪✨**