/**
 * Smart Support Widget
 * Context-aware support widget that adapts based on user's current page/action
 */

import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../../store/AuthContext';
import SupportButton from './SupportButton';

interface SupportWidgetProps {
  className?: string;
}

const SupportWidget: React.FC<SupportWidgetProps> = ({ className }) => {
  const location = useLocation();
  const { user } = useAuth();
  const [contextualSupport, setContextualSupport] = useState({
    issueType: 'general' as 'order' | 'payment' | 'product' | 'account' | 'general',
    orderNumber: undefined as string | undefined,
    productId: undefined as string | undefined
  });

  useEffect(() => {
    // Determine support context based on current page
    const path = location.pathname;
    const searchParams = new URLSearchParams(location.search);

    let issueType: 'order' | 'payment' | 'product' | 'account' | 'general' = 'general';
    let orderNumber: string | undefined;
    let productId: string | undefined;

    // Context detection based on URL
    if (path.includes('/orders') || path.includes('/checkout')) {
      issueType = 'order';
      orderNumber = searchParams.get('order') || undefined;
    } else if (path.includes('/payment') || path.includes('/billing')) {
      issueType = 'payment';
    } else if (path.includes('/products') || path.includes('/products/')) {
      issueType = 'product';
      // Extract product ID from URL
      const productMatch = path.match(/\/product\/([^\/]+)/);
      productId = productMatch ? productMatch[1] : undefined;
    } else if (path.includes('/account') || path.includes('/profile')) {
      issueType = 'account';
    }

    setContextualSupport({
      issueType,
      orderNumber,
      productId
    });
  }, [location]);

  // Don't show on certain pages where it might interfere
  const hiddenPaths = ['/login', '/register', '/admin'];
  const shouldHide = hiddenPaths.some(hiddenPath => location.pathname.includes(hiddenPath));

  if (shouldHide) {
    return null;
  }

  return (
    <div className={className}>
      <SupportButton
        orderNumber={contextualSupport.orderNumber}
        productId={contextualSupport.productId}
        issueType={contextualSupport.issueType}
      />
    </div>
  );
};

export default SupportWidget;