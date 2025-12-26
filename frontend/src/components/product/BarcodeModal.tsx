import React from 'react';
import { motion } from 'framer-motion';
import { XIcon } from 'lucide-react';
import { BarcodeDisplay } from './BarcodeDisplay';
import { ProductVariant } from '../../types';

interface BarcodeModalProps {
  variant: ProductVariant;
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  canGenerate?: boolean;
  className?: string;
}

export const BarcodeModal: React.FC<BarcodeModalProps> = ({
  variant,
  isOpen,
  onClose,
  title = 'Product Barcode & QR Code',
  canGenerate = false,
  className = '',
}) => {
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
        className={`bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto ${className}`}
        onClick={(e: React.MouseEvent) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold text-gray-900">{title}</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-md hover:bg-gray-100"
            aria-label="Close modal"
          >
            <XIcon size={24} />
          </button>
        </div>

        {/* BarcodeDisplay Component */}
        <div className="mb-6">
          <BarcodeDisplay
            variant={variant}
            showBoth={true}
            size="lg"
            canGenerate={canGenerate}
          />
        </div>

        {/* Additional Information */}
        <div className="border-t pt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Product Information</h4>
              <div className="space-y-1 text-gray-600">
                <p><span className="font-medium">Product:</span> {variant.product_name || 'N/A'}</p>
                <p><span className="font-medium">Variant:</span> {variant.name}</p>
                <p><span className="font-medium">SKU:</span> {variant.sku}</p>
              </div>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Pricing & Stock</h4>
              <div className="space-y-1 text-gray-600">
                <p><span className="font-medium">Price:</span> ${variant.sale_price || variant.base_price}</p>
                {variant.sale_price && (
                  <p><span className="font-medium">Original:</span> <span className="line-through">${variant.base_price}</span></p>
                )}
                <p><span className="font-medium">Stock:</span> {variant.stock} units</p>
              </div>
            </div>
          </div>
        </div>

        {/* Usage Tips */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">Usage Tips</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Use the barcode for inventory management and point-of-sale systems</li>
            <li>• Share the QR code for quick product access and mobile scanning</li>
            <li>• Download codes for printing on labels or packaging</li>
            <li>• Both codes contain the same product information for consistency</li>
          </ul>
        </div>
      </motion.div>
    </motion.div>
  );
};