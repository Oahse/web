/**
 * Fast Customer Support Component
 * Redirects to WhatsApp Business with pre-filled context
 */

import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { MessageCircle, Phone, Mail, Clock, User, ShoppingBag } from 'lucide-react';
import { User as UserType } from '../../types';
import { NotificationModal } from '../ui/NotificationModal';

interface SupportOption {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  action: () => void;
  availability: string;
  responseTime: string;
}

interface CustomerSupportProps {
  orderNumber?: string;
  productId?: string;
  issueType?: 'order' | 'payment' | 'product' | 'account' | 'general';
  className?: string;
}

const CustomerSupport: React.FC<CustomerSupportProps> = ({
  orderNumber,
  productId,
  issueType = 'general',
  className = ''
}) => {
  const { user } = useAuth() as { user: UserType | null };
  const [isLoading, setIsLoading] = useState(false);
  const [showNotification, setShowNotification] = useState(false);

  // WhatsApp Business number (replace with your actual number)
  const WHATSAPP_BUSINESS_NUMBER = '+1234567890'; // Replace with actual number

  const generateWhatsAppMessage = (type: string) => {
    const userInfo = user ? {
      name: user.full_name || `${user.firstname} ${user.lastname}`,
      email: user.email,
      userId: user.id
    } : {
      name: 'Guest User',
      email: 'Not provided',
      userId: 'Guest'
    };

    const contextInfo = {
      timestamp: new Date().toLocaleString(),
      orderNumber: orderNumber || 'N/A',
      productId: productId || 'N/A',
      issueType: issueType,
      userAgent: navigator.userAgent,
      currentPage: window.location.pathname
    };

    let message = '';

    switch (type) {
      case 'urgent':
        message = `🚨 URGENT SUPPORT REQUEST 🚨

Hello! I need immediate assistance with my account.

👤 Customer Details:
• Name: ${userInfo.name}
• Email: ${userInfo.email}
• User ID: ${userInfo.userId}

📋 Issue Details:
• Type: ${issueType.toUpperCase()}
• Order #: ${contextInfo.orderNumber}
• Product ID: ${contextInfo.productId}
• Page: ${contextInfo.currentPage}
• Time: ${contextInfo.timestamp}

Please help me resolve this issue as quickly as possible. Thank you!`;
        break;

      case 'order':
        message = `📦 ORDER SUPPORT REQUEST

Hi! I need help with my order.

👤 Customer Details:
• Name: ${userInfo.name}
• Email: ${userInfo.email}

📋 Order Information:
• Order Number: ${contextInfo.orderNumber}
• Issue Type: ${issueType}
• Request Time: ${contextInfo.timestamp}

Could you please assist me with this order? Thank you!`;
        break;

      case 'general':
        message = `💬 CUSTOMER SUPPORT REQUEST

Hello! I need assistance with my account.

👤 Customer Details:
• Name: ${userInfo.name}
• Email: ${userInfo.email}

📋 Request Details:
• Issue Category: ${issueType}
• Current Page: ${contextInfo.currentPage}
• Time: ${contextInfo.timestamp}

Please help me with my inquiry. Thank you!`;
        break;

      default:
        message = `Hi! I need help with my Banwee account. My name is ${userInfo.name} and my email is ${userInfo.email}. Thank you!`;
    }

    return encodeURIComponent(message);
  };

  const openWhatsApp = (messageType: string) => {
    setIsLoading(true);
    
    try {
      const message = generateWhatsAppMessage(messageType);
      const whatsappUrl = `https://wa.me/${WHATSAPP_BUSINESS_NUMBER.replace(/[^0-9]/g, '')}?text=${message}`;
      
      // Open WhatsApp in new tab
      window.open(whatsappUrl, '_blank');
      
      // Track support request
      if (typeof (window as any).gtag !== 'undefined') {
        (window as any).gtag('event', 'customer_support_request', {
          method: 'whatsapp',
          message_type: messageType,
          user_id: user?.id || 'guest',
          issue_type: issueType
        });
      }
    } catch (error) {
      console.error('Error opening WhatsApp:', error);
      // Fallback to copying message to clipboard
      const message = decodeURIComponent(generateWhatsAppMessage(messageType));
      navigator.clipboard.writeText(message).then(() => {
        setShowNotification(true);
      });
    } finally {
      setIsLoading(false);
    }
  };

  const supportOptions: SupportOption[] = [
    {
      id: 'whatsapp-urgent',
      title: 'Urgent Support',
      description: 'Get immediate help via WhatsApp',
      icon: <MessageCircle className="w-6 h-6 text-green-600" />,
      action: () => openWhatsApp('urgent'),
      availability: '24/7',
      responseTime: '< 2 minutes'
    },
    {
      id: 'whatsapp-order',
      title: 'Order Help',
      description: 'Questions about your orders',
      icon: <ShoppingBag className="w-6 h-6 text-blue-600" />,
      action: () => openWhatsApp('order'),
      availability: '9 AM - 9 PM',
      responseTime: '< 5 minutes'
    },
    {
      id: 'whatsapp-general',
      title: 'General Support',
      description: 'Account & general inquiries',
      icon: <User className="w-6 h-6 text-purple-600" />,
      action: () => openWhatsApp('general'),
      availability: '9 AM - 6 PM',
      responseTime: '< 10 minutes'
    }
  ];

  return (
    <div className={`bg-surface rounded-lg shadow-lg p-6 ${className}`}>
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-copy mb-2">
          Need Help? We're Here! 🚀
        </h2>
        <p className="text-copy-light">
          Get instant support via WhatsApp with our customer service team
        </p>
      </div>

      <div className="space-y-4">
        {supportOptions.map((option) => (
          <div
            key={option.id}
            className="border border-border rounded-lg p-4 hover:border-primary hover:shadow-md transition-all cursor-pointer"
            onClick={option.action}
          >
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                {/* Icons will be updated manually if necessary based on their colors */}
                {option.id === 'whatsapp-urgent' && <MessageCircle className="w-6 h-6 text-primary" />}
                {option.id === 'whatsapp-order' && <ShoppingBag className="w-6 h-6 text-info" />}
                {option.id === 'whatsapp-general' && <User className="w-6 h-6 text-secondary" />}
              </div>
              
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-lg font-semibold text-copy">
                    {option.title}
                  </h3>
                  <span className="text-sm text-primary font-medium">
                    {option.responseTime}
                  </span>
                </div>
                
                <p className="text-copy-light mb-2">
                  {option.description}
                </p>
                
                <div className="flex items-center space-x-4 text-sm text-copy-muted">
                  <div className="flex items-center space-x-1">
                    <Clock className="w-4 h-4" />
                    <span>{option.availability}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="mt-6 pt-6 border-t border-border">
        <h3 className="text-lg font-semibold text-copy mb-3">
          Quick Actions
        </h3>
        
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => openWhatsApp('urgent')}
            disabled={isLoading}
            className="flex items-center justify-center space-x-2 bg-primary text-copy-inverse px-4 py-3 rounded-lg hover:bg-primary-dark transition-colors disabled:opacity-50"
          >
            <MessageCircle className="w-5 h-5" />
            <span>Chat Now</span>
          </button>
          
          <button
            onClick={() => window.open(`tel:${WHATSAPP_BUSINESS_NUMBER}`, '_self')}
            className="flex items-center justify-center space-x-2 bg-info text-copy-inverse px-4 py-3 rounded-lg hover:bg-info-dark transition-colors"
          >
            <Phone className="w-5 h-5" />
            <span>Call Us</span>
          </button>
        </div>
      </div>

      {/* Support Info */}
      <div className="mt-6 p-4 bg-background rounded-lg">
        <h4 className="font-semibold text-copy mb-2">
          💡 For Faster Support:
        </h4>
        <ul className="text-sm text-copy-light space-y-1">
          <li>• Have your order number ready</li>
          <li>• Describe your issue clearly</li>
          <li>• Include screenshots if helpful</li>
          <li>• Check our FAQ first for quick answers</li>
        </ul>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-surface rounded-lg p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-copy-light">Opening WhatsApp...</p>
          </div>
        </div>
      )}

      {/* Notification Modal */}
      <NotificationModal
        isOpen={showNotification}
        onClose={() => setShowNotification(false)}
        title="Message Copied"
        message="Message copied to clipboard! Please paste it in WhatsApp."
        variant="success"
        autoClose={true}
        autoCloseDelay={3000}
      />
    </div>
  );
};

export default CustomerSupport;