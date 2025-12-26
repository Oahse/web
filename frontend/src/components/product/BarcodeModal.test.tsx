import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import { BarcodeModal } from './BarcodeModal';
import { ProductVariant } from '../../types';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}));

// Mock BarcodeDisplay component
vi.mock('./BarcodeDisplay', () => ({
  BarcodeDisplay: ({ variant, showBoth, size, canGenerate }: any) => (
    <div data-testid="barcode-display">
      <div>Variant: {variant.name}</div>
      <div>SKU: {variant.sku}</div>
      <div>Show Both: {showBoth ? 'true' : 'false'}</div>
      <div>Size: {size}</div>
      <div>Can Generate: {canGenerate ? 'true' : 'false'}</div>
    </div>
  ),
}));

describe('BarcodeModal', () => {
  const mockVariant: ProductVariant = {
    id: '123e4567-e89b-12d3-a456-426614174000',
    product_id: 'prod-123',
    sku: 'TEST-SKU-001',
    name: 'Test Variant',
    base_price: 29.99,
    sale_price: 24.99,
    stock: 100,
    images: [],
    product_name: 'Test Product',
    barcode: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
    qr_code: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
  };

  const defaultProps = {
    variant: mockVariant,
    isOpen: true,
    onClose: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders when isOpen is true', () => {
    render(<BarcodeModal {...defaultProps} />);
    
    expect(screen.getByText('Product Barcode & QR Code')).toBeInTheDocument();
    expect(screen.getByTestId('barcode-display')).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(<BarcodeModal {...defaultProps} isOpen={false} />);
    
    expect(screen.queryByText('Product Barcode & QR Code')).not.toBeInTheDocument();
  });

  it('displays custom title when provided', () => {
    render(<BarcodeModal {...defaultProps} title="Custom Title" />);
    
    expect(screen.getByText('Custom Title')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn();
    render(<BarcodeModal {...defaultProps} onClose={onClose} />);
    
    const closeButton = screen.getByLabelText('Close modal');
    fireEvent.click(closeButton);
    
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when backdrop is clicked', () => {
    const onClose = vi.fn();
    render(<BarcodeModal {...defaultProps} onClose={onClose} />);
    
    const backdrop = screen.getByText('Product Barcode & QR Code').closest('.fixed');
    if (backdrop) {
      fireEvent.click(backdrop);
      expect(onClose).toHaveBeenCalledTimes(1);
    }
  });

  it('does not call onClose when modal content is clicked', () => {
    const onClose = vi.fn();
    render(<BarcodeModal {...defaultProps} onClose={onClose} />);
    
    const modalContent = screen.getByText('Product Barcode & QR Code').closest('.bg-white');
    if (modalContent) {
      fireEvent.click(modalContent);
      expect(onClose).not.toHaveBeenCalled();
    }
  });

  it('passes correct props to BarcodeDisplay', () => {
    render(<BarcodeModal {...defaultProps} canGenerate={true} />);
    
    expect(screen.getByText('Variant: Test Variant')).toBeInTheDocument();
    expect(screen.getByText('SKU: TEST-SKU-001')).toBeInTheDocument();
    expect(screen.getByText('Show Both: true')).toBeInTheDocument();
    expect(screen.getByText('Size: lg')).toBeInTheDocument();
    expect(screen.getByText('Can Generate: true')).toBeInTheDocument();
  });

  it('displays product information correctly', () => {
    render(<BarcodeModal {...defaultProps} />);
    
    expect(screen.getByText('Product Information')).toBeInTheDocument();
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('Test Variant')).toBeInTheDocument();
    expect(screen.getByText('TEST-SKU-001')).toBeInTheDocument();
  });

  it('displays pricing information correctly', () => {
    render(<BarcodeModal {...defaultProps} />);
    
    expect(screen.getByText('Pricing & Stock')).toBeInTheDocument();
    expect(screen.getByText('$24.99')).toBeInTheDocument(); // sale_price
    expect(screen.getByText('$29.99')).toBeInTheDocument(); // base_price (crossed out)
    expect(screen.getByText('100 units')).toBeInTheDocument();
  });

  it('displays usage tips', () => {
    render(<BarcodeModal {...defaultProps} />);
    
    expect(screen.getByText('Usage Tips')).toBeInTheDocument();
    expect(screen.getByText(/Use the barcode for inventory management/)).toBeInTheDocument();
    expect(screen.getByText(/Share the QR code for quick product access/)).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<BarcodeModal {...defaultProps} className="custom-class" />);
    
    const modalContent = screen.getByText('Product Barcode & QR Code').closest('.bg-white');
    expect(modalContent).toHaveClass('custom-class');
  });

  it('handles variant without sale price', () => {
    const variantWithoutSale = {
      ...mockVariant,
      sale_price: undefined
    };
    
    render(<BarcodeModal {...defaultProps} variant={variantWithoutSale} />);
    
    expect(screen.getByText('$29.99')).toBeInTheDocument(); // base_price only
    expect(screen.queryByText('Original:')).not.toBeInTheDocument();
  });
});