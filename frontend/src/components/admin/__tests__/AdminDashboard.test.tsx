import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { AdminDashboard } from '../AdminDashboard';
import { AuthContext } from '../../../contexts/AuthContext';
import { BrowserRouter } from 'react-router-dom';

// Mock the APIs
vi.mock('../../../apis/admin', () => ({
  default: {
    getDashboardStats: vi.fn(),
    getRecentOrders: vi.fn(),
    getRevenueChart: vi.fn(),
  },
}));

vi.mock('../../../apis/analytics', () => ({
  default: {
    getOverviewStats: vi.fn(),
    getSalesData: vi.fn(),
  },
}));

describe('AdminDashboard Component', () => {
  const mockAdminUser = {
    id: '1',
    email: 'admin@example.com',
    firstname: 'Admin',
    lastname: 'User',
    role: 'Admin',
    is_active: true,
    is_verified: true,
    created_at: '2023-01-01T00:00:00Z',
  };

  const mockAuthContext = {
    user: mockAdminUser,
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    updateUser: vi.fn(),
  };

  const mockDashboardStats = {
    total_revenue: 125000,
    total_orders: 1250,
    total_users: 5000,
    total_products: 150,
    revenue_growth: 12.5,
    orders_growth: 8.3,
    users_growth: 15.2,
    products_growth: 5.1,
  };

  const mockRecentOrders = [
    {
      id: '1',
      order_number: 'ORD-001',
      user: { firstname: 'John', lastname: 'Doe' },
      total_amount: 99.99,
      status: 'completed',
      created_at: '2023-12-01T10:00:00Z',
    },
    {
      id: '2',
      order_number: 'ORD-002',
      user: { firstname: 'Jane', lastname: 'Smith' },
      total_amount: 149.99,
      status: 'processing',
      created_at: '2023-12-01T11:00:00Z',
    },
  ];

  const renderWithProviders = (component: React.ReactElement) => {
    return render(
      <BrowserRouter>
        <AuthContext.Provider value={mockAuthContext}>
          {component}
        </AuthContext.Provider>
      </BrowserRouter>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard with loading state initially', () => {
    renderWithProviders(<AdminDashboard />);

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('displays dashboard statistics after loading', async () => {
    const { AdminAPI } = await import('../../../apis/admin');
    (AdminAPI.getDashboardStats as any).mockResolvedValue({
      success: true,
      data: mockDashboardStats,
    });
    (AdminAPI.getRecentOrders as any).mockResolvedValue({
      success: true,
      data: mockRecentOrders,
    });

    renderWithProviders(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('$125,000')).toBeInTheDocument();
      expect(screen.getByText('1,250')).toBeInTheDocument();
      expect(screen.getByText('5,000')).toBeInTheDocument();
      expect(screen.getByText('150')).toBeInTheDocument();
    });
  });

  it('displays growth percentages', async () => {
    const { AdminAPI } = await import('../../../apis/admin');
    (AdminAPI.getDashboardStats as any).mockResolvedValue({
      success: true,
      data: mockDashboardStats,
    });
    (AdminAPI.getRecentOrders as any).mockResolvedValue({
      success: true,
      data: mockRecentOrders,
    });

    renderWithProviders(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('+12.5%')).toBeInTheDocument();
      expect(screen.getByText('+8.3%')).toBeInTheDocument();
      expect(screen.getByText('+15.2%')).toBeInTheDocument();
      expect(screen.getByText('+5.1%')).toBeInTheDocument();
    });
  });

  it('displays recent orders', async () => {
    const { AdminAPI } = await import('../../../apis/admin');
    (AdminAPI.getDashboardStats as any).mockResolvedValue({
      success: true,
      data: mockDashboardStats,
    });
    (AdminAPI.getRecentOrders as any).mockResolvedValue({
      success: true,
      data: mockRecentOrders,
    });

    renderWithProviders(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('ORD-001')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('$99.99')).toBeInTheDocument();
      expect(screen.getByText('ORD-002')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      expect(screen.getByText('$149.99')).toBeInTheDocument();
    });
  });

  it('displays order status badges', async () => {
    const { AdminAPI } = await import('../../../apis/admin');
    (AdminAPI.getDashboardStats as any).mockResolvedValue({
      success: true,
      data: mockDashboardStats,
    });
    (AdminAPI.getRecentOrders as any).mockResolvedValue({
      success: true,
      data: mockRecentOrders,
    });

    renderWithProviders(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Completed')).toBeInTheDocument();
      expect(screen.getByText('Processing')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    const { AdminAPI } = await import('../../../apis/admin');
    (AdminAPI.getDashboardStats as any).mockRejectedValue({
      message: 'Failed to load dashboard data',
    });

    renderWithProviders(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load dashboard data')).toBeInTheDocument();
    });
  });

  it('shows empty state when no recent orders', async () => {
    const { AdminAPI } = await import('../../../apis/admin');
    (AdminAPI.getDashboardStats as any).mockResolvedValue({
      success: true,
      data: mockDashboardStats,
    });
    (AdminAPI.getRecentOrders as any).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('No recent orders')).toBeInTheDocument();
    });
  });

  it('formats large numbers correctly', async () => {
    const largeStats = {
      ...mockDashboardStats,
      total_revenue: 1250000,
      total_users: 50000,
    };

    const { AdminAPI } = await import('../../../apis/admin');
    (AdminAPI.getDashboardStats as any).mockResolvedValue({
      success: true,
      data: largeStats,
    });
    (AdminAPI.getRecentOrders as any).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('$1,250,000')).toBeInTheDocument();
      expect(screen.getByText('50,000')).toBeInTheDocument();
    });
  });

  it('displays negative growth correctly', async () => {
    const negativeGrowthStats = {
      ...mockDashboardStats,
      revenue_growth: -5.2,
      orders_growth: -2.1,
    };

    const { AdminAPI } = await import('../../../apis/admin');
    (AdminAPI.getDashboardStats as any).mockResolvedValue({
      success: true,
      data: negativeGrowthStats,
    });
    (AdminAPI.getRecentOrders as any).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<AdminDashboard />);

    await waitFor(() => {
      expect(screen.getByText('-5.2%')).toBeInTheDocument();
      expect(screen.getByText('-2.1%')).toBeInTheDocument();
    });
  });

  it('refreshes data when refresh button is clicked', async () => {
    const { AdminAPI } = await import('../../../apis/admin');
    (AdminAPI.getDashboardStats as any).mockResolvedValue({
      success: true,
      data: mockDashboardStats,
    });
    (AdminAPI.getRecentOrders as any).mockResolvedValue({
      success: true,
      data: mockRecentOrders,
    });

    renderWithProviders(<AdminDashboard />);

    await waitFor(() => {
      expect(AdminAPI.getDashboardStats).toHaveBeenCalledTimes(1);
    });

    const refreshButton = screen.getByLabelText('Refresh dashboard');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(AdminAPI.getDashboardStats).toHaveBeenCalledTimes(2);
    });
  });
});