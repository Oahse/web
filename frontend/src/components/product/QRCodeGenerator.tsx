import React, { useState, useEffect } from 'react';
import { QrCodeIcon, DownloadIcon, Share2Icon } from 'lucide-react';
import { ProductVariant } from '../../types';
import { ProductsAPI } from '../../api/products';

interface QRCodeGeneratorProps {
  variant: ProductVariant;
  size?: 'sm' | 'md' | 'lg';
  showDownload?: boolean;
  showShare?: boolean;
  customData?: Record<string, any>;
}

export const QRCodeGenerator: React.FC<QRCodeGeneratorProps> = ({
  variant,
  size = 'md',
  showDownload = true,
  showShare = true,
  customData
}) => {
  const [qrCodeUrl, setQrCodeUrl] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const sizeClasses = {
    sm: 'w-32 h-32',
    md: 'w-48 h-48',
    lg: 'w-64 h-64'
  };

  useEffect(() => {
    generateQRCode();
  }, [variant.id]);

  const generateQRCode = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      // Use existing QR code from variant or generate new one
      if (variant.qr_code) {
        setQrCodeUrl(variant.qr_code);
      } else {
        // Generate QR code with custom data
        const qrData = {
          product_id: variant.product_id,
          variant_id: variant.id,
          sku: variant.sku,
          name: variant.name,
          price: variant.sale_price || variant.base_price,
          ...customData
        };
        
        // Create QR code URL (you might want to use a QR code library here)
        const qrCodeDataUrl = await createQRCodeImage(qrData);
        setQrCodeUrl(qrCodeDataUrl);
      }
    } catch (err) {
      setError('Failed to generate QR code');
      console.error('QR Code generation error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const createQRCodeImage = async (data: Record<string, any>): Promise<string> => {
    // This is a placeholder - you'd typically use a QR code library like qrcode.js
    // For now, we'll create a simple data URL representation
    const jsonString = JSON.stringify(data);
    const encodedData = btoa(jsonString);
    
    // Create a simple QR code representation (you should replace this with a real QR code library)
    return `data:image/svg+xml;base64,${createSimpleQRCode(encodedData)}`;
  };

  const createSimpleQRCode = (data: string): string => {
    // Simple SVG QR code placeholder - replace with real QR code generation
    const svg = `
      <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
        <rect width="200" height="200" fill="white"/>
        <rect x="10" y="10" width="180" height="180" fill="none" stroke="black" stroke-width="2"/>
        <text x="100" y="100" text-anchor="middle" font-size="8" font-family="monospace">
          ${data.substring(0, 20)}...
        </text>
      </svg>
    `;
    return btoa(svg);
  };

  const downloadQRCode = () => {
    if (!qrCodeUrl) return;
    
    const link = document.createElement('a');
    link.href = qrCodeUrl;
    link.download = `qrcode-${variant.sku}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const shareQRCode = async () => {
    if (!qrCodeUrl) return;
    
    try {
      if (navigator.share) {
        await navigator.share({
          title: `${variant.name} QR Code`,
          text: `Scan this QR code for ${variant.name}`,
          url: qrCodeUrl
        });
      } else {
        // Fallback: copy to clipboard
        await navigator.clipboard.writeText(qrCodeUrl);
        alert('QR Code URL copied to clipboard!');
      }
    } catch (err) {
      console.error('Share failed:', err);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <QrCodeIcon className="mr-2 h-5 w-5 text-blue-600" />
          QR Code
        </h3>
        <div className="flex space-x-2">
          {showShare && (
            <button
              onClick={shareQRCode}
              disabled={!qrCodeUrl}
              className="p-2 text-gray-600 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Share QR Code"
            >
              <Share2Icon className="h-4 w-4" />
            </button>
          )}
          {showDownload && (
            <button
              onClick={downloadQRCode}
              disabled={!qrCodeUrl}
              className="p-2 text-gray-600 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Download QR Code"
            >
              <DownloadIcon className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {isLoading ? (
        <div className={`${sizeClasses[size]} flex items-center justify-center border-2 border-dashed border-gray-300 rounded-lg`}>
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-sm text-gray-600">Generating QR Code...</p>
          </div>
        </div>
      ) : error ? (
        <div className={`${sizeClasses[size]} flex items-center justify-center border-2 border-dashed border-red-300 rounded-lg`}>
          <div className="text-center">
            <QrCodeIcon className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      ) : qrCodeUrl ? (
        <div className="flex flex-col items-center space-y-4">
          <div className={`${sizeClasses[size]} bg-white p-4 rounded-lg border border-gray-200`}>
            <img
              src={qrCodeUrl}
              alt={`QR Code for ${variant.name}`}
              className="w-full h-full object-contain"
            />
          </div>
          <div className="text-center space-y-2">
            <p className="text-sm font-medium text-gray-900">{variant.name}</p>
            <p className="text-xs text-gray-600 font-mono">SKU: {variant.sku}</p>
            <p className="text-sm font-semibold text-green-600">
              ${(variant.sale_price || variant.base_price).toFixed(2)}
            </p>
          </div>
        </div>
      ) : (
        <div className={`${sizeClasses[size]} flex items-center justify-center border-2 border-dashed border-gray-300 rounded-lg`}>
          <div className="text-center">
            <QrCodeIcon className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-600">No QR Code Available</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default QRCodeGenerator;
