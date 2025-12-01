# Contributing to Banwee E-commerce Platform

Thank you for your interest in contributing to Banwee! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors. We expect all participants to:

- Be respectful and considerate
- Welcome newcomers and help them get started
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Publishing others' private information
- Any conduct that could be considered inappropriate in a professional setting

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Git installed and configured
- Docker and Docker Compose (for containerized development)
- OR: Python 3.11+, Node.js 18+, PostgreSQL, Redis (for local development)
- A GitHub account
- Familiarity with the project's tech stack

### Setting Up Your Development Environment

1. **Fork the repository** on GitHub

2. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/banweemvp.git
   cd banweemvp
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/Oahse/banweemvp.git
   ```

4. **Set up the development environment**
   ```bash
   # Using Docker (recommended)
   ./docker-start.sh
   
   # OR follow local setup instructions in README.md
   ```

5. **Verify the setup**
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000/docs

## Development Workflow

### 1. Create a Feature Branch

Always create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications
- `chore/` - Maintenance tasks

### 2. Make Your Changes

- Write clean, readable code
- Follow the project's coding standards
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 3. Test Your Changes

```bash
# Backend tests
cd backend
pytest
pytest -v  # verbose output
pytest --cov  # with coverage

# Frontend tests
cd frontend
npm test -- --run
npm test -- --coverage
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add user profile editing feature"
```

See [Commit Message Guidelines](#commit-message-guidelines) below.

### 5. Keep Your Branch Updated

```bash
git fetch upstream
git rebase upstream/main
```

### 6. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 7. Create a Pull Request

- Go to the original repository on GitHub
- Click "New Pull Request"
- Select your feature branch
- Fill out the PR template with details about your changes

## Coding Standards

### Python (Backend)

- Follow PEP 8 style guide
- Use type hints for function parameters and return values
- Maximum line length: 100 characters
- Use meaningful variable and function names
- Add docstrings to all functions and classes

```python
async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    """
    Retrieve a user by their email address.
    
    Args:
        email: The user's email address
        db: Database session
        
    Returns:
        User object if found, None otherwise
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()
```

### TypeScript (Frontend)

- Follow ESLint configuration
- Use TypeScript for type safety
- Use functional components with hooks
- Maximum line length: 100 characters
- Use meaningful component and variable names

```typescript
interface ProductCardProps {
  product: Product;
  onAddToCart: (productId: string) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({ 
  product, 
  onAddToCart 
}) => {
  // Component implementation
};
```

### General Guidelines

- **DRY**: Don't Repeat Yourself - extract common logic
- **KISS**: Keep It Simple, Stupid - avoid over-engineering
- **YAGNI**: You Aren't Gonna Need It - don't add unused features
- **Single Responsibility**: Each function/class should do one thing well
- **Meaningful Names**: Use descriptive names for variables and functions

## Testing Guidelines

### Backend Testing

- Write unit tests for all service methods
- Write property-based tests for complex logic using Hypothesis
- Test both success and error cases
- Mock external dependencies (Stripe, Mailgun)
- Aim for >80% code coverage

```python
def test_create_order_success(test_db, test_user):
    """Test successful order creation."""
    order_data = {
        "user_id": test_user.id,
        "items": [{"product_id": "...", "quantity": 1}]
    }
    order = create_order(order_data, test_db)
    assert order.id is not None
    assert order.status == "pending"
```

### Frontend Testing

- Write unit tests for utility functions
- Write component tests for UI components
- Write property-based tests using fast-check
- Test user interactions and state changes
- Aim for >70% code coverage

```typescript
describe('ProductCard', () => {
  it('should display product information', () => {
    const product = { name: 'Test Product', price: 99.99 };
    render(<ProductCard product={product} />);
    expect(screen.getByText('Test Product')).toBeInTheDocument();
  });
});
```

## Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring without changing functionality
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependency updates

### Examples

```
feat(auth): add password reset functionality

Implement password reset flow with email verification.
Users can now request a password reset link via email.

Closes #123
```

```
fix(cart): resolve cart total calculation error

Fixed bug where discount was not applied correctly
to cart total when multiple items were present.

Fixes #456
```

## Pull Request Process

### Before Submitting

- [ ] Code follows the project's style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated if needed
- [ ] Commit messages follow the guidelines
- [ ] Branch is up to date with main

### PR Template

When creating a PR, include:

1. **Description**: What does this PR do?
2. **Motivation**: Why is this change needed?
3. **Changes**: List of specific changes made
4. **Testing**: How was this tested?
5. **Screenshots**: If UI changes, include before/after screenshots
6. **Related Issues**: Link to related issues

### Review Process

1. Automated checks will run (tests, linting)
2. At least one maintainer will review your code
3. Address any feedback or requested changes
4. Once approved, a maintainer will merge your PR

### After Merging

- Delete your feature branch
- Update your local repository
- Celebrate your contribution! 🎉

## Issue Reporting

### Before Creating an Issue

- Search existing issues to avoid duplicates
- Check if the issue is already fixed in the latest version
- Gather relevant information (error messages, screenshots, etc.)

### Creating a Good Issue

Include:

1. **Clear Title**: Summarize the issue in one line
2. **Description**: Detailed explanation of the issue
3. **Steps to Reproduce**: How to reproduce the bug
4. **Expected Behavior**: What should happen
5. **Actual Behavior**: What actually happens
6. **Environment**: OS, browser, versions, etc.
7. **Screenshots**: If applicable
8. **Possible Solution**: If you have ideas

### Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Documentation improvements
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention needed
- `question`: Further information requested

## Questions?

If you have questions about contributing:

- Check the [README.md](README.md) for general information
- Review existing issues and PRs
- Ask in [GitHub Discussions](https://github.com/Oahse/banweemvp/discussions)
- Contact the maintainers

## Recognition

Contributors will be recognized in:

- The project's README
- Release notes for significant contributions
- Our contributors page (coming soon)

Thank you for contributing to Banwee! 🙏
