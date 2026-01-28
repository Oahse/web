// frontend/src/components/product/ReviewForm.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vitest, beforeEach } from 'vitest';
import ReviewForm from './ReviewForm'; // Default export
import { useAuth } from '../../store/AuthContext';
import { ReviewsAPI } from '../../apis';
import { toast } from 'react-hot-toast';

// --- Mock external dependencies ---
vitest.mock('../../contexts/AuthContext', () => ({
  useAuth: vitest.fn(),
}));

vitest.mock('../../apis', () => ({
  ReviewsAPI: {
    createReview: vitest.fn(),
  },
}));

vitest.mock('react-hot-toast', () => ({
  toast: {
    success: vitest.fn(),
    error: vitest.fn(),
  },
}));

// Mock lucide-react Star icon
vitest.mock('lucide-react', () => ({
  Star: vitest.fn((props) => (
    <div
      data-testid={`star-${props.key}`}
      onClick={props.onClick}
      onMouseEnter={props.onMouseEnter}
      onMouseLeave={props.onMouseLeave}
      data-filled={props.fill === 'currentColor' ? 'true' : 'false'}
    >
      ★
    </div>
  )),
}));

describe('ReviewForm Component', () => {
  const mockProductId = 'prod-123';
  const mockOnReviewSubmitted = vitest.fn();
  const mockUseAuth = useAuth as vitest.Mock;
  const mockCreateReview = ReviewsAPI.createReview as vitest.Mock;

  beforeEach(() => {
    vitest.clearAllMocks();
    mockUseAuth.mockReturnValue({ isAuthenticated: true }); // Default to authenticated
  });

  it('renders "Please log in" message when unauthenticated', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false });
    render(<ReviewForm productId={mockProductId} onReviewSubmitted={mockOnReviewSubmitted} />);
    expect(screen.getByText('Please log in to submit a review.')).toBeInTheDocument();
    expect(screen.queryByLabelText('Your Rating')).not.toBeInTheDocument();
  });

  it('renders review form when authenticated', () => {
    render(<ReviewForm productId={mockProductId} onReviewSubmitted={mockOnReviewSubmitted} />);
    expect(screen.getByText('Your Rating')).toBeInTheDocument();
    expect(screen.getByLabelText('Your Comment')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Submit Review' })).toBeInTheDocument();
  });

  it('updates rating on star click', () => {
    render(<ReviewForm productId={mockProductId} onReviewSubmitted={mockOnReviewSubmitted} />);
    fireEvent.click(screen.getByTestId('star-4')); // Click 4th star
    expect(screen.getByTestId('star-4')).toHaveAttribute('data-filled', 'true');
    expect(screen.getByTestId('star-5')).toHaveAttribute('data-filled', 'false');
  });

  it('updates comment on textarea change', () => {
    render(<ReviewForm productId={mockProductId} onReviewSubmitted={mockOnReviewSubmitted} />);
    const commentInput = screen.getByLabelText('Your Comment') as HTMLTextAreaElement;
    fireEvent.change(commentInput, { target: { value: 'This is a great product!' } });
    expect(commentInput.value).toBe('This is a great product!');
  });

  it('shows error toast if unauthenticated user tries to submit', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false });
    render(<ReviewForm productId={mockProductId} onReviewSubmitted={mockOnReviewSubmitted} />);
    // Even though the form is not rendered, a direct call would test this branch
    // For rendering, the message "Please log in" prevents interaction
    // Simulating clicking on a non-existent button would be invalid.
    // This test covers the internal logic if isAuthenticated somehow changes or form is visible
    fireEvent.submit(screen.getByText('Write a Review').closest('div')!.querySelector('form')!);
    expect(toast.error).toHaveBeenCalledWith('You must be logged in to submit a review.');
  });

  it('shows error toast if no rating is provided on submission', async () => {
    render(<ReviewForm productId={mockProductId} onReviewSubmitted={mockOnReviewSubmitted} />);
    const commentInput = screen.getByLabelText('Your Comment');
    fireEvent.change(commentInput, { target: { value: 'Some comment' } });
    fireEvent.click(screen.getByRole('button', { name: 'Submit Review' }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Please provide a rating.');
      expect(mockCreateReview).not.toHaveBeenCalled();
    });
  });

  it('calls createReview and onReviewSubmitted on successful submission', async () => {
    mockCreateReview.mockResolvedValueOnce(true);
    render(<ReviewForm productId={mockProductId} onReviewSubmitted={mockOnReviewSubmitted} />);
    fireEvent.click(screen.getByTestId('star-5')); // Select 5 stars
    const commentInput = screen.getByLabelText('Your Comment');
    fireEvent.change(commentInput, { target: { value: 'Excellent product!' } });
    fireEvent.click(screen.getByRole('button', { name: 'Submit Review' }));

    await waitFor(() => {
      expect(mockCreateReview).toHaveBeenCalledWith(mockProductId, 5, 'Excellent product!');
      expect(toast.success).toHaveBeenCalledWith('Review submitted successfully!');
      expect(mockOnReviewSubmitted).toHaveBeenCalledTimes(1);
      expect(commentInput).toHaveValue(''); // Form resets
      expect(screen.getByTestId('star-1')).toHaveAttribute('data-filled', 'false'); // Rating resets
    });
  });

  it('shows error toast on failed submission', async () => {
    mockCreateReview.mockRejectedValueOnce(new Error('API Error'));
    render(<ReviewForm productId={mockProductId} onReviewSubmitted={mockOnReviewSubmitted} />);
    fireEvent.click(screen.getByTestId('star-3'));
    fireEvent.change(screen.getByLabelText('Your Comment'), { target: { value: 'Bad product.' } });
    fireEvent.click(screen.getByRole('button', { name: 'Submit Review' }));

    await waitFor(() => {
      expect(mockCreateReview).toHaveBeenCalledTimes(1);
      expect(toast.error).toHaveBeenCalledWith('Failed to submit review.');
    });
  });

  it('disables submit button and shows loading text during submission', async () => {
    mockCreateReview.mockImplementationOnce(() => new Promise(() => {})); // Never resolve
    render(<ReviewForm productId={mockProductId} onReviewSubmitted={mockOnReviewSubmitted} />);
    fireEvent.click(screen.getByTestId('star-4'));
    fireEvent.change(screen.getByLabelText('Your Comment'), { target: { value: 'Test' } });
    fireEvent.click(screen.getByRole('button', { name: 'Submit Review' }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Submitting...' })).toBeDisabled();
    });
  });
});
