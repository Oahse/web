// frontend/src/components/dashboard/widgets/CustomizableDashboard.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vitest, beforeEach, afterEach } from 'vitest';
import { CustomizableDashboard } from './CustomizableDashboard';

// --- Mock external dependencies ---
// Mock react-grid-layout and react-resizable
vitest.mock('react-grid-layout', () => ({
  Responsive: vitest.fn(({ children, onLayoutChange, layout, ...props }) => (
    <div data-testid="mock-responsive-grid-layout" {...props}>
      {children}
    </div>
  )),
  WidthProvider: vitest.fn((Component) => (props) => <Component {...props} />),
}));
vitest.mock('react-resizable/css/styles.css', () => ({ default: {} })); // Mock CSS import
vitest.mock('react-grid-layout/css/styles.css', () => ({ default: {} })); // Mock CSS import

// Mock lucide-react icons
vitest.mock('lucide-react', () => ({
  PlusIcon: vitest.fn(() => <svg data-testid="icon-plus" />),
  SettingsIcon: vitest.fn(() => <svg data-testid="icon-settings" />),
  TrashIcon: vitest.fn(() => <svg data-testid="icon-trash" />),
  GripVerticalIcon: vitest.fn(() => <svg data-testid="icon-grip-vertical" />),
  EditIcon: vitest.fn(() => <svg data-testid="icon-edit" />),
  SaveIcon: vitest.fn(() => <svg data-testid="icon-save" />),
  XIcon: vitest.fn(() => <svg data-testid="icon-x" />),
}));

describe('CustomizableDashboard Component', () => {
  const mockMetricWidget = vitest.fn(() => <div data-testid="mock-metric-widget">Metric Content</div>);
  const mockChartWidget = vitest.fn(() => <div data-testid="mock-chart-widget">Chart Content</div>);

  const mockWidgetTemplates = [
    {
      id: 'template-metric',
      name: 'Test Metric',
      description: 'A test metric widget',
      type: 'metric',
      component: mockMetricWidget,
      defaultProps: { value: 0, label: 'Units' },
      defaultLayout: { w: 2, h: 2, minW: 1, minH: 1 },
      icon: <svg data-testid="icon-template-metric" />,
      category: 'metrics',
    },
    {
      id: 'template-chart',
      name: 'Test Chart',
      description: 'A test chart widget',
      type: 'chart',
      component: mockChartWidget,
      defaultProps: { type: 'line' },
      defaultLayout: { w: 4, h: 3, minW: 2, minH: 2 },
      icon: <svg data-testid="icon-template-chart" />,
      category: 'charts',
    },
  ];

  const initialWidgets = [
    {
      id: 'widget-1',
      title: 'Initial Metric',
      type: 'metric',
      component: mockMetricWidget,
      props: { value: 100, label: 'Sales' },
      config: { showHeader: true, exportable: true, refreshInterval: 30000 },
      layout: { x: 0, y: 0, w: 2, h: 2 },
    },
  ];

  const mockOnWidgetsChange = vitest.fn();
  const mockOnSave = vitest.fn();

  beforeEach(() => {
    vitest.clearAllMocks();
    vitest.spyOn(Date, 'now').mockReturnValue(123456789);
    vitest.spyOn(Math, 'random').mockReturnValue(0.123456789);
  });

  afterEach(() => {
    vitest.restoreAllMocks();
  });

  it('renders initial widgets', () => {
    render(
      <CustomizableDashboard
        initialWidgets={initialWidgets}
        widgetTemplates={mockWidgetTemplates}
        onWidgetsChange={mockOnWidgetsChange}
        onSave={mockOnSave}
      />
    );
    expect(screen.getByText('Initial Metric')).toBeInTheDocument();
    expect(screen.getByTestId('mock-metric-widget')).toBeInTheDocument();
  });

  it('toggles edit mode', () => {
    render(
      <CustomizableDashboard
        initialWidgets={initialWidgets}
        widgetTemplates={mockWidgetTemplates}
        onWidgetsChange={mockOnWidgetsChange}
        onSave={mockOnSave}
      />
    );
    const editButton = screen.getByRole('button', { name: 'Edit' });
    fireEvent.click(editButton);
    expect(screen.getByText('Edit Mode')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Exit Edit' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Add Widget' })).toBeInTheDocument();
  });

  it('adds a new widget from the library', async () => {
    render(
      <CustomizableDashboard
        initialWidgets={initialWidgets}
        widgetTemplates={mockWidgetTemplates}
        onWidgetsChange={mockOnWidgetsChange}
        onSave={mockOnSave}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
    fireEvent.click(screen.getByRole('button', { name: 'Add Widget' }));
    
    expect(screen.getByText('Add Widget')).toBeInTheDocument();
    expect(screen.getByText('Test Metric')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Test Metric')); // Click on template
    
    await waitFor(() => {
      expect(screen.getByText('Test Metric')).toBeInTheDocument(); // New widget title
      expect(mockOnWidgetsChange).toHaveBeenCalledTimes(1);
      // Check for presence of the new widget in the mock onWidgetsChange call
      const updatedWidgets = mockOnWidgetsChange.mock.calls[0][0];
      expect(updatedWidgets.length).toBe(2);
      expect(updatedWidgets[1].title).toBe('Test Metric');
    });
  });

  it('removes a widget', async () => {
    render(
      <CustomizableDashboard
        initialWidgets={initialWidgets}
        widgetTemplates={mockWidgetTemplates}
        onWidgetsChange={mockOnWidgetsChange}
        onSave={mockOnSave}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
    fireEvent.click(screen.getByTitle('Remove Widget')); // Click trash icon on initial widget
    
    await waitFor(() => {
      expect(screen.queryByText('Initial Metric')).not.toBeInTheDocument();
      expect(mockOnWidgetsChange).toHaveBeenCalledTimes(1);
      expect(mockOnWidgetsChange).toHaveBeenCalledWith([]);
    });
  });

  it('duplicates a widget', async () => {
    render(
      <CustomizableDashboard
        initialWidgets={initialWidgets}
        widgetTemplates={mockWidgetTemplates}
        onWidgetsChange={mockOnWidgetsChange}
        onSave={mockOnSave}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
    fireEvent.click(screen.getByTitle('Duplicate Widget'));
    
    await waitFor(() => {
      expect(screen.getByText('Initial Metric (Copy)')).toBeInTheDocument();
      expect(mockOnWidgetsChange).toHaveBeenCalledTimes(1);
      const updatedWidgets = mockOnWidgetsChange.mock.calls[0][0];
      expect(updatedWidgets.length).toBe(2);
      expect(updatedWidgets[1].title).toBe('Initial Metric (Copy)');
    });
  });

  it('edits widget settings', async () => {
    render(
      <CustomizableDashboard
        initialWidgets={initialWidgets}
        widgetTemplates={mockWidgetTemplates}
        onWidgetsChange={mockOnWidgetsChange}
        onSave={mockOnSave}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
    fireEvent.click(screen.getByTitle('Edit Widget')); // Click edit icon on initial widget
    
    expect(screen.getByText('Edit Widget')).toBeInTheDocument();
    const titleInput = screen.getByLabelText('Title') as HTMLInputElement;
    fireEvent.change(titleInput, { target: { value: 'Updated Metric Title' } });
    
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    
    await waitFor(() => {
      expect(screen.getByText('Updated Metric Title')).toBeInTheDocument();
      expect(mockOnWidgetsChange).toHaveBeenCalledTimes(1);
      expect(mockOnWidgetsChange).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({ id: 'widget-1', title: 'Updated Metric Title' }),
        ])
      );
    });
  });

  it('calls onSave when "Save" button is clicked and exits edit mode', async () => {
    render(
      <CustomizableDashboard
        initialWidgets={initialWidgets}
        widgetTemplates={mockWidgetTemplates}
        onWidgetsChange={mockOnWidgetsChange}
        onSave={mockOnSave}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    
    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledTimes(1);
      expect(mockOnSave).toHaveBeenCalledWith(initialWidgets); // Initial widgets, as no changes were made through UI
      expect(screen.queryByText('Edit Mode')).not.toBeInTheDocument();
    });
  });

  it('passes isDraggable and isResizable to ResponsiveGridLayout based on isEditMode', () => {
    const MockResponsiveGridLayout = require('react-grid-layout').Responsive as vitest.Mock;
    render(
      <CustomizableDashboard
        initialWidgets={initialWidgets}
        widgetTemplates={mockWidgetTemplates}
        onWidgetsChange={mockOnWidgetsChange}
        onSave={mockOnSave}
      />
    );
    // Initially not in edit mode
    expect(MockResponsiveGridLayout).toHaveBeenCalledWith(expect.objectContaining({
      isDraggable: false,
      isResizable: false,
    }), {});

    fireEvent.click(screen.getByRole('button', { name: 'Edit' }));
    expect(MockResponsiveGridLayout).toHaveBeenCalledWith(expect.objectContaining({
      isDraggable: true,
      isResizable: true,
    }), {});
  });
});
