// frontend/src/components/dashboard/DashboardLayout.test.tsx
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vitest, beforeEach } from 'vitest';
import { DashboardLayout } from './DashboardLayout';
import { useAuth } from '../../store/AuthContext';
import { DashboardSkeleton } from '../ui/SkeletonDashboard'; // Assuming this exists or is created
import { Button } from '../ui/Button'; // Mocked button
import {
  BarChart3Icon, UsersIcon, ShoppingCartIcon, DollarSignIcon,
  TrendingUpIcon, AlertCircleIcon, RefreshCwIcon, SettingsIcon,
  DownloadIcon, FilterIcon
} from 'lucide-react'; // Mocked icons

// --- Mock external dependencies ---
vitest.mock('../../contexts/AuthContext', () => ({
  useAuth: vitest.fn(),
}));

vitest.mock('../ui/SkeletonDashboard', () => ({
  DashboardSkeleton: vitest.fn(() => <div data-testid="mock-dashboard-skeleton">Dashboard Loading Skeleton</div>),
}));

vitest.mock('../ui/Button', () => ({
  Button: vitest.fn((props) => (
    <button {...props} data-testid={`mock-button-${props.children?.toString().replace(/\s/g, '-').toLowerCase()}`}>
      {props.children}
    </button>
  )),
}));

// Mock lucide-react icons
vitest.mock('lucide-react', () => ({
  BarChart3Icon: vitest.fn(() => <svg data-testid="icon-bar-chart" />),
  UsersIcon: vitest.fn(() => <svg data-testid="icon-users" />),
  ShoppingCartIcon: vitest.fn(() => <svg data-testid="icon-shopping-cart" />),
  DollarSignIcon: vitest.fn(() => <svg data-testid="icon-dollar-sign" />),
  TrendingUpIcon: vitest.fn(() => <svg data-testid="icon-trending-up" />),
  AlertCircleIcon: vitest.fn(() => <svg data-testid="icon-alert-circle" />),
  RefreshCwIcon: vitest.fn(() => <svg data-testid="icon-refresh-cw" />),
  SettingsIcon: vitest.fn(() => <svg data-testid="icon-settings" />),
  DownloadIcon: vitest.fn(() => <svg data-testid="icon-download" />),
  FilterIcon: vitest.fn(() => <svg data-testid="icon-filter" />),
}));


// Mock the DashboardWidgetComponent to control its behavior for DashboardLayout tests
const MockDashboardWidgetComponent = vitest.fn(({ widget, onRefresh, onExport, refreshing }) => (
  <div data-testid={`widget-component-${widget.id}`}>
    <h3>{widget.title}</h3>
    {widget.refreshable && (
      <button onClick={onRefresh} disabled={refreshing} data-testid={`refresh-btn-${widget.id}`}>
        Refresh {refreshing && '(Spinning)'}
      </button>
    )}
    {widget.exportable && (
      <button onClick={() => onExport('csv')} data-testid={`export-btn-${widget.id}-csv`}>
        Export CSV
      </button>
    )}
    <div data-testid={`widget-content-${widget.id}`}>{widget.data.value || 'Content'}</div>
  </div>
));
// Manually add the mocked component to the module
vitest.mock('react', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    __esModule: true,
    default: { ...actual.default }, // Keep other React exports
    // @ts-ignore
    memo: (Component) => Component, // Bypass React.memo for testing simplicity
  };
});
// Need to re-mock DashboardWidgetComponent because it's defined in the same file
const originalDashboardWidgetComponent = vitest.hoisted(() => {
  return vitest.fn(({ widget, onRefresh, onExport, refreshing }) => (
    <div data-testid={`widget-component-${widget.id}`}>
      <h3>{widget.title}</h3>
      {widget.refreshable && (
        <button onClick={onRefresh} disabled={refreshing} data-testid={`refresh-btn-${widget.id}`}>
          Refresh {refreshing && '(Spinning)'}
        </button>
      )}
      {widget.exportable && (
        <button onClick={() => onExport('csv')} data-testid={`export-btn-${widget.id}-csv`}>
          Export CSV
        </button>
      )}
      <div data-testid={`widget-content-${widget.id}`}>{widget.data.value || 'Content'}</div>
    </div>
  ));
});

vitest.mock('./DashboardLayout', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    DashboardWidgetComponent: originalDashboardWidgetComponent, // Use the hoisted mock
  };
});



describe('DashboardLayout Component', () => {
  const mockUseAuth = useAuth as vitest.Mock;
  const mockDashboardSkeleton = DashboardSkeleton as vitest.Mock;
  const mockButton = Button as vitest.Mock;
  const mockDashboardWidgetComponent = originalDashboardWidgetComponent; // Access the hoisted mock

  const mockWidgets = [
    { id: 'widget-1', title: 'Total Sales', type: 'metric', data: { value: 1000 }, refreshable: true, exportable: true },
    { id: 'widget-2', title: 'Top Products', type: 'table', data: { value: 'Product List' }, refreshable: false, exportable: true },
    { id: 'widget-3', title: 'User Activity', type: 'chart', data: { value: 'Chart Data' }, refreshable: true, exportable: false },
    { id: 'supplier-widget', title: 'Supplier Specific', type: 'metric', data: { value: 500 } },
    { id: 'customer-widget', title: 'Customer Specific', type: 'metric', data: { value: 200 } },
  ];

  const mockOnRefresh = vitest.fn();
  const mockOnExport = vitest.fn();

  beforeEach(() => {
    vitest.clearAllMocks();
    mockUseAuth.mockReturnValue({ user: { role: 'Admin' } }); // Default to Admin
    mockDashboardSkeleton.mockReturnValue(<div data-testid="mock-dashboard-skeleton"></div>);
    mockButton.mockImplementation((props) => <button {...props} data-testid={`mock-button-${props.children?.toString().replace(/\s/g, '-').toLowerCase()}`}>{props.children}</button>);
  });

  it('renders title and last updated time', () => {
    vitest.useFakeTimers();
    const now = new Date();
    vitest.setSystemTime(now);

    render(<DashboardLayout title="My Dashboard" widgets={mockWidgets} />);
    expect(screen.getByText('My Dashboard')).toBeInTheDocument();
    expect(screen.getByText(`Last updated: ${now.toLocaleTimeString()}`)).toBeInTheDocument();
    vitest.useRealTimers();
  });

  it('renders DashboardSkeleton when loading is true', () => {
    render(<DashboardLayout title="My Dashboard" widgets={mockWidgets} loading={true} />);
    expect(screen.getByTestId('mock-dashboard-skeleton')).toBeInTheDocument();
    expect(screen.queryByTestId('widget-component-widget-1')).not.toBeInTheDocument();
  });

  it('renders DashboardWidgetComponent for each widget when not loading', () => {
    render(<DashboardLayout title="My Dashboard" widgets={mockWidgets} />);
    expect(screen.queryByTestId('mock-dashboard-skeleton')).not.toBeInTheDocument();
    expect(screen.getByTestId('widget-component-widget-1')).toBeInTheDocument();
    expect(screen.getByTestId('widget-component-widget-2')).toBeInTheDocument();
    expect(screen.getByTestId('widget-component-widget-3')).toBeInTheDocument();
  });

  it('calls onRefresh when "Refresh All" button is clicked', async () => {
    render(<DashboardLayout title="My Dashboard" widgets={mockWidgets} onRefresh={mockOnRefresh} />);
    const refreshAllButton = screen.getByTestId('mock-button-refresh-all');
    fireEvent.click(refreshAllButton);
    expect(mockOnRefresh).toHaveBeenCalledWith(undefined); // undefined signifies refresh all
  });

  it('shows spinning icon on "Refresh All" when refreshing', async () => {
    mockOnRefresh.mockImplementation(async () => {
      await new Promise(resolve => setTimeout(resolve, 100)); // Simulate async work
    });
    const { rerender } = render(<DashboardLayout title="My Dashboard" widgets={mockWidgets} onRefresh={mockOnRefresh} />);
    fireEvent.click(screen.getByTestId('mock-button-refresh-all'));
    // Before promise resolves, should show spinning
    expect(screen.getByTestId('icon-refresh-cw')).toHaveClass('animate-spin');
    // After promise resolves, should stop spinning
    await act(async () => {
      vitest.runAllTimers(); // Advance timers to resolve the promise
    });
    expect(screen.getByTestId('icon-refresh-cw')).not.toHaveClass('animate-spin');
  });

  it('calls onRefresh with widget id when individual widget refresh button is clicked', () => {
    render(<DashboardLayout title="My Dashboard" widgets={mockWidgets} onRefresh={mockOnRefresh} />);
    fireEvent.click(screen.getByTestId('refresh-btn-widget-1'));
    expect(mockOnRefresh).toHaveBeenCalledWith('widget-1');
  });

  it('calls onExport with widget id and format when individual widget export button is clicked', () => {
    render(<DashboardLayout title="My Dashboard" widgets={mockWidgets} onExport={mockOnExport} />);
    fireEvent.click(screen.getByTestId('export-btn-widget-1-csv'));
    expect(mockOnExport).toHaveBeenCalledWith('widget-1', 'csv');
  });

  it('filters widgets for "Customer" role', () => {
    mockUseAuth.mockReturnValue({ user: { role: 'Customer' } });
    render(<DashboardLayout title="Customer View" widgets={mockWidgets} />);
    expect(screen.queryByTestId('widget-component-widget-1')).not.toBeInTheDocument(); // generic widget
    expect(screen.getByTestId('widget-component-customer-widget')).toBeInTheDocument();
    expect(screen.queryByTestId('widget-component-supplier-widget')).not.toBeInTheDocument();
  });

  it('filters widgets for "Supplier" role', () => {
    mockUseAuth.mockReturnValue({ user: { role: 'Supplier' } });
    render(<DashboardLayout title="Supplier View" widgets={mockWidgets} />);
    expect(screen.queryByTestId('widget-component-widget-1')).not.toBeInTheDocument(); // generic widget
    expect(screen.queryByTestId('widget-component-customer-widget')).not.toBeInTheDocument();
    expect(screen.getByTestId('widget-component-supplier-widget')).toBeInTheDocument();
  });

  it('renders the real-time updates indicator', () => {
    render(<DashboardLayout title="My Dashboard" widgets={[]} />);
    expect(screen.getByText('Live Updates')).toBeInTheDocument();
  });
});
