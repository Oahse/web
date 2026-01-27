// =============================================================================
// MAIN HOOKS - Core functionality
// =============================================================================

// Async operations and API calls
export { useAsync, useApi, usePaginatedApi } from './useAsync';

// Authentication
export { useAuth, useAuthRedirect, useAuthenticatedAction } from './useAuth';

// Context hooks
export {
  useAuth as useAuthContext,
  useWishlist
} from './useContexts';

// Cart hook - exported directly from CartContext
export { useCart } from '../contexts/CartContext';

// =============================================================================
// SPECIALIZED HOOKS - Keep these separate
// =============================================================================

export { useAnalytics } from './useAnalytics';
export { useCategories } from './useCategories';
export { useFileUpload } from './useFileUpload';
export { useSubscription, useSubscriptionAction } from './useSubscription';
export { useWhatsAppSupport } from './useWhatsAppSupport';
export { useSkeleton } from './useSkeleton';
export { useUI } from './useUI';
export { useData } from './useData';
export { usePolling } from './usePolling';