import { useState } from 'react';
import { toast } from 'react-hot-toast';
import { uploadMultipleFiles, deleteMultipleFiles } from '../lib/github.jsx';
import { useErrorHandler } from './useErrorHandler';

const DEFAULT_MAX_SIZE_KB = 100; // 100kb limit
const DEFAULT_ALLOWED_TYPES = [
  'image/jpeg',
  'image/jpg', 
  'image/png',
  'image/webp',
  'image/gif',
  'application/pdf',
  'text/plain',
  'application/json'
];

export const useFileUpload = (options = {}) => {
  const {
    maxSizeKB = DEFAULT_MAX_SIZE_KB,
    allowedTypes = DEFAULT_ALLOWED_TYPES,
    category = 'uploads',
    showErrorToast = true,
    onSuccess,
    onError,
    onProgress
  } = options;

  const [state, setState] = useState({
    loading: false,
    progress: 0,
    error: null,
    uploadedFiles: [],
  });

  const { handleError } = useErrorHandler({
    toastType: showErrorToast ? 'always' : 'never',
    onError,
  });

  const validateFile = (file) => {
    const maxSizeBytes = maxSizeKB * 1024;
    if (file.size > maxSizeBytes) {
      return `File size must be less than ${maxSizeKB}KB. Current size: ${Math.round(file.size / 1024)}KB`;
    }

    if (!allowedTypes.includes(file.type)) {
      return `File type not allowed. Allowed types: ${allowedTypes.join(', ')}`;
    }

    return null;
  };

  const validateFiles = (files) => {
    const valid = [];
    const errors = [];

    files.forEach(file => {
      const error = validateFile(file);
      if (error) {
        errors.push(`${file.name}: ${error}`);
      } else {
        valid.push(file);
      }
    });

    return { valid, errors };
  };

  const uploadFiles = async (files) => {
    setState(prev => ({ ...prev, loading: true, progress: 0, error: null }));

    try {
      const { valid, errors } = validateFiles(files);
      
      if (errors.length > 0) {
        const errorMessage = `File validation failed:\n${errors.join('\n')}`;
        throw new Error(errorMessage);
      }

      if (valid.length === 0) {
        throw new Error('No valid files to upload');
      }

      const results = await uploadMultipleFiles(valid, category);
      
      const uploadedFiles = [];
      const uploadErrors = [];

      results.forEach((result, index) => {
        if (result.error) {
          uploadErrors.push(`${result.name}: ${result.error}`);
        } else if (result.url) {
          uploadedFiles.push({
            name: result.name,
            url: result.url,
            githubPath: result.githubPath || '',
            size: valid[index]?.size || 0,
            type: valid[index]?.type || '',
          });
        }
      });

      if (uploadErrors.length > 0) {
        const errorMessage = `Some files failed to upload:\n${uploadErrors.join('\n')}`;
        throw new Error(errorMessage);
      }

      setState({
        loading: false,
        progress: 100,
        error: null,
        uploadedFiles,
      });

      if (onSuccess) {
        onSuccess(uploadedFiles);
      }

      if (showErrorToast) {
        toast.success(`Successfully uploaded ${uploadedFiles.length} file(s)`);
      }

      return uploadedFiles;

    } catch (error) {
      const apiError = handleError(error);
      
      setState({
        loading: false,
        progress: 0,
        error: apiError,
        uploadedFiles: [],
      });

      return [];
    }
  };

  const uploadSingleFile = async (file) => {
    const results = await uploadFiles([file]);
    return results[0] || null;
  };

  const deleteFiles = async (filePaths) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const results = await deleteMultipleFiles(filePaths);
      
      const failures = results.filter(r => !r.success);
      if (failures.length > 0) {
        const errorMessage = `Failed to delete some files:\n${failures.map(f => f.filePath).join('\n')}`;
        throw new Error(errorMessage);
      }

      setState(prev => ({
        ...prev,
        loading: false,
        uploadedFiles: prev.uploadedFiles.filter(
          file => !filePaths.some(path => path.githubPath === file.githubPath)
        ),
      }));

      if (showErrorToast) {
        toast.success(`Successfully deleted ${results.length} file(s)`);
      }

      return true;

    } catch (error) {
      const apiError = handleError(error);
      
      setState(prev => ({
        ...prev,
        loading: false,
        error: apiError,
      }));

      return false;
    }
  };

  const reset = () => {
    setState({
      loading: false,
      progress: 0,
      error: null,
      uploadedFiles: [],
    });
  };

  const getFileUrl = (githubPath) => {
    const owner = import.meta.env.VITE_GITHUB_OWNER || 'your-username';
    const repo = import.meta.env.VITE_GITHUB_REPO || 'your-repo';
    const branch = import.meta.env.VITE_GITHUB_BRANCH || 'main';
    return `https://cdn.jsdelivr.net/gh/${owner}/${repo}@${branch}/${githubPath}`;
  };

  return {
    ...state,
    uploadFiles,
    uploadSingleFile,
    deleteFiles,
    reset,
    validateFile,
    validateFiles,
    getFileUrl,
    maxSizeKB,
    allowedTypes,
    category,
  };
};

export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const isImageFile = (file) => {
  return file.type.startsWith('image/');
};

export const createFilePreview = (file) => {
  return URL.createObjectURL(file);
};

export const cleanupFilePreview = (url) => {
  URL.revokeObjectURL(url);
};

export default useFileUpload;