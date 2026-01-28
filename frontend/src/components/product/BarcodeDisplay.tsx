import React, { useState } from 'react';
import { QrCodeIcon, ScanLineIcon } from 'lucide-react';
import { ProductVariant, BarcodeData } from '../../types';
import { ProductsAPI } from '../../api/products';

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
    sm: 'w-20 h-12 sm:w-24 sm:h-16',
    md: 'w-24 h-16 sm:w-32 sm:h-20',
    lg: 'w-32 h-20 sm:w-48 sm:h-32'
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-main">
          {variant.name} - Codes
        </h3>
        {canGenerate && (
          <button
            onClick={handleGenerateCodes}
            disabled={isGenerating}
            className="px-4 py-2 bg-primary text-white rounded-md hover:bg-primary-dark disabled:opacity-50 transition-colors w-full sm:w-auto"
          >
            {isGenerating ? 'Generating...' : 'Generate Codes'}
          </button>
        )}
      </div>

      <div className={`grid ${showBoth ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1'} gap-4 lg:gap-6`}>
        {/* Barcode */}
        {(showBoth || !codes.qr_code) && (
          <div className="border border-border-light rounded-lg p-4 bg-surface">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-3 gap-2">
              <h4 className="font-medium text-main flex items-center">
                <ScanLineIcon size={16} className="mr-2 text-primary" />
                Barcode
              </h4>
              {codes.barcode && (
                <button
                  onClick={() => downloadCode(codes.barcode!, `barcode-${variant.sku}.png`)}
                  className="text-sm text-primary hover:text-primary-dark transition-colors w-full sm:w-auto text-left sm:text-right"
                >
                  Download
                </button>
              )}
            </div>
            {codes.barcode ? (
              <div className="flex justify-center bg-surface p-4 rounded border border-border">
                <img
                  src={codes.barcode}
                  alt={`Barcode for ${variant.sku}`}
                  className={`${sizeClasses[size]} object-contain max-w-full h-auto`}
                />
              </div>
            ) : (
              <div className={`${sizeClasses[size]} border-2 border-dashed border-border flex items-center justify-center text-copy-light bg-surface-hover rounded min-h-[4rem]`}>
                <div className="text-center">
                  <ScanLineIcon size={24} className="mx-auto mb-2 text-copy-light" />
                  <p className="text-sm">No barcode available</p>
                </div>
              </div>
            )}
            <p className="text-xs text-copy-light mt-2 text-center font-mono break-all">SKU: {variant.sku}</p>
          </div>
        )}

        {/* QR Code */}
        {(showBoth || !codes.barcode) && (
          <div className="border border-border-light rounded-lg p-4 bg-surface">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-3 gap-2">
              <h4 className="font-medium text-main flex items-center">
                <QrCodeIcon size={16} className="mr-2 text-primary" />
                QR Code
              </h4>
              {codes.qr_code && (
                <button
                  onClick={() => downloadCode(codes.qr_code!, `qrcode-${variant.sku}.png`)}
                  className="text-sm text-primary hover:text-primary-dark transition-colors w-full sm:w-auto text-left sm:text-right"
                >
                  Download
                </button>
              )}
            </div>
            {codes.qr_code ? (
              <div className="flex justify-center bg-surface p-4 rounded border border-border">
                <img
                  src={codes.qr_code}
                  alt={`QR Code for ${variant.name}`}
                  className={`${sizeClasses[size]} object-contain max-w-full h-auto`}
                />
              </div>
            ) : (
              <div className={`${sizeClasses[size]} border-2 border-dashed border-border flex items-center justify-center text-copy-light bg-surface-hover rounded min-h-[4rem]`}>
                <div className="text-center">
                  <QrCodeIcon size={24} className="mx-auto mb-2 text-copy-light" />
                  <p className="text-sm">No QR code available</p>
                </div>
              </div>
            )}
            <p className="text-xs text-copy-light mt-2 text-center break-words">{variant.name}</p>
          </div>
        )}
      </div>

      {/* Product Info */}
      <div className="bg-surface-hover rounded-lg p-4 text-sm text-copy space-y-2">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <span className="font-medium text-main">Product:</span>
            <p className="text-copy-light break-words">{variant.product_name || 'N/A'}</p>
          </div>
          <div>
            <span className="font-medium text-main">Variant:</span>
            <p className="text-copy-light break-words">{variant.name}</p>
          </div>
          <div>
            <span className="font-medium text-main">Price:</span>
            <p className="text-copy-light">${variant.sale_price || variant.base_price}</p>
          </div>
          <div>
            <span className="font-medium text-main">Stock:</span>
            <p className={`${(variant.stock || 0) > 10 ? 'text-success' : (variant.stock || 0) > 0 ? 'text-warning' : 'text-error'}`}>
              {variant.stock || 0} units
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BarcodeDisplay;