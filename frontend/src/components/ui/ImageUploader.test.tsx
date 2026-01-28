// frontend/src/components/ui/ImageUploader.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vitest } from 'vitest';
import { ImageUploader } from './ImageUploader';
import { toast } from 'react-hot-toast';
import * as githubService from '../../utils/github'; // Import as a module to mock

// Mock external dependencies
vitest.mock('react-hot-toast', () => ({
  toast: {
    success: vitest.fn(),
    error: vitest.fn(),
  },
}));

vitest.mock('../../lib/github', () => ({
  uploadSingleFile: vitest.fn(),
}));

// Mock URL.createObjectURL
const mockCreateObjectURL = vitest.fn(() => 'blob:http://localhost/mock-object-url');
const originalCreateObjectURL = URL.createObjectURL;
const originalRevokeObjectURL = URL.revokeObjectURL;

beforeAll(() => {
  URL.createObjectURL = mockCreateObjectURL;
  URL.revokeObjectURL = vitest.fn();
});

afterAll(() => {
  URL.createObjectURL = originalCreateObjectURL;
  URL.revokeObjectURL = originalRevokeObjectURL;
});

describe('ImageUploader Component', () => {
  const mockOnUploadSuccess = vitest.fn();

  beforeEach(() => {
    vitest.clearAllMocks();
    mockCreateObjectURL.mockClear();
  });

  it('renders correctly with default label and no image', () => {
    render(<ImageUploader onUploadSuccess={mockOnUploadSuccess} />);
    expect(screen.getByText('Upload Image')).toBeInTheDocument();
    expect(screen.getByText('Select Image')).toBeInTheDocument();
    expect(screen.queryByRole('img', { name: /preview/i })).not.toBeInTheDocument();
  });

  it('renders with currentImageUrl provided', () => {
    const imageUrl = 'http://example.com/current-image.jpg';
    render(<ImageUploader onUploadSuccess={mockOnUploadSuccess} currentImageUrl={imageUrl} />);
    const img = screen.getByRole('img', { name: /preview/i });
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('src', imageUrl);
    expect(screen.queryByText('Select Image')).not.toBeInTheDocument(); // Change to Select Image is hidden if there is a current image
  });

  it('allows selecting a file and displays a preview', async () => {
    render(<ImageUploader onUploadSuccess={mockOnUploadSuccess} />);
    const file = new File(['hello'], 'hello.png', { type: 'image/png' });
    const input = screen.getByLabelText('Select Image');

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockCreateObjectURL).toHaveBeenCalledWith(file);
      const img = screen.getByRole('img', { name: /preview/i });
      expect(img).toBeInTheDocument();
      expect(img).toHaveAttribute('src', 'blob:http://localhost/mock-object-url');
      expect(screen.getByText('Change Image')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /upload/i })).toBeInTheDocument();
    });
  });

  it('uploads selected file successfully', async () => {
    (githubService.uploadSingleFile as vitest.Mock).mockResolvedValue({ cdnUrl: 'http://example.com/uploaded.jpg' });
    render(<ImageUploader onUploadSuccess={mockOnUploadSuccess} />);

    const file = new File(['hello'], 'hello.png', { type: 'image/png' });
    fireEvent.change(screen.getByLabelText('Select Image'), { target: { files: [file] } });

    fireEvent.click(screen.getByRole('button', { name: /upload/i }));

    await waitFor(() => {
      expect(githubService.uploadSingleFile).toHaveBeenCalledWith(file, 'avatars');
      expect(mockOnUploadSuccess).toHaveBeenCalledWith('http://example.com/uploaded.jpg');
      expect(toast.success).toHaveBeenCalledWith('Image uploaded successfully!');
      expect(screen.queryByRole('button', { name: /upload/i })).not.toBeInTheDocument();
      const img = screen.getByRole('img', { name: /preview/i });
      expect(img).toBeInTheDocument();
      expect(img).toHaveAttribute('src', 'http://example.com/uploaded.jpg');
    });
  });

  it('handles upload failure', async () => {
    (githubService.uploadSingleFile as vitest.Mock).mockRejectedValue(new Error('Upload failed'));
    render(<ImageUploader onUploadSuccess={mockOnUploadSuccess} />);

    const file = new File(['hello'], 'hello.png', { type: 'image/png' });
    fireEvent.change(screen.getByLabelText('Select Image'), { target: { files: [file] } });

    fireEvent.click(screen.getByRole('button', { name: /upload/i }));

    await waitFor(() => {
      expect(githubService.uploadSingleFile).toHaveBeenCalled();
      expect(mockOnUploadSuccess).not.toHaveBeenCalled();
      expect(toast.error).toHaveBeenCalledWith('Failed to upload image.');
      expect(screen.getByRole('button', { name: /upload/i })).toBeInTheDocument(); // Upload button should still be there
    });
  });

  it('removes image and clears preview', async () => {
    const imageUrl = 'http://example.com/current-image.jpg';
    render(<ImageUploader onUploadSuccess={mockOnUploadSuccess} currentImageUrl={imageUrl} />);

    // Initially, the current image should be displayed
    expect(screen.getByRole('img', { name: /preview/i })).toHaveAttribute('src', imageUrl);

    fireEvent.click(screen.getByRole('button', { name: /remove/i }));

    await waitFor(() => {
      expect(mockOnUploadSuccess).toHaveBeenCalledWith('');
      expect(screen.queryByRole('img', { name: /preview/i })).not.toBeInTheDocument();
      expect(screen.getByText('Select Image')).toBeInTheDocument();
    });
  });
});
