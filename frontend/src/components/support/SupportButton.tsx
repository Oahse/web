/**
 * Floating Support Button Component
 * Quick access customer support button that appears on all pages
 */

import React, { useState } from 'react';
import { MessageCircle, X, Headphones } from 'lucide-react';
import CustomerSupport from './CustomerSupport';

interface SupportButtonProps {
  orderNumber?: string;
  productId?: string;
  issueType?: 'order' | 'payment' | 'product' | 'account' | 'general';
  position?: 'bottom-right' | 'bottom-left';
}

const SupportButton: React.FC<SupportButtonProps> = ({
  orderNumber,
  productId,
  issueType = 'general',
  position = 'bottom-right'
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const positionClasses = {
    'bottom-right': 'bottom-6 right-6',
    'bottom-left': 'bottom-6 left-6'
  };

  const openWhatsAppDirect = () => {
    const WHATSAPP_NUMBER = '+1234567890'; // Replace with actual number
    const message = encodeURIComponent(
      `Hi! I need help with my Banwee account. ${orderNumber ? `Order #: ${orderNumber}` : ''}`
    );
    const whatsappUrl = `https://wa.me/${WHATSAPP_NUMBER.replace(/[^0-9]/g, '')}?text=${message}`;
    window.open(whatsappUrl, '_blank');
  };

  return (
    <>
      {/* Floating Support Button */}
      <div className={`fixed ${positionClasses[position]} z-40`}>
        {!isOpen ? (
          <button
            onClick={() => setIsOpen(true)}
            className="bg-green-600 hover:bg-green-700 text-white rounded-full p-4 shadow-lg hover:shadow-xl transition-all duration-300 group"
            aria-label="Customer Support"
          >
            <MessageCircle className="w-6 h-6 group-hover:scale-110 transition-transform" />
            
            {/* Pulse animation */}
            <div className="absolute inset-0 rounded-full bg-green-600 animate-ping opacity-20"></div>
            
            {/* Tooltip */}
            <div className="absolute bottom-full right-0 mb-2 px-3 py-1 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
              Need Help? Chat with us!
              <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
            </div>
          </button>
        ) : (
          <button
            onClick={() => setIsOpen(false)}
            className="bg-gray-600 hover:bg-gray-700 text-white rounded-full p-4 shadow-lg hover:shadow-xl transition-all duration-300"
            aria-label="Close Support"
          >
            <X className="w-6 h-6" />
          </button>
        )}
      </div>

      {/* Quick WhatsApp Button (always visible) */}
      <div className={`fixed ${position === 'bottom-right' ? 'bottom-6 right-20' : 'bottom-6 left-20'} z-30`}>
        <button
          onClick={openWhatsAppDirect}
          className="bg-green-500 hover:bg-green-600 text-white rounded-full p-3 shadow-md hover:shadow-lg transition-all duration-300 opacity-80 hover:opacity-100"
          title="Quick WhatsApp Support"
        >
          <Headphones className="w-5 h-5" />
        </button>
      </div>

      {/* Support Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
            onClick={() => setIsOpen(false)}
          ></div>
          
          {/* Modal */}
          <div className="flex items-center justify-center min-h-screen p-4">
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
              {/* Close button */}
              <button
                onClick={() => setIsOpen(false)}
                className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 z-10"
              >
                <X className="w-6 h-6" />
              </button>
              
              {/* Support Component */}
              <CustomerSupport
                orderNumber={orderNumber}
                productId={productId}
                issueType={issueType}
                className="border-0 shadow-none"
              />
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SupportButton;