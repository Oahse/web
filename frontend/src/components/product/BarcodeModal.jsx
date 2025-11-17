import { useCallback, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { ScanLineIcon, DownloadIcon, CopyIcon, XIcon } from 'lucide-react';

export const BarcodeModal = ({
  code,
  format = 'CODE128',
  width = 300,
  height = 100,
  title = 'Product Barcode',
  isOpen,
  onClose,
  className = '',
}) => {
  const canvasRef = useRef(null);

  const generateBarcode = useCallback((text, canvas) => {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = width;
    canvas.height = height;

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, width, height);

    ctx.fillStyle = '#000000';

    const barWidth = width / (text.length * 8);
    const barHeight = height * 0.7;
    const startY = height * 0.1;

    text.split('').forEach((char, index) => {
      const charCode = char.charCodeAt(0);
      const pattern = charCode % 8;

      for (let i = 0; i < 8; i++) {
        if ((pattern >> i) & 1) {
          const x = (index * 8 + i) * barWidth;
          ctx.fillRect(x, startY, barWidth * 0.8, barHeight);
        }
      }
    });

    ctx.fillStyle = '#000000';
    ctx.font = '12px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(text, width / 2, height * 0.9);

    ctx.font = '10px sans-serif';
    ctx.fillText(format, width / 2, height * 0.95);
  }, [width, height, format]);

  useEffect(() => {
    if (isOpen && canvasRef.current && code) {
      generateBarcode(code, canvasRef.current);
    }
  }, [code, format, width, height, isOpen, generateBarcode]);

  const handleDownload = () => {
    if (canvasRef.current) {
      const link = document.createElement('a');
      link.download = `barcode-${code}-${Date.now()}.png`;
      link.href = canvasRef.current.toDataURL();
      link.click();
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      alert('Barcode copied to clipboard!');
    } catch (error) {
      console.error('Error copying to clipboard:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.8, opacity: 0 }}
        className={`bg-white rounded-lg p-6 max-w-md w-full ${className}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <ScanLineIcon size={24} className="text-primary" />
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XIcon size={20} />
          </button>
        </div>

        <div className="flex justify-center mb-4">
          <div className="p-4 bg-white border-2 border-gray-200 rounded-lg">
            <canvas
              ref={canvasRef}
              className="block"
              style={{ width: width, height: height }}
            />
          </div>
        </div>

        <div className="mb-4 space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Format:</span>
            <span className="text-sm font-medium text-gray-700">{format}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Code:</span>
            <span className="text-sm font-mono text-gray-700 bg-gray-50 px-2 py-1 rounded">
              {code}
            </span>
          </div>
        </div>

        <div className="flex space-x-2">
          <button
            onClick={handleDownload}
            className="flex-1 flex items-center justify-center space-x-2 bg-primary text-white px-4 py-2 rounded-md hover:bg-primary-dark transition-colors"
          >
            <DownloadIcon size={16} />
            <span>Download</span>
          </button>
          <button
            onClick={handleCopy}
            className="flex-1 flex items-center justify-center space-x-2 bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200 transition-colors"
          >
            <CopyIcon size={16} />
            <span>Copy Code</span>
          </button>
        </div>

        <div className="mt-4 p-3 bg-info-50 rounded-lg">
          <p className="text-xs text-info-700">
            <strong>Tip:</strong> Use this barcode for inventory management, point-of-sale systems, or product tracking.
          </p>
        </div>
      </motion.div>
    </motion.div>
  );
};