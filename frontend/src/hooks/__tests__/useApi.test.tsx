import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useApi } from '../useApi';

// Mock API function
const mockApiFunction = vi.fn();

// Test component that uses the useApi hook
const TestComponent = () => {
  const { data, loading, error, execute } = useApi();

  return (
    <div>
      <div data-testid="loading">{loading ? 'Loading' : 'Not Loading'}</div>
      <div data-testid="error">{error ? error.message : 'No Error'}</div>
      <div data-testid="data">{data ? JSON.stringify(data) : 'No Data'}</div>
      <button onClick={() => execute(mockApiFunction, 'test-param')}>Execute</button>
      <button onClick={() => execute(() => mockApiFunction('direct-call'))}>Execute Direct</button>
    </div>
  );
};

describe('useApi Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('provides initial state', () => {
    render(<TestComponent />);

    expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');
    expect(screen.getByTestId('error')).toHaveTextContent('No Error');
    expect(screen.getByTestId('data')).toHaveTextContent('No Data');
  });

  it('handles successful API call', async () => {
    const mockData = { id: 1, name: 'Test' };
    mockApiFunction.mockResolvedValue(mockData);

    render(<TestComponent />);

    const executeButton = screen.getByText('Execute');
    fireEvent.click(executeButton);

    // Should show loading state
    expect(screen.getByTestId('loading')).toHaveTextContent('Loading');

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');
      expect(screen.getByTestId('data')).toHaveTextContent(JSON.stringify(mockData));
      expect(screen.getByTestId('error')).toHaveTextContent('No Error');
    });

    expect(mockApiFunction).toHaveBeenCalledWith('test-param');
  });

  it('handles API call with error', async () => {
    const mockError = { message: 'API Error' };
    mockApiFunction.mockRejectedValue(mockError);

    render(<TestComponent />);

    const executeButton = screen.getByText('Execute');
    fireEvent.click(executeButton);

    // Should show loading state
    expect(screen.getByTestId('loading')).toHaveTextContent('Loading');

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');
      expect(screen.getByTestId('error')).toHaveTextContent('API Error');
      expect(screen.getByTestId('data')).toHaveTextContent('No Data');
    });
  });

  it('handles direct function execution', async () => {
    const mockData = { result: 'success' };
    mockApiFunction.mockResolvedValue(mockData);

    render(<TestComponent />);

    const executeButton = screen.getByText('Execute Direct');
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(screen.getByTestId('data')).toHaveTextContent(JSON.stringify(mockData));
    });

    expect(mockApiFunction).toHaveBeenCalledWith('direct-call');
  });

  it('handles multiple concurrent API calls', async () => {
    mockApiFunction
      .mockResolvedValueOnce({ call: 1 })
      .mockResolvedValueOnce({ call: 2 });

    render(<TestComponent />);

    const executeButton = screen.getByText('Execute');
    
    // Fire multiple calls quickly
    fireEvent.click(executeButton);
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');
    });

    // Should have the result from the last call
    expect(mockApiFunction).toHaveBeenCalledTimes(2);
  });

  it('clears error on successful call after error', async () => {
    mockApiFunction
      .mockRejectedValueOnce({ message: 'First Error' })
      .mockResolvedValueOnce({ success: true });

    render(<TestComponent />);

    const executeButton = screen.getByText('Execute');
    
    // First call - should error
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('First Error');
    });

    // Second call - should succeed and clear error
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('No Error');
      expect(screen.getByTestId('data')).toHaveTextContent('{"success":true}');
    });
  });

  it('handles API call that returns null/undefined', async () => {
    mockApiFunction.mockResolvedValue(null);

    render(<TestComponent />);

    const executeButton = screen.getByText('Execute');
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(screen.getByTestId('data')).toHaveTextContent('null');
      expect(screen.getByTestId('error')).toHaveTextContent('No Error');
    });
  });

  it('handles API call with complex error object', async () => {
    const complexError = {
      message: 'Validation Error',
      code: 422,
      details: { field: 'email', error: 'Invalid format' },
    };
    mockApiFunction.mockRejectedValue(complexError);

    render(<TestComponent />);

    const executeButton = screen.getByText('Execute');
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Validation Error');
    });
  });

  it('handles API call with string error', async () => {
    mockApiFunction.mockRejectedValue('Simple error message');

    render(<TestComponent />);

    const executeButton = screen.getByText('Execute');
    fireEvent.click(executeButton);

    await waitFor(() => {
      expect(screen.getByTestId('error')).toHaveTextContent('Simple error message');
    });
  });
});

// Test component for testing with initial execution
const TestComponentWithInitialExecution = () => {
  const { data, loading, error } = useApi(mockApiFunction, 'initial-param');

  return (
    <div>
      <div data-testid="loading">{loading ? 'Loading' : 'Not Loading'}</div>
      <div data-testid="error">{error ? error.message || error : 'No Error'}</div>
      <div data-testid="data">{data ? JSON.stringify(data) : 'No Data'}</div>
    </div>
  );
};

describe('useApi Hook with Initial Execution', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('executes API call on mount when function is provided', async () => {
    const mockData = { initial: true };
    mockApiFunction.mockResolvedValue(mockData);

    render(<TestComponentWithInitialExecution />);

    // Should start loading immediately
    expect(screen.getByTestId('loading')).toHaveTextContent('Loading');

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');
      expect(screen.getByTestId('data')).toHaveTextContent(JSON.stringify(mockData));
    });

    expect(mockApiFunction).toHaveBeenCalledWith('initial-param');
  });

  it('handles error on initial execution', async () => {
    const mockError = { message: 'Initial Error' };
    mockApiFunction.mockRejectedValue(mockError);

    render(<TestComponentWithInitialExecution />);

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');
      expect(screen.getByTestId('error')).toHaveTextContent('Initial Error');
    });
  });
});