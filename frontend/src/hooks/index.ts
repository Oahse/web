// =============================================================================
// CONSOLIDATED HOOKS - Use these instead of individual ones
// =============================================================================

// Async operations, API calls, and error handling
export { 
  useAsyncOperations, 
  useOptimisticUpdate, 
  useRetry,
  // Backward compatibility
  useApi,
  useAsyncOperation,
  useErrorHandler
} from './useAsync';

// Authentication actions and redirects
export { 
  useAuthActions,
  // Backward compatibility
  useAuthRedirect,
  useAuthenticatedAction
} from './useAuth';

// UI state management (skeleton, loading, modals, forms, network)
export { 
  useNetworkStatus,
  useSkeleton,
  useMultipleSkeleton,
  useLoadingState,
  useModal,
  useFormState
} from './useUIState';

// Data management and pagination
export { 
  usePagination,
  usePaginatedData,
  usePaginatedApi
} from './useDataManagement';

// All context hooks in one place
export {
  useAuth,
  useCart,
  useWishlist,
  useSkeletonContext,
  useTheme
} from './useContexts';

// Enhanced functionality
export { useEnhancedCart } from './useEnhancedCart';
export { useEnhancedWishlist } from './useEnhancedWishlist';

// =============================================================================
// SPECIALIZED HOOKS - Keep these separate
// =============================================================================

// Keep these as they serve specific purposes
export { useAnalytics } from './useAnalytics';
export { useCategories } from './useCategories';
export { useFileUpload } from './useFileUpload';
export { useSubscriptionAction } from './useSubscriptionAction';
export { useWhatsAppSupport } from './useWhatsAppSupport';
export { useSkeleton } from './useSkeleton';