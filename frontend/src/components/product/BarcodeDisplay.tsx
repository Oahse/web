import React, { useState } from 'react';
import { ProductVariant, BarcodeData } from '../../types';
import { ProductsAPI } from '../../apis/products';

interface BarcodeDisplayProps {
  variant: ProductVariant;
  showBoth?: boolean;
  size?: 'sm' | 'md' | 'lg';
  onCodesGenerated?: (codes: BarcodeData) => void;
  canGenerate?: boolean;
}

export const BarcodeDisplay: React.FC<BarcodeDisplayProps> = ({
  variant,
  showBoth = true,
  size = 'md',
  onCodesGenerated,
  canGenerate = false
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [codes, setCodes] = useState<BarcodeData>({
    variant_id: variant.id,
    barcode: variant.barcode,
    qr_code: variant.qr_code
  });

  const sizeClasses = {
    sm: 'w-24 h-16',
    md: 'w-32 h-20',
    lg: 'w-48 h-32'
  };

  const handleGenerateCodes = async () => {
    if (!canGenerate) return;
    
    setIsGenerating(true);
    try {
      const response = await ProductsAPI.generateVariantCodes(variant.id);
      if (response.success) {
        const newCodes = {
          variant_id: variant.id,
          barcode: response.data.barcode,
          qr_code: response.data.qr_code
        };
        setCodes(newCodes);
        onCodesGenerated?.(newCodes);
      }
    } catch (error) {
      console.error('Failed to generate codes:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadCode = (dataUrl: string, filename: string) => {
    const link = document.createElement('a');
    link.href = dataUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Product Codes</h3>
        {canGenerate && (
          <button
            onClick={handleGenerateCodes}
            disabled={isGenerating}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isGenerating ? 'Generating...' : 'Generate Codes'}
          </button>
        )}
      </div>

      <div className={`grid ${showBoth ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'} gap-4`}>
        {/* Barcode */}
        {(showBoth || !codes.qr_code) && (
          <div className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium">Barcode</h4>
              {codes.barcode && (
                <button
                  onClick={() => downloadCode(codes.barcode!, `barcode-${variant.sku}.png`)}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  Download
                </button>
              )}
            </div>
            {codes.barcode ? (
              <div className="flex justify-center">
                <img
                  src={codes.barcode}
                  alt={`Barcode for ${variant.sku}`}
                  className={`${sizeClasses[size]} object-contain border`}
                />
              </div>
            ) : (
              <div className={`${sizeClasses[size]} border-2 border-dashed border-gray-300 flex items-center justify-center text-gray-500`}>
                No barcode available
              </div>
            )}
            <p className="text-xs text-gray-600 mt-2 text-center">SKU: {variant.sku}</p>
          </div>
        )}

        {/* QR Code */}
        {(showBoth || !codes.barcode) && (
          <div className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium">QR Code</h4>
              {codes.qr_code && (
                <button
                  onClick={() => downloadCode(codes.qr_code!, `qrcode-${variant.sku}.png`)}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  Download
                </button>
              )}
            </div>
            {codes.qr_code ? (
              <div className="flex justify-center">
                <img
                  src={codes.qr_code}
                  alt={`QR Code for ${variant.name}`}
                  className={`${sizeClasses[size]} object-contain border`}
                />
              </div>
            ) : (
              <div className={`${sizeClasses[size]} border-2 border-dashed border-gray-300 flex items-center justify-center text-gray-500`}>
                No QR code available
              </div>
            )}
            <p className="text-xs text-gray-600 mt-2 text-center">{variant.name}</p>
          </div>
        )}
      </div>

      {/* Product Info */}
      <div className="text-sm text-gray-600 space-y-1">
        <p><span className="font-medium">Product:</span> {variant.product_name || 'N/A'}</p>
        <p><span className="font-medium">Variant:</span> {variant.name}</p>
        <p><span className="font-medium">Price:</span> ${variant.sale_price || variant.base_price}</p>
        <p><span className="font-medium">Stock:</span> {variant.stock} units</p>
      </div>
    </div>
  );
};

export default BarcodeDisplay;