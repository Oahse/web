import React, { useState } from 'react';
import { QrCodeIcon, DownloadIcon, PrinterIcon, CopyIcon, CheckIcon } from 'lucide-react';

/**
 * @typedef {object} QRCodeDisplayProps
 * @property {string} qrCode - base64 encoded QR code
 * @property {object} variant
 * @property {string} variant.id
 * @property {string} variant.name
 * @property {string} variant.sku
 * @property {string} [variant.product_name]
 * @property {'sm' | 'md' | 'lg'} [size='md']
 * @property {boolean} [showControls=true]
 * @property {string} [className]
 */

export const QRCodeDisplay = ({
  qrCode,
  variant,
  size = 'md',
  showControls = true,
  className
}) => {
  const [copied, setCopied] = useState(false);

  const sizeClasses = {
    sm: 'w-16 h-16',
    md: 'w-32 h-32',
    lg: 'w-48 h-48'
  };

  const downloadQRCode = () => {
    const link = document.createElement('a');
    link.href = `data:image/png;base64,${qrCode}`;
    link.download = `qr-code-${variant.sku}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const printQRCode = () => {
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(`
        <html>
          <head>
            <title>QR Code - ${variant.name}</title>
            <style>
              body { 
                font-family: Arial, sans-serif; 
                text-align: center; 
                padding: 20px; 
                background: white;
                color: black;
              }
              .qr-container { 
                display: inline-block; 
                border: 1px solid #e2e8f0; 
                padding: 20px; 
                margin: 20px; 
              }
              .qr-info { 
                margin-top: 10px; 
                font-size: 14px; 
              }
              img { 
                max-width: 200px; 
                height: auto; 
              }
            </style>
          </head>
          <body>
            <div class="qr-container">
              <h2>${variant.product_name || 'Product'}</h2>
              <h3>${variant.name}</h3>
              <img src="data:image/png;base64,${qrCode}" alt="QR Code" />
              <div class="qr-info">
                <p><strong>SKU:</strong> ${variant.sku}</p>
                <p><strong>Variant ID:</strong> ${variant.id}</p>
              </div>
            </div>
          </body>
        </html>
      `);
      printWindow.document.close();
      printWindow.print();
    }
  };

  const copyToClipboard = async () => {
    try {
      // Convert base64 to blob and copy to clipboard
      const response = await fetch(`data:image/png;base64,${qrCode}`);
      const blob = await response.blob();
      
      await navigator.clipboard.write([
        new ClipboardItem({ 'image/png': blob })
      ]);
      
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy QR code:', error);
      // Fallback: copy the base64 string
      try {
        await navigator.clipboard.writeText(`data:image/png;base64,${qrCode}`);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (fallbackError) {
        console.error('Failed to copy base64 string:', fallbackError);
      }
    }
  };

  if (!qrCode) {
    return (
      <div className={`flex items-center justify-center bg-surface-hover rounded-lg border-2 border-dashed border-border ${sizeClasses[size]} ${className || ''}`}>
        <div className="text-center">
          <QrCodeIcon size={24} className="text-copy-lighter mx-auto mb-2" />
          <span className="text-xs text-copy-light">No QR Code</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className || ''}`}>
      {/* QR Code Image */}
      <div className="relative group">
        <img
          src={`data:image/png;base64,${qrCode}`}
          alt={`QR Code for ${variant.name}`}
          className={`border border-border rounded-lg shadow-sm bg-surface p-2 ${sizeClasses[size]}`}
        />
        
        {/* Hover overlay with info */}
        <div className="absolute inset-0 bg-copy/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
          <div className="text-copy-inverse text-center text-xs">
            <QrCodeIcon size={16} className="mx-auto mb-1" />
            <div>QR Code</div>
            <div className="font-mono">{variant.sku}</div>
          </div>
        </div>
      </div>

      {/* Controls */}
      {showControls && (
        <div className="flex items-center justify-center space-x-2">
          <button
            onClick={downloadQRCode}
            className="p-2 text-copy-light hover:text-primary hover:bg-surface-hover rounded-md transition-colors"
            title="Download QR Code"
          >
            <DownloadIcon size={16} />
          </button>
          
          <button
            onClick={printQRCode}
            className="p-2 text-copy-light hover:text-primary hover:bg-surface-hover rounded-md transition-colors"
            title="Print QR Code"
          >
            <PrinterIcon size={16} />
          </button>
          
          <button
            onClick={copyToClipboard}
            className={`p-2 rounded-md transition-colors ${copied ? 'text-success bg-success/10' : 'text-copy-light hover:text-primary hover:bg-surface-hover'}`}
            title="Copy QR Code"
          >
            {copied ? <CheckIcon size={16} /> : <CopyIcon size={16} />}
          </button>
        </div>
      )}

      {/* Variant Info */}
      {size !== 'sm' && (
        <div className="text-center text-xs text-copy-light space-y-1">
          <div className="font-medium">{variant.name}</div>
          <div className="font-mono text-copy-lighter">{variant.sku}</div>
        </div>
      )}
    </div>
  );
};