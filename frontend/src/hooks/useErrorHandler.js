import { toast } from 'react-hot-toast';

export const useErrorHandler = (options = {}) => {
  const {
    toastType = 'always',
    logError = true,
    fallbackMessage = 'An unexpected error occurred',
    onError
  } = options;

  const handleError = (error) => {
    let apiError;

    if (error?.error && error?.message) {
      apiError = error;
    } else if (error?.response?.data) {
      apiError = {
        error: true,
        message: error.response.data.message || error.response.data.detail || fallbackMessage,
        details: error.response.data.details,
        status: error.response.status,
        timestamp: error.response.data.timestamp,
        path: error.response.data.path,
      };
    } else if (error?.message) {
      apiError = {
        error: true,
        message: error.message,
        status: 500,
      };
    } else {
      apiError = {
        error: true,
        message: fallbackMessage,
        status: 500,
      };
    }

    if (logError) {
      console.error('Error handled:', {
        message: apiError.message,
        status: apiError.status,
        details: apiError.details,
        timestamp: apiError.timestamp,
        path: apiError.path,
        originalError: error,
      });
    }

    if (toastType === 'always' || (toastType === 'mutation' && apiError.error)) {
      const message = getErrorMessage(apiError);
      toast.error(message);
    }

    if (onError) {
      onError(apiError);
    }

    return apiError;
  }

  return { handleError };
};

const getErrorMessage = (error) => {
  const status = error.status;
  const message = error.message;

  switch (status) {
    case 400:
      if (error.details && Array.isArray(error.details)) {
        const validationErrors = error.details;
        if (validationErrors.length === 1) {
          return validationErrors[0].message;
        } else if (validationErrors.length > 1) {
          return `Please check: ${validationErrors.map(e => e.field).join(', ')}`;
        }
      }
      return message || 'Invalid request. Please check your input.';
    
    case 401:
      return 'Please log in to continue.';
    
    case 403:
      return 'You don\'t have permission to perform this action.';
    
    case 404:
      return 'The requested resource was not found.';
    
    case 409:
      return message || 'This action conflicts with existing data.';
    
    case 422:
      if (error.details && Array.isArray(error.details)) {
        const validationErrors = error.details;
        if (validationErrors.length === 1) {
          return validationErrors[0].message;
        }
      }
      return message || 'Please check your input and try again.';
    
    case 429:
      return 'Too many requests. Please wait a moment and try again.';
    
    case 500:
      return 'Server error. Please try again later.';
    
    case 502:
    case 503:
    case 504:
      return 'Service temporarily unavailable. Please try again later.';
    
    default:
      if (status && status >= 500) {
        return 'Server error. Please try again later.';
      }
      return message || 'An unexpected error occurred.';
  }
};

export const useAsyncError = (options = {}) => {
  const { handleError } = useErrorHandler(options);

  const executeAsync = async (asyncFn) => {
    try {
      return await asyncFn();
    } catch (error) {
      handleError(error);
    }
  };

  return { executeAsync, handleError };
};

export const useFormErrorHandler = () => {
  const { handleError } = useErrorHandler();

  const handleFormError = (error, setFieldError) => {
    if (error?.details && Array.isArray(error.details) && setFieldError) {
      error.details.forEach((validationError) => {
        setFieldError(validationError.field, validationError.message);
      });
    } else {
      handleError(error);
    }
  };

  return { handleFormError };
};

export default useErrorHandler;