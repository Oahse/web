// frontend/src/components/ui/ComplexSkeletons.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vitest } from 'vitest';
import { Skeleton } from './Skeleton'; // Import base Skeleton to mock
import { CartSkeleton } from './CartSkeleton'; // Already has its own test, but listed for context
import { SkeletonCard } from './SkeletonCard';
import { SkeletonDashboard } from './SkeletonDashboard';
import { SkeletonForm } from './SkeletonForm';
import { SkeletonNavigation } from './SkeletonNavigation';
import { SkeletonProductCard } from './SkeletonProductCard';
import { SkeletonTable } from './SkeletonTable';

// Mock the base Skeleton component to simplify testing complex skeletons
// We assume Skeleton.test.tsx covers its internal logic.
vitest.mock('./Skeleton', () => ({
  Skeleton: vitest.fn((props) => <div data-testid="skeleton-base" {...props} />),
  SkeletonText: vitest.fn((props) => <div data-testid="skeleton-text" {...props} />),
  SkeletonRectangle: vitest.fn((props) => <div data-testid="skeleton-rectangle" {...props} />),
  SkeletonCircle: vitest.fn((props) => <div data-testid="skeleton-circle" {...props} />),
}));


describe('Complex Skeleton Components', () => {
  beforeEach(() => {
    vitest.clearAllMocks();
  });

  // --- SkeletonCard ---
  describe('SkeletonCard', () => {
    it('renders with product variant by default', () => {
      render(<SkeletonCard />);
      expect(screen.getByRole('status', { name: 'Loading product...' })).toBeInTheDocument();
      expect(screen.getByTestId('skeleton-rectangle')).toBeInTheDocument(); // Image placeholder
      expect(screen.getAllByTestId('skeleton-text').length).toBeGreaterThan(0); // Text placeholders
      expect(screen.getByTestId('skeleton-circle')).toBeInTheDocument(); // Rating placeholder
    });

    it('hides image when showImage is false', () => {
      render(<SkeletonCard showImage={false} />);
      expect(screen.queryByText('Image placeholder')).not.toBeInTheDocument(); // Assuming no specific text
      expect(screen.queryByTestId('skeleton-rectangle')).not.toHaveBeenCalledWith(expect.objectContaining({ height: '200px' }));
    });

    it('renders user variant correctly', () => {
      render(<SkeletonCard variant="user" />);
      expect(screen.getByRole('status', { name: 'Loading user...' })).toBeInTheDocument();
      expect(screen.getByTestId('skeleton-circle')).toBeInTheDocument(); // Avatar placeholder
      expect(screen.getAllByTestId('skeleton-text').length).toBeGreaterThan(0); // Name/email placeholders
    });
  });

  // --- SkeletonDashboard ---
  describe('SkeletonDashboard', () => {
    it('renders with mixed layout by default', () => {
      render(<SkeletonDashboard />);
      expect(screen.getByRole('status', { name: 'Loading dashboard...' })).toBeInTheDocument();
      // Check for some characteristic sub-components
      expect(screen.getAllByTestId('skeleton-text').length).toBeGreaterThan(5);
      expect(screen.getAllByTestId('skeleton-rectangle').length).toBeGreaterThan(5);
      expect(screen.getAllByTestId('skeleton-circle').length).toBeGreaterThan(2);
    });

    it('renders metrics cards when showMetrics is true', () => {
      render(<SkeletonDashboard showMetrics={true} showCharts={false} showTables={false} />);
      expect(screen.getByRole('status', { name: 'Loading dashboard...' })).toBeInTheDocument();
      expect(screen.getAllByTestId('skeleton-text').length).toBeGreaterThan(4); // Metrics have text
      expect(screen.getAllByTestId('skeleton-rectangle').length).toBeGreaterThan(4);
      expect(screen.getAllByTestId('skeleton-circle').length).toBeGreaterThan(4); // 4 metrics cards, each with a circle
    });

    it('renders charts when showCharts is true', () => {
      render(<SkeletonDashboard showCharts={true} showMetrics={false} showTables={false} />);
      expect(screen.getByTestId('skeleton-rectangle')).toHaveBeenCalledWith(expect.objectContaining({ height: '200px' })); // Chart placeholder
    });
  });

  // --- SkeletonForm ---
  describe('SkeletonForm', () => {
    it('renders default vertical form with specified fields', () => {
      render(<SkeletonForm fields={3} />);
      expect(screen.getByRole('status', { name: 'Loading form...' })).toBeInTheDocument();
      expect(screen.getAllByTestId('skeleton-text').length).toBe(3); // Labels
      expect(screen.getAllByTestId('skeleton-rectangle').length).toBe(3); // Input fields
    });

    it('renders horizontal layout correctly', () => {
      render(<SkeletonForm fields={2} layout="horizontal" />);
      expect(screen.getByRole('status', { name: 'Loading form...' })).toBeInTheDocument();
      expect(screen.getAllByTestId('skeleton-text').length).toBe(2);
      expect(screen.getAllByTestId('skeleton-rectangle').length).toBe(2);
    });

    it('renders buttons when showButtons is true', () => {
      render(<SkeletonForm showButtons={true} />);
      expect(screen.getAllByTestId('skeleton-rectangle').length).toBeGreaterThan(3); // Should include button placeholders
    });
  });

  // --- SkeletonNavigation ---
  describe('SkeletonNavigation', () => {
    it('renders header variant by default', () => {
      render(<SkeletonNavigation />);
      expect(screen.getByRole('status', { name: 'Loading navigation...' })).toBeInTheDocument();
      expect(screen.getAllByTestId('skeleton-text').length).toBeGreaterThan(0); // Menu items
      expect(screen.getAllByTestId('skeleton-rectangle').length).toBeGreaterThan(0); // Logo, search
      expect(screen.getAllByTestId('skeleton-circle').length).toBeGreaterThan(0); // Profile, user avatar
    });

    it('renders sidebar variant correctly', () => {
      render(<SkeletonNavigation variant="sidebar" />);
      expect(screen.getByRole('status', { name: 'Loading sidebar...' })).toBeInTheDocument();
      expect(screen.getAllByTestId('skeleton-text').length).toBeGreaterThan(0);
      expect(screen.getAllByTestId('skeleton-circle').length).toBeGreaterThan(0);
    });

    it('hides logo when showLogo is false for header variant', () => {
      render(<SkeletonNavigation variant="header" showLogo={false} />);
      expect(screen.queryAllByTestId('skeleton-rectangle')).not.toHaveBeenCalledWith(expect.objectContaining({ width: '120px', height: '32px' })); // Assuming this is the logo size
    });
  });

  // --- SkeletonProductCard ---
  describe('SkeletonProductCard', () => {
    it('renders a product card skeleton', () => {
      render(<SkeletonProductCard />);
      expect(screen.getByRole('status', { name: 'Loading content...' })).toBeInTheDocument(); // Base Skeleton role
      expect(screen.getAllByTestId('skeleton-rectangle').length).toBeGreaterThan(0); // Image, price
      expect(screen.getAllByTestId('skeleton-text').length).toBeGreaterThan(0); // Title, description
      expect(screen.getByTestId('skeleton-circle')).toBeInTheDocument(); // Cart button
    });
  });

  // --- SkeletonTable ---
  describe('SkeletonTable', () => {
    it('renders a default table skeleton with header and data rows', () => {
      render(<SkeletonTable rows={3} columns={3} />);
      expect(screen.getByRole('status', { name: 'Loading table...' })).toBeInTheDocument();
      expect(screen.getAllByTestId('skeleton-text').length).toBeGreaterThan(3 * 3); // Headers + cells
      expect(screen.queryAllByTestId('skeleton-rectangle')).not.toHaveBeenCalledWith(expect.objectContaining({ width: '24px', height: '24px' })); // No actions by default
    });

    it('renders with actions when showActions is true', () => {
      render(<SkeletonTable rows={1} columns={2} showActions={true} />);
      expect(screen.getAllByTestId('skeleton-rectangle').length).toBeGreaterThan(0); // Should include action button placeholders
    });

    it('renders detailed variant correctly', () => {
      render(<SkeletonTable rows={1} variant="detailed" />);
      expect(screen.getByRole('status', { name: 'Loading table...' })).toBeInTheDocument();
      expect(screen.getByTestId('skeleton-circle')).toBeInTheDocument(); // Avatar in detailed row
      expect(screen.getAllByTestId('skeleton-text').length).toBeGreaterThan(0);
    });
  });
});
