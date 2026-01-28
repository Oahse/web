import { useState, useEffect, useCallback } from 'react';
import ShippingAPI, { ShippingMethod } from '../api/shipping';
import { toast } from 'react-hot-toast';

interface UseShippingOptions {
  autoLoad?: boolean;
  onError?: (error: any) => void;
}

export const useShipping = (options: UseShippingOptions = {}) => {
  const { autoLoad = true, onError } = options;
  
  const [shippingMethods, setShippingMethods] = useState<ShippingMethod[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadShippingMethods = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const methods = await ShippingAPI.getShippingMethods();
      
      // Sort by price (cheapest first)
      const sortedMethods = methods.sort((a, b) => a.price - b.price);
      
      setShippingMethods(sortedMethods);
      
      return sortedMethods;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to load shipping methods';
      setError(errorMessage);
      
      if (onError) {
        onError(err);
      } else {
        toast.error(errorMessage);
      }
      
      return [];
    } finally {
      setLoading(false);
    }
  }, [onError]);

  const calculateShippingCost = useCallback(async (
    orderAmount: number,
    shippingMethodId?: string
  ) => {
    try {
      const result = await ShippingAPI.calculateShippingCost(orderAmount, shippingMethodId);
      return result;
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to calculate shipping cost';
      setError(errorMessage);
      toast.error(errorMessage);
      throw err;
    }
  }, []);

  const getShippingMethod = useCallback((methodId: string) => {
    return shippingMethods.find(method => method.id === methodId);
  }, [shippingMethods]);

  const getCheapestMethod = useCallback(() => {
    return shippingMethods.length > 0 ? shippingMethods[0] : null;
  }, [shippingMethods]);

  const getAvailableMethods = useCallback(() => {
    return shippingMethods.filter(method => method.is_active);
  }, [shippingMethods]);

  // Auto-load shipping methods on mount if enabled
  useEffect(() => {
    if (autoLoad) {
      loadShippingMethods();
    }
  }, [autoLoad, loadShippingMethods]);

  return {
    shippingMethods,
    loading,
    error,
    loadShippingMethods,
    calculateShippingCost,
    getShippingMethod,
    getCheapestMethod,
    getAvailableMethods,
    refresh: loadShippingMethods
  };
};

export default useShipping;