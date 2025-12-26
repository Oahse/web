/**
 * Analytics tracking hook
 * Automatically tracks user interactions and e-commerce events
 */
import { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { AnalyticsAPI } from '../apis/analytics';

// Generate or get session ID
const getSessionId = (): string => {
  let sessionId = sessionStorage.getItem('analytics_session_id');
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('analytics_session_id', sessionId);
  }
  return sessionId;
};

export const useAnalytics = () => {
  const location = useLocation();
  const { user } = useAuth();
  const sessionId = getSessionId();

  // Track page views
  useEffect(() => {
    trackEvent('page_view', {
      page_url: location.pathname + location.search,
      page_title: document.title
    });
  }, [location]);

  const trackEvent = useCallback(async (
    eventType: string,
    data?: any,
    options?: {
      page_url?: string;
      page_title?: string;
      order_id?: string;
      product_id?: string;
      revenue?: number;
    }
  ) => {
    try {
      await AnalyticsAPI.trackEvent({
        session_id: sessionId,
        event_type: eventType,
        data: data || {},
        page_url: options?.page_url || location.pathname + location.search,
        page_title: options?.page_title || document.title,
        order_id: options?.order_id,
        product_id: options?.product_id,
        revenue: options?.revenue
      });
    } catch (error) {
      console.error('Failed to track analytics event:', error);
    }
  }, [sessionId, location]);

  // E-commerce specific tracking methods
  const trackPurchase = useCallback((orderId: string, revenue: number, items?: any[]) => {
    trackEvent('purchase', { items }, { order_id: orderId, revenue });
  }, [trackEvent]);

  const trackAddToCart = useCallback((productId: string, variantId?: string, quantity?: number, price?: number) => {
    trackEvent('cart_add', { 
      product_id: productId, 
      variant_id: variantId, 
      quantity, 
      price 
    }, { product_id: productId });
  }, [trackEvent]);

  const trackRemoveFromCart = useCallback((productId: string, variantId?: string, quantity?: number) => {
    trackEvent('cart_remove', { 
      product_id: productId, 
      variant_id: variantId, 
      quantity 
    }, { product_id: productId });
  }, [trackEvent]);

  const trackCheckoutStart = useCallback((cartValue?: number) => {
    trackEvent('checkout_start', { cart_value: cartValue });
  }, [trackEvent]);

  const trackCheckoutStep = useCallback((step: number, stepName: string, data?: any) => {
    trackEvent('checkout_step', { step, step_name: stepName, ...data });
  }, [trackEvent]);

  const trackCheckoutComplete = useCallback((orderId: string, revenue: number) => {
    trackEvent('checkout_complete', { order_id: orderId, revenue }, { order_id: orderId, revenue });
  }, [trackEvent]);

  const trackCheckoutAbandon = useCallback((step: number, stepName: string) => {
    trackEvent('checkout_abandon', { step, step_name: stepName });
  }, [trackEvent]);

  const trackRefundRequest = useCallback((orderId: string, amount: number, reason: string) => {
    trackEvent('refund_request', { order_id: orderId, amount, reason }, { order_id: orderId });
  }, [trackEvent]);

  const trackUserRegister = useCallback(() => {
    trackEvent('user_register');
  }, [trackEvent]);

  const trackUserLogin = useCallback(() => {
    trackEvent('user_login');
  }, [trackEvent]);

  return {
    trackEvent,
    trackPurchase,
    trackAddToCart,
    trackRemoveFromCart,
    trackCheckoutStart,
    trackCheckoutStep,
    trackCheckoutComplete,
    trackCheckoutAbandon,
    trackRefundRequest,
    trackUserRegister,
    trackUserLogin,
    sessionId
  };
};

export default useAnalytics;