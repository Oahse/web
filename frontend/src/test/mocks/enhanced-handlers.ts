/**
 * Enhanced MSW Handlers for Comprehensive API Mocking
 * Provides comprehensive API mocking for all testing scenarios
 */

import { rest } from 'msw';
import { mockUsers, mockProducts, mockAPIErrors } from '../utils';

const API_BASE_URL = 'http://localhost:8000/v1';

// Enhanced authentication handlers with more scenarios
export const enhancedAuthHandlers = [
  // Login with various scenarios
  rest.post(`${API_BASE_URL}/auth/login`, (req, res, ctx) => {
    const { email, password } = req.body as any;
    
    // Simulate different login scenarios
    if (email === 'test@example.com' && password === 'password123') {
      return res(
        ctx.status(200),
        ctx.json({
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          token_type: 'bearer',
          user: mockUsers.customer,
        })
      );
    }
    
    if (email === 'admin@example.com' && password === 'admin123') {
      return res(
        ctx.status(200),
        ctx.json({
          access_token: 'mock-admin-token',
          refresh_token: 'mock-admin-refresh',
          token_type: 'bearer',
          user: mockUsers.admin,
        })
      );
    }
    
    if (email === 'locked@example.com') {
      return res(
        ctx.status(423),
        ctx.json({ detail: 'Account is locked' })
      );
    }
    
    if (email === 'unverified@example.com') {
      return res(
        ctx.status(403),
        ctx.json({ detail: 'Email not verified' })
      );
    }
    
    return res(
      ctx.status(401),
      ctx.json({ detail: 'Invalid credentials' })
    );
  }),

  // Enhanced registration with validation
  rest.post(`${API_BASE_URL}/auth/register`, (req, res, ctx) => {
    const { email, password, firstname, lastname } = req.body as any;
    
    // Validation scenarios
    if (!email || !password || !firstname || !lastname) {
      return res(
        ctx.status(422),
        ctx.json({
          detail: 'Validation failed',
          errors: {
            email: !email ? ['Email is required'] : [],
            password: !password ? ['Password is required'] : [],
            firstname: !firstname ? ['First name is required'] : [],
            lastname: !lastname ? ['Last name is required'] : [],
          }
        })
      );
    }
    
    if (email === 'existing@example.com') {
      return res(
        ctx.status(422),
        ctx.json({ detail: 'Email already registered' })
      );
    }
    
    if (password.length < 8) {
      return res(
        ctx.status(422),
        ctx.json({
          detail: 'Validation failed',
          errors: {
            password: ['Password must be at least 8 characters']
          }
        })
      );
    }
    
    return res(
      ctx.status(201),
      ctx.json({
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        token_type: 'bearer',
        user: { ...mockUsers.customer, email, firstname, lastname },
      })
    );
  }),

  // Token refresh with various scenarios
  rest.post(`${API_BASE_URL}/auth/refresh`, (req, res, ctx) => {
    const { refresh_token } = req.body as any;
    
    if (refresh_token === 'valid-refresh-token') {
      return res(
        ctx.status(200),
        ctx.json({
          access_token: 'new-access-token',
          token_type: 'bearer',
        })
      );
    }
    
    if (refresh_token === 'expired-refresh-token') {
      return res(
        ctx.status(401),
        ctx.json({ detail: 'Refresh token expired' })
      );
    }
    
    return res(
      ctx.status(401),
      ctx.json({ detail: 'Invalid refresh token' })
    );
  }),

  // Password reset flow
  rest.post(`${API_BASE_URL}/auth/forgot-password`, (req, res, ctx) => {
    const { email } = req.body as any;
    
    if (!email) {
      return res(
        ctx.status(422),
        ctx.json({ detail: 'Email is required' })
      );
    }
    
    return res(
      ctx.status(200),
      ctx.json({ message: 'Password reset email sent' })
    );
  }),

  rest.post(`${API_BASE_URL}/auth/reset-password`, (req, res, ctx) => {
    const { token, password } = req.body as any;
    
    if (!token || !password) {
      return res(
        ctx.status(422),
        ctx.json({ detail: 'Token and password are required' })
      );
    }
    
    if (token === 'invalid-token') {
      return res(
        ctx.status(400),
        ctx.json({ detail: 'Invalid or expired token' })
      );
    }
    
    return res(
      ctx.status(200),
      ctx.json({ message: 'Password reset successful' })
    );
  }),
];

// Enhanced product handlers with filtering and pagination
export const enhancedProductHandlers = [
  // Advanced product search and filtering
  rest.get(`${API_BASE_URL}/products`, (req, res, ctx) => {
    const page = parseInt(req.url.searchParams.get('page') || '1');
    const limit = parseInt(req.url.searchParams.get('limit') || '20');
    const category = req.url.searchParams.get('category');
    const search = req.url.searchParams.get('search');
    const sort = req.url.searchParams.get('sort') || 'name';
    const order = req.url.searchParams.get('order') || 'asc';
    const minPrice = parseFloat(req.url.searchParams.get('min_price') || '0');
    const maxPrice = parseFloat(req.url.searchParams.get('max_price') || '999999');
    
    let products = [mockProducts.simple, mockProducts.withVariants];
    
    // Apply filters
    if (category) {
      products = products.filter(p => p.category.toLowerCase() === category.toLowerCase());
    }
    
    if (search) {
      products = products.filter(p => 
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        p.description.toLowerCase().includes(search.toLowerCase())
      );
    }
    
    // Price filtering
    products = products.filter(p => p.price >= minPrice && p.price <= maxPrice);
    
    // Sorting
    products.sort((a, b) => {
      let aVal, bVal;
      switch (sort) {
        case 'price':
          aVal = a.price;
          bVal = b.price;
          break;
        case 'created_at':
          aVal = new Date(a.created_at).getTime();
          bVal = new Date(b.created_at).getTime();
          break;
        default:
          aVal = a.name.toLowerCase();
          bVal = b.name.toLowerCase();
      }
      
      if (order === 'desc') {
        return aVal < bVal ? 1 : -1;
      }
      return aVal > bVal ? 1 : -1;
    });
    
    // Pagination
    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    const paginatedProducts = products.slice(startIndex, endIndex);
    
    return res(
      ctx.status(200),
      ctx.json({
        items: paginatedProducts,
        total: products.length,
        page,
        limit,
        pages: Math.ceil(products.length / limit),
        has_next: endIndex < products.length,
        has_prev: page > 1,
      })
    );
  }),

  // Product recommendations
  rest.get(`${API_BASE_URL}/products/:id/recommendations`, (req, res, ctx) => {
    const { id } = req.params;
    const limit = parseInt(req.url.searchParams.get('limit') || '5');
    
    // Return related products (simplified)
    const recommendations = [mockProducts.simple, mockProducts.withVariants].slice(0, limit);
    
    return res(ctx.status(200), ctx.json(recommendations));
  }),

  // Product reviews
  rest.get(`${API_BASE_URL}/products/:id/reviews`, (req, res, ctx) => {
    const { id } = req.params;
    const page = parseInt(req.url.searchParams.get('page') || '1');
    const limit = parseInt(req.url.searchParams.get('limit') || '10');
    
    const mockReviews = [
      {
        id: '1',
        user: mockUsers.customer,
        rating: 5,
        comment: 'Great product!',
        created_at: '2023-01-01T00:00:00Z',
      },
      {
        id: '2',
        user: mockUsers.customer,
        rating: 4,
        comment: 'Good quality, fast shipping.',
        created_at: '2023-01-02T00:00:00Z',
      },
    ];
    
    return res(
      ctx.status(200),
      ctx.json({
        items: mockReviews,
        total: mockReviews.length,
        page,
        limit,
        pages: Math.ceil(mockReviews.length / limit),
      })
    );
  }),
];

// Enhanced error simulation handlers
export const enhancedErrorHandlers = [
  // Network timeout simulation
  rest.get(`${API_BASE_URL}/test/timeout`, (req, res, ctx) => {
    return res(
      ctx.delay(35000), // Longer than typical timeout
      ctx.status(200),
      ctx.json({ message: 'This should timeout' })
    );
  }),

  // Rate limiting simulation
  rest.get(`${API_BASE_URL}/test/rate-limit`, (req, res, ctx) => {
    return res(
      ctx.status(429),
      ctx.set('Retry-After', '60'),
      ctx.json({ 
        detail: 'Too many requests',
        retry_after: 60 
      })
    );
  }),

  // Server maintenance simulation
  rest.get(`${API_BASE_URL}/test/maintenance`, (req, res, ctx) => {
    return res(
      ctx.status(503),
      ctx.json({ 
        detail: 'Service temporarily unavailable',
        maintenance: true 
      })
    );
  }),

  // Partial content simulation
  rest.get(`${API_BASE_URL}/test/partial`, (req, res, ctx) => {
    return res(
      ctx.status(206),
      ctx.set('Content-Range', 'bytes 0-499/1000'),
      ctx.json({ partial: true, data: 'partial content' })
    );
  }),
];

// Combine all enhanced handlers
export const enhancedHandlers = [
  ...enhancedAuthHandlers,
  ...enhancedProductHandlers,
  ...enhancedErrorHandlers,
];

export default enhancedHandlers;