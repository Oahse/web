/**
 * MSW (Mock Service Worker) Handlers
 * Provides API mocking for comprehensive testing
 */

import { rest } from 'msw';

const mockUsers = {
  customer: {
    id: '1',
    email: 'customer@test.com',
    firstname: 'John',
    lastname: 'Doe',
    role: 'Customer' as const,
    verified: true,
    phone: '+1234567890',
    created_at: '2023-01-01T00:00:00Z',
  },
  admin: {
    id: '2',
    email: 'admin@test.com',
    firstname: 'Admin',
    lastname: 'User',
    role: 'Admin' as const,
    verified: true,
    phone: '+1234567891',
    created_at: '2023-01-01T00:00:00Z',
  },
};

const mockProducts = {
  simple: {
    id: '1',
    name: 'Test Product',
    description: 'A test product for testing',
    price: 29.99,
    category: 'Electronics',
    brand: 'TestBrand',
    sku: 'TEST-001',
    stock_quantity: 100,
    is_active: true,
    images: ['https://example.com/image1.jpg'],
    variants: [],
    created_at: '2023-01-01T00:00:00Z',
  },
  withVariants: {
    id: '2',
    name: 'Variable Product',
    description: 'A product with variants',
    price: 49.99,
    category: 'Clothing',
    brand: 'TestBrand',
    sku: 'VAR-001',
    stock_quantity: 50,
    is_active: true,
    images: ['https://example.com/image2.jpg'],
    variants: [
      {
        id: '1',
        name: 'Small Red',
        price: 49.99,
        sku: 'VAR-001-SM-RED',
        stock_quantity: 10,
        attributes: { size: 'Small', color: 'Red' },
      },
    ],
    created_at: '2023-01-01T00:00:00Z',
  },
};

const API_BASE_URL = 'http://localhost:8000/v1';

// Auth handlers
export const authHandlers = [
  // Login
  rest.post(`${API_BASE_URL}/auth/login`, (req, res, ctx) => {
    const { email, password } = req.body as any;
    
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
    
    return res(
      ctx.status(401),
      ctx.json({ detail: 'Invalid credentials' })
    );
  }),

  // Register
  rest.post(`${API_BASE_URL}/auth/register`, (req, res, ctx) => {
    const { email } = req.body as any;
    
    if (email === 'existing@example.com') {
      return res(
        ctx.status(422),
        ctx.json({ detail: 'Email already registered' })
      );
    }
    
    return res(
      ctx.status(201),
      ctx.json({
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        token_type: 'bearer',
        user: { ...mockUsers.customer, email },
      })
    );
  }),

  // Refresh token
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
    
    return res(
      ctx.status(401),
      ctx.json({ detail: 'Invalid refresh token' })
    );
  }),

  // Logout
  rest.post(`${API_BASE_URL}/auth/logout`, (req, res, ctx) => {
    return res(ctx.status(200), ctx.json({ message: 'Logged out successfully' }));
  }),

  // Get current user
  rest.get(`${API_BASE_URL}/users/me`, (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res(
        ctx.status(401),
        ctx.json({ detail: 'Not authenticated' })
      );
    }
    
    return res(ctx.status(200), ctx.json(mockUsers.customer));
  }),
];

// Product handlers
export const productHandlers = [
  // Get products
  rest.get(`${API_BASE_URL}/products`, (req, res, ctx) => {
    const page = parseInt(req.url.searchParams.get('page') || '1');
    const limit = parseInt(req.url.searchParams.get('limit') || '20');
    const category = req.url.searchParams.get('category');
    const search = req.url.searchParams.get('search');
    
    let products = [mockProducts.simple, mockProducts.withVariants];
    
    // Filter by category
    if (category) {
      products = products.filter(p => p.category.toLowerCase() === category.toLowerCase());
    }
    
    // Filter by search
    if (search) {
      products = products.filter(p => 
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        p.description.toLowerCase().includes(search.toLowerCase())
      );
    }
    
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
      })
    );
  }),

  // Get single product
  rest.get(`${API_BASE_URL}/products/:id`, (req, res, ctx) => {
    const { id } = req.params;
    const product = id === '1' ? mockProducts.simple : mockProducts.withVariants;
    
    if (!product) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Product not found' })
      );
    }
    
    return res(ctx.status(200), ctx.json(product));
  }),

  // Get featured products
  rest.get(`${API_BASE_URL}/products/featured`, (req, res, ctx) => {
    const limit = parseInt(req.url.searchParams.get('limit') || '10');
    const products = [mockProducts.simple, mockProducts.withVariants].slice(0, limit);
    
    return res(ctx.status(200), ctx.json(products));
  }),

  // Search products
  rest.get(`${API_BASE_URL}/products/search`, (req, res, ctx) => {
    const query = req.url.searchParams.get('q') || '';
    const products = [mockProducts.simple, mockProducts.withVariants].filter(p =>
      p.name.toLowerCase().includes(query.toLowerCase())
    );
    
    return res(ctx.status(200), ctx.json(products));
  }),
];

// Cart handlers
export const cartHandlers = [
  // Get cart
  rest.get(`${API_BASE_URL}/cart`, (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    
    if (!authHeader) {
      return res(
        ctx.status(401),
        ctx.json({ detail: 'Not authenticated' })
      );
    }
    
    return res(
      ctx.status(200),
      ctx.json({
        id: '1',
        items: [
          {
            id: '1',
            product: mockProducts.simple,
            variant_id: null,
            quantity: 2,
            price: mockProducts.simple.price,
            total: mockProducts.simple.price * 2,
          },
        ],
        total_items: 2,
        total_price: mockProducts.simple.price * 2,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z',
      })
    );
  }),

  // Add to cart
  rest.post(`${API_BASE_URL}/cart/items`, (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    
    if (!authHeader) {
      return res(
        ctx.status(401),
        ctx.json({ detail: 'Not authenticated' })
      );
    }
    
    const { variant_id, quantity } = req.body as any;
    
    return res(
      ctx.status(201),
      ctx.json({
        id: '2',
        product: mockProducts.simple,
        variant_id,
        quantity,
        price: mockProducts.simple.price,
        total: mockProducts.simple.price * quantity,
      })
    );
  }),

  // Update cart item
  rest.put(`${API_BASE_URL}/cart/items/:id`, (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    
    if (!authHeader) {
      return res(
        ctx.status(401),
        ctx.json({ detail: 'Not authenticated' })
      );
    }
    
    const { quantity } = req.body as any;
    
    return res(
      ctx.status(200),
      ctx.json({
        id: req.params.id,
        product: mockProducts.simple,
        variant_id: null,
        quantity,
        price: mockProducts.simple.price,
        total: mockProducts.simple.price * quantity,
      })
    );
  }),

  // Remove from cart
  rest.delete(`${API_BASE_URL}/cart/items/:id`, (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    
    if (!authHeader) {
      return res(
        ctx.status(401),
        ctx.json({ detail: 'Not authenticated' })
      );
    }
    
    return res(ctx.status(204));
  }),

  // Clear cart
  rest.delete(`${API_BASE_URL}/cart`, (req, res, ctx) => {
    const authHeader = req.headers.get('Authorization');
    
    if (!authHeader) {
      return res(
        ctx.status(401),
        ctx.json({ detail: 'Not authenticated' })
      );
    }
    
    return res(ctx.status(204));
  }),
];

// Category handlers
export const categoryHandlers = [
  // Get categories
  rest.get(`${API_BASE_URL}/categories`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
        {
          id: '1',
          name: 'Electronics',
          slug: 'electronics',
          description: 'Electronic devices and gadgets',
          image: 'https://example.com/electronics.jpg',
          product_count: 150,
        },
        {
          id: '2',
          name: 'Clothing',
          slug: 'clothing',
          description: 'Fashion and apparel',
          image: 'https://example.com/clothing.jpg',
          product_count: 200,
        },
      ])
    );
  }),

  // Get single category
  rest.get(`${API_BASE_URL}/categories/:id`, (req, res, ctx) => {
    const { id } = req.params;
    
    const categories = {
      '1': {
        id: '1',
        name: 'Electronics',
        slug: 'electronics',
        description: 'Electronic devices and gadgets',
        image: 'https://example.com/electronics.jpg',
        product_count: 150,
      },
      '2': {
        id: '2',
        name: 'Clothing',
        slug: 'clothing',
        description: 'Fashion and apparel',
        image: 'https://example.com/clothing.jpg',
        product_count: 200,
      },
    };
    
    const category = categories[id as keyof typeof categories];
    
    if (!category) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Category not found' })
      );
    }
    
    return res(ctx.status(200), ctx.json(category));
  }),
];

// Error simulation handlers
export const errorHandlers = [
  // Simulate server error
  rest.get(`${API_BASE_URL}/test/server-error`, (req, res, ctx) => {
    return res(
      ctx.status(500),
      ctx.json({ detail: 'Internal server error' })
    );
  }),

  // Simulate network timeout
  rest.get(`${API_BASE_URL}/test/timeout`, (req, res, ctx) => {
    return res(
      ctx.delay(35000), // Longer than typical timeout
      ctx.status(200),
      ctx.json({ message: 'This should timeout' })
    );
  }),

  // Simulate rate limiting
  rest.get(`${API_BASE_URL}/test/rate-limit`, (req, res, ctx) => {
    return res(
      ctx.status(429),
      ctx.json({ detail: 'Too many requests' })
    );
  }),
];

// GitHub API handlers
export const githubHandlers = [
  // Get file content (for checking if file exists)
  rest.get('https://api.github.com/repos/:owner/:repo/contents/:path*', (req, res, ctx) => {
    const { path } = req.params;
    
    // Simulate file not found for new files
    if (path?.toString().includes('new-file')) {
      return res(
        ctx.status(404),
        ctx.json({ message: 'Not Found' })
      );
    }
    
    // Simulate existing file
    return res(
      ctx.status(200),
      ctx.json({
        name: 'existing-file.png',
        path: 'products/existing-file.png',
        sha: 'existing-sha-123',
        size: 1024,
        url: 'https://api.github.com/repos/test/test/contents/products/existing-file.png',
        html_url: 'https://github.com/test/test/blob/main/products/existing-file.png',
        git_url: 'https://api.github.com/repos/test/test/git/blobs/existing-sha-123',
        download_url: 'https://raw.githubusercontent.com/test/test/main/products/existing-file.png',
        type: 'file',
        content: 'base64-encoded-content',
        encoding: 'base64',
      })
    );
  }),

  // Create or update file
  rest.put('https://api.github.com/repos/:owner/:repo/contents/:path*', (req, res, ctx) => {
    const { path } = req.params;
    const body = req.body as any;
    
    return res(
      ctx.status(201),
      ctx.json({
        content: {
          name: path?.toString().split('/').pop() || 'file.png',
          path: path?.toString() || 'products/file.png',
          sha: 'new-sha-456',
          size: 2048,
          url: `https://api.github.com/repos/test/test/contents/${path}`,
          html_url: `https://github.com/test/test/blob/main/${path}`,
          git_url: 'https://api.github.com/repos/test/test/git/blobs/new-sha-456',
          download_url: `https://raw.githubusercontent.com/test/test/main/${path}`,
          type: 'file',
        },
        commit: {
          sha: 'commit-sha-789',
          url: 'https://api.github.com/repos/test/test/git/commits/commit-sha-789',
          html_url: 'https://github.com/test/test/commit/commit-sha-789',
          author: {
            name: 'Test User',
            email: 'test@example.com',
            date: '2023-01-01T00:00:00Z',
          },
          committer: {
            name: 'Test User',
            email: 'test@example.com',
            date: '2023-01-01T00:00:00Z',
          },
          message: body.message || 'Upload file',
        },
      })
    );
  }),

  // Delete file
  rest.delete('https://api.github.com/repos/:owner/:repo/contents/:path*', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        content: null,
        commit: {
          sha: 'delete-commit-sha',
          url: 'https://api.github.com/repos/test/test/git/commits/delete-commit-sha',
          html_url: 'https://github.com/test/test/commit/delete-commit-sha',
          author: {
            name: 'Test User',
            email: 'test@example.com',
            date: '2023-01-01T00:00:00Z',
          },
          committer: {
            name: 'Test User',
            email: 'test@example.com',
            date: '2023-01-01T00:00:00Z',
          },
          message: 'Delete file',
        },
      })
    );
  }),
];

// Combine all handlers
export const handlers = [
  ...authHandlers,
  ...productHandlers,
  ...cartHandlers,
  ...categoryHandlers,
  ...errorHandlers,
  ...githubHandlers,
];