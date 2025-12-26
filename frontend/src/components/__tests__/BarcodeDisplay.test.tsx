import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { BarcodeDisplay } from '../product/BarcodeDisplay';
import { ProductsAPI } from '../../apis/products';
import { ProductVariant } from '../../types';

// Mock the ProductsAPI
vi.mock('../../apis/products', () => ({
  ProductsAPI: {
    generateVariantCodes: vi.fn(),
  },
}));

describe('BarcodeDisplay', () => {
  const mockVariant: ProductVariant = {
    id: '123e4567-e89b-12d3-a456-426614174000',
    product_id: '123e4567-e89b-12d3-a456-426614174001',
    sku: 'TEST-SKU-001',
    name: 'Test Variant',
    base_price: 29.99,
    sale_price: 24.99,
    stock: 10,
    images: [],
    barcode: 'data:image/png;base64,existing_barcode_data',
    qr_code: 'data:image/png;base64,existing_qr_code_data',
  };

  const mockVariantWithoutCodes: ProductVariant = {
    ...mockVariant,
    barcode: undefined,
    qr_code: undefined,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders barcode and QR code when available', () => {
    render(<BarcodeDisplay variant={mockVariant} />);

    expect(screen.getByText('Product Codes')).toBeInTheDocument();
    expect(screen.getByText('Barcode')).toBeInTheDocument();
    expect(screen.getByText('QR Code')).toBeInTheDocument();
    expect(screen.getByAltText('Barcode for TEST-SKU-001')).toBeInTheDocument();
    expect(screen.getByAltText('QR Code for Test Variant')).toBeInTheDocument();
  });

  it('shows placeholder when codes are not available', () => {
    render(<BarcodeDisplay variant={mockVariantWithoutCodes} />);

    expect(screen.getByText('No barcode available')).toBeInTheDocument();
    expect(screen.getByText('No QR code available')).toBeInTheDocument();
  });

  it('shows generate button when canGenerate is true', () => {
    render(<BarcodeDisplay variant={mockVariantWithoutCodes} canGenerate={true} />);

    expect(screen.getByText('Generate Codes')).toBeInTheDocument();
  });

  it('hides generate button when canGenerate is false', () => {
    render(<BarcodeDisplay variant={mockVariantWithoutCodes} canGenerate={false} />);

    expect(screen.queryByText('Generate Codes')).not.toBeInTheDocument();
  });

  it('generates codes when generate button is clicked', async () => {
    const mockGeneratedCodes = {
      success: true,
      data: {
        barcode: 'data:image/png;base64,new_barcode_data',
        qr_code: 'data:image/png;base64,new_qr_code_data',
      },
    };

    (ProductsAPI.generateVariantCodes as any).mockResolvedValue(mockGeneratedCodes);

    const onCodesGenerated = vi.fn();
    render(
      <BarcodeDisplay 
        variant={mockVariantWithoutCodes} 
        canGenerate={true} 
        onCodesGenerated={onCodesGenerated}
      />
    );

    const generateButton = screen.getByText('Generate Codes');
    fireEvent.click(generateButton);

    expect(screen.getByText('Generating...')).toBeInTheDocument();

    await waitFor(() => {
      expect(ProductsAPI.generateVariantCodes).toHaveBeenCalledWith(mockVariantWithoutCodes.id);
      expect(onCodesGenerated).toHaveBeenCalledWith({
        variant_id: mockVariantWithoutCodes.id,
        barcode: mockGeneratedCodes.data.barcode,
        qr_code: mockGeneratedCodes.data.qr_code,
      });
    });
  });

  it('handles generation error gracefully', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    (ProductsAPI.generateVariantCodes as any).mockRejectedValue(new Error('Generation failed'));

    render(<BarcodeDisplay variant={mockVariantWithoutCodes} canGenerate={true} />);

    const generateButton = screen.getByText('Generate Codes');
    fireEvent.click(generateButton);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to generate codes:', expect.any(Error));
    });

    consoleErrorSpy.mockRestore();
  });

  it('shows only barcode when showBoth is false and qr_code is not available', () => {
    const variantWithOnlyBarcode = {
      ...mockVariant,
      qr_code: undefined,
    };

    render(<BarcodeDisplay variant={variantWithOnlyBarcode} showBoth={false} />);

    expect(screen.getByText('Barcode')).toBeInTheDocument();
    expect(screen.queryByText('QR Code')).not.toBeInTheDocument();
  });

  it('shows only QR code when showBoth is false and barcode is not available', () => {
    const variantWithOnlyQR = {
      ...mockVariant,
      barcode: undefined,
    };

    render(<BarcodeDisplay variant={variantWithOnlyQR} showBoth={false} />);

    expect(screen.getByText('QR Code')).toBeInTheDocument();
    expect(screen.queryByText('Barcode')).not.toBeInTheDocument();
  });

  it('applies correct size classes', () => {
    const { rerender } = render(<BarcodeDisplay variant={mockVariant} size="sm" />);
    
    let barcodeImg = screen.getByAltText('Barcode for TEST-SKU-001');
    expect(barcodeImg).toHaveClass('w-24', 'h-16');

    rerender(<BarcodeDisplay variant={mockVariant} size="md" />);
    barcodeImg = screen.getByAltText('Barcode for TEST-SKU-001');
    expect(barcodeImg).toHaveClass('w-32', 'h-20');

    rerender(<BarcodeDisplay variant={mockVariant} size="lg" />);
    barcodeImg = screen.getByAltText('Barcode for TEST-SKU-001');
    expect(barcodeImg).toHaveClass('w-48', 'h-32');
  });

  it('shows download buttons when codes are available', () => {
    render(<BarcodeDisplay variant={mockVariant} />);

    const downloadButtons = screen.getAllByText('Download');
    expect(downloadButtons).toHaveLength(2); // One for barcode, one for QR code
  });

  it('triggers download when download button is clicked', () => {
    // Mock document.createElement and related methods
    const mockLink = {
      href: '',
      download: '',
      click: vi.fn(),
    };
    const createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(mockLink as any);
    const appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => {});
    const removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => {});

    render(<BarcodeDisplay variant={mockVariant} />);

    const downloadButtons = screen.getAllByText('Download');
    fireEvent.click(downloadButtons[0]); // Click first download button (barcode)

    expect(createElementSpy).toHaveBeenCalledWith('a');
    expect(mockLink.href).toBe(mockVariant.barcode);
    expect(mockLink.download).toMatch(/barcode-TEST-SKU-001\.png/);
    expect(mockLink.click).toHaveBeenCalled();
    expect(appendChildSpy).toHaveBeenCalledWith(mockLink);
    expect(removeChildSpy).toHaveBeenCalledWith(mockLink);

    createElementSpy.mockRestore();
    appendChildSpy.mockRestore();
    removeChildSpy.mockRestore();
  });

  it('displays product information correctly', () => {
    const variantWithProductInfo = {
      ...mockVariant,
      product_name: 'Test Product',
      product_description: 'Test Description',
    };

    render(<BarcodeDisplay variant={variantWithProductInfo} />);

    expect(screen.getByText('Product:')).toBeInTheDocument();
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('Variant:')).toBeInTheDocument();
    expect(screen.getByText('Test Variant')).toBeInTheDocument();
    expect(screen.getByText('Price:')).toBeInTheDocument();
    expect(screen.getByText('$24.99')).toBeInTheDocument();
    expect(screen.getByText('Stock:')).toBeInTheDocument();
    expect(screen.getByText('10 units')).toBeInTheDocument();
  });

  it('shows base price when sale price is not available', () => {
    const variantWithoutSale = {
      ...mockVariant,
      sale_price: undefined,
    };

    render(<BarcodeDisplay variant={variantWithoutSale} />);

    expect(screen.getByText('$29.99')).toBeInTheDocument();
  });

  it('disables generate button when generating', async () => {
    (ProductsAPI.generateVariantCodes as any).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    render(<BarcodeDisplay variant={mockVariantWithoutCodes} canGenerate={true} />);

    const generateButton = screen.getByText('Generate Codes');
    fireEvent.click(generateButton);

    expect(screen.getByText('Generating...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /generating/i })).toBeDisabled();
  });
});