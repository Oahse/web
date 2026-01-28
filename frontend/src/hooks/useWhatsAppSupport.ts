/**
 * WhatsApp Support Hook
 * Manages WhatsApp Business integration for customer support
 */

import { useCallback } from 'react';
import { useAuth } from '../store/AuthContext';
import { User } from '../types';

interface WhatsAppConfig {
  businessNumber: string;
  businessName: string;
  defaultMessage: string;
}

interface SupportContext {
  orderNumber?: string;
  productId?: string;
  issueType?: 'order' | 'payment' | 'product' | 'account' | 'general' | 'urgent';
  customMessage?: string;
}

interface NotificationData {
  title: string;
  message: string;
  variant: 'success' | 'info' | 'warning';
}

interface WhatsAppResult {
  success: boolean;
  notification?: NotificationData;
}

const useWhatsAppSupport = () => {
  const { user } = useAuth() as { user: User | null };

  // WhatsApp Business Configuration
  const config: WhatsAppConfig = {
    businessNumber: '+1234567890', // Replace with actual WhatsApp Business number
    businessName: 'Banwee Support',
    defaultMessage: 'Hi! I need help with my Banwee account.'
  };

  const generateSupportMessage = useCallback((context: SupportContext = {}) => {
    const {
      orderNumber,
      productId,
      issueType = 'general',
      customMessage
    } = context;

    // User information
    const userInfo = user ? {
      name: user.full_name || `${user.firstname} ${user.lastname}`,
      email: user.email,
      userId: user.id
    } : {
      name: 'Guest User',
      email: 'Not provided',
      userId: 'Guest'
    };

    // Context information
    const contextInfo = {
      timestamp: new Date().toLocaleString(),
      orderNumber: orderNumber || 'N/A',
      productId: productId || 'N/A',
      issueType: issueType.toUpperCase(),
      currentPage: window.location.pathname,
      userAgent: navigator.userAgent.split(' ')[0] // Simplified user agent
    };

    // Custom message takes priority
    if (customMessage) {
      return `${customMessage}

👤 Customer: ${userInfo.name}
📧 Email: ${userInfo.email}
🕒 Time: ${contextInfo.timestamp}`;
    }

    // Generate message based on issue type
    let message = '';

    switch (issueType) {
      case 'urgent':
        message = `🚨 URGENT SUPPORT NEEDED 🚨

Hello ${config.businessName} team! I need immediate assistance.

👤 Customer Details:
• Name: ${userInfo.name}
• Email: ${userInfo.email}
• User ID: ${userInfo.userId}

🔥 URGENT Issue:
• Type: ${contextInfo.issueType}
• Order #: ${contextInfo.orderNumber}
• Product: ${contextInfo.productId}
• Page: ${contextInfo.currentPage}
• Time: ${contextInfo.timestamp}

This is urgent - please help ASAP! 🙏`;
        break;

      case 'order':
        message = `📦 ORDER SUPPORT REQUEST

Hi! I need help with my order.

👤 Customer Info:
• Name: ${userInfo.name}
• Email: ${userInfo.email}

📋 Order Details:
• Order Number: ${contextInfo.orderNumber}
• Issue: Order-related inquiry
• Time: ${contextInfo.timestamp}

Could you please help me with this order? Thank you! 😊`;
        break;

      case 'payment':
        message = `💳 PAYMENT SUPPORT REQUEST

Hello! I'm having issues with payment.

👤 Customer Info:
• Name: ${userInfo.name}
• Email: ${userInfo.email}

💰 Payment Issue:
• Order #: ${contextInfo.orderNumber}
• Issue Type: Payment/Billing
• Time: ${contextInfo.timestamp}

Please help me resolve this payment issue. Thanks!`;
        break;

      case 'product':
        message = `🛍️ PRODUCT INQUIRY

Hi! I have a question about a product.

👤 Customer Info:
• Name: ${userInfo.name}
• Email: ${userInfo.email}

🔍 Product Details:
• Product ID: ${contextInfo.productId}
• Page: ${contextInfo.currentPage}
• Time: ${contextInfo.timestamp}

Could you help me with this product? Thank you!`;
        break;

      case 'account':
        message = `👤 ACCOUNT SUPPORT REQUEST

Hello! I need help with my account.

👤 Customer Info:
• Name: ${userInfo.name}
• Email: ${userInfo.email}
• User ID: ${userInfo.userId}

🔧 Account Issue:
• Issue Type: Account/Profile
• Time: ${contextInfo.timestamp}

Please assist me with my account. Thank you!`;
        break;

      default:
        message = `💬 GENERAL SUPPORT REQUEST

Hi ${config.businessName}! I need some help.

👤 Customer Info:
• Name: ${userInfo.name}
• Email: ${userInfo.email}

📋 Request Details:
• Time: ${contextInfo.timestamp}
• Page: ${contextInfo.currentPage}

${config.defaultMessage} Thank you for your help! 😊`;
    }

    return message;
  }, [user, config]);

  const openWhatsApp = useCallback((context: SupportContext = {}) => {
    try {
      const message = generateSupportMessage(context);
      const encodedMessage = encodeURIComponent(message);
      const cleanNumber = config.businessNumber.replace(/[^0-9]/g, '');
      const whatsappUrl = `https://wa.me/${cleanNumber}?text=${encodedMessage}`;

      // Open WhatsApp in new tab
      const newWindow = window.open(whatsappUrl, '_blank');
      
      // Fallback if popup blocked
      if (!newWindow || newWindow.closed || typeof newWindow.closed === 'undefined') {
        // Copy message to clipboard as fallback
        navigator.clipboard.writeText(message).then(() => {
          // Return notification data instead of showing alert
          return {
            success: true,
            notification: {
              title: 'Message Copied',
              message: `WhatsApp couldn't open automatically. Message copied to clipboard!\n\nPlease paste it in WhatsApp: ${config.businessNumber}`,
              variant: 'info' as const
            }
          };
        }).catch(() => {
          // Return notification data for final fallback
          return {
            success: false,
            notification: {
              title: 'Manual Action Required',
              message: `Please send this message to ${config.businessNumber} on WhatsApp:\n\n${message}`,
              variant: 'warning' as const
            }
          };
        });
      }

      // Track support request
      if (typeof (window as any).gtag !== 'undefined') {
        (window as any).gtag('event', 'whatsapp_support_request', {
          event_category: 'customer_support',
          event_label: context.issueType || 'general',
          custom_parameters: {
            user_id: user?.id || 'guest',
            issue_type: context.issueType,
            has_order: !!context.orderNumber,
            has_product: !!context.productId
          }
        });
      }

      return { success: true };
    } catch (error) {
      console.error('Error opening WhatsApp:', error);
      
      // Return notification data for error handling
      const fallbackMessage = generateSupportMessage(context);
      return {
        success: false,
        notification: {
          title: 'Error Opening WhatsApp',
          message: `Error opening WhatsApp. Please contact us at ${config.businessNumber} with this message:\n\n${fallbackMessage}`,
          variant: 'warning' as const
        }
      };
    }
  }, [generateSupportMessage, config, user]);

  const copyMessageToClipboard = useCallback(async (context: SupportContext = {}) => {
    try {
      const message = generateSupportMessage(context);
      await navigator.clipboard.writeText(message);
      return { success: true, message };
    } catch (error) {
      console.error('Error copying to clipboard:', error);
      return { success: false, message: generateSupportMessage(context) };
    }
  }, [generateSupportMessage]);

  const getWhatsAppUrl = useCallback((context: SupportContext = {}) => {
    const message = generateSupportMessage(context);
    const encodedMessage = encodeURIComponent(message);
    const cleanNumber = config.businessNumber.replace(/[^0-9]/g, '');
    return `https://wa.me/${cleanNumber}?text=${encodedMessage}`;
  }, [generateSupportMessage, config]);

  const isWhatsAppAvailable = useCallback(() => {
    // Check if WhatsApp is likely available (mobile device or WhatsApp Web)
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const hasWhatsAppWeb = 'serviceWorker' in navigator; // Proxy for modern browser
    
    return isMobile || hasWhatsAppWeb;
  }, []);

  return {
    openWhatsApp,
    generateSupportMessage,
    copyMessageToClipboard,
    getWhatsAppUrl,
    isWhatsAppAvailable,
    config
  };
};

export default useWhatsAppSupport;