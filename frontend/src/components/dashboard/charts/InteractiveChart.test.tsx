// frontend/src/components/dashboard/charts/InteractiveChart.test.tsx
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vitest, beforeEach, afterEach } from 'vitest';
import { InteractiveChart } from './InteractiveChart';

// Mock chart.js and react-chartjs-2 completely
vitest.mock('chart.js', () => ({
  Chart: { register: vitest.fn() },
  CategoryScale: vitest.fn(),
  LinearScale: vitest.fn(),
  PointElement: vitest.fn(),
  LineElement: vitest.fn(),
  BarElement: vitest.fn(),
  Title: vitest.fn(),
  Tooltip: vitest.fn(),
  Legend: vitest.fn(),
  ArcElement: vitest.fn(),
  TimeScale: vitest.fn(),
  Filler: vitest.fn(),
}));

// Mock react-chartjs-2 components. Their render function will just call their props.
vitest.mock('react-chartjs-2', () => ({
  Line: vitest.fn((props) => (
    <div data-testid="mock-chart-line" onClick={(e) => props.options.onClick(e, [{ index: 0, datasetIndex: 0 }])}>
      Line Chart
      <canvas data-testid="mock-chart-canvas" />
    </div>
  )),
  Bar: vitest.fn((props) => (
    <div data-testid="mock-chart-bar" onClick={(e) => props.options.onClick(e, [{ index: 0, datasetIndex: 0 }])}>
      Bar Chart
      <canvas data-testid="mock-chart-canvas" />
    </div>
  )),
  Pie: vitest.fn((props) => (
    <div data-testid="mock-chart-pie" onClick={(e) => props.options.onClick(e, [{ index: 0, datasetIndex: 0 }])}>
      Pie Chart
      <canvas data-testid="mock-chart-canvas" />
    </div>
  )),
  Doughnut: vitest.fn((props) => (
    <div data-testid="mock-chart-doughnut" onClick={(e) => props.options.onClick(e, [{ index: 0, datasetIndex: 0 }])}>
      Doughnut Chart
      <canvas data-testid="mock-chart-canvas" />
    </div>
  )),
}));

// Mock lucide-react icons
vitest.mock('lucide-react', () => ({
  DownloadIcon: vitest.fn(() => <svg data-testid="icon-download" />),
  MaximizeIcon: vitest.fn(() => <svg data-testid="icon-maximize" />),
  RefreshCwIcon: vitest.fn(() => <svg data-testid="icon-refresh-cw" />),
}));

describe('InteractiveChart Component', () => {
  const mockData = {
    labels: ['Jan', 'Feb', 'Mar'],
    datasets: [{
      label: 'Sales',
      data: [100, 200, 150],
      backgroundColor: 'red',
    }],
  };
  const mockOnDataPointClick = vitest.fn();
  const mockOnExport = vitest.fn();
  const mockOnRefresh = vitest.fn();

  // Mock HTMLCanvasElement.prototype.toDataURL
  const mockToDataURL = vitest.fn(() => 'data:image/png;base64,mockpngdata');
  const mockClick = vitest.fn();
  const mockCreateElement = vitest.spyOn(document, 'createElement');

  beforeEach(() => {
    vitest.clearAllMocks();
    // Setup mock canvas
    Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
      value: vitest.fn(() => ({})),
      configurable: true,
    });
    Object.defineProperty(HTMLCanvasElement.prototype, 'toDataURL', {
      value: mockToDataURL,
      configurable: true,
    });
    mockCreateElement.mockImplementation((tagName) => {
      if (tagName === 'a') {
        const mockLink = {
          href: '',
          download: '',
          click: mockClick,
        };
        return mockLink as unknown as HTMLElement;
      }
      return vitest.importActual('jsdom').JSDOM.fragment('<div></div>').firstChild;
    });
  });

  it('renders loading skeleton when loading is true', () => {
    render(<InteractiveChart type="line" data={mockData} loading={true} />);
    expect(screen.getByRole('status', { name: 'Loading content...' })).toBeInTheDocument();
    expect(screen.queryByTestId('mock-chart-line')).not.toBeInTheDocument();
  });

  it('renders Line chart by default and passes data/options', () => {
    render(<InteractiveChart type="line" data={mockData} title="Test Chart" />);
    expect(screen.getByTestId('mock-chart-line')).toBeInTheDocument();
    expect(screen.getByText('Test Chart')).toBeInTheDocument();
    const LineChart = require('react-chartjs-2').Line;
    expect(LineChart).toHaveBeenCalledWith(
      expect.objectContaining({
        data: mockData,
        options: expect.objectContaining({
          plugins: expect.objectContaining({ title: { display: true, text: 'Test Chart' } }),
        }),
      }),
      {}
    );
  });

  it('renders Bar chart when type is "bar"', () => {
    render(<InteractiveChart type="bar" data={mockData} />);
    expect(screen.getByTestId('mock-chart-bar')).toBeInTheDocument();
  });

  it('renders Pie chart when type is "pie"', () => {
    render(<InteractiveChart type="pie" data={mockData} />);
    expect(screen.getByTestId('mock-chart-pie')).toBeInTheDocument();
  });

  it('renders Doughnut chart when type is "doughnut"', () => {
    render(<InteractiveChart type="doughnut" data={mockData} />);
    expect(screen.getByTestId('mock-chart-doughnut')).toBeInTheDocument();
  });

  it('calls onDataPointClick when a data point is clicked', () => {
    render(<InteractiveChart type="line" data={mockData} onDataPointClick={mockOnDataPointClick} />);
    fireEvent.click(screen.getByTestId('mock-chart-line')); // Simulate chart area click
    expect(mockOnDataPointClick).toHaveBeenCalledWith(
      expect.objectContaining({ dataIndex: 0, datasetIndex: 0, label: 'Jan', value: 100 }),
      0
    );
  });

  it('handles drill-down functionality', async () => {
    const drillDownData = {
      'Jan': { labels: ['Week 1', 'Week 2'], datasets: [{ label: 'Sales', data: [50, 50] }] },
    };
    render(<InteractiveChart type="line" data={mockData} enableDrillDown={true} drillDownData={drillDownData} />);
    
    // Drill down into 'Jan'
    fireEvent.click(screen.getByTestId('mock-chart-line'));

    await waitFor(() => {
      expect(screen.getByText('›')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Jan' })).toBeInTheDocument(); // Drill-up button
      // Verify chart data updated (implicitly by checking what ChartJS.Line was called with)
      const LineChart = require('react-chartjs-2').Line;
      expect(LineChart).toHaveBeenCalledWith(expect.objectContaining({ data: drillDownData.Jan }), {});
    });

    // Drill up
    fireEvent.click(screen.getByRole('button', { name: 'Jan' }));
    await waitFor(() => {
      expect(screen.queryByText('›')).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Jan' })).not.toBeInTheDocument();
      const LineChart = require('react-chartjs-2').Line;
      expect(LineChart).toHaveBeenCalledWith(expect.objectContaining({ data: mockData }), {});
    });
  });

  it('exports PNG image when "Export PNG" is clicked', () => {
    render(<InteractiveChart type="line" data={mockData} title="My Chart" />);
    fireEvent.click(screen.getByTitle('Export'));
    fireEvent.click(screen.getByRole('button', { name: 'Export PNG' }));

    expect(mockToDataURL).toHaveBeenCalledWith('image/png');
    expect(mockCreateElement).toHaveBeenCalledWith('a');
    expect(mockClick).toHaveBeenCalledTimes(1);
  });

  it('calls onExport with "csv" when "Export CSV" is clicked', () => {
    render(<InteractiveChart type="line" data={mockData} onExport={mockOnExport} />);
    fireEvent.click(screen.getByTitle('Export'));
    fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }));
    expect(mockOnExport).toHaveBeenCalledWith('csv');
  });

  it('calls onRefresh when refresh button is clicked', () => {
    render(<InteractiveChart type="line" data={mockData} refreshable={true} onRefresh={mockOnRefresh} />);
    fireEvent.click(screen.getByTitle('Refresh'));
    expect(mockOnRefresh).toHaveBeenCalledTimes(1);
  });

  it('toggles fullscreen mode', () => {
    render(<InteractiveChart type="line" data={mockData} />);
    const chartContainer = screen.getByTestId('mock-chart-line').closest('div'); // The wrapping div for the chart
    
    // Initially not fullscreen
    expect(chartContainer).not.toHaveClass('fixed');

    fireEvent.click(screen.getByTitle('Fullscreen'));
    expect(chartContainer).toHaveClass('fixed', 'inset-4', 'z-50');

    fireEvent.click(screen.getByTitle('Fullscreen'));
    expect(chartContainer).not.toHaveClass('fixed');
  });
});
